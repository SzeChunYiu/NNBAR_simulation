"""Backend selection helpers for TPC clustering."""

import os

from sklearn.cluster import DBSCAN as SklearnDBSCAN
from sklearn.cluster import KMeans as SklearnKMeans
from sklearn.neighbors import NearestNeighbors as SklearnNearestNeighbors

from ..utils.gpu_backend import get_backend

_CUML_AVAILABLE = False
try:
    from cuml.cluster import DBSCAN as CuMLDBSCAN
    from cuml.cluster import KMeans as CuMLKMeans
    from cuml.neighbors import NearestNeighbors as CuMLNearestNeighbors

    _CUML_AVAILABLE = True
except ImportError:
    CuMLDBSCAN = None
    CuMLKMeans = None
    CuMLNearestNeighbors = None


def use_gpu_clustering() -> bool:
    """Return whether cuML clustering should be used for the current process."""
    if os.environ.get("NNBAR_FORCE_CPU", "0") == "1":
        return False
    gpu = get_backend()
    return gpu.use_gpu and _CUML_AVAILABLE and gpu.has_cuml
