"""Fail-closed audit helpers for scintillator WLS light collection.

The thesis Ch. 5 WLS parameterisation is treated as an evidence contract:
source text must expose both radial ``f(r)`` and longitudinal ``f(z)`` light-
collection functions, and those functions must be tied to a DEC or closure
artifact before the implementation is considered ready. Scalar light-yield or
attenuation constants are diagnostic evidence only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

CURRENT_WLS_SOURCE_SURFACES = (
    Path("nnbar_reconstruction/config/nnbar_geometry.yaml"),
    Path("NNBAR_Detector/src/Sensitive_Detector/ScintillatorSD.cc"),
    Path("NNBAR_Detector/src/sensitive/ScintillatorSD.cc"),
    Path("NNBAR_Detector/src/Detector_Module/Scintillator_geometry.cc"),
    Path("NNBAR_Detector/src/detector/Scintillator_geometry.cc"),
)

WLS_CLOSURE_SAMPLE = "cal_scintillator_wls_uniform_scan_v1"
WLS_CLOSURE_FIGURE_OF_MERIT = (
    "closure residual of source-backed f(r)/f(z) against detected photon yield map"
)

_RADIAL_FUNCTION_PATTERN = re.compile(
    r"\b(?:scintillator_)?wls[_a-z0-9]*f[_ ]?r\s*\("
    r"|\bf[_ ]?r\s*\("
    r"|\bf\s*\(\s*r\s*\)",
    re.IGNORECASE,
)
_LONGITUDINAL_FUNCTION_PATTERN = re.compile(
    r"\b(?:scintillator_)?wls[_a-z0-9]*f[_ ]?z\s*\("
    r"|\bf[_ ]?z\s*\("
    r"|\bf\s*\(\s*z\s*\)",
    re.IGNORECASE,
)
_SCALAR_LIGHT_YIELD_PATTERN = re.compile(
    r"energyDeposit\s*\*\s*11136(?:\.0*)?"
    r"|SCINTILLATIONYIELD"
    r"|\blight_yield\s*:"
    r"|photons\s*/\s*MeV"
    r"|\bscintYield_\b",
    re.IGNORECASE,
)
_ATTENUATION_PATTERN = re.compile(
    r"ABSLENGTH|atten(?:uation)?[_a-z0-9]*(?:scint|length)|atten_scint",
    re.IGNORECASE,
)
_WLS_COMMENT_PATTERN = re.compile(r"^\s*(?://|#).*\bWLS\b", re.IGNORECASE | re.MULTILINE)
_BLOCK_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)
_DEC_PATTERN = re.compile(r"\bDEC-\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class EvidencePackage:
    """Evidence inputs for the scintillator WLS contract audit.

    Args:
        source_surfaces: Source/config files to scan. Missing files are
            reported as blockers rather than raising exceptions.
        provenance: DEC identifier or record tying observed WLS functions to
            thesis Ch. 5 and the closure sample.
        closure_artifact: Optional artifact path; existence can satisfy the
            provenance gate even without a DEC string.
    """

    source_surfaces: tuple[str | Path, ...] = ()
    provenance: str | None = None
    closure_artifact: str | Path | None = None


@dataclass(frozen=True)
class ObservedWLSSurface:
    """One diagnostic observation from a scanned WLS-related surface.

    Args:
        path: Source/config surface that was scanned.
        kind: Stable category such as ``wls_radial_function``.
        status: ``source_backed`` for WLS functions or ``diagnostic_only`` for
            scalar/constants evidence.
        evidence: Short text label describing the pattern that matched.
        message: Deterministic human-readable summary.
    """

    path: Path
    kind: str
    status: str
    evidence: str
    message: str


@dataclass(frozen=True)
class WLSBlocker:
    """Fail-closed blocker for missing WLS contract evidence.

    Args:
        code: Stable blocker identifier.
        sample: Needed sample/evidence package.
        observable: Observable required to resolve the blocker.
        figure_of_merit: Metric that must pass before promotion.
        message: Deterministic summary suitable for task notes.
    """

    code: str
    sample: str
    observable: str
    figure_of_merit: str
    message: str


@dataclass(frozen=True)
class ScintillatorWLSAudit:
    """Combined WLS light-collection contract audit.

    Args:
        ready: True only when both WLS functions and DEC/closure provenance are
            present and no scanned surface is missing.
        observed_surfaces: Diagnostic observations from source/config scans.
        blockers: Fail-closed blockers for absent functions or provenance.
        required_sample: Closure sample needed for unresolved blockers.
    """

    ready: bool
    observed_surfaces: tuple[ObservedWLSSurface, ...]
    blockers: tuple[WLSBlocker, ...]
    required_sample: str = WLS_CLOSURE_SAMPLE


def audit_scintillator_wls_contract(
    package: EvidencePackage | None = None,
    *,
    root: str | Path = ".",
) -> ScintillatorWLSAudit:
    """Audit source-backed WLS ``f(r)`` and ``f(z)`` evidence.

    Args:
        package: Evidence surfaces and provenance to audit. Missing fields fail
            closed; scalar constants are recorded but not accepted as WLS
            functions.
        root: Repository root used to resolve relative source/artifact paths.

    Returns:
        Immutable audit report. ``ready`` is true only when both WLS functions
        are source-backed and tied to a DEC or closure artifact.
    """
    evidence = package or EvidencePackage()
    root_path = Path(root)
    observed: list[ObservedWLSSurface] = []
    blockers: list[WLSBlocker] = []

    for surface in evidence.source_surfaces:
        surface_observed, surface_blockers = _scan_surface(surface, root_path)
        observed.extend(surface_observed)
        blockers.extend(surface_blockers)

    observed_kinds = {surface.kind for surface in observed}
    has_radial = "wls_radial_function" in observed_kinds
    has_longitudinal = "wls_longitudinal_function" in observed_kinds
    has_scalar_only = bool(
        observed_kinds & {"scalar_light_yield", "attenuation_length"}
    ) and not (has_radial and has_longitudinal)

    if not has_radial:
        blockers.append(_missing_function_blocker("radial"))
    if not has_longitudinal:
        blockers.append(_missing_function_blocker("longitudinal"))
    if not _has_dec_or_closure(evidence, root_path):
        blockers.append(_missing_provenance_blocker(evidence))
    if has_scalar_only:
        blockers.append(_scalar_only_blocker())

    return ScintillatorWLSAudit(
        ready=not blockers,
        observed_surfaces=tuple(observed),
        blockers=tuple(blockers),
    )


def audit_current_scintillator_wls_contract(
    root: str | Path = ".",
) -> ScintillatorWLSAudit:
    """Audit the current checkout's known scintillator WLS-related surfaces.

    Args:
        root: Repository root used for relative path resolution.

    Returns:
        Fail-closed current-checkout report. The C++ mirror is optional at scan
        time: absent files become diagnostic blockers instead of tracebacks.
    """
    return audit_scintillator_wls_contract(
        EvidencePackage(source_surfaces=CURRENT_WLS_SOURCE_SURFACES),
        root=root,
    )


def _scan_surface(
    surface: str | Path, root: Path
) -> tuple[tuple[ObservedWLSSurface, ...], tuple[WLSBlocker, ...]]:
    path, display = _resolve_surface(surface, root)
    if not path.exists():
        return (), (_missing_surface_blocker(display),)

    raw_text = path.read_text(errors="replace")
    code_text = _strip_comments(raw_text)
    observed: list[ObservedWLSSurface] = []

    if _RADIAL_FUNCTION_PATTERN.search(code_text):
        observed.append(
            _observed(display, "wls_radial_function", "source_backed", "f(r)")
        )
    if _LONGITUDINAL_FUNCTION_PATTERN.search(code_text):
        observed.append(
            _observed(display, "wls_longitudinal_function", "source_backed", "f(z)")
        )
    if _SCALAR_LIGHT_YIELD_PATTERN.search(code_text):
        observed.append(
            _observed(
                display,
                "scalar_light_yield",
                "diagnostic_only",
                "scalar photons/MeV yield",
            )
        )
    if _ATTENUATION_PATTERN.search(code_text):
        observed.append(
            _observed(
                display,
                "attenuation_length",
                "diagnostic_only",
                "attenuation/ABSLENGTH constant",
            )
        )
    if _WLS_COMMENT_PATTERN.search(raw_text) and not (
        _RADIAL_FUNCTION_PATTERN.search(code_text)
        or _LONGITUDINAL_FUNCTION_PATTERN.search(code_text)
    ):
        observed.append(
            _observed(display, "wls_geometry_comment", "diagnostic_only", "WLS comment")
        )

    return tuple(observed), ()


def _observed(
    display: str, kind: str, status: str, evidence: str
) -> ObservedWLSSurface:
    return ObservedWLSSurface(
        path=Path(display),
        kind=kind,
        status=status,
        evidence=evidence,
        message=f"{display}: observed {evidence} as {kind} ({status})",
    )


def _resolve_surface(surface: str | Path, root: Path) -> tuple[Path, str]:
    original = Path(surface)
    if original.is_absolute():
        return original, str(original)
    return root / original, str(original)


def _strip_comments(text: str) -> str:
    without_blocks = _BLOCK_COMMENT_PATTERN.sub(" ", text)
    code_lines = []
    for line in without_blocks.splitlines():
        line = line.split("//", 1)[0]
        line = line.split("#", 1)[0]
        code_lines.append(line)
    return "\n".join(code_lines)


def _has_dec_or_closure(evidence: EvidencePackage, root: Path) -> bool:
    if evidence.provenance and _DEC_PATTERN.search(evidence.provenance):
        return True
    if evidence.closure_artifact is None:
        return False
    artifact = Path(evidence.closure_artifact)
    if not artifact.is_absolute():
        artifact = root / artifact
    return artifact.exists()


def _missing_function_blocker(axis: str) -> WLSBlocker:
    if axis == "radial":
        code = "missing_wls_radial_function"
        observable = "detected light-collection response vs local radial coordinate r"
    else:
        code = "missing_wls_longitudinal_function"
        observable = "detected light-collection response vs local longitudinal coordinate z"
    return WLSBlocker(
        code=code,
        sample=WLS_CLOSURE_SAMPLE,
        observable=observable,
        figure_of_merit=WLS_CLOSURE_FIGURE_OF_MERIT,
        message=(
            f"{code}: need {WLS_CLOSURE_SAMPLE} with {observable}; "
            f"figure of merit: {WLS_CLOSURE_FIGURE_OF_MERIT}"
        ),
    )


def _missing_provenance_blocker(evidence: EvidencePackage) -> WLSBlocker:
    supplied = evidence.provenance or evidence.closure_artifact or "none"
    return WLSBlocker(
        code="missing_wls_provenance",
        sample="scintillator-wls evidence package",
        observable="DEC record or closure artifact tying f(r)/f(z) to Ch. 5",
        figure_of_merit="sample ID, command, artifact hash, fit covariance, closure residual",
        message=(
            "missing_wls_provenance: need DEC or closure artifact tying source "
            f"functions to Ch. 5; supplied={supplied}"
        ),
    )


def _scalar_only_blocker() -> WLSBlocker:
    return WLSBlocker(
        code="scalar_scintillator_response_without_wls_contract",
        sample=WLS_CLOSURE_SAMPLE,
        observable="joint f(r) and f(z) light-collection map, not a scalar yield only",
        figure_of_merit=WLS_CLOSURE_FIGURE_OF_MERIT,
        message=(
            "scalar_scintillator_response_without_wls_contract: current scalar "
            "light-yield/attenuation evidence cannot replace WLS f(r)/f(z); "
            f"needed sample={WLS_CLOSURE_SAMPLE}; figure of merit: "
            f"{WLS_CLOSURE_FIGURE_OF_MERIT}"
        ),
    )


def _missing_surface_blocker(display: str) -> WLSBlocker:
    return WLSBlocker(
        code=f"missing_surface:{display}",
        sample="source/config checkout",
        observable="scintillator WLS source/config surface",
        figure_of_merit="file exists or optional mirror is explicitly absent in task notes",
        message=f"missing_surface:{display}",
    )
