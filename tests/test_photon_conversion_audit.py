from __future__ import annotations

from pathlib import Path

import pandas as pd

from nnbar_reconstruction.analysis.photon_conversion_audit import (
    THESIS_CH5_CONVERSION_FRACTIONS,
    audit_conversion_fractions,
    discover_photon_sample,
    run_audit,
)


def _write_conversion_fixture(path: Path, counts: dict[str, int]) -> Path:
    rows = []
    event_id = 0
    for volume, count in counts.items():
        for _ in range(count):
            rows.append({
                "event_id": event_id,
                "first_interaction_subdetector": volume,
            })
            event_id += 1
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def _thesis_counts(scale: int = 1000) -> dict[str, int]:
    return {
        volume: int(round(fraction * scale))
        for volume, fraction in THESIS_CH5_CONVERSION_FRACTIONS.items()
    }


def _codes(report) -> list[str]:
    return [blocker.code for blocker in report.blockers]


def test_run_audit_fails_closed_when_100mev_photon_sample_is_missing(tmp_path):
    report = run_audit(tmp_path)

    assert report.ready is False
    assert report.sample_path is None
    assert _codes(report) == ["sample_missing"]
    assert "100 MeV mono-photon" in report.blockers[0].reason


def test_synthetic_thesis_conversion_fractions_have_no_blockers(tmp_path):
    parquet_path = _write_conversion_fixture(tmp_path / "photon_100MeV.parquet", _thesis_counts())

    report = audit_conversion_fractions(parquet_path)

    assert report.ready is True
    assert report.blockers == ()
    assert report.total_photons == 1000
    assert report.fractions == THESIS_CH5_CONVERSION_FRACTIONS


def test_fraction_mismatch_reports_one_blocker_with_offending_volume(tmp_path):
    counts = _thesis_counts()
    counts["leadglass"] -= 30
    counts["silicon"] += 30
    parquet_path = _write_conversion_fixture(tmp_path / "photon_100MeV.parquet", counts)

    report = audit_conversion_fractions(parquet_path)

    assert report.ready is False
    assert _codes(report) == ["conversion_fractions_unverified"]
    assert "leadglass" in report.blockers[0].reason
    assert "silicon" in report.blockers[0].reason


def test_interaction_parquet_uses_earliest_conversion_volume_per_event(tmp_path):
    sample_dir = tmp_path / "photon_100MeV_conversion"
    sample_dir.mkdir()
    interaction_path = sample_dir / "Interaction_output_0.parquet"
    pd.DataFrame(
        [
            {"Event_ID": 100, "Name": "gamma", "Proc": "msc", "Current_Vol": "Silicon", "t": 0.1},
            {"Event_ID": 100, "Name": "e+", "Proc": "conv", "Current_Vol": "LeadGlassPV", "t": 10.0},
            {"Event_ID": 100, "Name": "e-", "Proc": "conv", "Current_Vol": "Beampipe_5_wall_PV", "t": 2.0},
            {"Event_ID": 101, "Name": "e+", "Proc": "conv", "Current_Vol": "TPCPV", "t": 1.0},
            {"Event_ID": 101, "Name": "e-", "Proc": "conv", "Current_Vol": "siliconPV_1", "t": 9.0},
            {"Event_ID": 102, "Name": "e+", "Proc": "conv", "Current_Vol": "Scint_barPV_H", "t": 5.0},
            {"Event_ID": 102, "Name": "e-", "Proc": "conv", "Current_Vol": "LeadGlassPV", "t": 3.0},
            {"Event_ID": 103, "Name": "e+", "Proc": "conv", "Current_Vol": "siliconPV_2", "t": 4.0},
            {"Event_ID": 103, "Name": "e-", "Proc": "conv", "Current_Vol": "Scint_FB_barPV_V", "t": 0.5},
        ]
    ).to_parquet(interaction_path, index=False)

    report = audit_conversion_fractions(interaction_path, tolerance=1.0)

    assert discover_photon_sample(tmp_path) == interaction_path
    assert report.ready is True
    assert report.total_photons == 4
    assert report.fractions == {
        "silicon": 0.0,
        "beampipe": 0.25,
        "tpc": 0.25,
        "scintillator": 0.25,
        "leadglass": 0.25,
    }
