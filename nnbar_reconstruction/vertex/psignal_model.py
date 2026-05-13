"""
P-Signal Classifier Models for NNBAR.

Predicts the probability that a track candidate originates from the signal
(annihilation) vertex versus being a Compton scatter or background track.

Two model architectures:
1. PointNetMini - Fast, simple, works well for mostly-linear tracks
2. TrackGNN - GNN with EdgeConv layers, captures local geometry

Adapted from HIBEAM vertex finding pipeline.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

# Optional torch_geometric for GNN
try:
    from torch_geometric.nn import MessagePassing, global_max_pool
    from torch_geometric.data import Data, Batch
    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False


# ============================================================================
# PointNet Model
# ============================================================================

class PointNetMini(nn.Module):
    """
    PointNet-style classifier for track point clouds.

    Architecture:
        Per-point MLP: 3 -> hidden -> hidden -> emb
        Global max pooling
        Classification head: emb -> emb -> 1

    Input: (B, N, 3) point coordinates, (B, N) boolean mask
    Output: (B,) logits for p_signal
    """

    def __init__(self, hidden: int = 64, emb: int = 128, dropout: float = 0.1):
        super().__init__()

        # Per-point feature extraction
        self.point_mlp = nn.Sequential(
            nn.Linear(3, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, emb),
            nn.ReLU(),
        )

        # Classification head
        self.head = nn.Sequential(
            nn.Linear(emb, emb),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(emb, 1),
        )

    def forward(self, X: torch.Tensor, M: torch.Tensor) -> torch.Tensor:
        """
        Args:
            X: (B, N, 3) point coordinates
            M: (B, N) boolean mask

        Returns:
            logits: (B,) classification logits
        """
        # Per-point features
        h = self.point_mlp(X)  # (B, N, emb)

        # Masked max pooling
        neg_inf = torch.finfo(h.dtype).min
        mask = M.unsqueeze(-1)  # (B, N, 1)
        h_masked = torch.where(mask, h, neg_inf)
        g = torch.amax(h_masked, dim=1)  # (B, emb)

        # Classification
        logits = self.head(g).squeeze(-1)  # (B,)
        return logits


# ============================================================================
# GNN Model
# ============================================================================

if HAS_TORCH_GEOMETRIC:

    class EdgeConvLayer(MessagePassing):
        """
        EdgeConv layer from DGCNN paper.

        Aggregates edge features: h_ij = MLP([h_i, h_j - h_i])
        """

        def __init__(self, in_dim: int, out_dim: int):
            super().__init__(aggr='max')
            self.mlp = nn.Sequential(
                nn.Linear(in_dim * 2, out_dim),
                nn.ReLU(),
                nn.Linear(out_dim, out_dim),
            )

        def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
            return self.propagate(edge_index, x=x)

        def message(self, x_i: torch.Tensor, x_j: torch.Tensor) -> torch.Tensor:
            # x_i: target node features, x_j: source node features
            edge_feat = torch.cat([x_i, x_j - x_i], dim=-1)
            return self.mlp(edge_feat)


    class TrackGNN(nn.Module):
        """
        GNN-based track classifier using EdgeConv layers.

        Architecture:
            1. Initial embedding (3 -> hidden)
            2. EdgeConv layers (message passing)
            3. Global max pooling
            4. Classification head

        Better for tracks with curvature or multiple scattering.
        """

        def __init__(
            self,
            hidden: int = 64,
            emb: int = 128,
            n_layers: int = 3,
            dropout: float = 0.1,
        ):
            super().__init__()

            # Initial embedding
            self.embed = nn.Linear(3, hidden)

            # EdgeConv layers
            self.convs = nn.ModuleList()
            for i in range(n_layers):
                in_dim = hidden if i == 0 else emb
                self.convs.append(EdgeConvLayer(in_dim, emb))

            # Classification head
            self.head = nn.Sequential(
                nn.Linear(emb, emb),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(emb, 1),
            )

        def forward(self, data) -> torch.Tensor:
            """
            Args:
                data: PyG Data object with x, edge_index, batch

            Returns:
                logits: (B,) classification logits
            """
            x = F.relu(self.embed(data.x))

            for conv in self.convs:
                x = F.relu(conv(x, data.edge_index))

            # Global pooling
            g = global_max_pool(x, data.batch)

            # Classification
            logits = self.head(g).squeeze(-1)
            return logits

else:
    # Placeholder if torch_geometric not available
    class EdgeConvLayer:
        pass

    class TrackGNN:
        def __init__(self, *args, **kwargs):
            raise ImportError("TrackGNN requires torch_geometric. Install with: pip install torch_geometric")


# ============================================================================
# Data Utilities
# ============================================================================

def normalize_hits(H: np.ndarray, mode: str = "center_rms") -> np.ndarray:
    """
    Normalize hit coordinates to zero-centered, unit RMS.

    Args:
        H: (N, 3) hit coordinates
        mode: Normalization mode ('center_rms' or 'center')

    Returns:
        Normalized hit coordinates (N, 3)
    """
    if H.size == 0:
        return H

    # Center
    C = H.mean(axis=0, keepdims=True)
    X = H - C

    # Scale
    if mode == "center_rms":
        rms = np.sqrt((X ** 2).sum(axis=1).mean())
        s = rms if np.isfinite(rms) and rms > 1e-6 else 1.0
        return (X / s).astype(np.float32)

    return X.astype(np.float32)


def build_knn_graph(H: np.ndarray, k: int = 8) -> np.ndarray:
    """
    Build k-NN edge index from point cloud.

    Args:
        H: (N, 3) point coordinates
        k: Number of neighbors

    Returns:
        edge_index: (2, E) edge indices
    """
    from sklearn.neighbors import NearestNeighbors

    n = H.shape[0]
    k_actual = min(k, n - 1)
    if k_actual < 1:
        return np.zeros((2, 0), dtype=np.int64)

    nbrs = NearestNeighbors(n_neighbors=k_actual + 1).fit(H)
    _, indices = nbrs.kneighbors(H)

    # Build edge list (excluding self-loops)
    src, dst = [], []
    for i in range(n):
        for j in indices[i, 1:]:  # Skip self (index 0)
            src.append(i)
            dst.append(j)

    return np.array([src, dst], dtype=np.int64)


# ============================================================================
# P-Signal Predictor (for inference)
# ============================================================================

@dataclass
class PSignalConfig:
    """Configuration for P-Signal model."""
    model_type: str = "pointnet"  # 'pointnet' or 'gnn'
    hidden: int = 64
    emb: int = 128
    n_layers: int = 3  # GNN only
    k_neighbors: int = 8  # GNN only
    dropout: float = 0.1


class PSignalPredictor:
    """
    P-Signal classifier for track signal probability prediction.

    Usage:
        predictor = PSignalPredictor.from_checkpoint("model.ckpt")
        probs = predictor.predict(tracks)
    """

    def __init__(
        self,
        model: nn.Module,
        config: PSignalConfig,
        device: torch.device = None,
    ):
        self.model = model
        self.config = config
        self.device = device or torch.device("cpu")
        self.model.to(self.device)
        self.model.eval()

    @classmethod
    def from_checkpoint(cls, ckpt_path: str, device: torch.device = None):
        """
        Load P-Signal model from checkpoint.

        Args:
            ckpt_path: Path to checkpoint file
            device: Target device

        Returns:
            PSignalPredictor instance
        """
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        ckpt = torch.load(ckpt_path, map_location=device)

        # Extract config
        config = PSignalConfig(
            model_type=ckpt.get("model_type", "pointnet"),
            hidden=ckpt.get("hidden", 64),
            emb=ckpt.get("emb", 128),
            n_layers=ckpt.get("n_layers", 3),
            k_neighbors=ckpt.get("k_neighbors", 8),
        )

        # Create model
        if config.model_type == "gnn":
            if not HAS_TORCH_GEOMETRIC:
                raise ImportError("GNN model requires torch_geometric")
            model = TrackGNN(
                hidden=config.hidden,
                emb=config.emb,
                n_layers=config.n_layers,
                dropout=config.dropout,
            )
        else:
            model = PointNetMini(
                hidden=config.hidden,
                emb=config.emb,
                dropout=config.dropout,
            )

        # Load weights
        model.load_state_dict(ckpt["model"])

        return cls(model, config, device)

    @torch.no_grad()
    def predict_single(self, hits: np.ndarray) -> float:
        """
        Predict p_signal for a single track.

        Args:
            hits: (N, 3) hit coordinates

        Returns:
            p_signal probability in [0, 1]
        """
        if hits.shape[0] < 2:
            return 0.0

        # Normalize
        hits_norm = normalize_hits(hits, "center_rms")

        if self.config.model_type == "gnn":
            if not HAS_TORCH_GEOMETRIC:
                raise ImportError("GNN model requires torch_geometric")

            # Build graph
            edge_index = build_knn_graph(hits_norm, k=self.config.k_neighbors)
            data = Data(
                x=torch.from_numpy(hits_norm).to(self.device),
                edge_index=torch.from_numpy(edge_index).to(self.device),
                batch=torch.zeros(len(hits_norm), dtype=torch.long, device=self.device),
            )

            logit = self.model(data)
        else:
            # PointNet
            X = torch.from_numpy(hits_norm).unsqueeze(0).to(self.device)  # (1, N, 3)
            M = torch.ones(1, len(hits_norm), dtype=torch.bool, device=self.device)

            logit = self.model(X, M)

        prob = torch.sigmoid(logit).item()
        return prob

    @torch.no_grad()
    def predict_batch(
        self,
        hits_list: List[np.ndarray],
        batch_size: int = 64,
    ) -> List[float]:
        """
        Predict p_signal for multiple tracks.

        Args:
            hits_list: List of (N, 3) hit arrays
            batch_size: Batch size for inference

        Returns:
            List of p_signal probabilities
        """
        # Normalize all hits
        normalized = []
        valid_indices = []
        for i, hits in enumerate(hits_list):
            if hits.shape[0] >= 2:
                normalized.append(normalize_hits(hits, "center_rms"))
                valid_indices.append(i)
            else:
                normalized.append(None)

        # Initialize results
        probs = [0.0] * len(hits_list)

        # Batch prediction
        valid_hits = [h for h in normalized if h is not None]

        if len(valid_hits) == 0:
            return probs

        if self.config.model_type == "gnn":
            batch_probs = self._predict_gnn_batch(valid_hits, batch_size)
        else:
            batch_probs = self._predict_pointnet_batch(valid_hits, batch_size)

        # Map back to original indices
        for idx, prob in zip(valid_indices, batch_probs):
            probs[idx] = prob

        return probs

    def _predict_pointnet_batch(
        self,
        hits_list: List[np.ndarray],
        batch_size: int,
    ) -> List[float]:
        """Batch prediction for PointNet."""
        probs = []

        for i in range(0, len(hits_list), batch_size):
            batch_hits = hits_list[i:i + batch_size]

            # Pad to max length
            lens = [H.shape[0] for H in batch_hits]
            Nmax = max(lens)
            B = len(batch_hits)

            X = torch.zeros(B, Nmax, 3, dtype=torch.float32)
            M = torch.zeros(B, Nmax, dtype=torch.bool)

            for j, H in enumerate(batch_hits):
                n = H.shape[0]
                X[j, :n] = torch.from_numpy(H)
                M[j, :n] = True

            X = X.to(self.device)
            M = M.to(self.device)

            logits = self.model(X, M)
            batch_probs = torch.sigmoid(logits).cpu().numpy()
            probs.extend(batch_probs)

        return probs

    def _predict_gnn_batch(
        self,
        hits_list: List[np.ndarray],
        batch_size: int,
    ) -> List[float]:
        """Batch prediction for GNN."""
        if not HAS_TORCH_GEOMETRIC:
            raise ImportError("GNN model requires torch_geometric")

        probs = []

        for i in range(0, len(hits_list), batch_size):
            batch_hits = hits_list[i:i + batch_size]

            # Build graphs
            data_list = []
            for H in batch_hits:
                edge_index = build_knn_graph(H, k=self.config.k_neighbors)
                data = Data(
                    x=torch.from_numpy(H),
                    edge_index=torch.from_numpy(edge_index),
                )
                data_list.append(data)

            batched = Batch.from_data_list(data_list).to(self.device)

            logits = self.model(batched)
            batch_probs = torch.sigmoid(logits).cpu().numpy()
            probs.extend(batch_probs)

        return probs


# ============================================================================
# Heuristic P-Signal (fallback when no model available)
# ============================================================================

def heuristic_psignal(
    track_hits: np.ndarray,
    vertex_estimate: Optional[np.ndarray] = None,
    target_z: float = 0.0,
) -> float:
    """
    Heuristic p_signal estimation based on track geometry.

    Signal tracks:
    - Originate from target foil (z ~ 0)
    - Point radially outward
    - Have consistent direction toward calorimeter

    Compton/background tracks:
    - Originate from cathode or elsewhere
    - May have scattered directions

    Args:
        track_hits: (N, 3) hit coordinates
        vertex_estimate: Estimated vertex position (optional)
        target_z: Z position of target foil (default 0)

    Returns:
        Estimated p_signal in [0, 1]
    """
    if len(track_hits) < 3:
        return 0.0

    # PCA for track direction
    centroid = track_hits.mean(axis=0)
    centered = track_hits - centroid

    # SVD for principal components
    _, s, vh = np.linalg.svd(centered, full_matrices=False)

    # Track direction (first principal component)
    direction = vh[0]

    # Ensure direction points outward (positive radial)
    r_centroid = np.sqrt(centroid[0]**2 + centroid[1]**2)
    radial_unit = np.array([centroid[0], centroid[1], 0]) / (r_centroid + 1e-6)

    if np.dot(direction[:2], radial_unit[:2]) < 0:
        direction = -direction

    # Find track endpoints (head and tail)
    projections = centered @ direction
    head_idx = np.argmax(projections)
    tail_idx = np.argmin(projections)

    head = track_hits[head_idx]
    tail = track_hits[tail_idx]

    # Inner point (closer to center)
    if np.sqrt(head[0]**2 + head[1]**2) < np.sqrt(tail[0]**2 + tail[1]**2):
        inner = head
    else:
        inner = tail

    # Feature 1: Inner point radial distance (signal tracks start from center)
    r_inner = np.sqrt(inner[0]**2 + inner[1]**2)
    # Signal: r_inner < 30 cm (near target)
    f1 = np.exp(-r_inner / 30.0)  # Decays with distance from center

    # Feature 2: Extrapolation to z=0
    # Project track backward to z=target_z
    if abs(direction[2]) > 1e-6:
        t_to_target = (target_z - inner[2]) / direction[2]
        projected = inner + t_to_target * direction
        r_projected = np.sqrt(projected[0]**2 + projected[1]**2)

        # Signal tracks extrapolate to small r at z=0
        f2 = np.exp(-r_projected / 20.0)
    else:
        # Track is parallel to z=0 plane
        f2 = 0.3 if abs(inner[2] - target_z) < 50 else 0.1

    # Feature 3: Track linearity (signal tracks are straighter)
    linearity = s[0] / (s.sum() + 1e-6)  # Fraction of variance in first PC
    f3 = linearity

    # Feature 4: Track length (signal tracks typically longer)
    length = np.linalg.norm(head - tail)
    f4 = min(1.0, length / 50.0)  # Saturates at 50 cm

    # Combine features (weighted average)
    p_signal = 0.4 * f1 + 0.3 * f2 + 0.2 * f3 + 0.1 * f4

    # Clamp to [0, 1]
    p_signal = np.clip(p_signal, 0.0, 1.0)

    return float(p_signal)


# ============================================================================
# Track Feature Extraction (for GNN vertex model)
# ============================================================================

def extract_track_features(
    track_hits: np.ndarray,
    vertex: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Extract features from a track for vertex GNN input.

    Returns 12 features as used by the vertex GNN model.

    Args:
        track_hits: (N, 3) hit coordinates
        vertex: Current vertex estimate (optional)

    Returns:
        features: (12,) feature vector
    """
    if len(track_hits) < 2:
        return np.zeros(12, dtype=np.float32)

    # Spatial extent
    dx = track_hits[:, 0].max() - track_hits[:, 0].min()
    dy = track_hits[:, 1].max() - track_hits[:, 1].min()
    dz = track_hits[:, 2].max() - track_hits[:, 2].min()

    # PCA for shape analysis
    centroid = track_hits.mean(axis=0)
    centered = track_hits - centroid

    cov = (centered.T @ centered) / (len(track_hits) - 1 + 1e-6)
    eigvals = np.linalg.eigvalsh(cov)
    eigvals = np.sort(eigvals)[::-1]  # Descending order
    w1, w2, w3 = eigvals[0], eigvals[1], eigvals[2]
    eps = 1e-6

    # Shape features from eigenvalues
    elongation_1 = (w1 - w2) / (w1 + eps)
    elongation_2 = (w2 - w3) / (w1 + eps)
    sphericity = w3 / (w1 + eps)
    dominant_mode = w1 / (w1 + w2 + w3 + eps)

    # Density
    volume = dx * dy * dz + eps
    density = np.log(len(track_hits) / volume)

    # Time spread (not available without timing info, use 0)
    time_std = 0.0

    # Physics features
    # Radiation length (simplified)
    x_over_X0 = 0.0  # Would need material info

    # Highland scattering angle estimate
    p_estimate = 500.0  # Assume 500 MeV/c
    X0_argon = 14.0  # cm
    track_length = np.sqrt(dx**2 + dy**2 + dz**2)
    highland_theta0 = (13.6 / p_estimate) * np.sqrt(track_length / X0_argon) * (1 + 0.038 * np.log(track_length / X0_argon))

    # Radial position
    r_surface = np.sqrt(centroid[0]**2 + centroid[1]**2)

    features = np.array([
        dx, dy, dz,
        elongation_1, elongation_2, sphericity, dominant_mode,
        density, time_std,
        x_over_X0, highland_theta0, r_surface,
    ], dtype=np.float32)

    return features


__all__ = [
    "PointNetMini",
    "TrackGNN",
    "EdgeConvLayer",
    "PSignalPredictor",
    "PSignalConfig",
    "normalize_hits",
    "build_knn_graph",
    "heuristic_psignal",
    "extract_track_features",
    "HAS_TORCH_GEOMETRIC",
]
