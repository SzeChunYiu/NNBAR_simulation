"""Fail-closed HIBEAM vertex method-comparison audit helpers."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence


DEPLOYABLE = "deployable"
ORACLE_ONLY = "oracle_only"

REQUIRED_METHODS = (
    "least_squares",
    "trackless",
    "graphnet",
    "clustering_gnn",
)
REQUIRED_COMPTON_LEVELS = (0, 1, 2, 4, 8)
REQUIRED_AXIS_METRICS = ("dx", "dy", "d_tot", "epsilon")
RADIAL_UNCERTAINTY_METRICS = ("sigma_r", "radial_uncertainty")
ASSOCIATION_EFFICIENCY_METRICS = (
    "signal_track_association_efficiency",
    "signal_hit_association_efficiency",
    "association_efficiency",
)
UNCERTAINTY_KEYS = (
    "uncertainty",
    "error",
    "std",
    "sigma",
    "stat_uncertainty",
    "ci95",
)

_PLACEHOLDER_RE = re.compile(
    r"^(?:|~|[-–—]|todo|tbd|placeholder|xxx|yyy|\\todo(?:number|plot|table|text)?)$",
    re.IGNORECASE,
)
_VERSION_PIN_RE = re.compile(r"(?:^|[_:-])v\d+(?:$|[_:-])", re.IGNORECASE)
_ARTICLE_METHOD_PATTERNS = {
    "least_squares": re.compile(r"Least[- ]Squares|Least[- ]squares", re.IGNORECASE),
    "trackless": re.compile(r"Trackless", re.IGNORECASE),
    "graphnet": re.compile(r"GraphNeT", re.IGNORECASE),
    "clustering_gnn": re.compile(r"Clustering\+GNN|Combined Clustering/GNN", re.IGNORECASE),
}


@dataclass(frozen=True)
class VertexMethodResult:
    """One method/Compton-level vertex-comparison evidence row."""

    method: str
    compton_level: int | None
    dataset_id: str
    truth_source: str
    split_id: str
    metric_definitions: Mapping[str, Any]
    metrics: Mapping[str, Any]
    artifact_path: str
    deployable_status: str
    label_source: str = ""
    blocker_messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class VertexMethodAudit:
    """Audit outcome for HIBEAM vertex method-comparison evidence."""

    ready: bool
    blockers: tuple[str, ...] = ()
    items: tuple[VertexMethodResult, ...] = ()


AuditResult = VertexMethodAudit


def audit_vertex_method_manifest(
    manifest_or_rows: Mapping[str, Any] | Sequence[Mapping[str, Any] | VertexMethodResult],
) -> VertexMethodAudit:
    """Audit caller-supplied vertex method result rows."""

    rows = _extract_rows(manifest_or_rows)
    blockers: list[str] = []
    items = [_result_item(row) for row in rows]

    if not rows:
        blockers.append("missing_results")

    present_methods = {item.method for item in items if item.method in REQUIRED_METHODS}
    for method in REQUIRED_METHODS:
        if method not in present_methods:
            blockers.append(f"missing_method:{method}")

    present_pairs = {
        (item.method, item.compton_level)
        for item in items
        if item.method in REQUIRED_METHODS and item.compton_level in REQUIRED_COMPTON_LEVELS
    }
    present_levels = {
        item.compton_level for item in items if item.compton_level in REQUIRED_COMPTON_LEVELS
    }
    for level in REQUIRED_COMPTON_LEVELS:
        if level not in present_levels:
            blockers.append(f"missing_compton_level:{level}")
    for method in REQUIRED_METHODS:
        for level in REQUIRED_COMPTON_LEVELS:
            if (method, level) not in present_pairs:
                blockers.append(f"missing_result:{method}:level:{level}")

    seen_pairs: set[tuple[str, int | None]] = set()
    for item in items:
        pair = (item.method, item.compton_level)
        if pair in seen_pairs:
            blockers.append(f"duplicate_result:{_prefix(item)}")
        seen_pairs.add(pair)
        _audit_result_item(item, blockers)

    return _audit(blockers, items)


def audit_article_method_tables(article_text: str) -> VertexMethodAudit:
    """Audit HIBEAM article text for unresolved method-table evidence gaps."""

    blockers: list[str] = []
    for method, pattern in _ARTICLE_METHOD_PATTERNS.items():
        if not pattern.search(article_text):
            blockers.append(f"article_missing_method:{method}")

    for level in REQUIRED_COMPTON_LEVELS:
        if not re.search(rf"\b{level}\s*(?:Compton|,|and\s+8)", article_text):
            blockers.append(f"article_missing_compton_level:{level}")

    if re.search(r"\\todo(?:number|plot|text|table)?\b|\bTODO\b", article_text, re.IGNORECASE):
        blockers.append("article_todo_marker")
    if re.search(r"\\obs\s*\{|\bXXX\b|\bYYY\b|\[APPENDIX\?\]", article_text):
        blockers.append("article_placeholder_reference")
    if re.search(r"(^|&)\s*~\s*(&|\\\\)", article_text, re.MULTILINE):
        blockers.append("article_placeholder_metric")
    if not re.search(r"hibeam[_-]vertex[_-][A-Za-z0-9_.-]*v\d+", article_text):
        blockers.append("article_missing_pinned_dataset_id")

    return _audit(blockers, ())


def audit_article_text(article_text: str) -> VertexMethodAudit:
    """Alias for auditing current HIBEAM article method tables."""

    return audit_article_method_tables(article_text)


def _extract_rows(
    manifest_or_rows: Mapping[str, Any] | Sequence[Mapping[str, Any] | VertexMethodResult],
) -> Sequence[Mapping[str, Any] | VertexMethodResult]:

    if isinstance(manifest_or_rows, Mapping):
        raw_rows = manifest_or_rows.get("results", ())
        if isinstance(raw_rows, Sequence) and not isinstance(raw_rows, (str, bytes)):
            return raw_rows
        return ()
    return manifest_or_rows


def _result_item(row: Mapping[str, Any] | VertexMethodResult) -> VertexMethodResult:
    if isinstance(row, VertexMethodResult):
        return row
    metric_definitions = _mapping(row.get("metric_definitions"))
    metrics = _mapping(row.get("metrics")) or metric_definitions
    return VertexMethodResult(
        method=str(row.get("method_name", row.get("method", ""))).strip(),
        compton_level=_as_int(row.get("compton_level")),
        dataset_id=str(row.get("dataset_id", "")).strip(),
        truth_source=str(row.get("truth_source", "")).strip(),
        split_id=str(row.get("split_id", "")).strip(),
        metric_definitions=metric_definitions,
        metrics=metrics,
        artifact_path=str(row.get("artifact_path", "")).strip(),
        deployable_status=str(
            row.get("deployable_status", row.get("evidence_status", ""))
        ).strip()
        or ORACLE_ONLY,
        label_source=str(row.get("label_source", "")).strip(),
        blocker_messages=tuple(
            str(message).strip()
            for message in row.get("blocker_messages", row.get("blockers", ()))
            if str(message).strip()
        ),
    )


def _audit_result_item(item: VertexMethodResult, blockers: list[str]) -> None:
    prefix = _prefix(item)
    if item.method not in REQUIRED_METHODS:
        blockers.append(f"unknown_method:{item.method or 'missing'}")
    if item.compton_level not in REQUIRED_COMPTON_LEVELS:
        blockers.append(f"unknown_compton_level:{prefix}")

    if not item.dataset_id:
        blockers.append(f"missing_dataset:{prefix}")
    elif _is_unpinned_identifier(item.dataset_id):
        blockers.append(f"unpinned_dataset:{prefix}")

    if not item.truth_source:
        blockers.append(f"missing_truth_source:{prefix}")
    elif _is_oracle_truth_source(item.truth_source):
        blockers.append(f"oracle_truth_source:{prefix}")

    if not item.split_id:
        blockers.append(f"missing_split_id:{prefix}")
    elif _is_unpinned_split_id(item.split_id):
        blockers.append(f"unpinned_split:{prefix}")

    if not item.artifact_path:
        blockers.append(f"missing_artifact_path:{prefix}")
    elif _looks_like_local_path(item.artifact_path) or _is_placeholder(item.artifact_path):
        blockers.append(f"unpinned_artifact_path:{prefix}")

    if item.deployable_status != DEPLOYABLE:
        blockers.append(f"oracle_only_result:{prefix}")
    if _is_oracle_label_source(item.label_source):
        blockers.append(f"oracle_label_source:{prefix}")

    for message in item.blocker_messages:
        blockers.append(f"row_blocker:{prefix}:{message}")

    _audit_metrics(item, blockers)


def _audit_metrics(item: VertexMethodResult, blockers: list[str]) -> None:
    prefix = _prefix(item)
    for metric in REQUIRED_AXIS_METRICS:
        _require_metric(item, metric, prefix, blockers, require_uncertainty=True)

    radial = _first_present_metric(item, RADIAL_UNCERTAINTY_METRICS)
    if radial is None:
        blockers.append(f"missing_radial_uncertainty:{prefix}")
    else:
        _require_definition(item, radial, prefix, blockers)
        if _is_blank_metric(item.metrics.get(radial)):
            blockers.append(f"missing_metric:{prefix}:{radial}")

    if _is_blank_metric(item.metrics.get("outlier_definition")) and _is_blank_metric(
        item.metric_definitions.get("outlier_definition")
    ):
        blockers.append(f"missing_outlier_definition:{prefix}")

    association = _first_present_metric(item, ASSOCIATION_EFFICIENCY_METRICS)
    if association is None:
        blockers.append(f"missing_association_efficiency:{prefix}")
    else:
        _require_metric(item, association, prefix, blockers, require_uncertainty=True)


def _require_metric(
    item: VertexMethodResult,
    metric: str,
    prefix: str,
    blockers: list[str],
    *,
    require_uncertainty: bool,
) -> None:

    _require_definition(item, metric, prefix, blockers)
    value = item.metrics.get(metric)
    if _is_blank_metric(value):
        blockers.append(f"missing_metric:{prefix}:{metric}")
        return
    if require_uncertainty and not _has_uncertainty(item.metrics, metric):
        blockers.append(f"missing_uncertainty:{prefix}:{metric}")


def _require_definition(
    item: VertexMethodResult,
    metric: str,
    prefix: str,
    blockers: list[str],
) -> None:

    if _is_blank_metric(item.metric_definitions.get(metric)):
        blockers.append(f"missing_metric_definition:{prefix}:{metric}")


def _first_present_metric(item: VertexMethodResult, metrics: Sequence[str]) -> str | None:
    for metric in metrics:
        if not _is_blank_metric(item.metrics.get(metric)):
            return metric
    return None


def _has_uncertainty(metrics: Mapping[str, Any], metric: str) -> bool:
    value = metrics.get(metric)
    if isinstance(value, Mapping):
        return any(not _is_blank_metric(value.get(key)) for key in UNCERTAINTY_KEYS)
    return any(
        not _is_blank_metric(metrics.get(f"{metric}_{suffix}"))
        for suffix in ("uncertainty", "error", "std", "sigma")
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _prefix(item: VertexMethodResult) -> str:
    method = item.method or "missing_method"
    level = item.compton_level if item.compton_level is not None else "missing"
    return f"{method}:level:{level}"


def _is_blank_metric(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, Mapping):
        if "value" in value:
            return _is_blank_metric(value.get("value"))
        return not value
    if isinstance(value, str):
        return bool(_PLACEHOLDER_RE.fullmatch(value.strip()))
    return False


def _is_placeholder(value: str) -> bool:
    return bool(_PLACEHOLDER_RE.fullmatch(value.strip()))


def _looks_like_local_path(value: str) -> bool:
    return value.startswith(("/", "~"))


def _is_unpinned_identifier(value: str) -> bool:
    cleaned = value.strip()
    lowered = cleaned.lower()
    if _looks_like_local_path(cleaned) or _is_placeholder(cleaned):
        return True
    if lowered in {"latest", "head", "main", "master", "dev"}:
        return True
    return _VERSION_PIN_RE.search(cleaned) is None


def _is_unpinned_split_id(value: str) -> bool:
    cleaned = value.strip()
    lowered = cleaned.lower()
    if _looks_like_local_path(cleaned) or _is_placeholder(cleaned):
        return True
    if lowered in {"latest", "head", "main", "master", "dev"}:
        return True
    return _VERSION_PIN_RE.search(cleaned) is None and "seed" not in lowered


def _is_oracle_label_source(value: str) -> bool:
    lowered = value.lower()
    if not lowered:
        return False
    oracle_tokens = (
        "particle_output",
        "particle label",
        "particle_label",
        "truth particle",
        "truth_particle",
        "truth label",
        "truth_label",
        "parent_id",
        "track_id",
        "oracle",
    )
    return any(token in lowered for token in oracle_tokens)


def _is_oracle_truth_source(value: str) -> bool:
    lowered = value.lower()
    oracle_tokens = (
        "particle_output",
        "particle label",
        "particle_label",
        "truth label",
        "truth_label",
        "parent_id",
        "track_id",
        "oracle",
    )
    return any(token in lowered for token in oracle_tokens)


def _audit(blockers: Sequence[str], items: Sequence[VertexMethodResult]) -> VertexMethodAudit:
    deduped = tuple(dict.fromkeys(blockers))
    return VertexMethodAudit(ready=not deduped, blockers=deduped, items=tuple(items))
