from __future__ import annotations

from nnbar_reconstruction.reconstruction.cutflow import EventCutObservables


def test_ch10_cutflow_order_matches_thesis_table():
    from nnbar_reconstruction.reconstruction.cutflow import CH10_CUTFLOW_ORDER

    assert CH10_CUTFLOW_ORDER == (
        "scintillator_energy",
        "tpc_tracks",
        "pion_count",
        "invariant_mass",
        "sphericity",
        "filtered_scintillator_balance",
    )


def test_lane_pi0_event_gate_order_is_pinned_for_future_pi0_selection():
    from nnbar_reconstruction.reconstruction.cutflow import PI0_EVENT_GATE_ORDER

    assert PI0_EVENT_GATE_ORDER == (
        "charged_tracks",
        "pi0_candidate",
        "fiducial_vertex",
        "visible_energy",
    )


def test_ch10_cutflow_thresholds_match_thesis_table():
    from nnbar_reconstruction.reconstruction.cutflow import (
        FILTERED_SCINTILLATOR_LOWER_MAX_MEV,
        FILTERED_SCINTILLATOR_UPPER_MAX_MEV,
        MIN_INVARIANT_MASS_MEV,
        MIN_PION_COUNT,
        MIN_SPHERICITY,
        MIN_TPC_TRACKS_TO_VERTEX,
        SCINTILLATOR_ENERGY_WINDOW_MEV,
    )

    assert SCINTILLATOR_ENERGY_WINDOW_MEV == (20.0, 2000.0)
    assert MIN_TPC_TRACKS_TO_VERTEX == 1
    assert MIN_PION_COUNT == 1
    assert MIN_INVARIANT_MASS_MEV == 500.0
    assert MIN_SPHERICITY == 0.2
    assert FILTERED_SCINTILLATOR_UPPER_MAX_MEV == 320.0
    assert FILTERED_SCINTILLATOR_LOWER_MAX_MEV == 930.0


def test_apply_ch10_cutflow_reports_first_failed_cut_in_order():
    from nnbar_reconstruction.reconstruction.cutflow import apply_ch10_cutflow

    event = EventCutObservables(
        scintillator_energy_mev=2500.0,
        tpc_tracks_to_vertex=0,
        pion_count=0,
        invariant_mass_mev=100.0,
        sphericity=0.0,
        filtered_scintillator_upper_mev=500.0,
        filtered_scintillator_lower_mev=1000.0,
    )

    result = apply_ch10_cutflow(event)

    assert result.passed is False
    assert result.first_failed_cut == "scintillator_energy"
    assert result.cut_results["scintillator_energy"] is False
    assert result.cut_results["tpc_tracks"] is False


def test_signal_efficiency_exceeds_60_percent_on_synthetic_signal_like_events():
    from nnbar_reconstruction.reconstruction.cutflow import compute_signal_efficiency

    passing = EventCutObservables(100.0, 1, 1, 1880.0, 0.5, 100.0, 200.0)
    failing = EventCutObservables(100.0, 0, 1, 1880.0, 0.5, 100.0, 200.0)
    events = [passing] * 7 + [failing] * 3

    assert compute_signal_efficiency(events) > 0.60


def test_background_rejection_exceeds_80_percent_on_synthetic_background_like_events():
    from nnbar_reconstruction.reconstruction.cutflow import compute_background_rejection

    rejected = EventCutObservables(2500.0, 0, 0, 100.0, 0.0, 500.0, 1000.0)
    accepted = EventCutObservables(100.0, 1, 1, 1880.0, 0.5, 100.0, 200.0)
    events = [rejected] * 9 + [accepted]

    assert compute_background_rejection(events) > 0.80
