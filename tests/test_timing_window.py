from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nnbar_reconstruction.reconstruction.timing_window import (
    apply_timing_cuts,
    compute_out_of_time_energy,
    leadglass_timing_window,
    photon_travel_time,
    pion_travel_time,
    scintillator_timing_window,
)


def _hit(position: np.ndarray, time_ns: float, energy_mev: float) -> dict[str, float]:
    return {
        "x": float(position[0]),
        "y": float(position[1]),
        "z": float(position[2]),
        "t": time_ns,
        "eDep": energy_mev,
    }


def test_scintillator_window_matches_chapter7_formula_and_closed_boundaries():
    vertex = np.array([0.0, 0.0, 0.0])
    stave = np.array([0.0, 150.0, 200.0])
    t0 = 12.5
    sigma = 1.25
    n_sigma = 2.0
    distance = np.linalg.norm(stave - vertex)

    lower, upper = scintillator_timing_window(
        vertex,
        stave,
        t0,
        sigma=sigma,
        n_sigma=n_sigma,
    )

    assert lower == pytest.approx(t0 + pion_travel_time(distance, 1000.0) - 2.0 * sigma)
    assert upper == pytest.approx(t0 + pion_travel_time(distance, 100.0) + 2.0 * sigma)

    hits = pd.DataFrame(
        [
            _hit(stave, lower - 1e-6, 10.0),
            _hit(stave, lower, 20.0),
            _hit(stave, upper, 30.0),
            _hit(stave, upper + 1e-6, 40.0),
        ]
    )

    accepted = apply_timing_cuts(
        hits,
        vertex=vertex,
        t0=t0,
        detector="scintillator",
        sigma=sigma,
        n_sigma=n_sigma,
    )

    assert accepted["eDep"].tolist() == [20.0, 30.0]


def test_scintillator_sigma_and_nsigma_overrides_change_acceptance_window():
    vertex = np.array([1.0, 2.0, 3.0])
    stave = np.array([11.0, -48.0, 123.0])
    t0 = -4.0
    distance = np.linalg.norm(stave - vertex)

    lower, upper = scintillator_timing_window(
        vertex,
        stave,
        t0,
        sigma=0.5,
        n_sigma=3.0,
    )

    assert lower == pytest.approx(t0 + pion_travel_time(distance, 1000.0) - 1.5)
    assert upper == pytest.approx(t0 + pion_travel_time(distance, 100.0) + 1.5)


def test_leadglass_window_matches_chapter7_formula_and_closed_boundaries():
    vertex = np.array([0.0, 0.0, 0.0])
    module = np.array([80.0, -60.0, 220.0])
    t0 = 9.0
    sigma = 2.25
    n_sigma = 2.0
    distance = np.linalg.norm(module - vertex)

    lower, upper = leadglass_timing_window(
        vertex,
        module,
        t0,
        sigma=sigma,
        n_sigma=n_sigma,
    )

    assert lower == pytest.approx(t0 + photon_travel_time(distance) - 2.0 * sigma)
    assert upper == pytest.approx(t0 + photon_travel_time(distance) + 2.0 * sigma)

    hits = pd.DataFrame(
        [
            _hit(module, lower - 1e-6, 10.0),
            _hit(module, lower, 20.0),
            _hit(module, upper, 30.0),
            _hit(module, upper + 1e-6, 40.0),
        ]
    )

    accepted = apply_timing_cuts(
        hits,
        vertex=vertex,
        t0=t0,
        detector="leadglass",
        sigma=sigma,
        n_sigma=n_sigma,
    )

    assert accepted["eDep"].tolist() == [20.0, 30.0]


def test_leadglass_filtered_energy_counts_only_out_of_window_hits():
    vertex = np.array([0.0, 0.0, 0.0])
    module = np.array([0.0, 125.0, 250.0])
    t0 = 5.0
    sigma = 1.75
    lower, upper = leadglass_timing_window(vertex, module, t0, sigma=sigma)

    hits = pd.DataFrame(
        [
            _hit(module, lower, 11.0),
            _hit(module, (lower + upper) / 2.0, 13.0),
            _hit(module, upper, 17.0),
            _hit(module, lower - 0.01, 23.0),
            _hit(module, upper + 0.01, 29.0),
        ]
    )

    filtered_mev = compute_out_of_time_energy(
        hits,
        vertex=vertex,
        t0=t0,
        detector="leadglass",
        sigma=sigma,
    )

    assert filtered_mev == pytest.approx(52.0)


def test_timing_helpers_reject_unknown_detector_names():
    vertex = np.array([0.0, 0.0, 0.0])
    hit_position = np.array([0.0, 125.0, 250.0])
    hits = pd.DataFrame([_hit(hit_position, time_ns=5.0, energy_mev=11.0)])

    with pytest.raises(ValueError, match="detector"):
        apply_timing_cuts(
            hits,
            vertex=vertex,
            t0=0.0,
            detector="lead_glass",
        )

    with pytest.raises(ValueError, match="detector"):
        compute_out_of_time_energy(
            hits,
            vertex=vertex,
            t0=0.0,
            detector="lead_glass",
        )
