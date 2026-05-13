from __future__ import annotations

import math


def test_identify_neutral_pion_uses_canonical_ch8_cuts_when_config_drifts(monkeypatch):
    from nnbar_reconstruction.reconstruction import object_identification as oi

    monkeypatch.setattr(
        oi,
        "get_particle_id_params",
        lambda: {
            "pi0_mass_min": 1.0,
            "pi0_mass_max": 10.0,
            "pi0_energy_max": 100.0,
            "pi0_scint_max": 1.0,
            "pi0_lg_max": 100.0,
            "pi0_lg_fraction_min": 0.99,
            "pi0_opening_angle_min": 89.0,
        },
    )

    candidate = oi.identify_neutral_pion(
        photon1_energy=130.0,
        photon2_energy=130.0,
        opening_angle=math.radians(60.0),
        scint_energy1=20.0,
        scint_energy2=20.0,
        lg_energy1=90.0,
        lg_energy2=90.0,
    )

    assert candidate.is_pi0 is True
    assert math.isclose(candidate.invariant_mass, 130.0, abs_tol=1e-9)
    assert math.isclose(candidate.lg_fraction, 180.0 / 260.0, rel_tol=1e-12)
