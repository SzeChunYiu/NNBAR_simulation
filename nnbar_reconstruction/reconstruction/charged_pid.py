"""Charged pion/proton PID threshold surface from thesis Chapter 8.

The active TPC dE/dx convention is electrons per centimeter (e-/cm), matching
the Chapter 7 definition ``N_e / Δx``.  The table below is a reproducible
digitization of the dotted ``t(n)`` line in extracted thesis Figure
``plots/Detector_Simulation/Charged_object_definition.jpg``:

* data axes detected from the image spines: x=[0.5, 10.5],
  y=[0, 250] e-/cm;
* neutral dark dotted-line components were interpolated to integer
  scintillator ranges n=1..10;
* values are rounded to the plotted precision (≈0.1 e-/cm).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Mapping


CHARGED_PID_TN_SOURCE = (
    "Digitized from thesis Ch.8 Fig. charged_OD extracted plot "
    "plots/Detector_Simulation/Charged_object_definition.jpg"
)

CHARGED_PID_TN_UNITS = "e-/cm"

CHARGED_PID_TN_THRESHOLDS_E_PER_CM: Mapping[int, float] = MappingProxyType(
    {
        1: 159.9,
        2: 120.1,
        3: 106.3,
        4: 87.2,
        5: 77.3,
        6: 72.4,
        7: 68.3,
        8: 61.7,
        9: 65.1,
        10: 63.2,
    }
)


class ChargedPIDRangeError(ValueError):
    """Raised when a scintillator range label is outside the thesis 1..10 bins."""


@dataclass(frozen=True)
class ChargedPIDDecision:
    """Classification from the Chapter 8 charged-PID threshold rule."""

    particle_label: str
    confidence: float
    threshold_e_per_cm: float
    scint_range: int
    dedx_e_per_cm: float


def normalize_scintillator_range(scint_range: int) -> int:
    """Return a validated thesis scintillator range label in ``1..10``."""
    if isinstance(scint_range, bool) or not isinstance(scint_range, int):
        raise ChargedPIDRangeError(
            f"scintillator range must be an integer label 1..10, got {scint_range!r}"
        )
    if scint_range not in CHARGED_PID_TN_THRESHOLDS_E_PER_CM:
        raise ChargedPIDRangeError(
            f"scintillator range must be in 1..10, got {scint_range!r}"
        )
    return scint_range


def threshold_for_scintillator_range(scint_range: int) -> float:
    """Return the thesis Ch.8 ``t(n)`` threshold in e-/cm."""
    return CHARGED_PID_TN_THRESHOLDS_E_PER_CM[
        normalize_scintillator_range(scint_range)
    ]


def classify_pion_proton_e_per_cm(
    dedx_e_per_cm: float,
    scint_range: int,
) -> ChargedPIDDecision:
    """Classify a charged track using ``proton if dE/dx >= t(n)``."""
    threshold = threshold_for_scintillator_range(scint_range)
    dedx = float(dedx_e_per_cm)
    if not isfinite(dedx) or dedx < 0:
        raise ValueError(f"dE/dx must be a finite non-negative e-/cm value, got {dedx!r}")

    particle_label = "proton" if dedx >= threshold else "pion"
    confidence = min(1.0, 0.5 + abs(dedx - threshold) / max(threshold, 1e-12))
    return ChargedPIDDecision(
        particle_label=particle_label,
        confidence=confidence,
        threshold_e_per_cm=threshold,
        scint_range=normalize_scintillator_range(scint_range),
        dedx_e_per_cm=dedx,
    )
