"""
TPC Track Finding Module

Implements DBSCAN-based clustering for finding tracks from raw TPC hits,
with multiple splitting strategies and PCA-based track fitting.

Also includes signal/Compton separation with both geometric and ML-based methods.
"""

from .clustering import (
    cluster_tpc_hits,
    dbscan_clustering,
    adaptive_epsilon,
)
from .track_fitting import (
    pca_line_fit,
    fit_track,
    fit_all_tracks,
    Track,
)
from .signal_separation import (
    separate_signal_compton,
    classify_track_origin,
    compute_signal_probability,
    filter_tracks_by_signal_probability,
    # ML-based methods
    load_psignal_model,
    is_psignal_model_loaded,
    compute_signal_probability_ml,
    separate_signal_compton_ml,
    compute_signal_probabilities_batch,
)
from .evaluate_clustering import (
    evaluate_clustering,
    evaluate_event_clustering,
    evaluate_all_events,
    save_detailed_report,
    print_clustering_summary,
    ClusteringMetrics,
    EventClusteringResult,
)

__all__ = [
    # Clustering
    "cluster_tpc_hits",
    "dbscan_clustering",
    "adaptive_epsilon",
    "fit_all_tracks",
    # Track fitting
    "pca_line_fit",
    "fit_track",
    "Track",
    # Signal separation (geometric)
    "separate_signal_compton",
    "classify_track_origin",
    "compute_signal_probability",
    "filter_tracks_by_signal_probability",
    # Signal separation (ML)
    "load_psignal_model",
    "is_psignal_model_loaded",
    "compute_signal_probability_ml",
    "separate_signal_compton_ml",
    "compute_signal_probabilities_batch",
    # Clustering evaluation
    "evaluate_clustering",
    "evaluate_event_clustering",
    "evaluate_all_events",
    "save_detailed_report",
    "print_clustering_summary",
    "ClusteringMetrics",
    "EventClusteringResult",
]
