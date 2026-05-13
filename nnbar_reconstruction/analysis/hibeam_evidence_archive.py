"""Fail-closed audit helpers for HIBEAM evidence archive readiness.

The helpers operate on caller-supplied manifests, governance text, and paper
text.  They intentionally do not read absolute local paths, train models, or
promote HIBEAM numbers; unresolved provenance is returned as blocker codes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Any, Iterable, Mapping, Sequence


READY_STATUSES = frozenset({"ready", "verified", "pinned"})
_DECISION_RE = re.compile(r"DEC-\d{4}-\d{2}-\d{2}-[A-Za-z0-9-]+")
_SHA256_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
_COMMIT_RE = re.compile(r"^(?:commit:)?[0-9a-fA-F]{7,40}$")
_TAG_RE = re.compile(r"^v?\d+(?:\.\d+)*(?:[-+][0-9A-Za-z_.-]+)?$")
_UNPINNED_REFS = {"", "head", "latest", "main", "master", "tip", "dev"}
_DATASET_ID_RE = re.compile(r"(?:^|\s|[-{,])id:\s*([A-Za-z0-9_.-]+)")
_PAPER_BLOCKERS = (
    ("paper_todo_marker", re.compile(r"\\todo(?:number|text|task)?\b|\bTODO\b")),
    ("paper_observation_placeholder", re.compile(r"\\obs\s*\{|\\obscite\b|\bXXX\b|\bYYY\b")),
    ("paper_tbd_marker", re.compile(r"\bTBD\b", re.IGNORECASE)),
    ("paper_placeholder_metric", re.compile(r"\bplaceholder\b|(^|&)\s*~\s*(&|\\\\)", re.IGNORECASE | re.MULTILINE)),
)


@dataclass(frozen=True)
class HibeamEvidenceItem:
    """One HIBEAM claim's required archive/provenance evidence.

    Args:
        claim_id: Stable identifier for the paper/thesis claim.
        dataset_registry_id: Plan-03 dataset registry ID.
        decision_log_id: Governing DEC entry ID.
        validation_report_path: Relative validation report path.
        ledger_row_id: Thesis reproduction ledger row ID.
        archive_member: Stable archive member path or ID.
        archive_digest: Stable digest for the archive member.
        pinned_ref: Commit, tag, or hash pin for the evidence package.
        status: Caller-supplied status; only ready/verified/pinned is accepted.
        blocker_text: Caller-supplied unresolved blocker description.
    """

    claim_id: str
    dataset_registry_id: str
    decision_log_id: str
    validation_report_path: str
    ledger_row_id: str
    archive_member: str
    archive_digest: str
    pinned_ref: str
    status: str
    blocker_text: str = ""

    def with_updates(self, **updates: Any) -> "HibeamEvidenceItem":
        """Return a copy with selected fields replaced.

        Args:
            **updates: Field names and replacement values.

        Returns:
            Updated evidence item.
        """

        return replace(self, **updates)


EvidenceItem = HibeamEvidenceItem


@dataclass(frozen=True)
class EvidenceAudit:
    """Audit outcome for a HIBEAM evidence surface.

    Args:
        ready: True only when no blockers remain.
        blockers: Stable blocker codes.
        items: Parsed evidence rows included in this audit.
    """

    ready: bool
    blockers: tuple[str, ...] = ()
    items: tuple[HibeamEvidenceItem, ...] = ()


def audit_hibeam_evidence_archive(
    evidence_items: Sequence[HibeamEvidenceItem | Mapping[str, Any]],
    *,
    registry_text: str = "",
    decision_log_text: str = "",
    ledger_text: str = "",
    validation_reports: Iterable[str] = (),
    paper_text: str = "",
) -> EvidenceAudit:
    """Audit HIBEAM claim evidence against supplied governance text.

    Args:
        evidence_items: Manifest rows describing each claim and its required
            dataset, DEC, validation report, ledger row, archive member, digest,
            pin, and status.
        registry_text: Dataset-registry text supplied by the caller.
        decision_log_text: Decision-log text supplied by the caller.
        ledger_text: Thesis reproduction ledger text supplied by the caller.
        validation_reports: Verified relative validation report paths.
        paper_text: Optional HIBEAM paper text to scan for placeholders.

    Returns:
        Fail-closed audit result with deterministic blocker codes.
    """

    registry_ids = _extract_dataset_ids(registry_text)
    decision_ids = set(_DECISION_RE.findall(decision_log_text))
    report_paths = set(validation_reports)

    blockers: list[str] = []
    items: list[HibeamEvidenceItem] = []
    for raw in evidence_items:
        item = _evidence_item(raw)
        items.append(item)
        _audit_item(item, registry_ids, decision_ids, ledger_text, report_paths, blockers)

    if not items:
        blockers.append("missing_evidence_items")

    if paper_text:
        blockers.extend(audit_paper_text(paper_text).blockers)

    return _audit_result(blockers, items)


def audit_evidence_package(
    evidence_items: Sequence[HibeamEvidenceItem | Mapping[str, Any]],
    *,
    registry_ids: Iterable[str] = (),
    decision_log_ids: Iterable[str] = (),
    validation_reports: Iterable[str] = (),
    ledger_row_ids: Iterable[str] = (),
    archive_digests: Mapping[str, str] | None = None,
) -> EvidenceAudit:
    """Audit HIBEAM evidence against explicit verified ID collections.

    Args:
        evidence_items: Evidence rows to audit.
        registry_ids: Verified dataset registry IDs.
        decision_log_ids: Verified DEC IDs.
        validation_reports: Verified validation report paths.
        ledger_row_ids: Verified ledger row IDs.
        archive_digests: Verified archive member to digest mapping.

    Returns:
        Audit result with blockers for any missing or unverified evidence.
    """

    registry_text = "\n".join(f"id: {dataset_id}" for dataset_id in registry_ids)
    decision_text = "\n".join(decision_log_ids)
    ledger_text = "\n".join(ledger_row_ids)
    audit = audit_hibeam_evidence_archive(
        evidence_items,
        registry_text=registry_text,
        decision_log_text=decision_text,
        ledger_text=ledger_text,
        validation_reports=validation_reports,
    )

    if archive_digests is None:
        return audit

    blockers = list(audit.blockers)
    for item in audit.items:
        expected = archive_digests.get(item.archive_member)
        if expected is None:
            blockers.append(f"unverified_archive_member:{item.claim_id}")
        elif expected != item.archive_digest:
            blockers.append(f"archive_digest_mismatch:{item.claim_id}")
    return _audit_result(blockers, audit.items)


def audit_paper_text(paper_text: str) -> EvidenceAudit:
    """Audit supplied HIBEAM paper text for unresolved placeholder tokens.

    Args:
        paper_text: LaTeX or prose text supplied by the caller.

    Returns:
        Audit result containing blocker codes for unresolved paper tokens.
    """

    blockers = [
        code
        for code, pattern in _PAPER_BLOCKERS
        if pattern.search(paper_text)
    ]
    return _audit_result(blockers)


def audit_article_text(article_text: str) -> EvidenceAudit:
    """Alias for paper-text placeholder auditing.

    Args:
        article_text: LaTeX or prose text supplied by the caller.

    Returns:
        Audit result containing blocker codes for unresolved paper tokens.
    """

    return audit_paper_text(article_text)


def _audit_item(
    item: HibeamEvidenceItem,
    registry_ids: set[str],
    decision_ids: set[str],
    ledger_text: str,
    validation_reports: set[str],
    blockers: list[str],
) -> None:
    """Append all fail-closed blockers for one evidence item."""

    claim_id = item.claim_id or "missing-claim"
    if not item.claim_id:
        blockers.append("missing_claim_id")

    if not item.dataset_registry_id:
        blockers.append(f"missing_dataset_registry_id:{claim_id}")
    elif _looks_like_local_path(item.dataset_registry_id):
        blockers.append(f"unpinned_dataset_registry_id:{claim_id}")
    elif item.dataset_registry_id not in registry_ids:
        blockers.append(f"unresolved_dataset_registry_id:{claim_id}")

    if not item.decision_log_id:
        blockers.append(f"missing_decision_log_id:{claim_id}")
    elif not _DECISION_RE.fullmatch(item.decision_log_id):
        blockers.append(f"invalid_decision_log_id:{claim_id}")
    elif item.decision_log_id not in decision_ids:
        blockers.append(f"unresolved_decision_log_id:{claim_id}")

    if not item.validation_report_path:
        blockers.append(f"missing_validation_report_path:{claim_id}")
    elif _looks_like_local_path(item.validation_report_path):
        blockers.append(f"unpinned_validation_report_path:{claim_id}")
    elif item.validation_report_path not in validation_reports:
        blockers.append(f"missing_validation_report:{claim_id}")

    if not item.ledger_row_id:
        blockers.append(f"missing_ledger_row_id:{claim_id}")
    elif item.ledger_row_id not in ledger_text:
        blockers.append(f"unresolved_ledger_row_id:{claim_id}")

    if not item.archive_member:
        blockers.append(f"missing_archive_member:{claim_id}")
    elif _looks_like_local_path(item.archive_member):
        blockers.append(f"unpinned_archive_member:{claim_id}")
    if not _is_stable_digest(item.archive_digest):
        blockers.append(f"unstable_archive_digest:{claim_id}")

    if not _is_stable_pin(item.pinned_ref):
        blockers.append(f"unpinned_ref:{claim_id}")

    status = item.status.lower()
    if not status:
        blockers.append(f"missing_status:{claim_id}")
    elif status not in READY_STATUSES:
        blockers.append(f"non_ready_status:{claim_id}:{status}")

    if item.blocker_text.strip():
        blockers.append(f"item_blocker_text:{claim_id}")


def _evidence_item(
    raw: HibeamEvidenceItem | Mapping[str, Any],
) -> HibeamEvidenceItem:
    """Convert a mapping into a normalized evidence item."""

    if isinstance(raw, HibeamEvidenceItem):
        return raw
    return HibeamEvidenceItem(
        claim_id=_text(raw.get("claim_id")),
        dataset_registry_id=_text(raw.get("dataset_registry_id")),
        decision_log_id=_text(raw.get("decision_log_id")),
        validation_report_path=_text(raw.get("validation_report_path")),
        ledger_row_id=_text(raw.get("ledger_row_id")),
        archive_member=_text(raw.get("archive_member")),
        archive_digest=_text(raw.get("archive_digest")),
        pinned_ref=_text(raw.get("pinned_ref")),
        status=_text(raw.get("status")),
        blocker_text=_text(raw.get("blocker_text")),
    )


def _audit_result(
    blockers: Iterable[str],
    items: Iterable[HibeamEvidenceItem] = (),
) -> EvidenceAudit:
    """Create a deterministic audit result with de-duplicated blockers."""

    unique = tuple(dict.fromkeys(blockers))
    return EvidenceAudit(ready=not unique, blockers=unique, items=tuple(items))


def _extract_dataset_ids(registry_text: str) -> set[str]:
    """Extract simple ``id: <dataset>`` entries from registry text."""

    return set(_DATASET_ID_RE.findall(registry_text))


def _text(value: Any) -> str:
    """Return stripped text for manifest values."""

    if value is None:
        return ""
    return str(value).strip()


def _looks_like_local_path(value: str) -> bool:
    """Return True for absolute, home-relative, or parent-traversal paths."""

    lowered = value.lower()
    return (
        value.startswith(("/", "~"))
        or ".." in value.split("/")
        or lowered.startswith(("file:", "latest/"))
    )


def _is_stable_digest(value: str) -> bool:
    """Return True when a digest has a stable SHA-256 shape."""

    return bool(_SHA256_RE.match(value))


def _is_stable_pin(value: str) -> bool:
    """Return True for a commit SHA, stable tag, or SHA-256 hash pin."""

    ref = value.strip()
    bare_ref = ref.removeprefix("commit:")
    if bare_ref.lower() in _UNPINNED_REFS or _looks_like_local_path(ref):
        return False
    return bool(_COMMIT_RE.match(ref) or _TAG_RE.match(ref) or _SHA256_RE.match(ref))
