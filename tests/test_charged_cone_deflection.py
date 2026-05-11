from pathlib import Path

import pytest

from nnbar_reconstruction.analysis.charged_cone_deflection import (
    ALLOWED_CONE_SCAN_RANGE_DEG,
    CANONICAL_CHARGED_CONE_ANGLE_DEG,
    REQUIRED_CONE_SCAN_ANGLES_DEG,
    EvidencePackage,
    audit_charged_cone_deflection,
    audit_current_charged_cone_deflection,
    audit_object_identification_cone_angle,
)


def test_charged_cone_constants_match_thesis_ch7_scan_surface():
    assert CANONICAL_CHARGED_CONE_ANGLE_DEG == pytest.approx(25.0)
    assert ALLOWED_CONE_SCAN_RANGE_DEG == (5.0, 85.0)
    assert min(REQUIRED_CONE_SCAN_ANGLES_DEG) == pytest.approx(5.0)
    assert max(REQUIRED_CONE_SCAN_ANGLES_DEG) == pytest.approx(85.0)
    assert 25.0 >= ALLOWED_CONE_SCAN_RANGE_DEG[0]
    assert 25.0 <= ALLOWED_CONE_SCAN_RANGE_DEG[1]


def test_missing_artifacts_and_provenance_fail_closed_with_specific_blockers():
    report = audit_charged_cone_deflection(EvidencePackage())

    assert report.ready is False
    blocker_text = "\n".join(blocker.message for blocker in report.blockers)
    assert "cal_singleelectron_v1" in blocker_text
    assert "single-track energy collection efficiency vs cone angle" in blocker_text
    assert "energy collection efficiency versus cone angle" in blocker_text
    assert "cal_singlepionplus_v1" in blocker_text
    assert "deflection angle versus pion kinetic energy" in blocker_text
    assert "energy-binned deflection-angle distribution" in blocker_text
    assert any(blocker.code == "missing_provenance" for blocker in report.blockers)


def test_toy_complete_evidence_package_is_ready(tmp_path):
    cone_scan = tmp_path / "cone_scan.json"
    deflection = tmp_path / "beampipe_deflection.json"
    cone_scan.write_text("{}")
    deflection.write_text("{}")

    report = audit_charged_cone_deflection(
        EvidencePackage(
            cone_scan_artifact=cone_scan,
            beampipe_deflection_artifact=deflection,
            provenance="DEC-2026-05-11-charged-cone-deflection",
        )
    )

    assert report.ready is True
    assert report.blockers == ()


def test_current_object_identification_config_exposes_25_degree_cone():
    report = audit_object_identification_cone_angle()

    assert report.config_cone_angle_deg == pytest.approx(25.0)
    assert report.config_contains_canonical_cone_angle is True
    assert report.cone_angle_present is True
    assert report.source_path.name == "object_identification.py"


def test_current_repository_audit_stays_blocked_without_real_scan_artifacts():
    report = audit_current_charged_cone_deflection(Path("."))

    assert report.ready is False
    assert report.object_identification is not None
    assert report.object_identification.cone_angle_present is True
    assert {blocker.code for blocker in report.blockers} >= {
        "missing_cone_scan_artifact",
        "missing_beampipe_deflection_artifact",
        "missing_provenance",
    }
