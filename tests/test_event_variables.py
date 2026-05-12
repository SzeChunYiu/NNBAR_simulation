from __future__ import annotations

from types import SimpleNamespace
from typing import get_type_hints

import numpy as np

from nnbar_reconstruction.analysis import event_variables as event_variables_module
from nnbar_reconstruction.analysis.event_variables import (
    compute_event_variables,
    compute_longitudinal_energy,
    compute_transverse_energy,
)
from nnbar_reconstruction.utils.coordinates import (
    compute_sphericity,
    compute_total_invariant_mass,
)


def _charged_for_event(entry=(0.0, 0.0, 0.0), particle_type="PION_PLUS"):
    return SimpleNamespace(
        energy=100.0,
        momentum=np.array([1.0, 0.0, 0.0]),
        momentum_magnitude=100.0,
        scint_energy=10.0,
        lg_energy=20.0,
        track=SimpleNamespace(center=np.array([0.0, 1.0, 1.0])),
        tpc_entry=None if entry is None else np.array(entry, dtype=float),
        particle_type=particle_type,
    )


def test_sphericity_uses_momentum_magnitudes_not_unit_directions():
    """Unequal MeV/c momenta should weight the tensor by |p|^2."""
    momenta_mev_c = np.array(
        [
            [10.0, 0.0, 0.0],
            [-10.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
    )

    assert compute_sphericity(momenta_mev_c) == np.float64(1.5 / 201.0)


def test_sphericity_handles_empty_single_and_zero_momentum_inputs():
    assert compute_sphericity(np.empty((0, 3))) == 0.0
    assert compute_sphericity(np.array([[1.0, 0.0, 0.0]])) == 0.0
    assert compute_sphericity(np.zeros((3, 3))) == 0.0


def test_longitudinal_energy_preserves_forward_backward_sign():
    charged = [SimpleNamespace(energy=100.0, momentum=np.array([0.0, 0.0, 2.0]))]
    neutral = [SimpleNamespace(energy=40.0, direction=np.array([0.0, 0.0, -3.0]))]

    longitudinal_mev = compute_longitudinal_energy(
        charged,
        neutral,
        vertex=np.zeros(3),
        beam_axis=np.array([0.0, 0.0, 5.0]),
    )

    assert longitudinal_mev == 60.0


def test_invariant_mass_smoke_case_reports_mev():
    energies_mev = np.array([100.0, 100.0])
    momenta_mev_c = np.array(
        [
            [100.0, 0.0, 0.0],
            [0.0, 100.0, 0.0],
        ]
    )

    invariant_mass_mev = compute_total_invariant_mass(energies_mev, momenta_mev_c)

    np.testing.assert_allclose(invariant_mass_mev, np.sqrt(20_000.0))


def test_transverse_energy_smoke_case_reports_mev_and_clips_directions():
    charged = [SimpleNamespace(energy=50.0, momentum=np.array([2.0, 0.0, 0.0]))]
    neutral = [SimpleNamespace(energy=100.0, direction=np.array([0.0, 0.0, 5.0]))]

    transverse_mev = compute_transverse_energy(
        charged,
        neutral,
        vertex=np.zeros(3),
        beam_axis=np.array([0.0, 0.0, 10.0]),
    )

    np.testing.assert_allclose(transverse_mev, 50.0)


def test_event_variables_to_dict_exposes_electron_pair_count():
    charged = [
        _charged_for_event([0.0, 0.0, 0.0], particle_type="ELECTRON_PAIR"),
        _charged_for_event([3.0, 4.0, 0.0], particle_type="ELECTRON_PAIR_MEMBER"),
    ]

    ev_dict = compute_event_variables(
        charged,
        neutral_objects=[],
        vertex=np.zeros(3),
    ).to_dict()

    assert ev_dict["n_electron_pairs"] == 1
    assert ev_dict["electron_pair_count_blocked"] is False
    assert ev_dict["electron_pair_blocker_reason"] == ""


def test_event_variables_reports_electron_pair_blocker_without_tpc_entries():
    charged = [
        _charged_for_event(entry=None, particle_type="PION_PLUS"),
        _charged_for_event(entry=None, particle_type="PION_MINUS"),
    ]

    ev_dict = compute_event_variables(
        charged,
        neutral_objects=[],
        vertex=np.zeros(3),
    ).to_dict()

    assert ev_dict["n_electron_pairs"] == 0
    assert ev_dict["electron_pair_count_blocked"] is True
    assert ev_dict["electron_pair_blocker_reason"] == "missing_tpc_entry"


def test_compute_event_variables_type_hints_resolve_scintillator_dataframe():
    """Runtime type-hint introspection should resolve optional scintillator hits."""
    globalns = {
        **vars(event_variables_module),
        "ChargedObject": object,
        "NeutralObject": object,
    }
    hints = get_type_hints(compute_event_variables, globalns=globalns)

    assert "scintillator_hits" in hints
