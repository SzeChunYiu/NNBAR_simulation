from pathlib import Path

from nnbar_reconstruction.analysis.magnetic_field_boundary import (
    MAGNETIC_BOUNDARY_DOCS,
    audit_current_magnetic_field_boundary,
    audit_magnetic_field_boundary,
)


def test_allowed_straight_line_no_curvature_boundary_is_ready():
    report = audit_magnetic_field_boundary(
        {
            "toy-plan": (
                "The no B-field baseline fits straight tracks with linear PCA. "
                "Momentum from curvature is not quoted in this configuration."
            )
        }
    )

    assert report.ready is True
    assert report.boundary_documented is True
    assert report.blockers == ()
    assert any(evidence.category == "straight_line_baseline" for evidence in report.evidence)


def test_charge_sign_and_momentum_from_curvature_claims_fail_closed():
    report = audit_magnetic_field_boundary(
        {
            "bad-plan": (
                "The no B-field boundary is acknowledged. "
                "The baseline reconstructs charge sign from helix curvature. "
                "It quotes momentum from curvature for each TPC track."
            )
        }
    )

    assert report.ready is False
    codes = [blocker.code for blocker in report.blockers]
    assert codes.count("forbidden_magnetic_claim") == 2
    blocker_text = "\n".join(blocker.message for blocker in report.blockers)
    assert "charge sign" in blocker_text
    assert "momentum from curvature" in blocker_text
    assert "validated magnetic-field scenario" in blocker_text


def test_deferred_scenario_and_systematics_language_is_acceptable_provenance():
    report = audit_magnetic_field_boundary(
        {
            "systematics-plan": (
                "L9 no B-field is out of current scope. No charge-sign or "
                "magnetic-momentum claim may be quoted until a bounded "
                "magnetic-field scenario exists."
            )
        }
    )

    assert report.ready is True
    assert report.deferred_provenance_present is True
    assert report.blockers == ()
    assert any(evidence.category == "deferred_scenario" for evidence in report.evidence)


def test_missing_boundary_documentation_is_a_blocker():
    report = audit_magnetic_field_boundary(
        {"ambiguous-plan": "TPC tracks are fit and downstream observables are quoted."}
    )

    assert report.ready is False
    assert {blocker.code for blocker in report.blockers} == {
        "missing_boundary_documentation"
    }
    blocker = report.blockers[0]
    assert blocker.observable == "charge sign or magnetic momentum from curvature"
    assert blocker.figure_of_merit == "explicit no-B-field boundary statement"


def test_current_plan_documents_smoke_audit_is_ready():
    report = audit_current_magnetic_field_boundary(Path("."))

    assert report.ready is True
    assert report.boundary_documented is True
    assert report.deferred_provenance_present is True
    assert report.blockers == ()
    assert set(report.sources) == set(MAGNETIC_BOUNDARY_DOCS)
    assert len(report.evidence) >= 4
