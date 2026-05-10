"""
DBSCAN-based clustering for TPC track finding.

Implements the clustering pipeline adapted from HIBEAM:
1. Transform to weighted cylindrical coordinates
2. Adaptive epsilon DBSCAN (GPU-accelerated with cuML)
3. Multiple splitting strategies for merged clusters
4. Track merging for fragments

GPU Acceleration:
- Uses cuML DBSCAN when available (10-50x speedup)
- Falls back to sklearn on CPU if cuML not available
- Configurable via USE_GPU environment variable
"""

import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import pandas as pd
import os

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(x, **kw):
        return x

logger = logging.getLogger(__name__)

# GPU backend imports
from ..utils.gpu_backend import get_backend, GPUBackend

# Import sklearn as fallback
from sklearn.cluster import DBSCAN as SklearnDBSCAN
from sklearn.neighbors import NearestNeighbors as SklearnNearestNeighbors
from sklearn.cluster import KMeans as SklearnKMeans

# Try importing cuML for GPU-accelerated clustering
_CUML_AVAILABLE = False
try:
    from cuml.cluster import DBSCAN as CuMLDBSCAN
    from cuml.neighbors import NearestNeighbors as CuMLNearestNeighbors
    from cuml.cluster import KMeans as CuMLKMeans
    _CUML_AVAILABLE = True
except ImportError:
    pass

from ..utils.config import get_config, get_clustering_params, get_tracking_params
from ..utils.coordinates import cartesian_to_cylindrical


_DEFAULT_CLUSTERING_CONFIG = {
    'dbscan': {
        'alpha': 1.5,
        'min_samples': 3,
        'k': 6,
        'phi_weight': 5.0,
        'z_weight': 1.0,
    },
    'hdbscan': {
        'min_cluster_size': 5,
        'min_samples': 3,
    },
    'refinement': {
        'gap_threshold': 5.0,
        'd_thresh': 2.0,
        'angle_thresh_deg': 20.0,
    },
}


def load_clustering_config(config_path=None) -> dict:
    """Load clustering parameters from YAML, falling back to defaults.

    Args:
        config_path: Path to YAML config file. Defaults to
            ``clustering_config.yaml`` in the same directory as this module.

    Returns:
        Merged configuration dict with dbscan, hdbscan, and refinement keys.
    """
    if config_path is None:
        config_path = Path(__file__).parent / 'clustering_config.yaml'
    else:
        config_path = Path(config_path)

    config = {k: dict(v) for k, v in _DEFAULT_CLUSTERING_CONFIG.items()}
    if not config_path.exists():
        return config

    try:
        import yaml
        with open(config_path, 'r') as fh:
            loaded = yaml.safe_load(fh) or {}
        if not isinstance(loaded, dict):
            return config
        for section, values in loaded.items():
            if section in config and isinstance(values, dict):
                config[section].update(values)
        return config
    except Exception as exc:
        logger.debug(
            "Failed to load clustering config from %s (%s); using defaults.",
            config_path,
            exc,
        )
        return config


def _use_gpu_clustering() -> bool:
    """Check if GPU clustering should be used."""
    if os.environ.get('NNBAR_FORCE_CPU', '0') == '1':
        return False
    gpu = get_backend()
    return gpu.use_gpu and _CUML_AVAILABLE and gpu.has_cuml


@dataclass
class ClusterResult:
    """Result of clustering a set of hits."""
    labels: np.ndarray           # Cluster labels (-1 = noise)
    n_clusters: int              # Number of clusters found
    hit_indices: np.ndarray      # Original hit indices
    cluster_sizes: Dict[int, int]  # Size of each cluster


def adaptive_epsilon(
    points: np.ndarray,
    k: int = 6,
    alpha: float = 1.5,
    min_eps: float = 0.1,
) -> float:
    """
    Compute adaptive epsilon for DBSCAN using k-NN distances.

    GPU-accelerated using cuML NearestNeighbors when available.

    Args:
        points: (N, D) array of points.
        k: Number of neighbors for distance estimation.
        alpha: Multiplier for median distance.
        min_eps: Minimum epsilon value.

    Returns:
        Adaptive epsilon value.
    """
    if len(points) < k + 1:
        return min_eps

    gpu = get_backend()

    if _use_gpu_clustering():
        # GPU path using cuML
        points_gpu = gpu.to_gpu(points.astype(np.float32))
        nn = CuMLNearestNeighbors(n_neighbors=k + 1)
        nn.fit(points_gpu)
        distances, _ = nn.kneighbors(points_gpu)

        # Transfer back to CPU for median calculation
        k_distances = gpu.to_numpy(distances[:, k])
        eps = alpha * float(np.median(k_distances))
    else:
        # CPU path using sklearn
        nn = SklearnNearestNeighbors(n_neighbors=k + 1)
        nn.fit(points)
        distances, _ = nn.kneighbors(points)

        k_distances = distances[:, k]
        eps = alpha * np.median(k_distances)

    return max(eps, min_eps)


def transform_to_clustering_space(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    phi_weight: float = 5.0,
    z_weight: float = 1.0,
) -> np.ndarray:
    """
    Transform Cartesian coordinates to weighted cylindrical space for clustering.

    The phi_weight emphasizes angular separation between tracks,
    while z_weight controls z-axis sensitivity.

    Args:
        x, y, z: Cartesian coordinates.
        phi_weight: Weight for azimuthal angle.
        z_weight: Weight for z coordinate.

    Returns:
        (N, 3) array in (r, phi*weight, z*weight) space.
    """
    r, phi, _ = cartesian_to_cylindrical(x, y, z)

    # Weighted cylindrical coordinates
    # Note: r*phi gives arc length, which is more physical than just phi
    return np.column_stack([
        r,
        r * phi * phi_weight,  # Arc-length weighted by phi_weight
        z * z_weight,
    ])


def dbscan_clustering(
    points: np.ndarray,
    eps: Optional[float] = None,
    min_samples: int = 3,
    adaptive: bool = True,
    alpha: float = 1.5,
    k: int = 6,
) -> ClusterResult:
    """
    Perform DBSCAN clustering with optional adaptive epsilon.

    GPU-accelerated using cuML DBSCAN when available (10-50x speedup).

    Args:
        points: (N, D) array of points.
        eps: Epsilon for DBSCAN. If None and adaptive=True, computed automatically.
        min_samples: Minimum samples for core point.
        adaptive: Whether to use adaptive epsilon.
        alpha: Alpha for adaptive epsilon.
        k: k for adaptive epsilon.

    Returns:
        ClusterResult with labels and statistics.
    """
    if len(points) < min_samples:
        return ClusterResult(
            labels=np.full(len(points), -1),
            n_clusters=0,
            hit_indices=np.arange(len(points)),
            cluster_sizes={},
        )

    if eps is None and adaptive:
        eps = adaptive_epsilon(points, k=k, alpha=alpha)
    elif eps is None:
        eps = 1.0

    gpu = get_backend()

    if _use_gpu_clustering():
        # GPU path using cuML DBSCAN
        points_gpu = gpu.to_gpu(points.astype(np.float32))
        db = CuMLDBSCAN(eps=eps, min_samples=min_samples)
        labels = db.fit_predict(points_gpu)

        # Transfer labels back to CPU
        labels = gpu.to_numpy(labels).astype(np.int32)
    else:
        # CPU path using sklearn
        db = SklearnDBSCAN(eps=eps, min_samples=min_samples)
        labels = db.fit_predict(points)

    # Count clusters (excluding noise label -1)
    unique_labels = set(labels)
    n_clusters = len(unique_labels - {-1})

    # Cluster sizes
    cluster_sizes = {}
    for label in unique_labels:
        if label >= 0:
            cluster_sizes[label] = np.sum(labels == label)

    return ClusterResult(
        labels=labels,
        n_clusters=n_clusters,
        hit_indices=np.arange(len(points)),
        cluster_sizes=cluster_sizes,
    )


def split_by_z_gap(
    points: np.ndarray,
    labels: np.ndarray,
    gap_threshold: float = 6.0,
) -> np.ndarray:
    """
    Split clusters that have large gaps in z.

    Args:
        points: Original (x, y, z) points.
        labels: Current cluster labels.
        gap_threshold: Minimum gap in cm to trigger split.

    Returns:
        Updated labels.
    """
    new_labels = labels.copy()
    max_label = labels.max()

    unique_clusters = set(labels) - {-1}

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_z = points[mask, 2]

        if len(cluster_z) < 4:
            continue

        # Sort by z and find gaps
        sorted_idx = np.argsort(cluster_z)
        sorted_z = cluster_z[sorted_idx]

        gaps = np.diff(sorted_z)
        large_gaps = np.where(gaps > gap_threshold)[0]

        if len(large_gaps) > 0:
            # Split at largest gap
            split_idx = large_gaps[np.argmax(gaps[large_gaps])]

            # Update labels for second part
            cluster_indices = np.where(mask)[0]
            sorted_cluster_indices = cluster_indices[sorted_idx]

            max_label += 1
            new_labels[sorted_cluster_indices[split_idx + 1:]] = max_label

    return new_labels


def split_by_direction(
    points: np.ndarray,
    labels: np.ndarray,
    angle_threshold: float = 0.7,  # cos(45 deg)
) -> np.ndarray:
    """
    Split clusters with inconsistent track directions.

    Uses PCA to detect multiple directions within a cluster.

    Args:
        points: Original (x, y, z) points.
        labels: Current cluster labels.
        angle_threshold: Cosine of maximum angle between sub-tracks.

    Returns:
        Updated labels.
    """
    from .track_fitting import pca_line_fit

    new_labels = labels.copy()
    max_label = labels.max()

    unique_clusters = set(labels) - {-1}

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_points = points[mask]

        if len(cluster_points) < 6:
            continue

        # Split cluster in half by z and compute directions
        sorted_idx = np.argsort(cluster_points[:, 2])
        mid = len(sorted_idx) // 2

        if mid < 3 or (len(sorted_idx) - mid) < 3:
            continue

        first_half = cluster_points[sorted_idx[:mid]]
        second_half = cluster_points[sorted_idx[mid:]]

        try:
            fit1 = pca_line_fit(first_half)
            fit2 = pca_line_fit(second_half)

            # Check angle between directions
            cos_angle = abs(np.dot(fit1['direction'], fit2['direction']))

            if cos_angle < angle_threshold:
                # Directions are too different - split
                cluster_indices = np.where(mask)[0]
                sorted_cluster_indices = cluster_indices[sorted_idx]

                max_label += 1
                new_labels[sorted_cluster_indices[mid:]] = max_label
        except:
            continue

    return new_labels


def split_by_radial_clustering(
    points: np.ndarray,
    labels: np.ndarray,
    r: np.ndarray,
    n_clusters: int = 2,
) -> np.ndarray:
    """
    Split clusters using KMeans on (r, z) residuals from linear fit.

    Helps separate parallel tracks at different radial positions.

    Args:
        points: Original (x, y, z) points.
        labels: Current cluster labels.
        r: Radial coordinates.
        n_clusters: Number of sub-clusters to attempt.

    Returns:
        Updated labels.
    """
    new_labels = labels.copy()
    max_label = labels.max()

    unique_clusters = set(labels) - {-1}

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_points = points[mask]
        cluster_r = r[mask]

        if len(cluster_points) < 2 * n_clusters * 3:
            continue

        # Fit linear model in z
        z = cluster_points[:, 2]
        z_mean = z.mean()
        z_std = z.std()
        if z_std < 0.1:
            continue

        # Residuals from linear fit in r vs z
        A = np.column_stack([z, np.ones(len(z))])
        try:
            coeffs, _, _, _ = np.linalg.lstsq(A, cluster_r, rcond=None)
            r_predicted = A @ coeffs
            residuals = cluster_r - r_predicted
        except:
            continue

        # KMeans on (r, residuals)
        features = np.column_stack([cluster_r, residuals])
        try:
            gpu = get_backend()
            if _use_gpu_clustering():
                # GPU path using cuML KMeans
                features_gpu = gpu.to_gpu(features.astype(np.float32))
                km = CuMLKMeans(n_clusters=n_clusters, n_init=10, random_state=42)
                sub_labels = km.fit_predict(features_gpu)
                sub_labels = gpu.to_numpy(sub_labels)
            else:
                km = SklearnKMeans(n_clusters=n_clusters, n_init=10, random_state=42)
                sub_labels = km.fit_predict(features)

            # Check if split is meaningful (balanced sizes)
            sizes = [np.sum(sub_labels == i) for i in range(n_clusters)]
            if min(sizes) < 3:
                continue

            # Apply split
            cluster_indices = np.where(mask)[0]
            for i in range(1, n_clusters):
                max_label += 1
                new_labels[cluster_indices[sub_labels == i]] = max_label
        except:
            continue

    return new_labels


def merge_collinear_fragments(
    points: np.ndarray,
    labels: np.ndarray,
    angle_threshold: float = 0.99,
    gap_threshold: float = 5.0,
    min_fragment_size: int = 3,
) -> np.ndarray:
    """
    Merge small collinear cluster fragments.

    Args:
        points: Original (x, y, z) points.
        labels: Current cluster labels.
        angle_threshold: Cosine threshold for collinearity.
        gap_threshold: Maximum gap in cm for merging.
        min_fragment_size: Maximum size of fragment to consider merging.

    Returns:
        Updated labels.
    """
    from .track_fitting import pca_line_fit

    new_labels = labels.copy()
    unique_clusters = list(set(labels) - {-1})

    if len(unique_clusters) < 2:
        return new_labels

    # Compute track parameters for each cluster
    track_params = {}
    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_points = points[mask]

        if len(cluster_points) < 3:
            continue

        try:
            fit = pca_line_fit(cluster_points)
            track_params[cluster_id] = {
                'center': fit['center'],
                'direction': fit['direction'],
                'head': fit['head'],
                'tail': fit['tail'],
                'size': len(cluster_points),
            }
        except:
            continue

    # Find mergeable pairs
    merged_to = {}  # Maps cluster to its merged parent

    for c1 in track_params:
        if track_params[c1]['size'] > min_fragment_size:
            continue

        best_match = None
        best_gap = float('inf')

        for c2 in track_params:
            if c1 == c2 or c1 in merged_to or c2 in merged_to:
                continue

            p1 = track_params[c1]
            p2 = track_params[c2]

            # Check collinearity
            cos_angle = abs(np.dot(p1['direction'], p2['direction']))
            if cos_angle < angle_threshold:
                continue

            # Check gap (minimum distance between endpoints)
            gaps = [
                np.linalg.norm(p1['head'] - p2['head']),
                np.linalg.norm(p1['head'] - p2['tail']),
                np.linalg.norm(p1['tail'] - p2['head']),
                np.linalg.norm(p1['tail'] - p2['tail']),
            ]
            min_gap = min(gaps)

            if min_gap < gap_threshold and min_gap < best_gap:
                best_match = c2
                best_gap = min_gap

        if best_match is not None:
            merged_to[c1] = best_match

    # Apply merges
    for fragment, parent in merged_to.items():
        new_labels[labels == fragment] = parent

    return new_labels


def split_clusters_by_perp_bimodality(
    points: np.ndarray,
    labels: np.ndarray,
    min_cluster_size: int = 8,
    weight_floor: float = 0.15,
    ashman_threshold: float = 2.0,
) -> np.ndarray:
    """
    Split clusters showing bimodal perpendicular distance (HIBEAM-inspired).

    This separates tracks that are parallel but offset perpendicular to
    the main cluster direction. Uses Ashman's D criterion to assess
    whether a bimodal split is meaningful.

    Args:
        points: Original (x, y, z) points.
        labels: Current cluster labels.
        min_cluster_size: Minimum cluster size to attempt splitting.
        weight_floor: Minimum fraction for sub-cluster (prevents false splits).
        ashman_threshold: Minimum Ashman D value for meaningful separation.

    Returns:
        Updated labels.
    """
    from .track_fitting import pca_line_fit

    new_labels = labels.copy()
    max_label = labels.max()
    unique_clusters = list(set(labels) - {-1})

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_points = points[mask]

        if len(cluster_points) < min_cluster_size:
            continue

        try:
            # Fit line to get direction
            fit = pca_line_fit(cluster_points, use_gpu=False)
            center = fit['center']
            direction = fit['direction']

            # Compute perpendicular distances to fitted line
            centered = cluster_points - center
            projections = np.dot(centered, direction)
            parallel_component = np.outer(projections, direction)
            perpendicular = centered - parallel_component
            perp_distances = np.linalg.norm(perpendicular, axis=1)

            # Check for bimodality using 1D K-means
            if _use_gpu_clustering():
                gpu = get_backend()
                perp_gpu = gpu.to_gpu(perp_distances.reshape(-1, 1).astype(np.float32))
                km = CuMLKMeans(n_clusters=2, n_init=10, random_state=42)
                sub_labels = km.fit_predict(perp_gpu)
                sub_labels = gpu.to_numpy(sub_labels)
            else:
                km = SklearnKMeans(n_clusters=2, n_init=10, random_state=42)
                sub_labels = km.fit_predict(perp_distances.reshape(-1, 1))

            # Check cluster sizes
            sizes = [np.sum(sub_labels == i) for i in range(2)]
            min_frac = min(sizes) / len(cluster_points)

            if min_frac < weight_floor:
                continue

            # Compute Ashman D criterion for bimodality
            # D = |μ1 - μ2| / sqrt(2 * (σ1² + σ2²))
            perp_0 = perp_distances[sub_labels == 0]
            perp_1 = perp_distances[sub_labels == 1]

            mu_diff = abs(np.mean(perp_0) - np.mean(perp_1))
            var_sum = np.var(perp_0) + np.var(perp_1)

            if var_sum < 1e-10:
                continue

            ashman_d = mu_diff / np.sqrt(2 * var_sum)

            if ashman_d < ashman_threshold:
                continue

            # Apply split
            cluster_indices = np.where(mask)[0]
            max_label += 1
            new_labels[cluster_indices[sub_labels == 1]] = max_label

        except Exception:
            continue

    return new_labels


def refine_clusters(
    points: np.ndarray,
    labels: np.ndarray,
    r: np.ndarray,
    iterations: int = 3,
) -> np.ndarray:
    """
    Apply iterative refinement with multiple splitting strategies.

    Args:
        points: Original (x, y, z) points.
        labels: Initial cluster labels.
        r: Radial coordinates.
        iterations: Number of refinement passes.

    Returns:
        Refined labels.
    """
    current_labels = labels.copy()

    for _ in range(iterations):
        n_before = len(set(current_labels) - {-1})

        # Apply splitting strategies
        current_labels = split_by_z_gap(points, current_labels)
        current_labels = split_by_direction(points, current_labels)
        current_labels = split_by_radial_clustering(points, current_labels, r)

        # Merge fragments
        current_labels = merge_collinear_fragments(points, current_labels)

        n_after = len(set(current_labels) - {-1})

        # Stop if no change
        if n_after == n_before:
            break

    return current_labels


def cluster_tpc_hits(
    tpc_data: pd.DataFrame,
    phi_weight: Optional[float] = None,
    z_weight: Optional[float] = None,
    min_samples: Optional[int] = None,
    refine: bool = False,
    use_cartesian: bool = True,
    eps: Optional[float] = None,
) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Main clustering function for TPC hits.

    Args:
        tpc_data: DataFrame with TPC hits (must have x, y, z columns).
        phi_weight: Weight for angular separation. If None, uses config.
        z_weight: Weight for z separation. If None, uses config.
        min_samples: Minimum samples for DBSCAN. If None, uses config.
        refine: Whether to apply refinement strategies.
        use_cartesian: If True, use simple Cartesian DBSCAN (recommended).
        eps: Fixed epsilon for DBSCAN. If None, uses adaptive.

    Returns:
        Tuple of (cluster labels, DataFrame with cluster assignments).
    """
    # Get parameters from config if not provided
    params = get_clustering_params()
    if phi_weight is None:
        phi_weight = params.get('phi_weight', 5.0)
    if z_weight is None:
        z_weight = params.get('z_weight', 1.0)
    if min_samples is None:
        min_samples = params.get('min_samples', 3)

    alpha = params.get('alpha', 1.5)
    k = params.get('k', 6)

    # Extract coordinates
    x = tpc_data['x'].values
    y = tpc_data['y'].values
    z = tpc_data['z'].values

    if len(x) < min_samples:
        labels = np.full(len(x), -1)
        tpc_data = tpc_data.copy()
        tpc_data['cluster_id'] = labels
        return labels, tpc_data

    # Use simple Cartesian DBSCAN for better track reconstruction
    if use_cartesian:
        points = np.column_stack([x, y, z])
        if eps is None:
            eps = 2.0  # Good default for TPC tracks
        db = SklearnDBSCAN(eps=eps, min_samples=min_samples)
        labels = db.fit_predict(points)
    else:
        # Transform to clustering space (legacy mode)
        clustering_points = transform_to_clustering_space(x, y, z, phi_weight, z_weight)

        # Initial clustering
        result = dbscan_clustering(
            clustering_points,
            min_samples=min_samples,
            adaptive=True,
            alpha=alpha,
            k=k,
        )
        labels = result.labels

        # Refinement
        if refine and result.n_clusters > 0:
            points = np.column_stack([x, y, z])
            r = np.sqrt(x**2 + y**2)
            labels = refine_clusters(points, labels, r)

    # Add cluster labels to DataFrame
    tpc_data = tpc_data.copy()
    tpc_data['cluster_id'] = labels

    return labels, tpc_data


def multi_scale_clustering(
    tpc_data: pd.DataFrame,
    scales: Optional[List[Dict]] = None,
) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Multi-scale clustering approach for varying track densities.

    Runs clustering at multiple scales and combines results.

    Args:
        tpc_data: DataFrame with TPC hits.
        scales: List of scale configurations. If None, uses config.

    Returns:
        Tuple of (cluster labels, DataFrame with cluster assignments).
    """
    if scales is None:
        params = get_clustering_params()
        scales = params.get('scales', [
            {'eps': 0.35, 'min_samples': 3, 'scale_xyz': [5.0, 5.0, 5.0]},
            {'eps': 0.55, 'min_samples': 4, 'scale_xyz': [10.0, 10.0, 10.0]},
            {'eps': 0.80, 'min_samples': 5, 'scale_xyz': [20.0, 20.0, 20.0]},
        ])

    x = tpc_data['x'].values
    y = tpc_data['y'].values
    z = tpc_data['z'].values

    if len(x) < 3:
        labels = np.full(len(x), -1)
        tpc_data = tpc_data.copy()
        tpc_data['cluster_id'] = labels
        return labels, tpc_data

    # Start with all points unclustered
    final_labels = np.full(len(x), -1)
    next_label = 0

    unclustered_mask = np.ones(len(x), dtype=bool)

    for scale_cfg in scales:
        eps = scale_cfg.get('eps', 0.5)
        min_samples = scale_cfg.get('min_samples', 3)
        scale_xyz = scale_cfg.get('scale_xyz', [1.0, 1.0, 1.0])

        if unclustered_mask.sum() < min_samples:
            break

        # Scale coordinates
        points = np.column_stack([
            x[unclustered_mask] / scale_xyz[0],
            y[unclustered_mask] / scale_xyz[1],
            z[unclustered_mask] / scale_xyz[2],
        ])

        # Cluster (using GPU if available)
        gpu = get_backend()
        if _use_gpu_clustering():
            points_gpu = gpu.to_gpu(points.astype(np.float32))
            db = CuMLDBSCAN(eps=eps, min_samples=min_samples)
            labels = db.fit_predict(points_gpu)
            labels = gpu.to_numpy(labels).astype(np.int32)
        else:
            db = SklearnDBSCAN(eps=eps, min_samples=min_samples)
            labels = db.fit_predict(points)

        # Assign labels
        unclustered_indices = np.where(unclustered_mask)[0]
        for i, idx in enumerate(unclustered_indices):
            if labels[i] >= 0:
                final_labels[idx] = next_label + labels[i]
                unclustered_mask[idx] = False

        n_new = len(set(labels) - {-1})
        next_label += n_new

    # Add cluster labels to DataFrame
    tpc_data = tpc_data.copy()
    tpc_data['cluster_id'] = final_labels

    return final_labels, tpc_data


