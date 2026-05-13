"""Fail-closed audit helpers for HIBEAM GNN feature/result contracts.

The helpers in this module intentionally operate on caller-supplied
schema dictionaries, result manifests, or text blobs.  They do not read
absolute local paths, train models, or promote paper numbers; they only
classify whether the supplied evidence is deployable or still blocked.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence

DEPLOYABLE = "deployable"
ORACLE_ONLY = "oracle_only"

REQUIRED_COMPTON_LEVELS = (0, 1, 2, 4, 8)
REQUIRED_TRACK_FEATURES = (
    "track_start_x",
    "track_start_y",
    "track_start_z",
    "track_end_x",
    "track_end_y",
    "track_end_z",
    "track_direction_x",
    "track_direction_y",
    "track_direction_z",
    "track_length",
    "n_hits",
    "mean_hit_spacing",
)
REQUIRED_MODEL_KEYS = ("track_gnn", "vertex_gnn")
REQUIRED_METRIC_KEYS = ("sigma_r", "epsilon", "uncertainty")

_ORACLE_SOURCE_CATEGORIES = {
    "truth",
    "truth_ancestry",
    "truth_label",
    "particle_label",
    "particle_parquet",
    "particle_parquet_label",
    "simulation_truth",
}
_ORACLE_NAME_PATTERNS = (
    "truth",
    "parent_id",
    "particle_id",
    "track_id",
    "true_cluster",
    "label",
)


@dataclass(frozen=True)
class FeatureContractItem:
    """Classified feature-contract row.

    Args:
        name: Feature-column name.
        source_category: Source classification supplied by the caller.
        evidence_status: ``deployable`` or ``oracle_only`` after audit.
        required_artifact: Schema, registry, or validation artifact needed
            to support this item.
        blocker: Optional fail-closed blocker code for this item.
    """

    name: str
    source_category: str
    evidence_status: str
    required_artifact: str
    blocker: str | None = None


@dataclass(frozen=True)
class AuditResult:
    """Audit outcome for a single evidence surface.

    Args:
        ready: True only when no blockers remain.
        blockers: Stable blocker codes explaining missing evidence.
        items: Optional feature rows classified by the audit.
    """

    ready: bool
    blockers: tuple[str, ...] = ()
    items: tuple[FeatureContractItem, ...] = ()


@dataclass(frozen=True)
class ContractAudit:
    """Combined HIBEAM GNN feature-schema and result-manifest audit."""

    ready: bool
    blockers: tuple[str, ...]
    feature_audit: AuditResult
    result_audit: AuditResult


def audit_hibeam_gnn_contract(
    feature_schema: Sequence[Mapping[str, Any]],
    result_manifest: Mapping[str, Any],
) -> ContractAudit:
    """Audit a feature schema and result manifest as one contract.

    Args:
        feature_schema: Iterable of feature-schema rows.
        result_manifest: Manifest describing datasets, models, split
            evidence, Compton-level rows, and metric uncertainties.

    Returns:
        Combined audit with merged blocker codes.
    """

    feature_audit = audit_feature_schema(feature_schema)
    result_audit = audit_result_manifest(result_manifest)
    blockers = feature_audit.blockers + result_audit.blockers
    return ContractAudit(
        ready=not blockers,
        blockers=blockers,
        feature_audit=feature_audit,
        result_audit=result_audit,
    )


def audit_feature_schema(
    feature_schema: Sequence[Mapping[str, Any]],
) -> AuditResult:
    """Classify HIBEAM GNN features as deployable or oracle-only.

    Truth ancestry, particle labels, and particle-parquet-derived labels
    are downgraded to ``oracle_only`` unless a caller supplies a truly
    reconstructed deployable source category.

    Args:
        feature_schema: Feature-schema row dictionaries.

    Returns:
        Audit result containing classified items and missing-evidence
        blockers.
    """

    blockers: list[str] = []
    items: list[FeatureContractItem] = []
    seen_names: set[str] = set()

    for raw in feature_schema:
        name = str(raw.get("name", "")).strip()
        source_category = str(raw.get("source_category", "")).strip()
        artifact = str(raw.get("required_artifact", "")).strip()
        requested_status = str(raw.get("evidence_status", "")).strip() or DEPLOYABLE

        status = requested_status
        blocker: str | None = None
        if _is_oracle_feature(name, source_category):
            status = ORACLE_ONLY
            blocker = f"oracle_feature:{name}"
            blockers.append(blocker)
        elif status != DEPLOYABLE:
            blocker = f"non_deployable_feature:{name}"
            blockers.append(blocker)

        if not artifact:
            missing = f"missing_feature_artifact:{name}"
            blockers.append(missing)
            blocker = blocker or missing

        if name:
            seen_names.add(name)
        items.append(
            FeatureContractItem(
                name=name,
                source_category=source_category,
                evidence_status=status,
                required_artifact=artifact,
                blocker=blocker,
            )
        )

    for required in REQUIRED_TRACK_FEATURES:
        if required not in seen_names:
            blockers.append(f"missing_feature:{required}")

    return _result(blockers, items)


def audit_result_manifest(result_manifest: Mapping[str, Any]) -> AuditResult:
    """Audit model, split, Compton-level, and metric evidence.

    Args:
        result_manifest: Caller-supplied manifest dictionary.

    Returns:
        Audit result with stable blocker codes for missing evidence.
    """

    blockers: list[str] = []

    for key in ("dataset_id", "artifact_path"):
        if not result_manifest.get(key):
            blockers.append(f"missing_{key}")

    models = _mapping(result_manifest.get("models"))
    for model_key in REQUIRED_MODEL_KEYS:
        if not models.get(model_key):
            blockers.append(f"missing_model:{model_key}")

    _audit_split(result_manifest.get("split"), blockers)

    rows = _result_rows(result_manifest.get("results"))
    levels_present = {_as_int(row.get("compton_level")) for row in rows}
    for level in REQUIRED_COMPTON_LEVELS:
        if level not in levels_present:
            blockers.append(f"missing_compton_level:{level}")

    for row in rows:
        level = _as_int(row.get("compton_level"))
        prefix = f"level:{level}" if level is not None else "level:missing"
        if row.get("deployable_status", DEPLOYABLE) != DEPLOYABLE:
            blockers.append(f"oracle_result:{prefix}")

        metrics = _mapping(row.get("metrics"))
        for metric in REQUIRED_METRIC_KEYS:
            if metrics.get(metric) is None:
                blockers.append(f"missing_metric:{prefix}:{metric}")

    return _result(blockers)


def audit_article_text(article_text: str) -> AuditResult:
    """Audit article text for unresolved HIBEAM result placeholders.

    Args:
        article_text: LaTeX article text supplied by the caller.

    Returns:
        Audit result with blockers for TODO markers, placeholder refs,
        and placeholder metric cells.
    """

    blockers: list[str] = []
    if re.search(r"\\todo(?:number|plot|text|table)?|TODO", article_text, re.IGNORECASE):
        blockers.append("article_todo_marker")
    if re.search(r"\\obs\{|XXX|YYY|\[APPENDIX\?\]", article_text):
        blockers.append("article_placeholder_reference")
    if re.search(r"(^|&)\s*~\s*(&|\\\\)", article_text) or "placeholder" in article_text.lower():
        blockers.append("article_placeholder_metric")

    return _result(blockers)


def audit_preparation_script_text(script_text: str) -> AuditResult:
    """Audit preparation-script text for oracle labels and split gaps.

    Args:
        script_text: Concatenated Python source text supplied by the caller.

    Returns:
        Audit result with blockers when training data depends on truth or
        lacks explicit train/validation/test split evidence.
    """

    blockers: list[str] = []
    patterns = {
        "parent_id": r"Parent_ID",
        "particle_parquet": r"Particle_output_0\.parquet",
        "truth_vertex": r"truth_vertex|truth_vertices",
        "truth_cluster": r"true_cluster|Track_ID",
        "label_from_particle_source": r"label\s*=\s*[01]|get_binary_label",
    }
    for code, pattern in patterns.items():
        if re.search(pattern, script_text):
            blockers.append(f"oracle_training_source:{code}")

    lower = script_text.lower()
    has_train = "train" in lower
    has_validation = "val" in lower or "validation" in lower
    has_test = bool(re.search(r"\btest\b|\btesting\b", lower))
    if not (has_train and has_validation and has_test):
        blockers.append("missing_test_split_evidence")

    return _result(blockers)


def _audit_split(split: Any, blockers: list[str]) -> None:
    """Append split-evidence blockers for incomplete split manifests."""

    if not isinstance(split, Mapping):
        blockers.append("missing_split_evidence")
        return

    if split.get("scope") != "per-event":
        blockers.append("missing_per_event_split_scope")
    if split.get("seed") is None:
        blockers.append("missing_split_seed")

    fractions = _mapping(split.get("fractions"))
    for key in ("train", "validation", "test"):
        if fractions.get(key) is None:
            blockers.append(f"missing_split_fraction:{key}")


def _is_oracle_feature(name: str, source_category: str) -> bool:
    """Return True when a feature is truth/particle-label derived."""

    source = source_category.lower()
    feature = name.lower()
    if source in _ORACLE_SOURCE_CATEGORIES:
        return True
    return any(pattern in feature for pattern in _ORACLE_NAME_PATTERNS)


def _result(
    blockers: Iterable[str],
    items: Iterable[FeatureContractItem] = (),
) -> AuditResult:
    """Create a deterministic audit result with de-duplicated blockers."""

    unique_blockers = tuple(dict.fromkeys(blockers))
    return AuditResult(
        ready=not unique_blockers,
        blockers=unique_blockers,
        items=tuple(items),
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    """Return ``value`` when it is a mapping, otherwise an empty mapping."""

    if isinstance(value, Mapping):
        return value
    return {}


def _result_rows(value: Any) -> tuple[Mapping[str, Any], ...]:
    """Return result rows when supplied as a sequence of mappings."""

    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(row for row in value if isinstance(row, Mapping))


def _as_int(value: Any) -> int | None:
    """Convert integer-like Compton levels without raising."""

    try:
        return int(value)
    except (TypeError, ValueError):
        return None
