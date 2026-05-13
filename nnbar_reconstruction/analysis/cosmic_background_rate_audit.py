"""Fail-closed cosmic-background rate closure audit.

This module validates the evidence needed before Ch. 9 can use the CRY
weighted cosmic-background rate.  It checks the non-zero thesis Eq. 6.1 bins,
rate-normalization fields, and the known gamma-bin4 shard/root-stub blocker
without reading production data or submitting jobs.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Iterable, Mapping

from nnbar_reconstruction.data_pipeline.cosmic_weights import PARTICLES, get_weight

EXPECTED_COSMIC_BINS = tuple(
    (particle, ebin)
    for ebin in range(6)
    for particle_idx, particle in enumerate(PARTICLES)
    if get_weight(ebin, particle_idx) > 0.0
)

_GAMMA_BIN4 = ("gamma", 4)
_RATE_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "weighted_sum": ("weighted_sum", "total_weighted_events", "weighted_events"),
    "livetime_seconds": (
        "livetime_seconds",
        "total_livetime_seconds",
        "livetime",
    ),
    "output_rate": (
        "output_rate",
        "output_rate_hz",
        "cosmic_rate_hz",
        "cosmic_background_rate",
    ),
}


@dataclass(frozen=True)
class CosmicBackgroundRateBlocker:
    """One machine-readable cosmic-background audit blocker.

    Args:
        code: Stable blocker code for tests and planning notes.
        field: Bin or rate field responsible for the blocker.
        message: Deterministic fail-closed explanation.
    """

    code: str
    field: str
    message: str


@dataclass(frozen=True)
class CosmicBinEvidence:
    """Evidence status for one expected CRY particle/energy bin.

    Args:
        particle: Canonical particle name from ``cosmic_weights.PARTICLES``.
        ebin: CRY energy-bin index.
        status: ``non_stub``, ``merged_artifact``, ``documented_blocker``,
            ``stub``, or ``missing``.
        output_rows: Numeric row count when supplied.
        output_bytes: Numeric output file size when supplied.
        source: Optional evidence source or merge-artifact path.
        blocker: Fail-closed blocker for incomplete evidence.
    """

    particle: str
    ebin: int
    status: str
    output_rows: float | None
    output_bytes: float | None
    source: str
    blocker: CosmicBackgroundRateBlocker | None = None


@dataclass(frozen=True)
class CosmicRateFieldEvidence:
    """Evidence status for one rate-normalization field.

    Args:
        name: Canonical field name.
        present: Whether an alias was supplied in the summary mapping.
        value: Numeric value after validation, or ``None`` when blocked.
        column: Supplied summary key that matched this field.
        source: ``rate_summary:<column>`` or ``missing``.
        blocker: Fail-closed blocker for missing or invalid evidence.
    """

    name: str
    present: bool
    value: float | None
    column: str | None
    source: str
    blocker: CosmicBackgroundRateBlocker | None = None


@dataclass(frozen=True)
class CosmicBackgroundRateAudit:
    """Complete cosmic-background rate closure audit result.

    Args:
        ready: True only when every expected non-zero bin has non-stub or merged
            evidence and every rate field is present, numeric, and in range.
        expected_bin_count: Number of non-zero Eq. 6.1 CRY bins expected.
        bin_evidence: Evidence keyed by ``(particle, ebin)``.
        rate_evidence: Rate-field evidence keyed by canonical field name.
        blockers: Explicit fail-closed blockers.
    """

    ready: bool
    expected_bin_count: int
    bin_evidence: Mapping[tuple[str, int], CosmicBinEvidence]
    rate_evidence: Mapping[str, CosmicRateFieldEvidence]
    blockers: tuple[CosmicBackgroundRateBlocker, ...]


def audit_cosmic_background_rate(
    bin_records: Iterable[Mapping[str, Any]],
    *,
    rate_summary: Mapping[str, Any] | None = None,
) -> CosmicBackgroundRateAudit:
    """Audit Ch. 9 cosmic-background weighted-rate evidence.

    Args:
        bin_records: One synthetic or discovered evidence record per CRY bin.
            Records use ``particle`` and ``ebin`` plus ``output_rows`` and
            ``output_bytes``.  ``documented_blocker`` records a known missing
            artifact, and ``merge_artifact`` closes the gamma-bin4 root-stub
            blocker when a merged parquet exists.
        rate_summary: Mapping with weighted-sum, livetime, and output-rate
            fields.  Known aliases include ``total_weighted_events`` and
            ``cosmic_rate_hz``.

    Returns:
        Fail-closed audit result with per-bin, per-rate-field, and aggregate
        readiness evidence.  The function never invents defaults.
    """

    records_by_bin = _records_by_bin(bin_records)
    bin_evidence: dict[tuple[str, int], CosmicBinEvidence] = {}
    blockers: list[CosmicBackgroundRateBlocker] = []

    for particle, ebin in EXPECTED_COSMIC_BINS:
        evidence = _bin_evidence(particle, ebin, records_by_bin.get((particle, ebin)))
        bin_evidence[(particle, ebin)] = evidence
        if evidence.blocker is not None:
            blockers.append(evidence.blocker)

    rate_evidence = {
        name: _rate_field_evidence(name, rate_summary or {})
        for name in _RATE_FIELD_ALIASES
    }
    blockers.extend(
        evidence.blocker for evidence in rate_evidence.values() if evidence.blocker
    )

    blocker_tuple = tuple(blockers)
    return CosmicBackgroundRateAudit(
        ready=not blocker_tuple,
        expected_bin_count=len(EXPECTED_COSMIC_BINS),
        bin_evidence=bin_evidence,
        rate_evidence=rate_evidence,
        blockers=blocker_tuple,
    )


def _records_by_bin(
    bin_records: Iterable[Mapping[str, Any]],
) -> dict[tuple[str, int], Mapping[str, Any]]:
    records: dict[tuple[str, int], Mapping[str, Any]] = {}
    for record in bin_records:
        particle = str(record.get("particle", ""))
        ebin_value = _numeric_value(record.get("ebin"))
        if particle in PARTICLES and ebin_value is not None:
            records[(particle, int(ebin_value))] = record
    return records


def _bin_evidence(
    particle: str,
    ebin: int,
    record: Mapping[str, Any] | None,
) -> CosmicBinEvidence:
    field = f"{particle}:{ebin}"
    if record is None:
        blocker = CosmicBackgroundRateBlocker(
            code=f"missing_bin:{particle}:{ebin}",
            field=field,
            message=f"Missing CRY evidence for {particle} energy bin {ebin}.",
        )
        return CosmicBinEvidence(particle, ebin, "missing", None, None, "missing", blocker)

    merge_artifact = _nonempty_string(record.get("merge_artifact"))
    if (particle, ebin) == _GAMMA_BIN4 and merge_artifact:
        return CosmicBinEvidence(
            particle,
            ebin,
            "merged_artifact",
            _numeric_value(record.get("output_rows")),
            _numeric_value(record.get("output_bytes")),
            merge_artifact,
        )

    rows = _numeric_value(record.get("output_rows", record.get("rows")))
    output_bytes = _numeric_value(record.get("output_bytes", record.get("bytes")))
    if rows is None or output_bytes is None:
        missing = "output_rows" if rows is None else "output_bytes"
        blocker = CosmicBackgroundRateBlocker(
            code=f"nonnumeric_bin_field:{particle}:{ebin}:{missing}",
            field=field,
            message=f"CRY bin {field} has nonnumeric {missing} evidence.",
        )
        return CosmicBinEvidence(
            particle, ebin, "stub", rows, output_bytes, _source(record), blocker
        )

    if rows > 0.0 and output_bytes > 4.0:
        return CosmicBinEvidence(
            particle, ebin, "non_stub", rows, output_bytes, _source(record)
        )

    documented = _nonempty_string(record.get("documented_blocker"))
    if documented:
        code = (
            "gamma_bin4_unmerged_shards"
            if (particle, ebin) == _GAMMA_BIN4
            else f"documented_bin_blocker:{particle}:{ebin}"
        )
        blocker = CosmicBackgroundRateBlocker(
            code=code,
            field=field,
            message=documented,
        )
        return CosmicBinEvidence(
            particle, ebin, "documented_blocker", rows, output_bytes, _source(record), blocker
        )

    blocker = CosmicBackgroundRateBlocker(
        code=f"stub_bin_output:{particle}:{ebin}",
        field=field,
        message=f"CRY bin {field} has stub or empty output without a documented blocker.",
    )
    return CosmicBinEvidence(
        particle, ebin, "stub", rows, output_bytes, _source(record), blocker
    )


def _rate_field_evidence(
    name: str,
    summary: Mapping[str, Any],
) -> CosmicRateFieldEvidence:
    for alias in _RATE_FIELD_ALIASES[name]:
        if alias in summary:
            return _validated_rate_field(name, alias, summary[alias])

    blocker = CosmicBackgroundRateBlocker(
        code=f"missing_rate_field:{name}",
        field=name,
        message=f"Missing cosmic-background rate summary field {name!r}.",
    )
    return CosmicRateFieldEvidence(name, False, None, None, "missing", blocker)


def _validated_rate_field(name: str, column: str, raw_value: Any) -> CosmicRateFieldEvidence:
    value = _numeric_value(raw_value)
    source = f"rate_summary:{column}"
    if value is None:
        blocker = CosmicBackgroundRateBlocker(
            code=f"nonnumeric_rate_field:{name}",
            field=name,
            message=f"Cosmic-background field {name!r} from {source} is not numeric.",
        )
        return CosmicRateFieldEvidence(name, True, None, column, source, blocker)

    if name == "livetime_seconds" and value <= 0.0:
        blocker = CosmicBackgroundRateBlocker(
            code=f"invalid_rate_field:{name}",
            field=name,
            message="Cosmic-background livetime must be positive.",
        )
        return CosmicRateFieldEvidence(name, True, value, column, source, blocker)

    if name in {"weighted_sum", "output_rate"} and value < 0.0:
        blocker = CosmicBackgroundRateBlocker(
            code=f"invalid_rate_field:{name}",
            field=name,
            message=f"Cosmic-background field {name!r} must be non-negative.",
        )
        return CosmicRateFieldEvidence(name, True, value, column, source, blocker)

    return CosmicRateFieldEvidence(name, True, value, column, source)


def _numeric_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(number):
        return None
    return number


def _nonempty_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _source(record: Mapping[str, Any]) -> str:
    return str(record.get("source") or record.get("path") or "bin_record")
