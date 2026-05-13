"""Fail-closed audit helpers for lead-glass PMT calibration evidence.

The thesis Ch. 5 PMT calibration is the linear relation
``E_gamma = 0.46 N_PMT + 8.02`` for ``N_PMT > 0``.  Current Python/C++
surfaces may expose other optical-model constants; this module reports those
as evidence states and blockers rather than retuning production code.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from pathlib import Path
import re
from typing import Iterable


THESIS_LEADGLASS_REFLECTIVITY_PERCENT = 90.0
CURRENT_PYTHON_SURFACES = (
    Path("nnbar_reconstruction/calibration/leadglass_calibration.py"),
)
CURRENT_CPP_REFLECTIVITY_SURFACES = (
    Path("NNBAR_Detector/src/detector/LeadGlass_geometry.cc"),
    Path("NNBAR_Detector/src/Detector_Module/LeadGlass_geometry.cc"),
)

_REFLECTIVITY_TOLERANCE_PERCENT = 1e-9
_PYTHON_PHOTONS_PER_MEV_PATTERN = re.compile(
    r"(?:nominal_cerenkov_yield|cerenkov_yield)\s*[^=\n]*=\s*"
    r"(?P<value>[0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)
_CPP_REFLECTIVITY_PATTERN = re.compile(
    r"reflectivity_coating\s*\[\s*\]\s*=\s*\{\s*"
    r"(?P<value>[0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PMTEnergyCalibration:
    """Thesis PMT-count to photon-energy calibration.

    Args:
        slope_mev_per_pmt: Slope multiplying ``N_PMT``.
        intercept_mev: Additive intercept in MeV.
        valid_when: Domain condition for the calibration.
        source: Human-readable provenance label.
    """

    slope_mev_per_pmt: float
    intercept_mev: float
    valid_when: str
    source: str

    def energy_mev(self, n_pmt: float) -> float:
        """Return calibrated photon energy for a positive PMT count.

        Args:
            n_pmt: PMT count. The thesis formula is valid only for
                ``N_PMT > 0``.

        Returns:
            Calibrated photon energy in MeV.

        Raises:
            ValueError: If ``n_pmt`` does not satisfy ``N_PMT > 0``.
        """
        count = float(n_pmt)
        if count <= 0.0:
            raise ValueError("N_PMT must satisfy N_PMT > 0 for the Ch. 5 formula")
        return self.slope_mev_per_pmt * count + self.intercept_mev


@dataclass(frozen=True)
class ObservedCalibrationSurface:
    """One observed current calibration-related surface.

    Args:
        path: Surface inspected.
        kind: Stable surface category.
        observed_value: Numeric value parsed from the surface.
        expected_value: Thesis value when comparable; ``None`` otherwise.
        unit: Unit for ``observed_value``.
        status: ``match``, ``mismatch``, or ``non_thesis``.
        message: Deterministic summary suitable for task notes.
    """

    path: Path
    kind: str
    observed_value: float
    expected_value: float | None
    unit: str
    status: str
    message: str


@dataclass(frozen=True)
class CalibrationBlocker:
    """Fail-closed blocker for unpromoted calibration evidence.

    Args:
        code: Stable blocker identifier.
        surface: Surface that produced the blocker.
        message: Deterministic human-readable explanation.
    """

    code: str
    surface: str
    message: str


@dataclass(frozen=True)
class LeadGlassPMTCalibrationAudit:
    """Audit result for lead-glass PMT calibration surfaces.

    Args:
        thesis_calibration: Ch. 5 PMT-count energy formula.
        thesis_reflectivity_percent: Ch. 5 lead-glass reflectivity value.
        observed_surfaces: Parsed current Python/C++ evidence.
        blockers: Fail-closed blockers for missing or mismatching evidence.
        ready: Whether all supplied surfaces are thesis-compatible.
    """

    thesis_calibration: PMTEnergyCalibration
    thesis_reflectivity_percent: float
    observed_surfaces: tuple[ObservedCalibrationSurface, ...]
    blockers: tuple[CalibrationBlocker, ...]
    ready: bool


THESIS_PMT_ENERGY_CALIBRATION = PMTEnergyCalibration(
    slope_mev_per_pmt=0.46,
    intercept_mev=8.02,
    valid_when="N_PMT > 0",
    source="Thesis Ch. 5 lead-glass PMT calibration: E_gamma = 0.46 N_PMT + 8.02",
)


def pmt_count_to_gamma_energy_mev(n_pmt: float) -> float:
    """Return Ch. 5 calibrated photon energy from a PMT count.

    Args:
        n_pmt: PMT count satisfying ``N_PMT > 0``.

    Returns:
        Photon energy in MeV from ``E_gamma = 0.46 N_PMT + 8.02``.

    Raises:
        ValueError: If ``n_pmt`` is not positive.
    """
    return THESIS_PMT_ENERGY_CALIBRATION.energy_mev(n_pmt)


def audit_leadglass_pmt_calibration(
    *,
    python_surfaces: Iterable[str | Path] = CURRENT_PYTHON_SURFACES,
    cpp_reflectivity_surfaces: Iterable[str | Path] = CURRENT_CPP_REFLECTIVITY_SURFACES,
    root: str | Path = ".",
) -> LeadGlassPMTCalibrationAudit:
    """Audit supplied Python/C++ lead-glass calibration-related surfaces.

    Args:
        python_surfaces: Python files to scan for generic photons/MeV
            Cerenkov-yield constants.
        cpp_reflectivity_surfaces: C++ files to scan for lead-glass coating
            reflectivity constants.
        root: Repository root used to resolve relative surface paths.

    Returns:
        Combined audit report. Missing files, generic photons/MeV evidence,
        and reflectivity mismatches produce blockers instead of exceptions.
    """
    root_path = Path(root)
    observed: list[ObservedCalibrationSurface] = []
    blockers: list[CalibrationBlocker] = []

    for surface in python_surfaces:
        surface_observed, surface_blockers = _scan_python_surface(surface, root_path)
        observed.extend(surface_observed)
        blockers.extend(surface_blockers)

    for surface in cpp_reflectivity_surfaces:
        surface_observed, surface_blockers = _scan_cpp_reflectivity_surface(
            surface, root_path
        )
        observed.extend(surface_observed)
        blockers.extend(surface_blockers)

    return LeadGlassPMTCalibrationAudit(
        thesis_calibration=THESIS_PMT_ENERGY_CALIBRATION,
        thesis_reflectivity_percent=THESIS_LEADGLASS_REFLECTIVITY_PERCENT,
        observed_surfaces=tuple(observed),
        blockers=tuple(blockers),
        ready=not blockers,
    )


def audit_current_leadglass_pmt_calibration(
    root: str | Path = ".",
) -> LeadGlassPMTCalibrationAudit:
    """Audit the current checkout's known lead-glass calibration surfaces.

    Args:
        root: Repository root used for relative path resolution.

    Returns:
        Fail-closed current-checkout audit. Optional external C++ surfaces are
        reported as ``missing_surface:<path>`` blockers when absent.
    """
    return audit_leadglass_pmt_calibration(root=root)


def _scan_python_surface(
    surface: str | Path, root: Path
) -> tuple[tuple[ObservedCalibrationSurface, ...], tuple[CalibrationBlocker, ...]]:
    path, display = _resolve_surface(surface, root)
    if not path.exists():
        return (), (_missing_surface_blocker(display),)

    text = path.read_text(errors="replace")
    match = _PYTHON_PHOTONS_PER_MEV_PATTERN.search(text)
    if match is None:
        return (), (
            CalibrationBlocker(
                code="missing_python_photons_per_mev",
                surface=display,
                message=f"{display} has no parsed generic photons/MeV lead-glass yield",
            ),
        )

    value = float(match.group("value"))
    observed = ObservedCalibrationSurface(
        path=Path(display),
        kind="python_cerenkov_yield",
        observed_value=value,
        expected_value=None,
        unit="photons_per_mev",
        status="non_thesis",
        message=(
            f"{display} reports {value:g} photons/MeV; this is not the thesis "
            "Ch. 5 PMT calibration E_gamma = 0.46 N_PMT + 8.02"
        ),
    )
    blocker = CalibrationBlocker(
        code="non_thesis_photons_per_mev",
        surface=display,
        message=observed.message,
    )
    return (observed,), (blocker,)


def _scan_cpp_reflectivity_surface(
    surface: str | Path, root: Path
) -> tuple[tuple[ObservedCalibrationSurface, ...], tuple[CalibrationBlocker, ...]]:
    path, display = _resolve_surface(surface, root)
    if not path.exists():
        return (), (_missing_surface_blocker(display),)

    text = path.read_text(errors="replace")
    match = _CPP_REFLECTIVITY_PATTERN.search(text)
    if match is None:
        return (), (
            CalibrationBlocker(
                code="missing_cpp_reflectivity",
                surface=display,
                message=f"{display} has no parsed reflectivity_coating[] value",
            ),
        )

    observed_percent = _coerce_reflectivity_percent(float(match.group("value")))
    matches_thesis = isclose(
        observed_percent,
        THESIS_LEADGLASS_REFLECTIVITY_PERCENT,
        rel_tol=0.0,
        abs_tol=_REFLECTIVITY_TOLERANCE_PERCENT,
    )
    status = "match" if matches_thesis else "mismatch"
    message = (
        f"{display} reports {observed_percent:g}% lead-glass coating "
        f"reflectivity; thesis expects {THESIS_LEADGLASS_REFLECTIVITY_PERCENT:g}%"
    )
    observed = ObservedCalibrationSurface(
        path=Path(display),
        kind="cpp_reflectivity",
        observed_value=observed_percent,
        expected_value=THESIS_LEADGLASS_REFLECTIVITY_PERCENT,
        unit="percent",
        status=status,
        message=message if matches_thesis else f"{message}; mismatch not accepted",
    )
    if matches_thesis:
        return (observed,), ()
    return (
        (observed,),
        (
            CalibrationBlocker(
                code="reflectivity_mismatch",
                surface=display,
                message=observed.message,
            ),
        ),
    )


def _resolve_surface(surface: str | Path, root: Path) -> tuple[Path, str]:
    original = Path(surface)
    if original.is_absolute():
        return original, str(original)
    return root / original, str(original)


def _missing_surface_blocker(display: str) -> CalibrationBlocker:
    return CalibrationBlocker(
        code=f"missing_surface:{display}",
        surface=display,
        message=f"missing_surface:{display}",
    )


def _coerce_reflectivity_percent(value: float) -> float:
    if value <= 1.0:
        return value * 100.0
    return value
