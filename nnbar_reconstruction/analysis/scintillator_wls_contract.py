"""Fail-closed audit for scintillator WLS light-collection evidence.

The thesis Ch. 5 WLS contract is geometric: light collected at a SiPM must be
parameterized with a radial ``f(r)`` term and a longitudinal ``f(z)`` term. This
module only inventories source/config text and reports blockers; it does not run
simulations or tune constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Sequence

WLS_FUNCTION = "wls_function"
SCALAR_RESPONSE = "scalar_response"
MISSING_SURFACE = "missing_surface"

_RADIAL_PATTERNS = (
    re.compile(r"f\s*\(\s*r\s*\)", re.IGNORECASE),
    re.compile(r"\bf[_-]?r\b", re.IGNORECASE),
    re.compile(r"radial[^\n]{0,80}(?:wls|fiber|fibre|light)", re.IGNORECASE),
    re.compile(r"(?:wls|fiber|fibre|light)[^\n]{0,80}radial", re.IGNORECASE),
)
_LONGITUDINAL_PATTERNS = (
    re.compile(r"f\s*\(\s*z\s*\)", re.IGNORECASE),
    re.compile(r"\bf[_-]?z\b", re.IGNORECASE),
    re.compile(r"longitudinal[^\n]{0,80}(?:wls|fiber|fibre|light)", re.IGNORECASE),
    re.compile(r"(?:wls|fiber|fibre|light)[^\n]{0,80}longitudinal", re.IGNORECASE),
)
_SCALAR_PATTERNS = (
    re.compile(r"\blight_yield\b", re.IGNORECASE),
    re.compile(r"\battenuation_length\b", re.IGNORECASE),
    re.compile(r"photons\s*/\s*MeV", re.IGNORECASE),
    re.compile(r"SCINTILLATIONYIELD", re.IGNORECASE),
    re.compile(r"energyDeposit\s*\*\s*11136", re.IGNORECASE),
    re.compile(r"scintillation yield", re.IGNORECASE),
)
_PROVENANCE_PATTERNS = (
    re.compile(r"DEC-\d{4}-\d{2}-\d{2}[-A-Za-z0-9_]*"),
    re.compile(r"closure artifact", re.IGNORECASE),
    re.compile(r"output/calibration/[^\s)]+", re.IGNORECASE),
    re.compile(r"summary\.json", re.IGNORECASE),
)
_SOURCE_SUFFIXES = {".cc", ".hh", ".cpp", ".cxx", ".hpp", ".py", ".yaml", ".yml"}
_TEXT_SUFFIXES = _SOURCE_SUFFIXES | {".md", ".txt"}


@dataclass(frozen=True)
class EvidenceFinding:
    """Evidence for one WLS contract feature.

    Args:
        kind: Stable category such as ``WLS_FUNCTION`` or ``SCALAR_RESPONSE``.
        present: Whether matching evidence was found.
        sources: Source paths or labels that contributed evidence.
        source_backed: Whether any evidence came from code/config rather than docs.
        provenance_present: Whether the same scanned source mentions DEC/closure evidence.
        snippets: Short matched lines for diagnostics only.
    """

    kind: str
    present: bool
    sources: tuple[str, ...] = ()
    source_backed: bool = False
    provenance_present: bool = False
    snippets: tuple[str, ...] = ()


@dataclass(frozen=True)
class TextScan:
    """Diagnostic scan result for one text surface.

    Args:
        path: Path or label scanned.
        radial_function: Evidence for explicit ``f(r)`` behavior.
        longitudinal_function: Evidence for explicit ``f(z)`` behavior.
        scalar_response: Evidence for scalar yield/attenuation behavior.
        provenance_present: Whether DEC or closure-artifact text was present.
    """

    path: str
    radial_function: EvidenceFinding
    longitudinal_function: EvidenceFinding
    scalar_response: EvidenceFinding
    provenance_present: bool


@dataclass(frozen=True)
class SurfaceStatus:
    """Status for a candidate source/config/docs surface.

    Args:
        path: Relative path or directory label.
        status: ``scanned`` or ``missing``.
        message: Diagnostic message; never a readiness claim by itself.
    """

    path: str
    status: str
    message: str


@dataclass(frozen=True)
class WlsBlocker:
    """Concrete blocker needed before WLS light-collection closure.

    Args:
        code: Stable machine-readable blocker code.
        needed_sample: Sample or artifact required to resolve the blocker.
        observable: Observable that must be measured.
        figure_of_merit: Figure of merit required for closure.
        message: Human-readable fail-closed summary.
    """

    code: str
    needed_sample: str
    observable: str
    figure_of_merit: str
    message: str


@dataclass(frozen=True)
class WlsAuditReport:
    """Aggregated scintillator WLS contract audit result.

    Args:
        ready: True only when both WLS functions are source-backed and provenanced.
        radial_function: Aggregate evidence for ``f(r)``.
        longitudinal_function: Aggregate evidence for ``f(z)``.
        scalar_response: Aggregate evidence for scalar yield/attenuation.
        surfaces: Candidate surfaces that were scanned or missing.
        blockers: Explicit blockers when ``ready`` is false.
    """

    ready: bool
    radial_function: EvidenceFinding
    longitudinal_function: EvidenceFinding
    scalar_response: EvidenceFinding
    surfaces: tuple[SurfaceStatus, ...]
    blockers: tuple[WlsBlocker, ...]


def scan_text_for_wls_evidence(text: str, source_name: str) -> TextScan:
    """Classify one text blob for WLS and scalar scintillator-response evidence.

    Args:
        text: Source/config/docs text to scan.
        source_name: Diagnostic path or label for the text.

    Returns:
        A ``TextScan`` separating radial WLS, longitudinal WLS, scalar response,
        and DEC/closure-artifact provenance evidence.
    """
    provenance_present = _matches_any(text, _PROVENANCE_PATTERNS)
    source_backed = _is_source_backed(source_name)
    return TextScan(
        path=source_name,
        radial_function=_finding(
            WLS_FUNCTION, text, source_name, _RADIAL_PATTERNS, source_backed, provenance_present
        ),
        longitudinal_function=_finding(
            WLS_FUNCTION, text, source_name, _LONGITUDINAL_PATTERNS, source_backed, provenance_present
        ),
        scalar_response=_finding(
            SCALAR_RESPONSE, text, source_name, _SCALAR_PATTERNS, source_backed, provenance_present
        ),
        provenance_present=provenance_present,
    )


def audit_current_scintillator_wls_contract(root: str | Path = ".") -> WlsAuditReport:
    """Audit the current repository for scintillator WLS contract evidence.

    Args:
        root: Repository root. Defaults to the current directory.

    Returns:
        Fail-closed WLS audit report.
    """
    return audit_scintillator_wls_contract(root)


def audit_scintillator_wls_contract(root: str | Path = ".") -> WlsAuditReport:
    """Audit repository text surfaces for source-backed ``f(r)`` and ``f(z)``.

    Args:
        root: Repository root containing optional ``NNBAR_Detector`` and Python
            reconstruction/config surfaces.

    Returns:
        ``WlsAuditReport``. ``ready`` is false unless both WLS functions are
        found in code/config and each source also carries DEC or closure evidence.
    """
    root_path = Path(root)
    scans: list[TextScan] = []
    surfaces: list[SurfaceStatus] = []

    for candidate in _candidate_files(root_path):
        if candidate.exists() and candidate.is_file():
            text = candidate.read_text(errors="replace")
            rel = _relative_label(candidate, root_path)
            scans.append(scan_text_for_wls_evidence(text, rel))
            surfaces.append(SurfaceStatus(rel, "scanned", "surface scanned"))
        elif not _is_generated_by_directory_walk(candidate, root_path):
            rel = _relative_label(candidate, root_path)
            surfaces.append(SurfaceStatus(rel, "missing", "optional audit surface is absent"))

    radial = _aggregate(WLS_FUNCTION, (scan.radial_function for scan in scans))
    longitudinal = _aggregate(WLS_FUNCTION, (scan.longitudinal_function for scan in scans))
    scalar = _aggregate(SCALAR_RESPONSE, (scan.scalar_response for scan in scans))
    ready = _function_ready(radial) and _function_ready(longitudinal)
    blockers = () if ready else _blockers(radial, longitudinal, scalar, surfaces)
    return WlsAuditReport(
        ready=ready,
        radial_function=radial,
        longitudinal_function=longitudinal,
        scalar_response=scalar,
        surfaces=tuple(surfaces),
        blockers=blockers,
    )


def _candidate_files(root: Path) -> tuple[Path, ...]:
    direct = [
        root / "nnbar_reconstruction" / "config" / "nnbar_geometry.yaml",
        root / "nnbar_reconstruction" / "analysis" / "geometry_constants.py",
        root / "nnbar_reconstruction" / "analysis" / "timing_windows.py",
        root / "nnbar_reconstruction" / "reconstruction" / "timing_window.py",
        root / "docs" / "rebuild_plans" / "18_intercalibration.md",
        root
        / "docs"
        / "rebuild_plans"
        / "24_reconstruction_question_tree"
        / "24_2_calorimetry.md",
    ]
    detector_dir = root / "NNBAR_Detector"
    if detector_dir.exists():
        direct.extend(_iter_scintillator_detector_files(detector_dir))
    else:
        direct.append(detector_dir)
    return tuple(direct)


def _iter_scintillator_detector_files(detector_dir: Path) -> tuple[Path, ...]:
    files = []
    for path in detector_dir.rglob("*"):
        if not path.is_file() or path.name.startswith("._"):
            continue
        if path.suffix not in _TEXT_SUFFIXES:
            continue
        haystack = str(path).lower()
        if "scint" in haystack or "wls" in haystack or "sipm" in haystack:
            files.append(path)
    return tuple(sorted(files))


def _is_generated_by_directory_walk(candidate: Path, root: Path) -> bool:
    try:
        rel = candidate.relative_to(root)
    except ValueError:
        rel = candidate
    return len(rel.parts) > 0 and rel.parts[0] == "NNBAR_Detector" and candidate.suffix in _TEXT_SUFFIXES


def _finding(
    kind: str,
    text: str,
    source_name: str,
    patterns: Sequence[re.Pattern[str]],
    source_backed: bool,
    provenance_present: bool,
) -> EvidenceFinding:
    snippets = _snippets(text, patterns)
    present = bool(snippets)
    return EvidenceFinding(
        kind=kind,
        present=present,
        sources=(source_name,) if present else (),
        source_backed=source_backed if present else False,
        provenance_present=provenance_present if present else False,
        snippets=snippets,
    )


def _aggregate(kind: str, findings: Iterable[EvidenceFinding]) -> EvidenceFinding:
    present = False
    source_backed = False
    provenance_present = False
    sources: list[str] = []
    snippets: list[str] = []
    for finding in findings:
        if not finding.present:
            continue
        present = True
        source_backed = source_backed or finding.source_backed
        provenance_present = provenance_present or finding.provenance_present
        sources.extend(source for source in finding.sources if source not in sources)
        snippets.extend(snippet for snippet in finding.snippets if snippet not in snippets)
    return EvidenceFinding(
        kind=kind,
        present=present,
        sources=tuple(sources),
        source_backed=source_backed,
        provenance_present=provenance_present,
        snippets=tuple(snippets[:8]),
    )


def _function_ready(finding: EvidenceFinding) -> bool:
    return finding.present and finding.source_backed and finding.provenance_present


def _blockers(
    radial: EvidenceFinding,
    longitudinal: EvidenceFinding,
    scalar: EvidenceFinding,
    surfaces: Sequence[SurfaceStatus],
) -> tuple[WlsBlocker, ...]:
    blockers: list[WlsBlocker] = []
    if not _function_ready(radial):
        blockers.append(
            _wls_blocker(
                "missing_radial_wls_function",
                "n_SiPM / n_scint versus radial distance r",
                "fit residual and pull width for f(r)",
                radial,
            )
        )
    if not _function_ready(longitudinal):
        blockers.append(
            _wls_blocker(
                "missing_longitudinal_wls_function",
                "n_SiPM / n_WLS versus longitudinal distance z",
                "fit residual and pull width for f(z)",
                longitudinal,
            )
        )
    if scalar.present and blockers:
        blockers.append(
            WlsBlocker(
                code="scalar_response_only",
                needed_sample="cal_scintillator_wls_muon200_v1",
                observable="scalar light_yield/attenuation contrasted with SiPM collection maps",
                figure_of_merit="closure residual after replacing scalar response with f(r)*f(z)",
                message=(
                    "Current evidence includes scalar scintillator light-yield or attenuation "
                    "surfaces, but not a provenanced source-backed WLS f(r)*f(z) contract."
                ),
            )
        )
    if any(surface.status == "missing" for surface in surfaces):
        missing = ", ".join(surface.path for surface in surfaces if surface.status == "missing")
        blockers.append(
            WlsBlocker(
                code="missing_optional_surfaces",
                needed_sample="source inventory before cal_scintillator_wls_muon200_v1 promotion",
                observable="presence of source/config surfaces that define WLS response",
                figure_of_merit="all required source/config surfaces scanned or explicitly waived",
                message=f"Optional WLS audit surfaces are absent: {missing}",
            )
        )
    return tuple(blockers)


def _wls_blocker(
    code: str,
    observable: str,
    figure_of_merit: str,
    finding: EvidenceFinding,
) -> WlsBlocker:
    if not finding.present:
        reason = "no matching function evidence was found"
    elif not finding.source_backed:
        reason = "matching text is docs-only rather than source/config evidence"
    else:
        reason = "source evidence lacks a DEC or closure artifact tie"
    return WlsBlocker(
        code=code,
        needed_sample="cal_scintillator_wls_muon200_v1",
        observable=observable,
        figure_of_merit=figure_of_merit,
        message=(
            f"{code}: {reason}; require cal_scintillator_wls_muon200_v1, "
            f"observable {observable}, and figure of merit {figure_of_merit}."
        ),
    )


def _matches_any(text: str, patterns: Sequence[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _snippets(text: str, patterns: Sequence[re.Pattern[str]]) -> tuple[str, ...]:
    snippets: list[str] = []
    for line in text.splitlines():
        if any(pattern.search(line) for pattern in patterns):
            cleaned = " ".join(line.strip().split())
            if cleaned and cleaned not in snippets:
                snippets.append(cleaned[:160])
        if len(snippets) >= 4:
            break
    return tuple(snippets)


def _is_source_backed(source_name: str) -> bool:
    path = Path(source_name)
    if path.suffix not in _SOURCE_SUFFIXES:
        return False
    parts = set(path.parts)
    return bool({"NNBAR_Detector", "nnbar_reconstruction"} & parts) or path.suffix in {
        ".cc",
        ".hh",
        ".cpp",
        ".cxx",
        ".hpp",
    }


def _relative_label(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
