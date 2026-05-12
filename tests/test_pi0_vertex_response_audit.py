from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from nnbar_reconstruction.analysis.pi0_vertex_response_audit import (
    STUDY1_RADII_CM,
    audit_pi0_vertex_response,
    discover_pi0_reco_sample,
    run_vertex_response_audit,
)


def _codes(report) -> set[str]:
    return {blocker.code for blocker in report.blockers}


def _write_vertex_reco(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def _row(radius: float, event_id: int, *, reconstructed: bool = True, mass: float = 135.0) -> dict:
    return {
        "Event_ID": event_id,
        "truth_vertex_x_cm": radius,
        "truth_vertex_y_cm": 0.0,
        "truth_vertex_r_cm": radius,
        "truth_ke_mev": 150.0,
        "truth_total_energy_mev": 150.0,
        "n_neutral_objects": 2 if reconstructed else 1,
        "n_pi0_candidates": 1 if reconstructed else 0,
        "pi0_mass_mev": mass if reconstructed else None,
        "opening_angle_deg": 42.0 + radius if reconstructed else None,
        "reco_photon_energy_mev": 75.0,
        "truth_photon_energy_mev": 75.0,
        "reco_total_energy_mev": 153.0 if reconstructed else None,
        "reco_eff_flag": reconstructed,
    }


def test_discover_pi0_reco_sample_prefers_reco_response_file(tmp_path):
    raw = _write_vertex_reco(tmp_path / "pi0_150MeV" / "Particle_output_0.parquet", [_row(0.0, 1)])
    expected = _write_vertex_reco(tmp_path / "pi0_reco_response" / "pi0_reco_150mev.parquet", [_row(0.0, 2)])

    assert discover_pi0_reco_sample(150, tmp_path) == expected
    assert discover_pi0_reco_sample(250, tmp_path) is None
    assert raw.exists()


def test_missing_reco_sample_fails_closed_without_creating_outputs(tmp_path):
    reports = run_vertex_response_audit(tmp_path, energies_mev=(150,))

    assert len(reports) == 1
    report = reports[0]
    assert not report.ready
    assert report.parquet_path is None
    assert "pi0_vertex_150mev_sample_missing" in _codes(report)
    assert list(tmp_path.iterdir()) == []


def test_synthetic_vertex_scan_groups_radius_metrics(tmp_path):
    sample = _write_vertex_reco(
        tmp_path / "pi0_reco_response" / "pi0_reco_150mev.parquet",
        [
            _row(0.0, 1, mass=134.0),
            _row(0.0, 2, mass=136.0),
            _row(5.0, 3, mass=130.0),
            _row(5.0, 4, reconstructed=False),
            _row(5.0, 5, mass=140.0),
        ],
    )

    report = audit_pi0_vertex_response(sample, 150, expected_radii_cm=(0.0, 5.0))

    assert report.ready
    assert report.energy_mev == 150
    assert report.total_events == 5
    assert [bin.radius_cm for bin in report.radius_bins] == [0.0, 5.0]
    r0, r5 = report.radius_bins
    assert r0.n_events == 2
    assert r0.n_reconstructed == 2
    assert r0.efficiency == pytest.approx(1.0)
    assert r0.mass_peak_mev == pytest.approx(135.0)
    assert r0.mass_sigma_mev == pytest.approx(2**0.5)
    assert r0.energy_bias_fraction == pytest.approx(0.02)
    assert r5.n_events == 3
    assert r5.n_reconstructed == 2
    assert r5.efficiency == pytest.approx(2 / 3)
    assert r5.mass_peak_mev == pytest.approx(135.0)
    assert report.blockers == ()


def test_missing_required_vertex_or_reco_columns_blocks(tmp_path):
    sample = _write_vertex_reco(
        tmp_path / "pi0_reco_response" / "pi0_reco_150mev.parquet",
        [{"Event_ID": 1, "pi0_mass_mev": 135.0}],
    )

    report = audit_pi0_vertex_response(sample, 150, expected_radii_cm=(0.0,))

    assert not report.ready
    assert "truth_vertex_r_missing" in _codes(report)
    assert "reco_efficiency_flag_missing" in _codes(report)
    assert report.radius_bins == ()


def test_missing_expected_radius_bin_blocks_even_when_present_bins_are_valid(tmp_path):
    sample = _write_vertex_reco(
        tmp_path / "pi0_reco_response" / "pi0_reco_150mev.parquet",
        [_row(0.0, 1), _row(0.0, 2)],
    )

    report = audit_pi0_vertex_response(sample, 150, expected_radii_cm=(0.0, 5.0))

    assert not report.ready
    assert [bin.radius_cm for bin in report.radius_bins] == [0.0]
    blockers = {blocker.code: blocker for blocker in report.blockers}
    assert "radius_bin_missing" in blockers
    assert "5" in blockers["radius_bin_missing"].reason


def test_study1_default_radii_match_parametric_scan_spec():
    assert STUDY1_RADII_CM == (0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0)
