from __future__ import annotations

import pandas as pd
import pytest

from nnbar_reconstruction.analysis.pion_multiplicity_closure import (
    PionMultiplicityEvidence,
    audit_current_pion_multiplicity_closure,
    audit_pion_multiplicity_closure,
    audit_table91_min_pion_gate,
)
from nnbar_reconstruction.reconstruction.cutflow import MIN_PION_COUNT


def _complete_truth_counts() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "charged_pion_count_truth": [2, 1, 0],
            "neutral_pion_count_truth": [1, 0, 2],
            "total_pion_count_truth": [3, 1, 2],
        }
    )


def _complete_reco_counts() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "charged_pion_count_reco": [2, 0, 1],
            "neutral_pion_count_reco": [1, 1, 1],
            "total_pion_count_reco": [3, 1, 2],
        }
    )


def _by_kind_and_multiplicity(report):
    return {
        (status.kind, status.multiplicity): status for status in report.column_statuses
    }


def test_complete_toy_closure_evidence_is_ready(tmp_path):
    heatmap = tmp_path / "sig_foil_v3_pion_truth_reco_heatmap.csv"
    heatmap.write_text("multiplicity,residual\ncharged,0\n")

    report = audit_pion_multiplicity_closure(
        _complete_truth_counts(),
        _complete_reco_counts(),
        PionMultiplicityEvidence(
            heatmap_artifact=heatmap,
            provenance="DEC-2026-05-12-pion-multiplicity-closure",
        ),
    )

    assert report.ready is True
    assert report.blockers == ()
    status = _by_kind_and_multiplicity(report)
    assert status[("truth", "charged")].status == "source_backed_truth"
    assert status[("truth", "neutral")].column == "neutral_pion_count_truth"
    assert status[("reco", "total")].status == "source_backed_reconstruction"
    assert report.table91_gate.ready is True
    assert report.table91_gate.min_pion_count == 1


def test_missing_truth_and_reco_columns_are_distinct_fail_closed_blockers():
    truth = pd.DataFrame({"charged_pion_count_truth": [2]})
    reco = pd.DataFrame({"neutral_pion_count_reco": [1]})

    report = audit_pion_multiplicity_closure(
        truth,
        reco,
        PionMultiplicityEvidence(provenance="DEC-present-but-no-artifact"),
    )

    assert report.ready is False
    codes = {blocker.code for blocker in report.blockers}
    assert "missing_truth_column:neutral" in codes
    assert "missing_truth_column:total" in codes
    assert "missing_reco_column:charged" in codes
    assert "missing_reco_column:total" in codes
    assert "missing_heatmap_artifact" in codes
    assert "missing_truth_column:charged" not in codes
    assert "missing_reco_column:neutral" not in codes

    status = _by_kind_and_multiplicity(report)
    assert status[("truth", "charged")].present is True
    assert status[("truth", "neutral")].present is False
    assert status[("reco", "neutral")].present is True
    assert status[("reco", "charged")].present is False


def test_table91_min_pion_gate_uses_event_variable_pion_count():
    gate = audit_table91_min_pion_gate()

    assert gate.ready is True
    assert gate.min_pion_count == MIN_PION_COUNT == 1
    assert gate.cut_name == "pion_count"
    assert gate.event_variable_source == "EventVariables.n_pions"
    assert "Ch. 9 Table 9.1" in gate.source
    assert gate.blocker is None


def test_current_repository_audit_blocks_missing_sig_foil_v3_heatmap():
    report = audit_current_pion_multiplicity_closure(root=".")

    assert report.ready is False
    blocker_text = "\n".join(blocker.message for blocker in report.blockers)
    assert "sig_foil_v3" in blocker_text
    assert "charged/neutral/total pion multiplicity truth-vs-reco" in blocker_text
    assert "confusion matrix or heatmap residuals" in blocker_text
    assert {blocker.code for blocker in report.blockers} >= {
        "missing_heatmap_artifact",
        "missing_provenance",
    }
