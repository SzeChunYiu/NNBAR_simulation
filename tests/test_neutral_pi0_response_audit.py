from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from nnbar_reconstruction.analysis.neutral_pi0_response_audit import (
    PI0_SAMPLE_ENERGIES_MEV,
    THESIS_PI0_MASS_PEAK_MEV,
    audit_pi0_response,
    discover_pi0_sample,
    run_audit,
)


def _codes(report) -> set[str]:
    return {blocker.code for blocker in report.blockers}


def _toy_pi0_parquet(path: Path, *, mass_center: float = 135.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    offsets = [-4.0, -2.0, 0.0, 2.0, 4.0]
    pd.DataFrame(
        {
            "event_id": list(range(len(offsets))),
            "pi0_mass_mev": [mass_center + offset for offset in offsets],
            "opening_angle_deg": [34.0, 35.0, 36.0, 37.0, 38.0],
            "truth_photon_energy_mev": [70.0, 71.0, 72.0, 73.0, 74.0],
            "reco_photon_energy_mev": [70.5, 71.5, 72.5, 73.5, 74.5],
        }
    ).to_parquet(path, index=False)
    return path


def test_empty_search_root_fails_closed_for_all_three_required_samples(tmp_path):
    reports = run_audit(tmp_path)

    assert [report.energy_mev for report in reports] == list(PI0_SAMPLE_ENERGIES_MEV)
    assert [report.ready for report in reports] == [False, False, False]
    for report in reports:
        assert report.parquet_path is None
        assert f"pi0_{report.energy_mev}mev_sample_missing" in _codes(report)


def test_discover_pi0_sample_locates_existing_monoenergetic_parquet(tmp_path):
    expected = _toy_pi0_parquet(tmp_path / "pi0_150MeV" / "Particle_output_0.parquet")
    _toy_pi0_parquet(tmp_path / "pi0_50MeV" / "Particle_output_0.parquet")

    assert discover_pi0_sample(150, tmp_path) == expected


def test_synthetic_pi0_mass_opening_angle_and_energy_bias_pass(tmp_path):
    sample = _toy_pi0_parquet(tmp_path / "pi0_150MeV" / "Particle_output_0.parquet")

    report = audit_pi0_response(sample, 150)

    assert report.ready is True
    assert report.blockers == ()
    assert report.mass_peak_mev == pytest.approx(135.0)
    assert report.mass_peak_mev == pytest.approx(THESIS_PI0_MASS_PEAK_MEV, abs=1.0)
    assert report.mass_sigma_mev > 0.0
    assert report.opening_angle_mean_deg == pytest.approx(36.0)
    assert report.photon_energy_bias_mev == pytest.approx(0.5)


def test_shifted_mass_peak_triggers_off_thesis_blocker_with_offset(tmp_path):
    sample = _toy_pi0_parquet(
        tmp_path / "pi0_250MeV" / "Particle_output_0.parquet",
        mass_center=160.0,
    )

    report = audit_pi0_response(sample, 250)

    assert report.ready is False
    blockers = {blocker.code: blocker for blocker in report.blockers}
    assert "mass_peak_off_thesis" in blockers
    assert "26" in blockers["mass_peak_off_thesis"].reason
    assert "10" in blockers["mass_peak_off_thesis"].reason


def test_missing_opening_angle_distribution_is_blocked(tmp_path):
    sample = tmp_path / "pi0_50MeV" / "Particle_output_0.parquet"
    sample.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "pi0_mass_mev": [134.0, 135.0, 136.0],
            "truth_photon_energy_mev": [60.0, 61.0, 62.0],
            "reco_photon_energy_mev": [60.0, 61.0, 62.0],
        }
    ).to_parquet(sample, index=False)

    report = audit_pi0_response(sample, 50)

    assert report.ready is False
    assert "opening_angle_distribution_unverified" in _codes(report)
