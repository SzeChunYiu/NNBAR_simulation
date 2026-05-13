from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from nnbar_reconstruction.analysis.event_variables import (
    compute_longitudinal_energy,
    compute_transverse_energy,
)
from nnbar_reconstruction.utils.coordinates import (
    compute_sphericity,
    compute_total_invariant_mass,
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
