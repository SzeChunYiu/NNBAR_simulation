import os
from pathlib import Path

import pytest

from nnbar_reconstruction.analysis.hibeam_vertex_method_closure import (
    DEPLOYABLE,
    ORACLE_ONLY,
    REQUIRED_COMPTON_LEVELS,
    REQUIRED_METHODS,
    audit_article_text,
    audit_vertex_method_manifest,
)


ARTICLE_TEX_ENV = "NNBAR_HIBEAM_ARTICLE_TEX"
DEFAULT_ARTICLE_TEX = (
    Path("/")
    / "Volumes"
    / "MyDrive"
    / "nnbar"
    / "papers"
    / "overleaf-696757e2"
    / "main.tex"
)


def _metric_definitions(level):
    return {
        "dx": {
            "value": 0.1 + level,
            "uncertainty": 0.01,
            "definition": "x_reco - x_true on the held-out test set",
        },
        "dy": {
            "value": 0.2 + level,
            "uncertainty": 0.01,
            "definition": "y_reco - y_true on the held-out test set",
        },
        "d_tot": {
            "value": 1.0 + level,
            "uncertainty": 0.05,
            "definition": "sqrt(dx^2 + dy^2) on the held-out test set",
        },
        "sigma_r": {
            "value": 1.5 + level,
            "definition": "radial vertex uncertainty on the held-out test set",
        },
        "epsilon": {
            "value": 0.99,
            "uncertainty": 0.002,
            "definition": "reconstructed events divided by generated events",
        },
        "outlier_definition": "d_tot > 50 mm on the held-out test set",
        "signal_track_association_efficiency": {
            "value": 0.97,
            "uncertainty": 0.003,
            "definition": "fraction of reconstructed signal tracks matched to validation truth",
        },
    }


def _complete_rows():
    rows = []
    for method in REQUIRED_METHODS:
        for level in REQUIRED_COMPTON_LEVELS:
            rows.append(
                {
                    "method_name": method,
                    "compton_level": level,
                    "dataset_id": f"hibeam_vertex_{method}_compton_scan_v1",
                    "truth_source": "validation_truth_vertex_manifest_v1",
                    "split_id": "per-event-train-val-test-seed-42",
                    "artifact_path": f"artifacts/hibeam/{method}/level_{level}/metrics.json",
                    "evidence_status": DEPLOYABLE,
                    "label_source": "reconstructed_tracks",
                    "metric_definitions": _metric_definitions(level),
                }
            )
    return rows


def test_complete_method_level_manifest_is_ready():
    audit = audit_vertex_method_manifest(_complete_rows())

    assert audit.ready is True
    assert audit.blockers == ()
    assert len(audit.items) == len(REQUIRED_METHODS) * len(REQUIRED_COMPTON_LEVELS)


def test_missing_graphnet_results_fail_closed():
    rows = [row for row in _complete_rows() if row["method_name"] != "graphnet"]

    audit = audit_vertex_method_manifest(rows)

    assert audit.ready is False
    assert "missing_method:graphnet" in audit.blockers
    assert "missing_result:graphnet:level:0" in audit.blockers


def test_missing_four_and_eight_compton_levels_fail_closed():
    rows = [row for row in _complete_rows() if row["compton_level"] not in {4, 8}]

    audit = audit_vertex_method_manifest(rows)

    assert audit.ready is False
    assert "missing_compton_level:4" in audit.blockers
    assert "missing_compton_level:8" in audit.blockers
    assert "missing_result:least_squares:level:4" in audit.blockers


def test_missing_uncertainty_columns_are_blockers():
    rows = _complete_rows()
    target = rows[0]
    target["metric_definitions"] = dict(target["metric_definitions"])
    target["metric_definitions"]["dx"] = {
        "value": 0.1,
        "definition": "x residual without an uncertainty column",
    }
    target["metric_definitions"]["signal_track_association_efficiency"] = {
        "value": 0.97,
        "definition": "association efficiency without an uncertainty column",
    }

    audit = audit_vertex_method_manifest(rows)

    assert audit.ready is False
    assert "missing_uncertainty:least_squares:level:0:dx" in audit.blockers
    assert (
        "missing_uncertainty:least_squares:level:0:signal_track_association_efficiency"
        in audit.blockers
    )


def test_oracle_only_labels_are_blockers():
    rows = _complete_rows()
    rows[0] = dict(rows[0])
    rows[0]["evidence_status"] = ORACLE_ONLY
    rows[0]["label_source"] = "truth_particle_labels"

    audit = audit_vertex_method_manifest(rows)

    assert audit.ready is False
    assert "oracle_only_result:least_squares:level:0" in audit.blockers
    assert "oracle_label_source:least_squares:level:0" in audit.blockers


def test_current_article_method_tables_still_block_thesis_readiness():
    article_path = Path(os.environ.get(ARTICLE_TEX_ENV, DEFAULT_ARTICLE_TEX)).expanduser()
    if not article_path.is_file():
        pytest.skip(f"current HIBEAM article is not available: {article_path}")

    audit = audit_article_text(article_path.read_text())

    assert audit.ready is False
    assert "article_todo_marker" in audit.blockers
    assert "article_placeholder_reference" in audit.blockers
    assert "article_placeholder_metric" in audit.blockers
