"""
Vertex Reconstruction Module

Implements both classical (weighted average) and ML-based (GNN) vertex reconstruction.

Also includes P-Signal classification for signal/Compton track separation.
"""

from .classical_vertex import (
    project_track_to_target,
    weighted_vertex_reconstruction,
    reconstruct_vertex,
    VertexResult,
)

from .evaluate_vertex import (
    evaluate_vertex_reconstruction,
    compute_vertex_residuals,
    compute_vertex_metrics,
    compare_methods,
    save_vertex_report,
    print_vertex_summary,
    print_comparison_summary,
    VertexMetrics,
    VertexResidual,
    MethodComparison,
)

from .psignal_model import (
    PointNetMini,
    PSignalPredictor,
    PSignalConfig,
    normalize_hits,
    build_knn_graph,
    heuristic_psignal,
    extract_track_features,
    HAS_TORCH_GEOMETRIC,
)

# GNN imports (may not be available without torch_geometric)
try:
    from .psignal_model import TrackGNN, EdgeConvLayer
    from .gnn_model import NNBARVertexGNN, NNBARVertexGNNV2
except ImportError:
    TrackGNN = None
    EdgeConvLayer = None
    NNBARVertexGNN = None
    NNBARVertexGNNV2 = None

__all__ = [
    # Classical vertex
    "project_track_to_target",
    "weighted_vertex_reconstruction",
    "reconstruct_vertex",
    "VertexResult",
    # Vertex evaluation
    "evaluate_vertex_reconstruction",
    "compute_vertex_residuals",
    "compute_vertex_metrics",
    "compare_methods",
    "save_vertex_report",
    "print_vertex_summary",
    "print_comparison_summary",
    "VertexMetrics",
    "VertexResidual",
    "MethodComparison",
    # P-Signal models
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
    # GNN vertex models
    "NNBARVertexGNN",
    "NNBARVertexGNNV2",
]
