import os
from pathlib import Path

import pytest

from nnbar_reconstruction.analysis.hibeam_gnn_feature_contract import (
    DEPLOYABLE,
    ORACLE_ONLY,
    REQUIRED_COMPTON_LEVELS,
    REQUIRED_TRACK_FEATURES,
    audit_article_text,
    audit_feature_schema,
    audit_hibeam_gnn_contract,
    audit_preparation_script_text,
    audit_result_manifest,
)


HIBEAM_ARTICLE_TEX_ENV = "NNBAR_HIBEAM_ARTICLE_TEX"
REPO_ROOT = Path(__file__).resolve().parents[1]
PREP_SCRIPT_PATHS = (
    Path("nnbar_reconstruction/training/prepare_training_data.py"),
    Path("nnbar_reconstruction/training/prepare_psignal_from_gun.py"),
)


@pytest.fixture
def hibeam_article_text():
    article_path = os.environ.get(HIBEAM_ARTICLE_TEX_ENV)
    if not article_path:
        pytest.skip(f"Set {HIBEAM_ARTICLE_TEX_ENV} to audit optional HIBEAM article")

    article = Path(article_path).expanduser()
    if not article.is_file():
        pytest.skip(f"{HIBEAM_ARTICLE_TEX_ENV} does not point to a file: {article}")

    return article.read_text()


@pytest.fixture
def hibeam_prep_script_text():
    missing = []
    text_parts = []
    for relative_path in PREP_SCRIPT_PATHS:
        path = REPO_ROOT / relative_path
        if not path.is_file():
            missing.append(str(relative_path))
            continue
        text_parts.append(path.read_text())

    if missing:
        pytest.skip("Missing optional HIBEAM prep evidence files: " + ", ".join(missing))

    return "\n".join(text_parts)


def test_tests_do_not_embed_machine_specific_hibeam_paper_paths():
    forbidden_prefixes = (
        "/" + "Volumes" + "/MyDrive/nnbar/papers",
        "/" + "Users" + "/",
        "/" + "home" + "/billy",
    )
    source = Path(__file__).read_text()

    for forbidden_prefix in forbidden_prefixes:
        assert forbidden_prefix not in source


def _deployable_schema():
    return [
        {
            "name": feature,
            "source_category": "reconstructed_track",
            "evidence_status": DEPLOYABLE,
            "required_artifact": "schemas/hibeam_track_features_v1.yml",
        }
        for feature in REQUIRED_TRACK_FEATURES
    ]


def _complete_manifest():
    return {
        "dataset_id": "hibeam_vertex_compton_scan_v1",
        "artifact_path": "artifacts/hibeam/gnn_results.json",
        "models": {
            "track_gnn": "models/track_gnn.pt",
            "vertex_gnn": "models/vertex_gnn.pt",
        },
        "split": {
            "id": "split-per-event-seed-42",
            "scope": "per-event",
            "seed": 42,
            "fractions": {"train": 0.8, "validation": 0.1, "test": 0.1},
        },
        "results": [
            {
                "compton_level": level,
                "deployable_status": DEPLOYABLE,
                "metrics": {
                    "sigma_r": 1.2 + level,
                    "epsilon": 0.99,
                    "uncertainty": 0.02,
                },
            }
            for level in REQUIRED_COMPTON_LEVELS
        ],
    }


def test_deployable_schema_and_complete_manifest_are_ready():
    audit = audit_hibeam_gnn_contract(_deployable_schema(), _complete_manifest())

    assert audit.ready is True
    assert audit.blockers == ()
    assert audit.feature_audit.ready is True
    assert audit.result_audit.ready is True


def test_truth_particle_columns_are_downgraded_to_oracle_only():
    schema = _deployable_schema() + [
        {
            "name": "Parent_ID",
            "source_category": "truth_ancestry",
            "evidence_status": DEPLOYABLE,
            "required_artifact": "Particle_output_0.parquet",
        }
    ]

    audit = audit_feature_schema(schema)
    statuses = {item.name: item.evidence_status for item in audit.items}

    assert audit.ready is False
    assert statuses["Parent_ID"] == ORACLE_ONLY
    assert "oracle_feature:Parent_ID" in audit.blockers


def test_missing_compton_levels_and_split_evidence_are_blockers():
    manifest = _complete_manifest()
    manifest.pop("split")
    manifest["results"] = [
        row for row in manifest["results"] if row["compton_level"] in {0, 1, 2}
    ]

    audit = audit_result_manifest(manifest)

    assert audit.ready is False
    assert "missing_compton_level:4" in audit.blockers
    assert "missing_compton_level:8" in audit.blockers
    assert "missing_split_evidence" in audit.blockers


def test_paper_todo_and_placeholder_metrics_are_blockers():
    article_text = r"""
    TrackGNN and VertexGNN are trained on \todonumber events.
    Table~\obs{XXX} reports all Compton levels.
    \begin{tabular}{r|rrrr}
    Total resolution & ~ & $12.5\pm27.6$ & ~ & $5.9\pm8.6$ \\
    \end{tabular}
    """

    audit = audit_article_text(article_text)

    assert audit.ready is False
    assert "article_todo_marker" in audit.blockers
    assert "article_placeholder_reference" in audit.blockers
    assert "article_placeholder_metric" in audit.blockers


def test_supplied_article_text_surfaces_fail_closed_blockers(hibeam_article_text):
    article_audit = audit_article_text(hibeam_article_text)

    assert article_audit.ready is False
    assert "article_todo_marker" in article_audit.blockers


def test_current_prep_scripts_surface_fail_closed_blockers(hibeam_prep_script_text):
    prep_audit = audit_preparation_script_text(hibeam_prep_script_text)

    assert prep_audit.ready is False
    assert any(
        blocker.startswith("oracle_training_source:") for blocker in prep_audit.blockers
    )
    assert "missing_test_split_evidence" in prep_audit.blockers
