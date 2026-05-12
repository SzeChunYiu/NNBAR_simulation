from __future__ import annotations

from pathlib import Path

import pandas as pd

from nnbar_reconstruction.analysis.photon_conversion_audit import (
    THESIS_CH5_CONVERSION_FRACTIONS,
    audit_conversion_fractions,
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
