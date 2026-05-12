from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from nnbar_reconstruction.analysis.pi0_multiplicity_response_audit import (
    REQUIRED_MULTIPLICITIES,
    audit_pi0_multiplicity_response,
    run_pi0_multiplicity_response_audit,
)


def _write_response(path: Path, *, event_count: int = 500, efficiency: float = 0.82, confusion: float = 0.08, opening: float = 42.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "event_count": [event_count],
            "reco_efficiency": [efficiency],
            "invariant_mass_confusion_rate": [confusion],
            "opening_angle_separation_deg": [opening],
        }
    ).to_parquet(path, index=False)
    return path


def _codes(report) -> set[str]:
    return {blocker.code for blocker in report.blockers}


def _by_multiplicity(report):
    return {response.multiplicity: response for response in report.responses}


def test_complete_one_two_three_pi0_tables_are_ready(tmp_path):
    paths = {
        multiplicity: _write_response(
            tmp_path / f"pi0_multiplicity_{multiplicity}pi0" / "response.parquet",
            event_count=500,
            efficiency=0.90 - 0.10 * multiplicity,
            confusion=0.02 * multiplicity,
            opening=50.0 - multiplicity,
        )
        for multiplicity in REQUIRED_MULTIPLICITIES
    }

    report = audit_pi0_multiplicity_response(paths)

    assert report.ready is True
    assert report.blockers == ()
    by_multiplicity = _by_multiplicity(report)
    assert set(by_multiplicity) == set(REQUIRED_MULTIPLICITIES)
    assert by_multiplicity[1].event_count == 500
    assert by_multiplicity[2].reco_efficiency == pytest.approx(0.70)
    assert by_multiplicity[3].invariant_mass_confusion_rate == pytest.approx(0.06)
    assert by_multiplicity[3].opening_angle_separation_deg == pytest.approx(47.0)


def test_empty_search_root_fails_closed_for_all_required_multiplicities(tmp_path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    report = run_pi0_multiplicity_response_audit(tmp_path)

    assert report.ready is False
    assert report.responses == ()
    assert _codes(report) == {
        "pi0_multiplicity_1pi0_sample_missing",
        "pi0_multiplicity_2pi0_sample_missing",
        "pi0_multiplicity_3pi0_sample_missing",
    }
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert after == before


def test_missing_columns_and_nonnumeric_metrics_are_distinct_blockers(tmp_path):
    one = _write_response(tmp_path / "pi0_multiplicity_1pi0" / "response.parquet")
    two = tmp_path / "pi0_multiplicity_2pi0" / "response.parquet"
    two.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "event_count": [500],
            "reco_efficiency": ["not-a-number"],
            "invariant_mass_confusion_rate": [0.11],
            "opening_angle_separation_deg": [37.0],
        }
    ).to_parquet(two, index=False)
    three = tmp_path / "pi0_multiplicity_3pi0" / "response.parquet"
    three.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "event_count": [500],
            "reco_efficiency": [0.51],
            "invariant_mass_confusion_rate": [0.17],
        }
    ).to_parquet(three, index=False)

    report = audit_pi0_multiplicity_response({1: one, 2: two, 3: three})

    assert report.ready is False
    assert _codes(report) >= {
        "nonnumeric_response_metric:2:reco_efficiency",
        "missing_response_column:3:opening_angle_separation_deg",
    }
    assert "missing_response_column:1:event_count" not in _codes(report)


def test_discovery_reads_staged_csv_or_parquet_tables_without_writing(tmp_path):
    _write_response(tmp_path / "pi0_multiplicity_1pi0" / "response.parquet")
    _write_response(tmp_path / "pi0_multiplicity_2pi0" / "response.parquet")
    csv_path = tmp_path / "pi0_multiplicity_3pi0" / "response.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "event_count": [500],
            "reco_efficiency": [0.55],
            "invariant_mass_confusion_rate": [0.14],
            "opening_angle_separation_deg": [33.0],
        }
    ).to_csv(csv_path, index=False)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    report = run_pi0_multiplicity_response_audit(tmp_path)

    assert report.ready is True
    assert report.blockers == ()
    assert _by_multiplicity(report)[3].parquet_path == csv_path
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert after == before
