import numpy as np
import pandas as pd

from nnbar_reconstruction.tracking.track_fitting import Track, compute_track_dedx


def _track(n_hits: int) -> Track:
    return Track(
        track_id=7,
        center=np.array([0.0, 0.0, 0.0]),
        direction=np.array([1.0, 0.0, 0.0]),
        head=np.array([0.0, 0.0, 0.0]),
        tail=np.array([8.0, 0.0, 0.0]),
        length=8.0,
        n_hits=n_hits,
        rms_residual=0.0,
        linearity=1.0,
        hit_indices=np.arange(n_hits),
        total_electrons=0.0,
        total_energy_dep=80.0,
    )


def _layered_hits(include_electrons: bool = True) -> pd.DataFrame:
    rows = []
    layer_specs = [
        # layer, x0, x1, electrons total, eDep total
        (0, 0.0, 2.0, 20.0, 2000.0),
        (1, 2.0, 4.0, 100.0, 20.0),
        (2, 4.0, 6.0, 40.0, 1000.0),
        (3, 6.0, 8.0, 200.0, 40.0),
    ]
    for layer, x0, x1, electrons, e_dep in layer_specs:
        first = {
            "Layer_ID": layer,
            "x": x0,
            "y": 0.0,
            "z": 0.0,
            "eDep": e_dep / 2.0,
        }
        second = {
            "Layer_ID": layer,
            "x": x1,
            "y": 0.0,
            "z": 0.0,
            "eDep": e_dep / 2.0,
        }
        if include_electrons:
            first["electrons"] = electrons / 2.0
            second["electrons"] = electrons / 2.0
        rows.extend([first, second])
    return pd.DataFrame(rows)


def test_compute_track_dedx_prefers_electrons_per_layer_over_edep():
    hits = _layered_hits(include_electrons=True)

    truncated, layers = compute_track_dedx(_track(len(hits)), hits, truncation=0.6)

    np.testing.assert_allclose(layers, np.array([10.0, 50.0, 20.0, 100.0]))
    # Four layers keep max(1, int(4 * 0.6)) == 2 lowest values: 10 and 20 e-/cm.
    assert truncated == 15.0


def test_compute_track_dedx_legacy_edep_fallback_is_explicit_without_electrons():
    hits = _layered_hits(include_electrons=False)

    truncated, layers = compute_track_dedx(_track(len(hits)), hits, truncation=0.6)

    np.testing.assert_allclose(layers, np.array([1000.0, 10.0, 500.0, 20.0]))
    # Four layers keep max(1, int(4 * 0.6)) == 2 lowest legacy MeV/cm values.
    assert truncated == 15.0
