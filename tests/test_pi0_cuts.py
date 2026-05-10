from __future__ import annotations

import math


def test_pi0_mass_window_matches_thesis_ch8():
    from nnbar_reconstruction.reconstruction.pi0_cuts import PI0_MASS_WINDOW_MEV

    assert PI0_MASS_WINDOW_MEV == (100.0, 180.0), "thesis Ch.8: diphoton mass in [100, 180] MeV"


def test_leadglass_fraction_keeps_local_and_final_thesis_values_distinct():
    from nnbar_reconstruction.reconstruction.pi0_cuts import (
        PI0_LOCAL_LEADGLASS_FRACTION_OPTIMUM,
        PI0_MIN_LEADGLASS_FRACTION,
    )

    assert PI0_LOCAL_LEADGLASS_FRACTION_OPTIMUM == 0.60, "thesis Ch.8: local significance optimum"
    assert PI0_MIN_LEADGLASS_FRACTION == 0.55, "thesis Ch.8 optimized criteria/table/summary: >55%"


def test_opening_angle_threshold_matches_optimized_thesis_cut():
    from nnbar_reconstruction.reconstruction.pi0_cuts import (
        PI0_LOCAL_OPENING_ANGLE_OPTIMUM_DEG,
        PI0_MIN_OPENING_ANGLE_DEG,
    )

    assert PI0_LOCAL_OPENING_ANGLE_OPTIMUM_DEG == 25.0, "thesis Ch.8: local significance optimum"
    assert PI0_MIN_OPENING_ANGLE_DEG == 30.0, "thesis Ch.8 optimized criteria/table: >30 degrees"


def test_pi0_energy_thresholds_match_thesis_ch8_optimized_criteria():
    from nnbar_reconstruction.reconstruction.pi0_cuts import (
        PI0_MAX_LEADGLASS_ENERGY_MEV,
        PI0_MAX_SCINTILLATOR_ENERGY_MEV,
        PI0_MAX_TOTAL_ENERGY_MEV,
    )

    assert PI0_MAX_SCINTILLATOR_ENERGY_MEV == 250.0
    assert PI0_MAX_LEADGLASS_ENERGY_MEV == 980.0
    assert PI0_MAX_TOTAL_ENERGY_MEV == 720.0


def test_pi0_candidate_selection_on_synthetic_accepts_signal_like_pair():
    from nnbar_reconstruction.reconstruction.pi0_cuts import evaluate_pi0_candidate

    result = evaluate_pi0_candidate(
        photon1_energy_mev=130.0,
        photon2_energy_mev=130.0,
        opening_angle_deg=60.0,
        scintillator_energy_mev=40.0,
        leadglass_energy_mev=180.0,
    )

    assert result.passed is True
    assert result.failed_cuts == ()
    assert math.isclose(result.invariant_mass_mev, 130.0, abs_tol=1e-9)
    assert math.isclose(result.leadglass_fraction, 180.0 / 260.0, abs_tol=1e-12)


def test_pi0_candidate_selection_rejects_each_failed_cut():
    from nnbar_reconstruction.reconstruction.pi0_cuts import evaluate_pi0_candidate

    cases = {
        "mass_window": dict(
            photon1_energy_mev=50.0,
            photon2_energy_mev=50.0,
            opening_angle_deg=90.0,
            scintillator_energy_mev=0.0,
            leadglass_energy_mev=60.0,
        ),
        "total_energy": dict(
            photon1_energy_mev=20.0,
            photon2_energy_mev=800.0,
            opening_angle_deg=60.0,
            scintillator_energy_mev=50.0,
            leadglass_energy_mev=500.0,
        ),
        "scintillator_energy": dict(
            photon1_energy_mev=100.0,
            photon2_energy_mev=100.0,
            opening_angle_deg=90.0,
            scintillator_energy_mev=260.0,
            leadglass_energy_mev=140.0,
        ),
        "leadglass_energy": dict(
            photon1_energy_mev=100.0,
            photon2_energy_mev=100.0,
            opening_angle_deg=90.0,
            scintillator_energy_mev=0.0,
            leadglass_energy_mev=1000.0,
        ),
        "leadglass_fraction": dict(
            photon1_energy_mev=100.0,
            photon2_energy_mev=100.0,
            opening_angle_deg=90.0,
            scintillator_energy_mev=80.0,
            leadglass_energy_mev=100.0,
        ),
        "opening_angle": dict(
            photon1_energy_mev=320.0,
            photon2_energy_mev=320.0,
            opening_angle_deg=25.0,
            scintillator_energy_mev=100.0,
            leadglass_energy_mev=400.0,
        ),
    }

    for failed_cut, kwargs in cases.items():
        result = evaluate_pi0_candidate(**kwargs)
        assert result.passed is False, failed_cut
        assert result.failed_cuts == (failed_cut,)


def test_pi0_failed_cuts_follow_thesis_efficiency_table_order():
    from nnbar_reconstruction.reconstruction.pi0_cuts import evaluate_pi0_candidate

    result = evaluate_pi0_candidate(
        photon1_energy_mev=20.0,
        photon2_energy_mev=800.0,
        opening_angle_deg=60.0,
        scintillator_energy_mev=260.0,
        leadglass_energy_mev=500.0,
    )

    assert result.failed_cuts == ("scintillator_energy", "total_energy")


def test_pi0_fraction_and_angle_boundaries_are_strict_thesis_table_cuts():
    from nnbar_reconstruction.reconstruction.pi0_cuts import evaluate_pi0_candidate

    fraction_at_threshold = evaluate_pi0_candidate(
        photon1_energy_mev=100.0,
        photon2_energy_mev=100.0,
        opening_angle_deg=90.0,
        scintillator_energy_mev=0.0,
        leadglass_energy_mev=110.0,
    )
    assert fraction_at_threshold.failed_cuts == ("leadglass_fraction",)

    energy_for_135_mev_at_30_deg = 135.0 / math.sqrt(2.0 * (1.0 - math.cos(math.radians(30.0))))
    angle_at_threshold = evaluate_pi0_candidate(
        photon1_energy_mev=energy_for_135_mev_at_30_deg,
        photon2_energy_mev=energy_for_135_mev_at_30_deg,
        opening_angle_deg=30.0,
        scintillator_energy_mev=0.0,
        leadglass_energy_mev=300.0,
    )
    assert angle_at_threshold.failed_cuts == ("opening_angle",)
