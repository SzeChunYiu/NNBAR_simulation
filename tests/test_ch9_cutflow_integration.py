from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd

from nnbar_reconstruction.analysis.event_selection import apply_selection_cuts
from nnbar_reconstruction.analysis.event_variables import EventVariables
from nnbar_reconstruction.reconstruction.timing_window import scintillator_timing_window


def make_event_variables(**overrides):
    values = dict(
        invariant_mass=1880.0,
        sphericity=0.5,
        total_energy=1900.0,
        scint_energy=400.0,
        lg_energy=1200.0,
        longitudinal_energy=0.0,
        transverse_energy=0.0,
        top_bottom_asymmetry=0.99,
        forward_backward_asymmetry=0.0,
        n_charged=2,
        n_neutral=1,
        n_pions=1,
        n_protons=0,
        vertex_r=999.0,
        n_tracks_to_vertex=1,
    )
    values.update(overrides)
    return EventVariables(**values)


def test_default_selection_uses_table_9_1_not_legacy_asymmetry_or_vertex_cuts():
    """A Table 9.1-passing event must pass by default even if legacy cuts fail."""
    ev = make_event_variables()

    result = apply_selection_cuts(ev)

    assert result.passed is True
    assert tuple(result.cut_results) == (
        "scintillator_energy",
        "tpc_tracks",
        "pion_count",
        "invariant_mass",
        "sphericity",
        "filtered_scintillator_balance",
    )
    assert "top_bottom_asymmetry" not in result.cut_results
    assert "vertex_radius" not in result.cut_results


def test_legacy_cuts_are_preserved_when_explicitly_requested():
    ev = make_event_variables()

    result = apply_selection_cuts(ev, cuts=["top_bottom_asymmetry", "vertex_radius"])

    assert result.passed is False
    assert result.cut_results == {
        "top_bottom_asymmetry": False,
        "vertex_radius": False,
    }


def test_event_variables_to_dict_exposes_filtered_scintillator_observables():
    ev = make_event_variables(
        filtered_scintillator_upper_mev=12.0,
        filtered_scintillator_lower_mev=34.0,
    )

    ev_dict = ev.to_dict()

    assert ev_dict["filtered_scintillator_upper_mev"] == 12.0
    assert ev_dict["filtered_scintillator_lower_mev"] == 34.0


def test_scintillator_filtered_energy_uses_timing_window_and_hemisphere_split():
    from nnbar_reconstruction.reconstruction.timing_window import (
        compute_filtered_scintillator_hemisphere_energies,
    )

    vertex = np.array([0.0, 0.0, 0.0])
    t0 = 25.0
    sigma = 1.0
    upper_pos = np.array([0.0, 100.0, 0.0])
    lower_pos = np.array([0.0, -100.0, 0.0])
    center_pos = np.array([0.0, 0.0, 100.0])

    upper_window = scintillator_timing_window(vertex, upper_pos, t0, sigma=sigma)
    lower_window = scintillator_timing_window(vertex, lower_pos, t0, sigma=sigma)
    center_window = scintillator_timing_window(vertex, center_pos, t0, sigma=sigma)

    hits = pd.DataFrame(
        [
            # In-window hits should not contribute to filtered energy.
            {"x": upper_pos[0], "y": upper_pos[1], "z": upper_pos[2], "t": sum(upper_window) / 2.0, "eDep": 11.0},
            {"x": lower_pos[0], "y": lower_pos[1], "z": lower_pos[2], "t": sum(lower_window) / 2.0, "eDep": 13.0},
            # Out-of-window hits should contribute in their hemisphere.
            {"x": upper_pos[0], "y": upper_pos[1], "z": upper_pos[2], "t": upper_window[1] + 5.0, "eDep": 120.0},
            {"x": lower_pos[0], "y": lower_pos[1], "z": lower_pos[2], "t": lower_window[0] - 5.0, "eDep": 240.0},
            # y == 0 is intentionally excluded from both thesis hemispheres.
            {"x": center_pos[0], "y": center_pos[1], "z": center_pos[2], "t": center_window[1] + 5.0, "eDep": 999.0},
        ]
    )

    filtered = compute_filtered_scintillator_hemisphere_energies(
        hits,
        vertex=vertex,
        t0=t0,
        sigma=sigma,
    )

    assert filtered == SimpleNamespace(upper_mev=120.0, lower_mev=240.0)
