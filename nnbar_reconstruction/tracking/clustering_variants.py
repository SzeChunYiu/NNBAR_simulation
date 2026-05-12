"""Alternative TPC clustering entry points."""

import logging
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .clustering_backends import (
    CuMLDBSCAN,
    SklearnDBSCAN,
    get_backend,
    use_gpu_clustering,
)
from ..utils.config import get_clustering_params


logger = logging.getLogger(__name__)

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
        if use_gpu_clustering():
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



def cluster_with_hdbscan(
    xyz: np.ndarray,
    min_cluster_size=5,
    min_samples=3,
) -> np.ndarray:
    """Cluster 3-D hit coordinates using HDBSCAN.

    Args:
        xyz: (N, 3) array of (x, y, z) coordinates.
        min_cluster_size: Minimum number of points to form a cluster.
        min_samples: Conservative clustering control passed to HDBSCAN.

    Returns:
        1-D integer labels with -1 marking noise.

    Raises:
        ImportError: If the optional ``hdbscan`` package is unavailable.
    """
    if len(xyz) < min_cluster_size:
        logger.debug(
            "cluster_with_hdbscan: %d points < min_cluster_size=%d; all noise.",
            len(xyz),
            min_cluster_size,
        )
        return np.full(len(xyz), -1, dtype=np.int32)

    try:
        import hdbscan as hdbscan_lib
    except ImportError as exc:
        raise ImportError(
            "hdbscan package is required for cluster_with_hdbscan; "
            "install it with `pip install hdbscan`."
        ) from exc

    clusterer = hdbscan_lib.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
    )
    labels = clusterer.fit_predict(xyz.astype(np.float64))
    n_clusters = len(set(labels.tolist()) - {-1})
    logger.info(
        "HDBSCAN: found %d cluster(s), %d noise point(s) from %d inputs.",
        n_clusters,
        int(np.sum(labels == -1)),
        len(xyz),
    )
    return labels.astype(np.int32)

def cluster_with_gpu_dbscan(
    xyz: np.ndarray,
    eps=2.0,
    min_samples=3,
) -> np.ndarray:
    """Cluster 3-D hit coordinates with optional cuML GPU DBSCAN.

    GPU execution is attempted only when ``NNBAR_ENABLE_GPU=1`` is set.
    Any missing dependency or runtime error falls back to sklearn DBSCAN.

    Args:
        xyz: (N, 3) array of (x, y, z) coordinates.
        eps: Neighbourhood radius for DBSCAN.
        min_samples: Minimum samples for a core point.

    Returns:
        1-D integer labels with -1 marking noise.
    """
    if len(xyz) < min_samples:
        return np.full(len(xyz), -1, dtype=np.int32)

    labels = None
    backend = 'sklearn'
    if os.getenv('NNBAR_ENABLE_GPU', '0') == '1':
        try:
            from cuml.cluster import DBSCAN as cuDBSCAN
            db = cuDBSCAN(eps=eps, min_samples=min_samples)
            labels_raw = db.fit_predict(xyz.astype(np.float32))
            try:
                labels = labels_raw.to_numpy()
            except AttributeError:
                labels = labels_raw
            labels = np.asarray(labels, dtype=np.int32)
            backend = 'cuml'
        except ImportError:
            logger.debug(
                "NNBAR_ENABLE_GPU=1 but cuml is unavailable; using sklearn DBSCAN."
            )
        except Exception as exc:
            logger.warning("cuML DBSCAN failed (%s); using sklearn DBSCAN.", exc)

    if labels is None:
        db = SklearnDBSCAN(eps=eps, min_samples=min_samples)
        labels = db.fit_predict(xyz).astype(np.int32)

    logger.info(
        "DBSCAN backend=%s produced %d cluster(s) from %d inputs.",
        backend,
        len(set(labels.tolist()) - {-1}),
        len(xyz),
    )
    return labels
