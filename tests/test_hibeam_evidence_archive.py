from pathlib import Path

import pytest

from nnbar_reconstruction.analysis.hibeam_evidence_archive import (
    HibeamEvidenceItem,
    audit_hibeam_evidence_archive,
    audit_paper_text,
)


_SHA = "a" * 64
_COMMIT = "b" * 40


def _complete_item():
    return HibeamEvidenceItem(
        claim_id="HIB-VTX-RESULTS",
        dataset_registry_id="hibeam_vertex_compton_scan_v1",
        decision_log_id="DEC-2026-05-11-1",
        validation_report_path="docs/reports/hibeam_vertex_validation.md",
        ledger_row_id="HIB-ARTICLE-TAB-RESULTS",
        archive_member="archive/hibeam_vertex/results.json",
        archive_digest=f"sha256:{_SHA}",
        pinned_ref=f"commit:{_COMMIT}",
        status="ready",
        blocker_text="",
    )


def test_complete_pinned_evidence_package_is_ready():
    audit = audit_hibeam_evidence_archive(
        [_complete_item()],
        registry_text="datasets:\n  - id: hibeam_vertex_compton_scan_v1\n",
        decision_log_text="## DEC-2026-05-11-1\n**Status.** approved\n",
        ledger_text="| HIB-ARTICLE-TAB-RESULTS | HIBEAM article result |",
        validation_reports={"docs/reports/hibeam_vertex_validation.md"},
        paper_text="All values are final, cited, and pinned.",
    )

    assert audit.ready is True
    assert audit.blockers == ()


def test_missing_dataset_registry_and_decision_log_links_are_blockers():
    item = _complete_item().with_updates(
        dataset_registry_id="",
        decision_log_id="",
    )

    audit = audit_hibeam_evidence_archive(
        [item],
        registry_text="datasets: []",
        decision_log_text="",
        ledger_text="| HIB-ARTICLE-TAB-RESULTS | HIBEAM article result |",
        validation_reports={"docs/reports/hibeam_vertex_validation.md"},
    )

    assert audit.ready is False
    assert "missing_dataset_registry_id:HIB-VTX-RESULTS" in audit.blockers
    assert "missing_decision_log_id:HIB-VTX-RESULTS" in audit.blockers


def test_placeholder_hibeam_paper_tokens_are_blockers():
    article_text = r"""
    TrackGNN uses \todonumber events, Table~\obs{XXX} is pending,
    and the abstract still says TBD.
    """

    audit = audit_paper_text(article_text)

    assert audit.ready is False
    assert "paper_todo_marker" in audit.blockers
    assert "paper_observation_placeholder" in audit.blockers
    assert "paper_tbd_marker" in audit.blockers


def test_unhashed_archive_member_and_unpinned_local_path_are_blockers():
    item = _complete_item().with_updates(
        archive_digest="",
        pinned_ref="/Volumes/MyDrive/nnbar/local/results.json",
    )

    audit = audit_hibeam_evidence_archive(
        [item],
        registry_text="datasets:\n  - id: hibeam_vertex_compton_scan_v1\n",
        decision_log_text="## DEC-2026-05-11-1\n",
        ledger_text="| HIB-ARTICLE-TAB-RESULTS | HIBEAM article result |",
        validation_reports={"docs/reports/hibeam_vertex_validation.md"},
    )

    assert audit.ready is False
    assert "unstable_archive_digest:HIB-VTX-RESULTS" in audit.blockers
    assert "unpinned_ref:HIB-VTX-RESULTS" in audit.blockers


def test_current_hibeam_paper_and_governance_texts_surface_blockers():
    paper = Path("/Volumes/MyDrive/nnbar/papers/overleaf-696757e2/main.tex")
    if not paper.exists():
        pytest.skip("local HIBEAM paper checkout is not available")

    item = _complete_item().with_updates(
        dataset_registry_id="hibeam_vertex_compton_scan_v1",
        decision_log_id="DEC-2026-05-11-HIBEAM-ARCHIVE",
        validation_report_path="docs/reports/hibeam_vertex_validation.md",
        ledger_row_id="HIB-ARTICLE-TAB-RESULTS",
        archive_digest="sha256:not-a-real-digest",
        pinned_ref="",
        status="blocked",
        blocker_text="awaiting dataset registry and archive pin",
    )

    audit = audit_hibeam_evidence_archive(
        [item],
        registry_text=Path("docs/rebuild_plans/03_dataset_registry.md").read_text(),
        decision_log_text=Path("docs/governance/DECISION_LOG.md").read_text(),
        ledger_text=Path("docs/thesis_reproduction_ledger.md").read_text(),
        validation_reports=set(),
        paper_text=paper.read_text(),
    )

    assert audit.ready is False
    assert "unresolved_dataset_registry_id:HIB-VTX-RESULTS" in audit.blockers
    assert "unresolved_decision_log_id:HIB-VTX-RESULTS" in audit.blockers
    assert "unresolved_ledger_row_id:HIB-VTX-RESULTS" in audit.blockers
    assert "missing_validation_report:HIB-VTX-RESULTS" in audit.blockers
    assert "paper_todo_marker" in audit.blockers
    assert "paper_observation_placeholder" in audit.blockers
