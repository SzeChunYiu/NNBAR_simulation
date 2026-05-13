"""
GNN-based Vertex Reconstruction Model for NNBAR.

Adapted from HIBEAM ImprovedVertexModel with:
- Multi-head cross attention for candidate pooling
- Residual MLP encoder for candidate features
- Separate coordinate prediction heads
- Learnable position encoding

The model takes track candidates (with projected vertices and features)
and predicts the true vertex position using attention-weighted pooling
followed by a refinement network.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
import math

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def check_torch():
    if not HAS_TORCH:
        raise ImportError("PyTorch required. Install with: pip install torch")


# ============================================================================
# Model Components
# ============================================================================

class ResidualMLP(nn.Module):
    """MLP block with residual connection and layer normalization."""

    def __init__(self, dim: int, hidden_mult: int = 4, dropout: float = 0.1):
        super().__init__()
        hidden = dim * hidden_mult
        self.norm = nn.LayerNorm(dim)
        self.fc1 = nn.Linear(dim, hidden)
        self.fc2 = nn.Linear(hidden, dim)
        self.dropout = nn.Dropout(dropout)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        x = self.norm(x)
        x = self.fc1(x)
        x = self.act(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.dropout(x)
        return residual + x


class MultiHeadCrossAttention(nn.Module):
    """Multi-head attention for pooling track candidates."""

    def __init__(
        self,
        d_query: int,
        d_key: int,
        d_out: int,
        n_heads: int = 4,
        dropout: float = 0.1
    ):
        super().__init__()
        assert d_out % n_heads == 0, "d_out must be divisible by n_heads"

        self.n_heads = n_heads
        self.head_dim = d_out // n_heads
        self.scale = self.head_dim ** -0.5

        self.q_proj = nn.Linear(d_query, d_out)
        self.k_proj = nn.Linear(d_key, d_out)
        self.v_proj = nn.Linear(d_key, d_out)
        self.out_proj = nn.Linear(d_out, d_out)

        self.dropout = nn.Dropout(dropout)
        self.norm_q = nn.LayerNorm(d_query)
        self.norm_k = nn.LayerNorm(d_key)

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            query: [B, 1, D_q] or [B, D_q]
            key: [B, C, D_k]
            value: [B, C, D_v]
            mask: [B, C] boolean mask (True = valid)

        Returns:
            output: [B, D_out]
            weights: [B, C] attention weights
        """
        if query.dim() == 2:
            query = query.unsqueeze(1)  # [B, 1, D_q]

        B, C, _ = key.shape

        # Normalize inputs
        query = self.norm_q(query)
        key = self.norm_k(key)

        # Project
        q = self.q_proj(query)  # [B, 1, D_out]
        k = self.k_proj(key)    # [B, C, D_out]
        v = self.v_proj(value)  # [B, C, D_out]

        # Reshape for multi-head
        q = q.view(B, 1, self.n_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, C, self.n_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, C, self.n_heads, self.head_dim).transpose(1, 2)

        # Attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale  # [B, H, 1, C]

        # Apply mask
        if mask is not None:
            mask_expanded = mask.unsqueeze(1).unsqueeze(2)  # [B, 1, 1, C]
            scores = scores.masked_fill(~mask_expanded, float("-inf"))

        # Softmax
        weights = F.softmax(scores, dim=-1)  # [B, H, 1, C]
        weights = self.dropout(weights)

        # Apply attention
        out = torch.matmul(weights, v)  # [B, H, 1, head_dim]
        out = out.transpose(1, 2).contiguous().view(B, 1, -1)  # [B, 1, D_out]
        out = self.out_proj(out).squeeze(1)  # [B, D_out]

        # Average weights across heads
        avg_weights = weights.mean(dim=1).squeeze(1)  # [B, C]

        return out, avg_weights


class CandidateEncoder(nn.Module):
    """Encode track candidate features with residual MLP blocks."""

    def __init__(
        self,
        in_dim: int,
        hidden_dim: int = 128,
        n_layers: int = 3,
        dropout: float = 0.1
    ):
        super().__init__()

        # Input projection
        self.input_proj = nn.Linear(in_dim, hidden_dim)
        self.input_norm = nn.LayerNorm(hidden_dim)

        # Residual blocks
        self.blocks = nn.ModuleList([
            ResidualMLP(hidden_dim, hidden_mult=4, dropout=dropout)
            for _ in range(n_layers)
        ])

        # Output normalization
        self.output_norm = nn.LayerNorm(hidden_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, C, D_in] candidate features

        Returns:
            [B, C, hidden_dim] encoded features
        """
        x = self.input_proj(x)
        x = self.input_norm(x)
        x = F.gelu(x)

        for block in self.blocks:
            x = block(x)

        x = self.output_norm(x)
        return x


class CoordinateHead(nn.Module):
    """Predict delta for a single coordinate."""

    def __init__(self, in_dim: int, hidden_dim: int = 64, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(in_dim),
            nn.Linear(in_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ============================================================================
# Main Model
# ============================================================================

class NNBARVertexGNN(nn.Module):
    """
    GNN-based vertex reconstruction model for NNBAR.

    Takes track candidates (projected vertices and features) and predicts
    the true vertex position using:
    1. Candidate encoding with residual MLPs
    2. Multi-head cross attention for weighted pooling
    3. Position encoding of anchor point
    4. Separate coordinate prediction heads

    The model learns to weight track candidates based on their quality
    and predict a refinement delta from the weighted anchor.
    """

    def __init__(
        self,
        cand_in_dim: int = 12,
        hidden_dim: int = 128,
        n_encoder_layers: int = 3,
        n_attention_heads: int = 4,
        dropout: float = 0.1,
    ):
        """
        Args:
            cand_in_dim: Dimension of candidate features.
            hidden_dim: Hidden dimension throughout the model.
            n_encoder_layers: Number of residual MLP layers in encoder.
            n_attention_heads: Number of attention heads.
            dropout: Dropout probability.
        """
        check_torch()
        super().__init__()

        self.cand_in_dim = cand_in_dim
        self.hidden_dim = hidden_dim

        # Candidate encoder
        self.cand_encoder = CandidateEncoder(
            in_dim=cand_in_dim,
            hidden_dim=hidden_dim,
            n_layers=n_encoder_layers,
            dropout=dropout,
        )

        # Learnable query token (no backbone for NNBAR)
        self.query_token = nn.Parameter(torch.randn(1, hidden_dim) * 0.02)

        # Multi-head cross attention for candidate pooling
        self.cross_attention = MultiHeadCrossAttention(
            d_query=hidden_dim,
            d_key=hidden_dim,
            d_out=hidden_dim,
            n_heads=n_attention_heads,
            dropout=dropout,
        )

        # Position encoding for anchor refinement
        self.pos_encoder = nn.Sequential(
            nn.Linear(3, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, hidden_dim),
        )

        # Fusion layer
        fuse_dim = hidden_dim * 2  # attention output + position encoding
        self.fusion = nn.Sequential(
            nn.LayerNorm(fuse_dim),
            nn.Linear(fuse_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        # Separate coordinate heads (x/y need more capacity since z is easier)
        self.head_x = CoordinateHead(hidden_dim, hidden_dim=64, dropout=dropout)
        self.head_y = CoordinateHead(hidden_dim, hidden_dim=64, dropout=dropout)
        self.head_z = CoordinateHead(hidden_dim, hidden_dim=32, dropout=dropout)

        self._init_weights()

    def _init_weights(self):
        """Initialize weights with small values for stability."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.LayerNorm):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(
        self,
        cand_vxyz: torch.Tensor,
        cand_feat: torch.Tensor,
        cand_mask: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.

        Args:
            cand_vxyz: [B, C, 3] candidate projected vertices
            cand_feat: [B, C, D] candidate features
            cand_mask: [B, C] boolean mask (True = valid candidate)

        Returns:
            Dictionary with:
            - v_pred: [B, 3] predicted vertex
            - attn_w: [B, C] attention weights
            - anchors: [B, 3] weighted anchor position
            - delta: [B, 3] predicted delta
        """
        V = cand_vxyz.float()
        F_c = cand_feat.float()
        M = cand_mask.bool()

        # Handle unbatched input
        if V.dim() == 2:
            V = V.unsqueeze(0)
        if F_c.dim() == 2:
            F_c = F_c.unsqueeze(0)
        if M.dim() == 1:
            M = M.unsqueeze(0)

        B, C, _ = F_c.shape

        # Encode candidates
        cand_emb = self.cand_encoder(F_c)  # [B, C, H]

        # Get query (learnable token)
        query = self.query_token.expand(B, -1)  # [B, H]

        # Cross attention pooling
        pooled, attn_weights = self.cross_attention(
            query=query,
            key=cand_emb,
            value=cand_emb,
            mask=M
        )  # pooled: [B, H], attn_weights: [B, C]

        # Compute weighted anchor position
        V_anchor = (V * attn_weights.unsqueeze(-1)).sum(1)  # [B, 3]

        # Encode anchor position
        pos_emb = self.pos_encoder(V_anchor)  # [B, H]

        # Fusion
        fused = torch.cat([pooled, pos_emb], dim=-1)  # [B, 2H]
        fused = self.fusion(fused)  # [B, H]

        # Predict coordinate deltas separately
        dx = self.head_x(fused)  # [B, 1]
        dy = self.head_y(fused)  # [B, 1]
        dz = self.head_z(fused)  # [B, 1]

        dxyz = torch.cat([dx, dy, dz], dim=-1)  # [B, 3]
        V_pred = V_anchor + dxyz  # [B, 3]

        return {
            "v_pred": V_pred,
            "attn_w": attn_weights,
            "anchors": V_anchor,
            "delta": dxyz,
        }


class NNBARVertexGNNV2(nn.Module):
    """
    V2: Deeper model with transformer-style self-attention on candidates.

    Adds self-attention layers between candidates before cross-attention pooling,
    allowing candidates to share information about their relative positions
    and qualities.
    """

    def __init__(
        self,
        cand_in_dim: int = 12,
        hidden_dim: int = 128,
        n_self_attn_layers: int = 2,
        n_attention_heads: int = 4,
        dropout: float = 0.1,
    ):
        check_torch()
        super().__init__()

        self.cand_in_dim = cand_in_dim
        self.hidden_dim = hidden_dim

        # Input projection
        self.input_proj = nn.Linear(cand_in_dim, hidden_dim)
        self.input_norm = nn.LayerNorm(hidden_dim)

        # Self-attention layers on candidates
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=n_attention_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            activation='gelu',
            batch_first=True,
            norm_first=True,
        )
        self.self_attention = nn.TransformerEncoder(
            encoder_layer,
            num_layers=n_self_attn_layers
        )

        # Query token
        self.query_token = nn.Parameter(torch.randn(1, hidden_dim) * 0.02)

        # Cross attention
        self.cross_attention = MultiHeadCrossAttention(
            d_query=hidden_dim,
            d_key=hidden_dim,
            d_out=hidden_dim,
            n_heads=n_attention_heads,
            dropout=dropout,
        )

        # Position encoding
        self.pos_encoder = nn.Sequential(
            nn.Linear(3, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, hidden_dim),
        )

        # Fusion
        fuse_dim = hidden_dim * 2
        self.fusion = nn.Sequential(
            nn.LayerNorm(fuse_dim),
            nn.Linear(fuse_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        # Coordinate heads
        self.head_x = CoordinateHead(hidden_dim, hidden_dim=64, dropout=dropout)
        self.head_y = CoordinateHead(hidden_dim, hidden_dim=64, dropout=dropout)
        self.head_z = CoordinateHead(hidden_dim, hidden_dim=32, dropout=dropout)

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.LayerNorm):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(
        self,
        cand_vxyz: torch.Tensor,
        cand_feat: torch.Tensor,
        cand_mask: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """Forward pass with self-attention on candidates."""
        V = cand_vxyz.float()
        F_c = cand_feat.float()
        M = cand_mask.bool()

        if V.dim() == 2:
            V = V.unsqueeze(0)
        if F_c.dim() == 2:
            F_c = F_c.unsqueeze(0)
        if M.dim() == 1:
            M = M.unsqueeze(0)

        B, C, _ = F_c.shape

        # Project input
        x = self.input_proj(F_c)
        x = self.input_norm(x)
        x = F.gelu(x)

        # Self-attention on candidates
        src_key_padding_mask = ~M  # Transformer expects True = ignore
        x = self.self_attention(x, src_key_padding_mask=src_key_padding_mask)

        # Query
        query = self.query_token.expand(B, -1)

        # Cross attention
        pooled, attn_weights = self.cross_attention(
            query=query,
            key=x,
            value=x,
            mask=M
        )

        # Anchor
        V_anchor = (V * attn_weights.unsqueeze(-1)).sum(1)

        # Position encoding
        pos_emb = self.pos_encoder(V_anchor)

        # Fusion
        fused = torch.cat([pooled, pos_emb], dim=-1)
        fused = self.fusion(fused)

        # Predict deltas
        dx = self.head_x(fused)
        dy = self.head_y(fused)
        dz = self.head_z(fused)

        dxyz = torch.cat([dx, dy, dz], dim=-1)
        V_pred = V_anchor + dxyz

        return {
            "v_pred": V_pred,
            "attn_w": attn_weights,
            "anchors": V_anchor,
            "delta": dxyz,
        }


# ============================================================================
# Uncertainty Components
# ============================================================================

class UncertaintyHead(nn.Module):
    """
    Per-coordinate uncertainty head for heteroscedastic regression.

    Takes encoded features and outputs (mu, log_sigma) pairs for each of the
    three spatial coordinates.  The log_sigma output is clamped to [-6, 3] to
    prevent numerical instability during early training.
    """

    LOG_SIGMA_MIN = -6.0
    LOG_SIGMA_MAX = 3.0

    def __init__(self, in_dim: int, hidden_dim: int = 64, dropout: float = 0.1):
        """
        Args:
            in_dim: Input feature dimension (must match the fused representation).
            hidden_dim: Hidden layer dimension.
            dropout: Dropout probability.
        """
        check_torch()
        super().__init__()

        self.shared = nn.Sequential(
            nn.LayerNorm(in_dim),
            nn.Linear(in_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        # 3 means + 3 log-sigmas in a single linear layer
        self.out_proj = nn.Linear(hidden_dim, 6)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: [B, in_dim] encoded feature vector.

        Returns:
            mu:        [B, 3] predicted coordinate means (absolute position).
            log_sigma: [B, 3] log of predicted standard deviations (clamped).
        """
        h = self.shared(x)          # [B, hidden_dim]
        out = self.out_proj(h)      # [B, 6]
        mu = out[:, :3]
        log_sigma = out[:, 3:].clamp(self.LOG_SIGMA_MIN, self.LOG_SIGMA_MAX)
        return mu, log_sigma


# ============================================================================
# Functional Loss Helpers
# ============================================================================

def log_cosh_loss(pred: "torch.Tensor", target: "torch.Tensor") -> "torch.Tensor":
    """
    Log-cosh loss — more robust than MSE for vertex regression.

    Behaves like L2 near zero and like L1 for large residuals, providing
    robustness to outlier events while remaining everywhere differentiable.

    Args:
        pred:   [B, 3] (or any shape) predicted vertex.
        target: Same shape as pred.

    Returns:
        Scalar mean log-cosh loss.
    """
    check_torch()
    diff = pred - target
    return torch.mean(torch.log(torch.cosh(diff + 1e-12)))


def coordinate_weighted_loss(
    pred: "torch.Tensor",
    target: "torch.Tensor",
    weights: Tuple[float, float, float] = (1.0, 1.0, 2.0),
) -> "torch.Tensor":
    """
    Coordinate-specific weighted log-cosh loss.

    Applies per-coordinate weights before averaging so that better-constrained
    coordinates (z in NNBAR) can be penalised more heavily during training.

    Args:
        pred:    [B, 3] predicted vertex (x, y, z order).
        target:  [B, 3] true vertex.
        weights: (w_x, w_y, w_z) scalar multipliers.  Default gives z 2× weight.

    Returns:
        Scalar weighted mean loss.
    """
    check_torch()
    diff = pred - target                                      # [B, 3]
    per_coord = torch.log(torch.cosh(diff + 1e-12))          # [B, 3]
    w = torch.tensor(weights, dtype=pred.dtype, device=pred.device)  # [3]
    return torch.mean((per_coord * w).sum(dim=-1))


# ============================================================================
# Uncertainty-Aware Wrapper
# ============================================================================

class UncertaintyVertexGNN(nn.Module):
    """
    Wraps NNBARVertexGNN with per-coordinate uncertainty estimation.

    The base model predicts the vertex position; the UncertaintyHead adds a
    learnable heteroscedastic uncertainty (log_sigma) for each coordinate.
    During training, optimise with negative log-likelihood of a Gaussian:

        loss = 0.5 * exp(-2*log_sigma) * (pred - target)^2 + log_sigma

    In inference, call ``forward()`` to obtain (vertex_pred, log_sigma).
    """

    def __init__(
        self,
        cand_in_dim: int = 12,
        hidden_dim: int = 128,
        n_encoder_layers: int = 3,
        n_attention_heads: int = 4,
        dropout: float = 0.1,
    ):
        """
        Args:
            cand_in_dim: Feature dimension of each track candidate.
            hidden_dim:  Hidden dimension shared by the base model and head.
            n_encoder_layers: Number of residual MLP layers in the candidate encoder.
            n_attention_heads: Number of attention heads.
            dropout: Dropout probability.
        """
        check_torch()
        super().__init__()

        self.base = NNBARVertexGNN(
            cand_in_dim=cand_in_dim,
            hidden_dim=hidden_dim,
            n_encoder_layers=n_encoder_layers,
            n_attention_heads=n_attention_heads,
            dropout=dropout,
        )
        # The fused representation fed into coordinate heads has dimension hidden_dim
        self.uncertainty_head = UncertaintyHead(
            in_dim=hidden_dim,
            hidden_dim=hidden_dim // 2,
            dropout=dropout,
        )

    # ------------------------------------------------------------------
    # Internal helper: replicate the base model's forward up to the fused
    # representation so both vertex and uncertainty heads share the same
    # feature vector.
    # ------------------------------------------------------------------

    def _encode(
        self,
        cand_vxyz: "torch.Tensor",
        cand_feat: "torch.Tensor",
        cand_mask: "torch.Tensor",
    ) -> Tuple["torch.Tensor", "torch.Tensor"]:
        """
        Run encoding through the base model and return (fused, v_anchor).

        This intentionally bypasses the base model's coordinate heads so the
        uncertainty head operates on the same feature space.
        """
        V = cand_vxyz.float()
        F_c = cand_feat.float()
        M = cand_mask.bool()

        if V.dim() == 2:
            V = V.unsqueeze(0)
        if F_c.dim() == 2:
            F_c = F_c.unsqueeze(0)
        if M.dim() == 1:
            M = M.unsqueeze(0)

        B = F_c.shape[0]

        cand_emb = self.base.cand_encoder(F_c)
        query = self.base.query_token.expand(B, -1)
        pooled, attn_weights = self.base.cross_attention(
            query=query, key=cand_emb, value=cand_emb, mask=M
        )
        V_anchor = (V * attn_weights.unsqueeze(-1)).sum(1)
        pos_emb = self.base.pos_encoder(V_anchor)
        fused = torch.cat([pooled, pos_emb], dim=-1)
        fused = self.base.fusion(fused)
        return fused, V_anchor

    def forward(
        self,
        cand_vxyz: "torch.Tensor",
        cand_feat: "torch.Tensor",
        cand_mask: "torch.Tensor",
    ) -> Tuple["torch.Tensor", "torch.Tensor"]:
        """
        Forward pass returning vertex prediction and per-coordinate uncertainty.

        Args:
            cand_vxyz: [B, C, 3] candidate projected vertices.
            cand_feat: [B, C, D] candidate features.
            cand_mask: [B, C] boolean mask (True = valid).

        Returns:
            vertex_pred: [B, 3] predicted vertex position.
            log_sigma:   [B, 3] log of predicted standard deviation per coordinate.
        """
        fused, V_anchor = self._encode(cand_vxyz, cand_feat, cand_mask)

        # Coordinate deltas from base heads (reuse to avoid double forward)
        dx = self.base.head_x(fused)
        dy = self.base.head_y(fused)
        dz = self.base.head_z(fused)
        dxyz = torch.cat([dx, dy, dz], dim=-1)
        vertex_pred = V_anchor + dxyz

        # Uncertainty from dedicated head
        _mu_unused, log_sigma = self.uncertainty_head(fused)

        return vertex_pred, log_sigma


# ============================================================================
# Loss Functions
# ============================================================================

class LogCoshLoss(nn.Module):
    """Log-cosh loss - smooth, robust to outliers."""

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        diff = pred - target
        return torch.mean(torch.log(torch.cosh(diff + 1e-12)))


class HuberLoss(nn.Module):
    """Huber loss with configurable delta."""

    def __init__(self, delta: float = 1.0):
        super().__init__()
        self.delta = delta

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        return F.huber_loss(pred, target, delta=self.delta)


def get_loss_function(name: str = 'logcosh') -> nn.Module:
    """Get loss function by name."""
    if name == 'logcosh':
        return LogCoshLoss()
    elif name == 'huber':
        return HuberLoss(delta=1.0)
    elif name == 'mse':
        return nn.MSELoss()
    elif name == 'l1':
        return nn.L1Loss()
    else:
        raise ValueError(f"Unknown loss function: {name}")


# ============================================================================
# Utility Functions
# ============================================================================

def create_model(
    version: str = 'v1',
    cand_in_dim: int = 12,
    hidden_dim: int = 128,
    n_layers: int = 3,
    n_heads: int = 4,
    dropout: float = 0.1,
) -> nn.Module:
    """
    Create vertex GNN model.

    Args:
        version: 'v1' or 'v2'
        cand_in_dim: Input feature dimension
        hidden_dim: Hidden dimension
        n_layers: Number of encoder/self-attention layers
        n_heads: Number of attention heads
        dropout: Dropout probability

    Returns:
        Model instance
    """
    check_torch()

    if version == 'v1':
        return NNBARVertexGNN(
            cand_in_dim=cand_in_dim,
            hidden_dim=hidden_dim,
            n_encoder_layers=n_layers,
            n_attention_heads=n_heads,
            dropout=dropout,
        )
    elif version == 'v2':
        return NNBARVertexGNNV2(
            cand_in_dim=cand_in_dim,
            hidden_dim=hidden_dim,
            n_self_attn_layers=n_layers,
            n_attention_heads=n_heads,
            dropout=dropout,
        )
    else:
        raise ValueError(f"Unknown model version: {version}")


def load_model(
    checkpoint_path: str,
    device: str = 'cpu',
) -> nn.Module:
    """
    Load model from checkpoint.

    Args:
        checkpoint_path: Path to checkpoint file
        device: Device to load model on

    Returns:
        Loaded model
    """
    check_torch()

    checkpoint = torch.load(checkpoint_path, map_location=device)

    # Get model config from checkpoint
    config = checkpoint.get('config', {})
    version = config.get('version', 'v1')

    model = create_model(
        version=version,
        cand_in_dim=config.get('cand_in_dim', 12),
        hidden_dim=config.get('hidden_dim', 128),
        n_layers=config.get('n_layers', 3),
        n_heads=config.get('n_heads', 4),
        dropout=config.get('dropout', 0.1),
    )

    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()

    return model


if __name__ == "__main__":
    check_torch()

    # Test model
    print("Testing NNBARVertexGNN...")

    model = create_model(version='v1', cand_in_dim=12)
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Mock input
    B, C, D = 4, 10, 12
    cand_vxyz = torch.randn(B, C, 3)
    cand_feat = torch.randn(B, C, D)
    cand_mask = torch.ones(B, C, dtype=torch.bool)
    cand_mask[:, -2:] = False  # Last 2 candidates are padding

    # Forward pass
    output = model(cand_vxyz, cand_feat, cand_mask)

    print(f"Input shapes: vxyz={cand_vxyz.shape}, feat={cand_feat.shape}, mask={cand_mask.shape}")
    print(f"Output v_pred: {output['v_pred'].shape}")
    print(f"Output attn_w: {output['attn_w'].shape}")
    print(f"Attention weights sum: {output['attn_w'].sum(dim=1)}")  # Should be ~1

    # Test V2
    print("\nTesting NNBARVertexGNNV2...")
    model_v2 = create_model(version='v2', cand_in_dim=12)
    print(f"Model V2 parameters: {sum(p.numel() for p in model_v2.parameters()):,}")

    output_v2 = model_v2(cand_vxyz, cand_feat, cand_mask)
    print(f"V2 Output v_pred: {output_v2['v_pred'].shape}")
