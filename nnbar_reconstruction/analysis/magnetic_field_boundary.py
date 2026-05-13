"""Fail-closed audit helpers for the no-B-field reconstruction boundary.

The current reconstruction baseline treats TPC tracks as straight-line
objects.  Charge sign and magnetic momentum-from-curvature claims are therefore
outside the thesis-ready authority surface unless a future magnetic-field
scenario is explicitly introduced and validated.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Mapping

MAGNETIC_BOUNDARY_DOCS = (
    "docs/rebuild_plans/07_simulation_atomic_walkthrough/07_12_field_model.md",
    "docs/rebuild_plans/25_subsystem_tpc_hits_to_tracks.md",
    "docs/rebuild_plans/26_subsystem_track_fit_and_pulls.md",
    "docs/rebuild_plans/45_systematics_taxonomy.md",
)

MAGNETIC_OBSERVABLE = "charge sign or magnetic momentum from curvature"
BOUNDARY_FOM = "explicit no-B-field boundary statement"
FORBIDDEN_FOM = (
    "validated magnetic-field scenario with charge-sign and curvature-momentum "
    "closure"
)

_BOUNDARY_PATTERNS = (
    re.compile(r"\bno global magnetic field\b", re.IGNORECASE),
    re.compile(r"\bno[- ]B[- ]field\b", re.IGNORECASE),
    re.compile(r"\bwithout B[- ]field\b", re.IGNORECASE),
    re.compile(r"\bdoes not include a B[- ]field\b", re.IGNORECASE),
    re.compile(r"\bL9 no B[- ]field\b", re.IGNORECASE),
)

_STRAIGHT_LINE_PATTERNS = (
    re.compile(r"\bstraight[- ]line\b", re.IGNORECASE),
    re.compile(r"\bstraight tracks?\b", re.IGNORECASE),
    re.compile(r"\blinear[_ -]PCA\b", re.IGNORECASE),
    re.compile(r"\bLinear LS\b", re.IGNORECASE),
)

_DEFERRED_PATTERNS = (
    re.compile(r"\bdefer(?:red)?\b", re.IGNORECASE),
    re.compile(r"\buntil a? ?magnetic[- ]field scenario exists\b", re.IGNORECASE),
    re.compile(r"\bout of current scope\b", re.IGNORECASE),
    re.compile(r"\bmay not be quoted\b", re.IGNORECASE),
    re.compile(r"\breject such claims\b", re.IGNORECASE),
    re.compile(r"\bnon-baseline option\b", re.IGNORECASE),
    re.compile(r"\blimitation L9\b", re.IGNORECASE),
)

_FORBIDDEN_PATTERNS = (
    ("charge sign", re.compile(r"\bcharge[- ]sign\b", re.IGNORECASE)),
    (
        "momentum from curvature",
        re.compile(
            r"\bmomentum(?: measurement)?\s+from\s+curvature\b"
            r"|\bmagnetic[- ]momentum\b"
            r"|\bcurvature[- ]momentum\b",
            re.IGNORECASE,
        ),
    ),
)

_CLAIM_TERM = (
    r"(?:charge[- ]sign|magnetic[- ]momentum|curvature[- ]momentum|"
    r"momentum(?: measurement)?\s+from\s+curvature)"
)

_SAFE_CLAIM_PATTERNS = (
    re.compile(r"\bmay\s+not\s+be\s+quoted\b", re.IGNORECASE),
    re.compile(rf"\bno\s+{_CLAIM_TERM}(?:\s+or\s+{_CLAIM_TERM})?", re.IGNORECASE),
    re.compile(
        rf"\b{_CLAIM_TERM}\b[^.\n]{{0,80}}\b"
        r"(?:is|are|can|may|must|should)?\s*"
        r"(?:not|never|cannot|can't)\b[^.\n]{0,80}\b"
        r"(?:quoted|claimed|measured|reconstructed|estimated|used)\b",
        re.IGNORECASE,
    ),
    re.compile(rf"\b(?:does\s+)?not\s+include\b[^.\n]{{0,100}}\b{_CLAIM_TERM}\b", re.IGNORECASE),
    re.compile(
        rf"\b(?:defer(?:red)?|out[_ -]of(?: current)?[_ -]scope|non-baseline option|"
        rf"not directly applicable|reject(?:s|ed)?(?: such)? claims?)\b"
        rf"[^.\n]{{0,120}}\b{_CLAIM_TERM}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_CLAIM_TERM}\b[^.\n]{{0,120}}\b"
        rf"(?:defer(?:red)?|out[_ -]of(?: current)?[_ -]scope|non-baseline option|"
        rf"not directly applicable|reject(?:s|ed)?(?: such)? claims?)\b",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class MagneticBoundaryEvidence:
    """One no-B-field boundary evidence item found in a text surface.

    Args:
        source: Name of the inspected text surface.
        category: Evidence category, e.g. ``straight_line_baseline``.
        snippet: Trimmed sentence or line containing the evidence.
    """

    source: str
    category: str
    snippet: str


@dataclass(frozen=True)
class MagneticBoundaryBlocker:
    """Fail-closed blocker for an unsafe or undocumented magnetic boundary.

    Args:
        code: Stable machine-readable blocker code.
        source: Name of the inspected text surface.
        observable: Observable family blocked by the audit.
        figure_of_merit: Evidence required to clear the blocker.
        message: Deterministic human-readable summary.
        snippet: Trimmed sentence or line that triggered the blocker.
    """

    code: str
    source: str
    observable: str
    figure_of_merit: str
    message: str
    snippet: str


@dataclass(frozen=True)
class MagneticBoundaryAudit:
    """Complete no-B-field boundary audit result.

    Args:
        ready: True only when the boundary is documented and no unsafe claims
            are present.
        sources: Inspected source names.
        boundary_documented: Whether at least one source states the no-B-field
            boundary.
        deferred_provenance_present: Whether deferred scenario/systematics
            language is present.
        evidence: Boundary evidence records.
        blockers: Explicit fail-closed blockers.
    """

    ready: bool
    sources: tuple[str, ...]
    boundary_documented: bool
    deferred_provenance_present: bool
    evidence: tuple[MagneticBoundaryEvidence, ...]
    blockers: tuple[MagneticBoundaryBlocker, ...]


def audit_current_magnetic_field_boundary(root: str | Path = ".") -> MagneticBoundaryAudit:
    """Audit the current plan documents for no-B-field boundary claims.

    Args:
        root: Repository root containing the plan documents.

    Returns:
        Audit result for the four read-only magnetic-boundary references named
        in ``MAGNETIC_BOUNDARY_DOCS``.
    """
    root_path = Path(root)
    surfaces = {
        path: (root_path / path).read_text(encoding="utf-8")
        for path in MAGNETIC_BOUNDARY_DOCS
    }
    return audit_magnetic_field_boundary(surfaces)


def audit_magnetic_field_boundary(
    surfaces: Mapping[str, str] | Iterable[tuple[str, str]],
) -> MagneticBoundaryAudit:
    """Audit text surfaces for no-B-field reconstruction boundary safety.

    Args:
        surfaces: Mapping or iterable of ``(source, text)`` pairs to scan.

    Returns:
        Immutable audit. Missing no-B-field documentation and positive
        charge-sign or momentum-from-curvature claims fail closed.
    """
    items = tuple(surfaces.items() if isinstance(surfaces, Mapping) else surfaces)
    evidence: list[MagneticBoundaryEvidence] = []
    blockers: list[MagneticBoundaryBlocker] = []

    for source, text in items:
        evidence.extend(_evidence_for_source(source, text))
        blockers.extend(_forbidden_claim_blockers(source, text))

    boundary_documented = any(item.category == "no_b_field_boundary" for item in evidence)
    deferred_present = any(item.category == "deferred_scenario" for item in evidence)
    if not boundary_documented:
        blockers.append(_missing_boundary_blocker(tuple(source for source, _ in items)))

    return MagneticBoundaryAudit(
        ready=not blockers,
        sources=tuple(source for source, _ in items),
        boundary_documented=boundary_documented,
        deferred_provenance_present=deferred_present,
        evidence=tuple(evidence),
        blockers=tuple(blockers),
    )


def _evidence_for_source(source: str, text: str) -> tuple[MagneticBoundaryEvidence, ...]:
    evidence: list[MagneticBoundaryEvidence] = []
    for sentence in _sentences(text):
        if _matches_any(_BOUNDARY_PATTERNS, sentence):
            evidence.append(
                MagneticBoundaryEvidence(source, "no_b_field_boundary", sentence)
            )
        if _matches_any(_STRAIGHT_LINE_PATTERNS, sentence):
            evidence.append(
                MagneticBoundaryEvidence(source, "straight_line_baseline", sentence)
            )
        if _matches_any(_DEFERRED_PATTERNS, sentence):
            evidence.append(MagneticBoundaryEvidence(source, "deferred_scenario", sentence))
    return tuple(evidence)


def _forbidden_claim_blockers(
    source: str, text: str
) -> tuple[MagneticBoundaryBlocker, ...]:
    blockers: list[MagneticBoundaryBlocker] = []
    for sentence in _sentences(text):
        if _claim_is_safely_negated_or_deferred(sentence):
            continue
        for claim_label, pattern in _FORBIDDEN_PATTERNS:
            if pattern.search(sentence):
                blockers.append(
                    MagneticBoundaryBlocker(
                        code="forbidden_magnetic_claim",
                        source=source,
                        observable=MAGNETIC_OBSERVABLE,
                        figure_of_merit=FORBIDDEN_FOM,
                        message=(
                            f"{source} makes a positive {claim_label} claim in "
                            "the no-B-field baseline; require a validated "
                            "magnetic-field scenario before quoting it."
                        ),
                        snippet=sentence,
                    )
                )
    return tuple(blockers)


def _missing_boundary_blocker(sources: tuple[str, ...]) -> MagneticBoundaryBlocker:
    source_text = ", ".join(sources) if sources else "<none>"
    return MagneticBoundaryBlocker(
        code="missing_boundary_documentation",
        source=source_text,
        observable=MAGNETIC_OBSERVABLE,
        figure_of_merit=BOUNDARY_FOM,
        message=(
            "No inspected surface states the no-B-field boundary; add an "
            "explicit statement before charge-sign or magnetic momentum claims "
            "can be reviewed."
        ),
        snippet="",
    )


def _claim_is_safely_negated_or_deferred(sentence: str) -> bool:
    return _matches_any(_SAFE_CLAIM_PATTERNS, sentence)


def _matches_any(patterns: Iterable[re.Pattern[str]], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _sentences(text: str) -> tuple[str, ...]:
    chunks: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        chunks.extend(re.split(r"(?<=[.!?])\s+", stripped))
    return tuple(chunk.strip() for chunk in chunks if chunk.strip())
