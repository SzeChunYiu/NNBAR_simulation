from __future__ import annotations

from pathlib import Path

import pandas as pd

from nnbar_reconstruction.analysis.signal_kinematics_audit import (
    REQUIRED_EVIDENCE_KEYS,
    THESIS_SIGNAL_EVENT_COUNT,
    audit_current_signal_kinematics,
    audit_signal_kinematics,
)


def _toy_signal_parquet(tmp_path: Path, n_events: int = 3) -> Path:
    path = tmp_path / "Particle_output_0.parquet"
    pd.DataFrame(
        {
            "Event_ID": list(range(n_events)),
            "PDG": [22, 211, 2212][:n_events],
            "KE": [180.0, 120.0, 75.0][:n_events],
            "vx": [100.0, 100.5, 101.0][:n_events],
            "vy": [0.0, 1.0, 2.0][:n_events],
        }
    ).to_parquet(path, index=False)
    return path


def _complete_evidence(sample_path: Path) -> dict[str, object]:
    thesis_refs = {key: f"Ch. 6 synthetic fixture reference for {key}" for key in REQUIRED_EVIDENCE_KEYS}
    evidence: dict[str, object] = {
        "sample_path": sample_path,
        "n_events": THESIS_SIGNAL_EVENT_COUNT,
        "thesis_reference": thesis_refs,
    }
    for key in REQUIRED_EVIDENCE_KEYS:
        if key in {"sample_path", "n_events"}:
            continue
        evidence[key] = {
            "verified": True,
            "artifact": f"toy-{key}.json",
        }
    return evidence


def _codes(report) -> set[str]:
    return {blocker.code for blocker in report.blockers}


def test_missing_sample_path_fails_closed_with_sample_missing(tmp_path):
    evidence = _complete_evidence(tmp_path / "absent.parquet")
    evidence.pop("sample_path")

    report = audit_signal_kinematics(evidence)

    assert report.ready is False
    assert "sample_missing" in _codes(report)
    assert report.evidence_status["sample_path"].present is False
    assert report.evidence_status["sample_path"].thesis_reference.startswith("Ch. 6")


def test_present_under_statistics_parquet_does_not_validate_thesis_50k_sample(tmp_path):
    sample_path = _toy_signal_parquet(tmp_path, n_events=3)
    evidence = _complete_evidence(sample_path)
    evidence.pop("n_events")

    report = audit_signal_kinematics(evidence)

    assert report.ready is False
    assert "under_statistics" in _codes(report)
    assert report.n_events == 3
    assert report.required_events == THESIS_SIGNAL_EVENT_COUNT


def test_present_sample_without_verified_ke_peaks_is_blocked(tmp_path):
    evidence = _complete_evidence(_toy_signal_parquet(tmp_path))
    for key in ("photon_ke_peak", "pion_plus_ke_peak", "pion_minus_ke_peak", "proton_ke_peak"):
        evidence[key] = {"verified": False, "artifact": None}

    report = audit_signal_kinematics(evidence)

    assert report.ready is False
    assert "KE_peak_not_verified" in _codes(report)
    for key in ("photon_ke_peak", "pion_plus_ke_peak", "pion_minus_ke_peak", "proton_ke_peak"):
        assert report.evidence_status[key].verified is False


def test_present_sample_without_radial_distribution_is_blocked(tmp_path):
    evidence = _complete_evidence(_toy_signal_parquet(tmp_path))
    evidence.pop("foil_radial_distribution")

    report = audit_signal_kinematics(evidence)

    assert report.ready is False
    assert "vertex_distribution_unverified" in _codes(report)
    assert report.evidence_status["foil_radial_distribution"].present is False


def test_complete_synthetic_evidence_is_ready(tmp_path):
    report = audit_signal_kinematics(_complete_evidence(_toy_signal_parquet(tmp_path)))

    assert report.ready is True
    assert report.blockers == ()
    assert set(report.evidence_status) == set(REQUIRED_EVIDENCE_KEYS)
    assert all(status.thesis_reference.startswith("Ch. 6") for status in report.evidence_status.values())


def test_current_checkout_audit_remains_fail_closed_without_local_50k_sample(tmp_path):
    report = audit_current_signal_kinematics(root=tmp_path)

    assert report.ready is False
    assert _codes(report) >= {
        "sample_missing",
        "under_statistics",
        "KE_peak_not_verified",
        "vertex_distribution_unverified",
    }
