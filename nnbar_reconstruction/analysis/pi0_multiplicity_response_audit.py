"""Fail-closed multi-π⁰ response audit helpers.

The π⁰ multiplicity study is evidence-only: it inspects precomputed response
summary tables for same-vertex one-, two-, and three-π⁰ samples and reports
blockers instead of generating samples, retuning reconstruction cuts, or
submitting SLURM jobs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import re
from typing import Mapping

import pandas as pd

REQUIRED_MULTIPLICITIES = (1, 2, 3)
REQUIRED_RESPONSE_COLUMNS = (
    "event_count",
    "reco_efficiency",
    "invariant_mass_confusion_rate",
    "opening_angle_separation_deg",
)
_COLUMN_ALIASES = {
    "event_count": ("event_count", "n_events", "events"),
    "reco_efficiency": ("reco_efficiency", "reconstruction_efficiency", "efficiency"),
    "invariant_mass_confusion_rate": (
        "invariant_mass_confusion_rate",
        "mass_confusion_rate",
        "pi0_mass_confusion_rate",
    ),
    "opening_angle_separation_deg": (
        "opening_angle_separation_deg",
        "opening_angle_separation_mean_deg",
        "mean_opening_angle_separation_deg",
    ),
}


@dataclass(frozen=True)
class Pi0MultiplicityBlocker:
    """Structured blocker for a multi-π⁰ response audit.

    Args:
        code: Stable machine-readable blocker identifier.
        multiplicity: Required π⁰ multiplicity associated with the blocker.
        reason: Human-readable fail-closed explanation.
    """

    code: str
    multiplicity: int
    reason: str


@dataclass(frozen=True)
class Pi0MultiplicityResponse:
    """Response metrics for one required π⁰ multiplicity.

    Args:
        multiplicity: Number of same-event π⁰ primaries in the evidence table.
        parquet_path: Existing evidence table path. CSV inputs are also allowed;
            the attribute name mirrors older Parquet-focused audit helpers.
        event_count: Number of events represented by the response table.
        reco_efficiency: Reconstructed π⁰ efficiency for this multiplicity.
        invariant_mass_confusion_rate: Fraction of events with ambiguous or
            wrong diphoton invariant-mass assignment.
        opening_angle_separation_deg: Opening-angle separation summary in
            degrees for this multiplicity.
    """

    multiplicity: int
    parquet_path: Path
    event_count: int
    reco_efficiency: float
    invariant_mass_confusion_rate: float
    opening_angle_separation_deg: float


@dataclass(frozen=True)
class Pi0MultiplicityAuditReport:
    """Complete fail-closed multi-π⁰ response audit result.

    Args:
        ready: True only when all required multiplicities have numeric metrics.
        responses: Parsed response metrics in multiplicity order.
        blockers: Structured blockers for missing samples/schema/metrics.
    """

    ready: bool
    responses: tuple[Pi0MultiplicityResponse, ...]
    blockers: tuple[Pi0MultiplicityBlocker, ...]


def run_pi0_multiplicity_response_audit(search_root: str | Path) -> Pi0MultiplicityAuditReport:
    """Discover and audit existing one-, two-, and three-π⁰ response tables.

    Args:
        search_root: Directory containing staged response CSV/Parquet tables.

    Returns:
        Fail-closed report. Missing files become blockers; this function never
        writes files or launches simulations.
    """

    root = Path(search_root)
    paths = {
        multiplicity: discover_pi0_multiplicity_sample(multiplicity, root)
        for multiplicity in REQUIRED_MULTIPLICITIES
    }
    return audit_pi0_multiplicity_response(paths)


def discover_pi0_multiplicity_sample(multiplicity: int, search_root: str | Path) -> Path | None:
    """Locate a staged response table for one π⁰ multiplicity.

    Args:
        multiplicity: Required count, currently 1, 2, or 3.
        search_root: Directory to scan for existing ``*.parquet`` or ``*.csv``
            evidence tables.

    Returns:
        Deterministically selected existing table, or ``None`` when absent.
    """

    root = Path(search_root)
    if not root.exists():
        return None

    candidates = [
        path
        for pattern in ("*.parquet", "*.csv")
        for path in root.rglob(pattern)
        if not path.name.startswith("._") and _path_mentions_multiplicity(path, multiplicity)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=_discovery_key)[0]


def audit_pi0_multiplicity_response(
    evidence_paths: Mapping[int, str | Path | None],
) -> Pi0MultiplicityAuditReport:
    """Audit explicit response tables for required π⁰ multiplicities.

    Args:
        evidence_paths: Mapping from multiplicity ``1``, ``2``, and ``3`` to an
            existing CSV/Parquet response table path.

    Returns:
        Fail-closed report with parsed numeric metrics or blockers.
    """

    blockers: list[Pi0MultiplicityBlocker] = []
    responses: list[Pi0MultiplicityResponse] = []

    for multiplicity in REQUIRED_MULTIPLICITIES:
        raw_path = evidence_paths.get(multiplicity)
        if raw_path is None:
            blockers.append(_missing_sample_blocker(multiplicity))
            continue

        path = Path(raw_path)
        if not path.exists():
            blockers.append(_missing_sample_blocker(multiplicity, path))
            continue

        frame = _read_table(path, multiplicity, blockers)
        if frame is None:
            continue
        response = _response_from_frame(frame, multiplicity, path, blockers)
        if response is not None:
            responses.append(response)

    ordered_responses = tuple(sorted(responses, key=lambda item: item.multiplicity))
    ordered_blockers = tuple(blockers)
    return Pi0MultiplicityAuditReport(
        ready=not ordered_blockers and len(ordered_responses) == len(REQUIRED_MULTIPLICITIES),
        responses=ordered_responses,
        blockers=ordered_blockers,
    )


def _read_table(
    path: Path,
    multiplicity: int,
    blockers: list[Pi0MultiplicityBlocker],
) -> pd.DataFrame | None:
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
        return pd.read_parquet(path)
    except Exception as exc:  # pragma: no cover - depends on corrupt external files
        blockers.append(
            Pi0MultiplicityBlocker(
                code=f"pi0_multiplicity_{multiplicity}pi0_sample_unreadable",
                multiplicity=multiplicity,
                reason=f"Could not read multi-π⁰ response evidence table {path}: {exc}",
            )
        )
        return None


def _response_from_frame(
    frame: pd.DataFrame,
    multiplicity: int,
    path: Path,
    blockers: list[Pi0MultiplicityBlocker],
) -> Pi0MultiplicityResponse | None:
    metrics: dict[str, float] = {}
    for canonical in REQUIRED_RESPONSE_COLUMNS:
        value = _numeric_metric(frame, canonical, multiplicity, blockers)
        if value is not None:
            metrics[canonical] = value

    if set(metrics) != set(REQUIRED_RESPONSE_COLUMNS):
        return None

    invalid = _invalid_metrics(metrics, multiplicity)
    blockers.extend(invalid)
    if invalid:
        return None

    return Pi0MultiplicityResponse(
        multiplicity=multiplicity,
        parquet_path=path,
        event_count=int(metrics["event_count"]),
        reco_efficiency=float(metrics["reco_efficiency"]),
        invariant_mass_confusion_rate=float(metrics["invariant_mass_confusion_rate"]),
        opening_angle_separation_deg=float(metrics["opening_angle_separation_deg"]),
    )


def _numeric_metric(
    frame: pd.DataFrame,
    canonical: str,
    multiplicity: int,
    blockers: list[Pi0MultiplicityBlocker],
) -> float | None:
    column = _present_column(frame, canonical)
    if column is None:
        blockers.append(
            Pi0MultiplicityBlocker(
                code=f"missing_response_column:{multiplicity}:{canonical}",
                multiplicity=multiplicity,
                reason=(
                    f"Missing required multi-π⁰ response column {canonical!r} "
                    f"for {multiplicity}π⁰ evidence."
                ),
            )
        )
        return None

    numeric = pd.to_numeric(frame[column], errors="coerce").dropna()
    if numeric.empty:
        blockers.append(
            Pi0MultiplicityBlocker(
                code=f"nonnumeric_response_metric:{multiplicity}:{canonical}",
                multiplicity=multiplicity,
                reason=(
                    f"Column {column!r} for {multiplicity}π⁰ evidence does not "
                    "contain a finite numeric metric."
                ),
            )
        )
        return None
    return float(numeric.iloc[0])


def _present_column(frame: pd.DataFrame, canonical: str) -> str | None:
    for column in _COLUMN_ALIASES[canonical]:
        if column in frame.columns:
            return column
    return None


def _invalid_metrics(metrics: Mapping[str, float], multiplicity: int) -> tuple[Pi0MultiplicityBlocker, ...]:
    blockers: list[Pi0MultiplicityBlocker] = []
    for column, value in metrics.items():
        if not math.isfinite(float(value)):
            blockers.append(_invalid_metric_blocker(multiplicity, column, value, "is not finite"))
    if metrics.get("event_count", 0.0) <= 0:
        blockers.append(
            _invalid_metric_blocker(multiplicity, "event_count", metrics.get("event_count", 0.0), "must be positive")
        )
    for column in ("reco_efficiency", "invariant_mass_confusion_rate"):
        value = metrics.get(column, 0.0)
        if not 0.0 <= value <= 1.0:
            blockers.append(_invalid_metric_blocker(multiplicity, column, value, "must be in [0, 1]"))
    if metrics.get("opening_angle_separation_deg", 0.0) < 0.0:
        blockers.append(
            _invalid_metric_blocker(
                multiplicity,
                "opening_angle_separation_deg",
                metrics.get("opening_angle_separation_deg", 0.0),
                "must be nonnegative",
            )
        )
    return tuple(blockers)


def _invalid_metric_blocker(multiplicity: int, column: str, value: float, rule: str) -> Pi0MultiplicityBlocker:
    return Pi0MultiplicityBlocker(
        code=f"invalid_response_metric:{multiplicity}:{column}",
        multiplicity=multiplicity,
        reason=f"Metric {column!r} for {multiplicity}π⁰ evidence has value {value!r}; {rule}.",
    )


def _missing_sample_blocker(multiplicity: int, path: Path | None = None) -> Pi0MultiplicityBlocker:
    suffix = f" at {path}" if path is not None else ""
    return Pi0MultiplicityBlocker(
        code=f"pi0_multiplicity_{multiplicity}pi0_sample_missing",
        multiplicity=multiplicity,
        reason=(
            f"No existing response evidence table for {multiplicity}π⁰ events{suffix}; "
            "per lane spec this audit must not generate samples or submit SLURM."
        ),
    )


def _path_mentions_multiplicity(path: Path, multiplicity: int) -> bool:
    text = path.as_posix().lower().replace("π", "pi")
    if "pi0" not in text:
        return False
    patterns = (
        rf"pi0[_-]?multiplicity[_/-]?{multiplicity}(?:[_-]?pi0)?",
        rf"{multiplicity}[_-]?pi0",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _discovery_key(path: Path) -> tuple[int, str]:
    text = path.as_posix().lower()
    preferred = int(not any(token in text for token in ("response", "summary", "audit")))
    return preferred, text
