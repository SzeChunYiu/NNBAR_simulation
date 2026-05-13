import numpy as np
import pandas as pd

from nnbar_reconstruction.reconstruction.charged_reconstruction import (
    count_scintillator_layers,
)


class DummyTrack:
    def __init__(self):
        self.head = np.array([0.0, 0.0, 0.0])
        self.direction = np.array([1.0, 0.0, 0.0])


def _scint_hits(layer_ids):
    return pd.DataFrame(
        {
            "x": np.arange(1, len(layer_ids) + 1, dtype=float),
            "y": np.zeros(len(layer_ids)),
            "z": np.zeros(len(layer_ids)),
            "Layer_ID": layer_ids,
            "eDep": np.ones(len(layer_ids)),
        }
    )


def test_scintillator_range_counts_all_ten_zero_based_simulation_layers():
    hits = _scint_hits(range(10))

    assert count_scintillator_layers(DummyTrack(), hits) == 10


def test_scintillator_range_counts_thesis_one_based_layer_examples():
    all_layers = _scint_hits(range(1, 11))
    missing_two_layers = _scint_hits([1, 2, 3, 5, 6, 7, 9, 10])

    assert count_scintillator_layers(DummyTrack(), all_layers) == 10
    assert count_scintillator_layers(DummyTrack(), missing_two_layers) == 8


def test_scintillator_range_ignores_invalid_layers_beyond_configured_count():
    hits = _scint_hits([-1, *range(10), 10, 99])

    assert count_scintillator_layers(DummyTrack(), hits) == 10
