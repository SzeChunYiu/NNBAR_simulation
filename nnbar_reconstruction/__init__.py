"""
NNBAR Event Reconstruction Pipeline
====================================

Complete analysis chain for the NNBAR n-nbar oscillation experiment.

Modules:
    calibration: Detector calibration (scintillator, lead glass, TPC)
    tracking: TPC track finding from raw hits
    vertex: Vertex reconstruction (classical and GNN-based)
    reconstruction: Physics object reconstruction
    analysis: Event variables and selection
    utils: Configuration, data loading, coordinate transforms
    plotting: Visualization tools

Usage:
    from nnbar_reconstruction import reconstruct_event
    from nnbar_reconstruction.utils import load_config, load_event_data
"""

__version__ = "1.0.0"
__author__ = "NNBAR Collaboration"

from .utils.config import load_config, get_config
from .utils.data_loader import load_event_data, load_parquet_files

__all__ = [
    "load_config",
    "get_config",
    "load_event_data",
    "load_parquet_files",
]
