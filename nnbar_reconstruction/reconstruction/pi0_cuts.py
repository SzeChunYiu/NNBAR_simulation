"""Canonical neutral-pion cuts from the thesis object-definition chapter.

Chapter 8 contains both local one-variable optima and the final globally
optimized criteria.  The candidate selection constants below use the final
optimized criteria summarized in the Ch.8 efficiency table and summary, while
also recording the local optima so the 60%/55% lead-glass distinction is not
lost.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

# Thesis Ch.8 diphoton invariant-mass acceptance window.
PI0_MASS_WINDOW_MEV = (100.0, 180.0)

# Thesis Ch.8 local single-variable optimum and final optimized cut.
PI0_LOCAL_LEADGLASS_FRACTION_OPTIMUM = 0.60
PI0_MIN_LEADGLASS_FRACTION = 0.55

# Thesis Ch.8 local single-variable optimum and final optimized cut.
PI0_LOCAL_OPENING_ANGLE_OPTIMUM_DEG = 25.0
PI0_MIN_OPENING_ANGLE_DEG = 30.0

# Thesis Ch.8 globally optimized criteria.
PI0_MAX_TOTAL_ENERGY_MEV = 720.0
PI0_MAX_SCINTILLATOR_ENERGY_MEV = 250.0
PI0_MAX_LEADGLASS_ENERGY_MEV = 980.0


@dataclass(frozen=True)
class Pi0CutResult:
    """Result of applying the canonical π⁰ candidate cuts."""

    passed: bool
    failed_cuts: tuple[str, ...]
    invariant_mass_mev: float
    total_energy_mev: float
    scintillator_energy_mev: float
    leadglass_energy_mev: float
    leadglass_fraction: float
    opening_angle_deg: float


def diphoton_invariant_mass_mev(
    photon1_energy_mev: float,
    photon2_energy_mev: float,
    opening_angle_deg: float,
) -> float:
    """Compute ``sqrt(2 E1 E2 (1 - cos(theta)))`` for two photons."""

    angle_rad = math.radians(opening_angle_deg)
    mass_squared = 2.0 * photon1_energy_mev * photon2_energy_mev * (1.0 - math.cos(angle_rad))
    return math.sqrt(max(mass_squared, 0.0))


def evaluate_pi0_candidate(
    *,
    photon1_energy_mev: float,
    photon2_energy_mev: float,
    opening_angle_deg: float,
    scintillator_energy_mev: float,
    leadglass_energy_mev: float,
) -> Pi0CutResult:
    """Apply the thesis Ch.8 optimized π⁰ candidate cuts.

    The thesis table uses inclusive notation for the mass window and strict
    inequalities for the optimized energy/fraction/angle cuts.
    """

    invariant_mass = diphoton_invariant_mass_mev(
        photon1_energy_mev,
        photon2_energy_mev,
        opening_angle_deg,
    )
    total_energy = photon1_energy_mev + photon2_energy_mev
    leadglass_fraction = leadglass_energy_mev / total_energy if total_energy > 0.0 else 0.0

    mass_min, mass_max = PI0_MASS_WINDOW_MEV
    checks = (
        ("mass_window", mass_min <= invariant_mass <= mass_max),
        ("scintillator_energy", scintillator_energy_mev < PI0_MAX_SCINTILLATOR_ENERGY_MEV),
        ("leadglass_energy", leadglass_energy_mev < PI0_MAX_LEADGLASS_ENERGY_MEV),
        ("total_energy", total_energy < PI0_MAX_TOTAL_ENERGY_MEV),
        ("leadglass_fraction", leadglass_fraction > PI0_MIN_LEADGLASS_FRACTION),
        ("opening_angle", opening_angle_deg > PI0_MIN_OPENING_ANGLE_DEG),
    )
    failed_cuts = tuple(name for name, passed in checks if not passed)

    return Pi0CutResult(
        passed=not failed_cuts,
        failed_cuts=failed_cuts,
        invariant_mass_mev=invariant_mass,
        total_energy_mev=total_energy,
        scintillator_energy_mev=scintillator_energy_mev,
        leadglass_energy_mev=leadglass_energy_mev,
        leadglass_fraction=leadglass_fraction,
        opening_angle_deg=opening_angle_deg,
    )
