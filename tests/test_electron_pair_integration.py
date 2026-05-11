"""Regression tests for Ch.8 e+/e- conversion-pair integration."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np


def _charged_object(object_id: int, entry, particle_type: str = "PION_PLUS"):
    return SimpleNamespace(
        object_id=object_id,
        tpc_entry=np.array(entry, dtype=float),
        particle_type=particle_type,
        pid_confidence=0.75,
    )


def test_identify_electron_pair_includes_five_cm_boundary():
    from nnbar_reconstruction.reconstruction.object_identification import (
        identify_electron_pair,
    )

    origin = np.zeros(3)

    below, below_distance = identify_electron_pair(
        origin,
        np.array([4.999, 0.0, 0.0]),
        max_distance=5.0,
    )
    at_boundary, boundary_distance = identify_electron_pair(
        origin,
        np.array([3.0, 4.0, 0.0]),
        max_distance=5.0,
    )
    above, above_distance = identify_electron_pair(
        origin,
        np.array([5.001, 0.0, 0.0]),
        max_distance=5.0,
    )

    assert bool(below) is True
    assert below_distance < 5.0
    assert bool(at_boundary) is True
    assert boundary_distance == 5.0
    assert bool(above) is False
    assert above_distance > 5.0


def test_pair_rows_are_counted_once_for_event_output():
    from nnbar_reconstruction.reconstruction.electron_pair import (
        apply_electron_pair_labels,
        electron_pair_event_counts,
    )

    charged = [
        _charged_object(10, [0.0, 0.0, 0.0]),
        _charged_object(11, [3.0, 4.0, 0.0], particle_type="PION_MINUS"),
        _charged_object(12, [25.0, 0.0, 0.0]),
    ]

    pairs = apply_electron_pair_labels(charged, max_distance_cm=5.0)
    counts = electron_pair_event_counts(charged)

    assert len(pairs) == 1
    assert pairs[0].object_ids == (10, 11)
    assert pairs[0].distance_cm == 5.0
    assert charged[0].particle_type == "ELECTRON_PAIR"
    assert charged[1].particle_type == "ELECTRON_PAIR_MEMBER"
    assert counts["n_electron_pairs"] == 1
    assert counts["electron_pair_count_blocked"] is False


def test_downstream_pion_count_excludes_electron_pair_members():
    from nnbar_reconstruction.analysis.event_variables import count_particles
    from nnbar_reconstruction.reconstruction.electron_pair import (
        apply_electron_pair_labels,
        electron_pair_event_counts,
    )

    charged = [
        _charged_object(20, [0.0, 0.0, 0.0]),
        _charged_object(21, [3.0, 4.0, 0.0], particle_type="PION_MINUS"),
        _charged_object(22, [30.0, 0.0, 0.0]),
    ]

    apply_electron_pair_labels(charged, max_distance_cm=5.0)

    particle_counts = count_particles(charged, neutral_objects=[])
    pair_counts = electron_pair_event_counts(charged)

    assert particle_counts["pions"] == 1
    assert pair_counts["n_electron_pairs"] == 1


def test_event_count_reports_blocker_when_tpc_entries_are_missing():
    from nnbar_reconstruction.reconstruction.electron_pair import (
        electron_pair_event_counts,
    )

    counts = electron_pair_event_counts([
        SimpleNamespace(object_id=30, particle_type="PION_PLUS"),
        SimpleNamespace(object_id=31, particle_type="PION_MINUS"),
    ])

    assert counts["n_electron_pairs"] == 0
    assert counts["electron_pair_count_blocked"] is True
    assert counts["electron_pair_blocker_reason"] == "missing_tpc_entry"
