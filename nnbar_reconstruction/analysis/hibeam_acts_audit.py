"""Fail-closed audit helpers for HIBEAM ACTS/Kalman evidence.

This module only inspects caller-supplied dictionaries and local text files. It
intentionally does not import ``acts_tracking``, load models, submit jobs, or
promote performance numbers. A family is thesis-ready only when the required
HIBEAM article evidence keys are pinned and non-placeholder for every ACTS TPC
tracking method family.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

DEPLOYABLE = "deployable"
ORACLE_ONLY = "oracle_only"

REQUIRED_EVIDENCE_KEYS = (
    "dataset_id",
    "truth_source",
    "split",
    "sigma_r",
    "epsilon",
    "deployable_or_oracle",
)

_PLACEHOLDER_RE = re.compile(
    r"^(?:|~|[-–—]|todo|tbd|fixme|placeholder|xxx|yyy|n/?a|none)$",
    re.IGNORECASE,
)
_TODO_RE = re.compile(r"\\todo\w*|\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b", re.IGNORECASE)
_VERSION_PIN_RE = re.compile(r"(?:^|[_:-])v\d+(?:$|[_:-])", re.IGNORECASE)


@dataclass(frozen=True)
class ActsMethodFamily:
    """Data-only description of one HIBEAM ACTS tracking method family.

    Args:
        name: Stable audit key for the family.
        label: Human-readable method-family name.
        source_paths: Read-only files that currently contain the family.
        rationale: Why this family is part of the HIBEAM tracking surface.
    """

    name: str
    label: str
    source_paths: tuple[str, ...]
    rationale: str


REQUIRED_METHOD_FAMILIES = (
    ActsMethodFamily(
        name="kalman_fit",
        label="Kalman track fit",
        source_paths=(
            "acts_tracking/core/kalman_filter.py",
            "acts_tracking/core/full_kalman_fitter.py",
            "acts_tracking/core/fast_kalman_fitter.py",
        ),
        rationale="Track-parameter and covariance estimation before vertexing.",
    ),
    ActsMethodFamily(
        name="combinatorial_kalman_finder",
        label="CKF combinatorial track finder",
        source_paths=("acts_tracking/seeding/combinatorial_kalman.py",),
        rationale="Candidate branching and hit assignment before final fitting.",
    ),
    ActsMethodFamily(
        name="adaptive_vertex_fit",
        label="Adaptive/RAVE-style vertex fit",
        source_paths=(
            "acts_tracking/vertex/adaptive_fitter.py",
            "acts_tracking/vertex/fast_vertex_fitter.py",
        ),
        rationale="Robust vertex fitting with track weights/outlier suppression.",
    ),
    ActsMethodFamily(
        name="billoir_vertex_fit",
        label="Billoir/iterative vertex fit",
        source_paths=(
            "acts_tracking/vertex/iterative_fitter.py",
            "acts_tracking/vertex/fast_vertex_fitter.py",
        ),
        rationale="Independent classic vertex-fit baseline for comparison.",
    ),
    ActsMethodFamily(
        name="straight_track_seeding",
        label="Straight-track seeding",
        source_paths=(
            "acts_tracking/seeding/track_seeder.py",
            "acts_tracking/seeding/hibeam_seeder.py",
        ),
        rationale="Initial TPC space-point grouping and seed construction.",
    ),
    ActsMethodFamily(
        name="ambiguity_resolution",
        label="Shared-hit ambiguity resolution",
        source_paths=("acts_tracking/INTEGRATION_GUIDE.md",),
        rationale="Guide-listed HIBEAM TODO that must not be treated as validated.",
    ),
)


@dataclass(frozen=True)
class ActsMethodEvidence:
    """One evidence row for a required ACTS tracking method family.

    Args:
        method_family: Stable family key from ``REQUIRED_METHOD_FAMILIES``.
        dataset_id: Pinned dataset identifier backing the result.
        truth_source: Truth/deployable source used to compute validation labels.
        split: Train/validation/test split identifier.
        sigma_r: Radial resolution value or structured metric record.
        epsilon: Efficiency value or structured metric record.
        deployable_or_oracle: ``deployable`` or ``oracle_only`` status.
        artifact_path: Optional pinned metrics/report artifact path.
        blocker_messages: Caller-supplied explicit blockers for this row.
    """

    method_family: str
    dataset_id: Any = ""
    truth_source: Any = ""
    split: Any = ""
    sigma_r: Any = ""
    epsilon: Any = ""
    deployable_or_oracle: Any = ""
    artifact_path: str = ""
    blocker_messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActsTrackingAudit:
    """Audit result for HIBEAM ACTS/Kalman thesis-readiness evidence.

    Args:
        ready: True only when no blockers remain.
        blockers: Stable machine-readable blocker codes.
        items: Normalized evidence rows, one per inspected family.
        families: Required method-family definitions used by the audit.
    """

    ready: bool
    blockers: tuple[str, ...]
    items: tuple[ActsMethodEvidence, ...]
    families: tuple[ActsMethodFamily, ...] = REQUIRED_METHOD_FAMILIES


AuditResult = ActsTrackingAudit


def audit_acts_tracking_evidence(
    evidence_rows: Sequence[Mapping[str, Any] | ActsMethodEvidence],
    *,
    required_families: Sequence[ActsMethodFamily] = REQUIRED_METHOD_FAMILIES,
) -> ActsTrackingAudit:
    """Audit HIBEAM ACTS tracking evidence rows for fail-closed readiness.

    Args:
        evidence_rows: Caller-supplied rows keyed by ``method_family``.
        required_families: Data-only family list to require.

    Returns:
        Audit with missing family/evidence/placeholder blockers. Missing rows
        are expanded into placeholder items so per-key blockers are explicit.
    """

    normalized = [_evidence_item(row) for row in evidence_rows]
    by_family = {item.method_family: item for item in normalized if item.method_family}
    required_names = {family.name for family in required_families}
    blockers: list[str] = []
    items: list[ActsMethodEvidence] = []

    for item in normalized:
        if item.method_family and item.method_family not in required_names:
            blockers.append(f"unknown_family:{item.method_family}")

    for family in required_families:
        item = by_family.get(family.name)
        if item is None:
            blockers.append(f"missing_family:{family.name}")
            item = ActsMethodEvidence(method_family=family.name)
        _audit_item(item, blockers)
        items.append(item)

    return _audit(blockers, items, tuple(required_families))


def audit_current_acts_tracking(
    root: str | Path = ".",
    evidence_rows: Sequence[Mapping[str, Any] | ActsMethodEvidence] = (),
) -> ActsTrackingAudit:
    """Audit the current ACTS tree plus optional caller-supplied evidence.

    Args:
        root: Repository root that may contain ``acts_tracking/``.
        evidence_rows: Optional manifest rows; absent rows fail closed.

    Returns:
        Audit result. Missing ``INTEGRATION_GUIDE.md`` is reported as a blocker
        rather than raising, so tests and portable checkouts remain skip-safe.
    """

    root_path = Path(root)
    guide_path = root_path / "acts_tracking" / "INTEGRATION_GUIDE.md"
    audit = audit_acts_tracking_evidence(evidence_rows)
    extra: list[str] = []

    if not guide_path.is_file():
        extra.append("missing_integration_guide")
    else:
        guide_text = guide_path.read_text(encoding="utf-8")
        if _TODO_RE.search(guide_text):
            extra.append("todo_marker:integration_guide")

    return _audit(audit.blockers + tuple(extra), audit.items, audit.families)


def _evidence_item(row: Mapping[str, Any] | ActsMethodEvidence) -> ActsMethodEvidence:
    if isinstance(row, ActsMethodEvidence):
        return row
    return ActsMethodEvidence(
        method_family=str(row.get("method_family", row.get("family", ""))).strip(),
        dataset_id=row.get("dataset_id", ""),
        truth_source=row.get("truth_source", ""),
        split=row.get("split", row.get("split_id", "")),
        sigma_r=row.get("sigma_r", ""),
        epsilon=row.get("epsilon", ""),
        deployable_or_oracle=row.get(
            "deployable_or_oracle",
            row.get("deployable_status", row.get("evidence_status", "")),
        ),
        artifact_path=str(row.get("artifact_path", "")).strip(),
        blocker_messages=tuple(
            str(message).strip()
            for message in row.get("blocker_messages", row.get("blockers", ()))
            if str(message).strip()
        ),
    )


def _audit_item(item: ActsMethodEvidence, blockers: list[str]) -> None:
    family = item.method_family or "missing_family"
    _require_pinned_text(item.dataset_id, family, "dataset_id", blockers)
    _require_text(item.truth_source, family, "truth_source", blockers)
    _require_split(item.split, family, blockers)
    _require_metric(item.sigma_r, family, "sigma_r", blockers)
    _require_metric(item.epsilon, family, "epsilon", blockers)
    _require_status(item.deployable_or_oracle, family, blockers)

    if item.artifact_path and _contains_todo(item.artifact_path):
        blockers.append(f"todo_marker:{family}:artifact_path")
    for message in item.blocker_messages:
        blockers.append(f"row_blocker:{family}:{message}")


def _require_pinned_text(
    value: Any, family: str, key: str, blockers: list[str]
) -> None:
    if _contains_todo(value):
        blockers.append(f"todo_marker:{family}:{key}")
    if _is_blank(value):
        blockers.append(f"missing_{key}:{family}")
        return
    text = str(value).strip()
    if _looks_like_local_path(text) or _VERSION_PIN_RE.search(text) is None:
        blockers.append(f"unpinned_{key}:{family}")


def _require_text(value: Any, family: str, key: str, blockers: list[str]) -> None:
    if _contains_todo(value):
        blockers.append(f"todo_marker:{family}:{key}")
    if _is_blank(value):
        blockers.append(f"missing_{key}:{family}")


def _require_split(value: Any, family: str, blockers: list[str]) -> None:
    if _contains_todo(value):
        blockers.append(f"todo_marker:{family}:split")
    if _is_blank(value):
        blockers.append(f"missing_split:{family}")
        return
    text = str(value).lower()
    has_validation = "val" in text or "validation" in text
    if "train" not in text or not has_validation or "test" not in text:
        blockers.append(f"incomplete_split:{family}")


def _require_metric(value: Any, family: str, key: str, blockers: list[str]) -> None:
    if _contains_todo(value):
        blockers.append(f"todo_marker:{family}:{key}")
    if _is_blank(value):
        blockers.append(f"missing_{key}:{family}")


def _require_status(value: Any, family: str, blockers: list[str]) -> None:
    if _contains_todo(value):
        blockers.append(f"todo_marker:{family}:deployable_or_oracle")
    if _is_blank(value):
        blockers.append(f"missing_status:{family}")
        return
    text = str(value).strip().lower()
    if text not in {DEPLOYABLE, ORACLE_ONLY, "oracle"}:
        blockers.append(f"invalid_status:{family}")
    elif text in {ORACLE_ONLY, "oracle"}:
        blockers.append(f"oracle_only_status:{family}")


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, Mapping):
        if "value" in value:
            return _is_blank(value.get("value"))
        return not value
    if isinstance(value, str):
        return bool(_PLACEHOLDER_RE.fullmatch(value.strip()))
    return False


def _contains_todo(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_TODO_RE.search(value))
    if isinstance(value, Mapping):
        return any(_contains_todo(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return any(_contains_todo(item) for item in value)
    return False


def _looks_like_local_path(value: str) -> bool:
    return value.startswith(("/", "~"))


def _audit(
    blockers: Sequence[str],
    items: Sequence[ActsMethodEvidence],
    families: Sequence[ActsMethodFamily],
) -> ActsTrackingAudit:
    deduped = tuple(dict.fromkeys(blockers))
    return ActsTrackingAudit(
        ready=not deduped,
        blockers=deduped,
        items=tuple(items),
        families=tuple(families),
    )
