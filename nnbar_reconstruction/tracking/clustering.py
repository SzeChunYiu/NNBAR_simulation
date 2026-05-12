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
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from .clustering_backends import (
    CuMLDBSCAN,
    CuMLNearestNeighbors,
    SklearnDBSCAN,
    SklearnNearestNeighbors,
    get_backend,
    use_gpu_clustering as _use_gpu_clustering,
)
from .clustering_refinement import (
    merge_collinear_fragments,
    refine_clusters,
    split_by_direction,
    split_by_radial_clustering,
    split_by_z_gap,
    split_clusters_by_perp_bimodality,
)
from .clustering_variants import (
    cluster_with_gpu_dbscan,
    cluster_with_hdbscan,
    multi_scale_clustering,
)
from ..utils.config import get_clustering_params
from ..utils.coordinates import cartesian_to_cylindrical


logger = logging.getLogger(__name__)

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
