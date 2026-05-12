from pathlib import Path

from nnbar_reconstruction.analysis.hibeam_acts_audit import (
    DEPLOYABLE,
    REQUIRED_EVIDENCE_KEYS,
    REQUIRED_METHOD_FAMILIES,
    audit_acts_tracking_evidence,
    audit_current_acts_tracking,
)


def _complete_row(family_name):
    return {
        "method_family": family_name,
        "dataset_id": f"hibeam_acts_{family_name}_v1",
        "truth_source": "reconstruction_validation_truth_manifest_v1",
        "split": "train_val_test_seed_42_v1",
        "sigma_r": {
            "value": 1.5,
            "uncertainty": 0.1,
            "definition": "radial residual width on the held-out test split",
        },
        "epsilon": {
            "value": 0.97,
            "uncertainty": 0.01,
            "definition": "accepted reconstructed tracks divided by generated tracks",
        },
        "deployable_or_oracle": DEPLOYABLE,
        "artifact_path": f"artifacts/hibeam/acts/{family_name}/metrics_v1.json",
    }


def _complete_rows():
    return [_complete_row(family.name) for family in REQUIRED_METHOD_FAMILIES]


def test_complete_manifest_for_all_acts_families_is_ready():
    audit = audit_acts_tracking_evidence(_complete_rows())

    assert audit.ready is True
    assert audit.blockers == ()
    assert len(audit.items) == len(REQUIRED_METHOD_FAMILIES)
    assert set(REQUIRED_EVIDENCE_KEYS) == {
        "dataset_id",
        "truth_source",
        "split",
        "sigma_r",
        "epsilon",
        "deployable_or_oracle",
    }


def test_missing_and_todo_fields_surface_structured_blockers():
    rows = _complete_rows()
    rows[0] = dict(rows[0])
    rows[0].pop("dataset_id")
    rows[1] = dict(rows[1])
    rows[1]["sigma_r"] = "TODO: rerun closure study"
    rows[2] = dict(rows[2])
    rows[2].pop("deployable_or_oracle")

    audit = audit_acts_tracking_evidence(rows)

    first = REQUIRED_METHOD_FAMILIES[0].name
    second = REQUIRED_METHOD_FAMILIES[1].name
    third = REQUIRED_METHOD_FAMILIES[2].name
    assert audit.ready is False
    assert f"missing_dataset_id:{first}" in audit.blockers
    assert f"todo_marker:{second}:sigma_r" in audit.blockers
    assert f"missing_status:{third}" in audit.blockers


def test_missing_required_family_fails_closed():
    dropped = REQUIRED_METHOD_FAMILIES[-1].name
    rows = [row for row in _complete_rows() if row["method_family"] != dropped]

    audit = audit_acts_tracking_evidence(rows)

    assert audit.ready is False
    assert f"missing_family:{dropped}" in audit.blockers


def test_current_acts_tracking_without_evidence_remains_blocked():
    audit = audit_current_acts_tracking(Path("."))

    assert audit.ready is False
    assert f"missing_dataset_id:{REQUIRED_METHOD_FAMILIES[0].name}" in audit.blockers
    assert f"missing_sigma_r:{REQUIRED_METHOD_FAMILIES[0].name}" in audit.blockers
    assert "todo_marker:integration_guide" in audit.blockers


def test_missing_integration_guide_is_fail_closed_not_an_exception(tmp_path):
    audit = audit_current_acts_tracking(tmp_path)

    assert audit.ready is False
    assert "missing_integration_guide" in audit.blockers
    assert f"missing_dataset_id:{REQUIRED_METHOD_FAMILIES[0].name}" in audit.blockers
