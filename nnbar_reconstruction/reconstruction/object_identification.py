"""
Particle Identification for NNBAR reconstruction.

Implements identification of:
- Charged pions vs protons using TPC dE/dx and scintillator range
- Electron pairs from gamma conversion
- Neutral pions from diphoton invariant mass

Key physics concepts:
- Bethe-Bloch: dE/dx depends on particle velocity (βγ)
- At same momentum, heavier particles have lower β and higher dE/dx
- Hadronic range: pions penetrate further than protons at same kinetic energy
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Union
from dataclasses import dataclass
from enum import Enum

from ..utils.config import get_particle_id_params
from .charged_pid import (
    CHARGED_PID_TN_UNITS,
    ChargedPIDRangeError,
    classify_pion_proton_e_per_cm,
)
from .pi0_cuts import (
    PI0_MAX_TOTAL_ENERGY_MEV,
    PI0_MIN_LEADGLASS_FRACTION,
    PI0_MIN_OPENING_ANGLE_DEG,
    evaluate_pi0_candidate,
)


class ParticleType(Enum):
    """Particle type enumeration."""
    UNKNOWN = 0
    PION_PLUS = 1
    PION_MINUS = 2
    PROTON = 3
    ELECTRON = 4
    POSITRON = 5
    PHOTON = 6
    NEUTRAL_PION = 7


@dataclass
class ParticleID:
    """Result of particle identification."""
    particle_type: ParticleType
    confidence: float              # Confidence in identification [0, 1]
    dedx: float                    # Measured dE/dx in e-/cm (legacy MeV/cm fallback)
    scint_range: int               # Number of scintillator layers penetrated
    is_charged: bool
    mass_hypothesis: float         # Assumed mass in MeV
    momentum_estimate: float       # Estimated momentum in MeV/c
    beta_gamma: float              # Estimated βγ


# Bethe-Bloch parameters for argon gas
# These are approximate values - should be calibrated with simulation
BETHE_BLOCH_PARAMS = {
    'K': 0.307,          # MeV cm^2 / mol
    'Z': 18,             # Atomic number (argon)
    'A': 39.948,         # Atomic mass
    'I': 188e-6,         # Mean excitation energy in MeV
    'density': 1.662e-3, # g/cm^3 at STP
    'rho_correction': 0.2,
}

LEGACY_DEDX_UNITS_MEV_PER_CM = "MeV/cm"


def _is_legacy_mev_per_cm(dedx_units: str) -> bool:
    """Return whether ``dedx_units`` denotes the legacy eDep/path observable."""
    normalized = dedx_units.replace(" ", "").lower()
    if normalized in {"mev/cm", "mevpercm", "mevcm^-1", "mevcm-1"}:
        return True
    if normalized in {"e-/cm", "electrons/cm", "electronspercm", "e/cm"}:
        return False
    raise ValueError(
        "dedx_units must be 'e-/cm' for the thesis electron-count path "
        "or 'MeV/cm' for the legacy eDep/path fallback"
    )


def bethe_bloch_dedx(
    beta_gamma: float,
    mass: float,
    params: Dict = BETHE_BLOCH_PARAMS,
) -> float:
    """
    Calculate expected dE/dx using Bethe-Bloch formula.

    dE/dx = K * (Z/A) * (1/β²) * [ln(2 m_e c² β² γ² / I) - β²]

    Args:
        beta_gamma: βγ of the particle.
        mass: Particle mass in MeV.
        params: Bethe-Bloch parameters.

    Returns:
        Expected dE/dx in MeV/cm.
    """
    if beta_gamma <= 0:
        return 0.0

    # Calculate β and γ
    gamma = np.sqrt(1 + beta_gamma**2)
    beta = beta_gamma / gamma

    if beta <= 0:
        return 0.0

    K = params['K']
    Z = params['Z']
    A = params['A']
    I = params['I']
    rho = params['density']

    m_e = 0.511  # Electron mass in MeV

    # Bethe-Bloch formula (simplified, without density correction)
    term1 = K * (Z / A) * rho / (beta**2)
    term2 = np.log(2 * m_e * beta_gamma**2 / I) - beta**2

    dedx = term1 * term2

    return max(dedx, 0.1)  # Minimum realistic dE/dx


def momentum_from_dedx(
    dedx: float,
    mass: float,
    tolerance: float = 0.1,
) -> float:
    """
    Invert Bethe-Bloch to estimate momentum from dE/dx.

    Uses numerical search since Bethe-Bloch is not analytically invertible.

    Args:
        dedx: Measured dE/dx in MeV/cm.
        mass: Assumed particle mass in MeV.
        tolerance: Relative tolerance for search.

    Returns:
        Estimated momentum in MeV/c.
    """
    if dedx <= 0:
        return 0.0

    # Search over βγ range
    bg_range = np.logspace(-1, 2, 1000)  # 0.1 to 100

    dedx_values = np.array([bethe_bloch_dedx(bg, mass) for bg in bg_range])

    # Find closest match
    idx = np.argmin(np.abs(dedx_values - dedx))
    best_bg = bg_range[idx]

    # Convert βγ to momentum: p = m * β * γ = m * βγ
    momentum = mass * best_bg

    return momentum


def momentum_from_dedx_if_legacy_mev_per_cm(
    dedx: float,
    mass: float,
    dedx_units: str = CHARGED_PID_TN_UNITS,
) -> float:
    """Estimate momentum only when dE/dx is the legacy MeV/cm observable."""
    if not _is_legacy_mev_per_cm(dedx_units):
        return 0.0
    return momentum_from_dedx(dedx, mass)


def identify_pion_proton(
    dedx: float,
    scint_range: int,
    total_energy: float = 0.0,
) -> Tuple[ParticleType, float]:
    """
    Identify charged pion vs proton using dE/dx and scintillator range.

    Key physics:
    - At same momentum, protons have higher dE/dx (slower, heavier)
    - At same kinetic energy, pions penetrate further (lighter)

    The electron-count path implements thesis Ch.8:
    proton if ``TPC dE/dx >= t(n)``, charged pion otherwise.  The threshold
    surface is the digitized Ch.8 ``t(n)`` curve in e-/cm.  Legacy MeV/cm YAML
    coefficients are intentionally not used for this electron-count path.

    Args:
        dedx: Measured truncated mean dE/dx in e-/cm for electron-count
            samples.  Legacy eDep-only samples are a documented fallback in the
            dE/dx calculator, not the calibrated Ch.8 PID path.
        scint_range: Thesis scintillator range label in 1..10.
        total_energy: Total deposited energy (optional).

    Returns:
        Tuple of (particle_type, confidence).
    """
    try:
        decision = classify_pion_proton_e_per_cm(dedx, scint_range)
    except (ChargedPIDRangeError, ValueError):
        return ParticleType.UNKNOWN, 0.0

    particle_type = (
        ParticleType.PROTON
        if decision.particle_label == "proton"
        else ParticleType.PION_PLUS
    )
    return particle_type, float(np.clip(decision.confidence, 0.0, 1.0))


def identify_electron_pair(
    track1_entry: np.ndarray,
    track2_entry: np.ndarray,
    max_distance: Optional[float] = None,
) -> Tuple[bool, float]:
    """
    Identify electron-positron pair from gamma conversion.

    e+e- pairs have TPC entry points very close together
    (from photon converting in detector material).

    Args:
        track1_entry: TPC entry point of first track.
        track2_entry: TPC entry point of second track.
        max_distance: Maximum separation in cm.

    Returns:
        Tuple of (is_epair, distance).
    """
    if max_distance is None:
        params = get_particle_id_params()
        max_distance = params.get('epair_distance', 5.0)

    distance = np.linalg.norm(track1_entry - track2_entry)

    is_epair = distance < max_distance

    return is_epair, distance


@dataclass
class NeutralPionCandidate:
    """Candidate for neutral pion from two photons."""
    photon1_energy: float
    photon2_energy: float
    opening_angle: float
    invariant_mass: float
    total_energy: float
    scint_energy: float
    lg_energy: float
    lg_fraction: float
    is_pi0: bool
    confidence: float


def identify_neutral_pion(
    photon1_energy: float,
    photon2_energy: float,
    opening_angle: float,
    scint_energy1: float = 0.0,
    scint_energy2: float = 0.0,
    lg_energy1: float = 0.0,
    lg_energy2: float = 0.0,
) -> NeutralPionCandidate:
    """
    Identify neutral pion from two photon candidates.

    Implements Eq. 7.11 from thesis:
    m_0 = sqrt(2 * E1 * E2 * (1 - cos(theta)))

    Criteria from thesis:
    - Invariant mass: 100-180 MeV (around pi0 mass 135 MeV)
    - Total energy: < 720 MeV
    - Scintillator energy: < 250 MeV
    - Lead glass energy: < 980 MeV
    - Lead glass fraction: > 55%
    - Opening angle: > 30 degrees

    Args:
        photon1_energy, photon2_energy: Photon energies in MeV.
        opening_angle: Opening angle in radians.
        scint_energy1, scint_energy2: Scintillator contributions.
        lg_energy1, lg_energy2: Lead glass contributions.

    Returns:
        NeutralPionCandidate with identification result.
    """
    opening_angle_deg = np.degrees(opening_angle)
    scint_energy = scint_energy1 + scint_energy2
    lg_energy = lg_energy1 + lg_energy2

    # Apply the canonical thesis Ch.8 cuts from pi0_cuts.py.  Keeping the cut
    # values in one module prevents stale YAML/default parameters from silently
    # changing the pi0 selection used by reconstruction.
    cut_result = evaluate_pi0_candidate(
        photon1_energy_mev=photon1_energy,
        photon2_energy_mev=photon2_energy,
        opening_angle_deg=float(opening_angle_deg),
        scintillator_energy_mev=scint_energy,
        leadglass_energy_mev=lg_energy,
    )
    inv_mass = cut_result.invariant_mass_mev
    total_energy = cut_result.total_energy_mev
    lg_fraction = cut_result.leadglass_fraction
    is_pi0 = cut_result.passed

    # Compute confidence based on how well criteria are satisfied
    confidence_scores = []

    # Mass score (Gaussian around pi0 mass)
    pi0_mass = 134.977  # MeV
    mass_score = np.exp(-0.5 * ((inv_mass - pi0_mass) / 20)**2)
    confidence_scores.append(mass_score)

    # Energy score (prefer moderate energies)
    energy_score = (
        1.0
        if total_energy < PI0_MAX_TOTAL_ENERGY_MEV
        else np.exp(-(total_energy - PI0_MAX_TOTAL_ENERGY_MEV) / 100)
    )
    confidence_scores.append(energy_score)

    # LG fraction score
    frac_score = (
        min(1.0, lg_fraction / PI0_MIN_LEADGLASS_FRACTION)
        if lg_fraction > PI0_MIN_LEADGLASS_FRACTION
        else lg_fraction / PI0_MIN_LEADGLASS_FRACTION
    )
    confidence_scores.append(frac_score)

    # Opening angle score
    angle_score = (
        1.0
        if opening_angle_deg > PI0_MIN_OPENING_ANGLE_DEG
        else opening_angle_deg / PI0_MIN_OPENING_ANGLE_DEG
    )
    confidence_scores.append(angle_score)

    confidence = np.mean(confidence_scores) if is_pi0 else 0.0

    return NeutralPionCandidate(
        photon1_energy=photon1_energy,
        photon2_energy=photon2_energy,
        opening_angle=opening_angle,
        invariant_mass=inv_mass,
        total_energy=total_energy,
        scint_energy=scint_energy,
        lg_energy=lg_energy,
        lg_fraction=lg_fraction,
        is_pi0=is_pi0,
        confidence=confidence,
    )


def identify_particle_type(
    dedx: float,
    scint_range: int,
    total_energy: float,
    is_charged: bool,
    track_length: float = 0.0,
    dedx_units: str = CHARGED_PID_TN_UNITS,
) -> ParticleID:
    """
    Full particle identification for a reconstructed object.

    Args:
        dedx: Truncated mean TPC dE/dx.  The default/current thesis path is
            e-/cm from ionization electrons.  Pass ``dedx_units="MeV/cm"``
            only for old eDep/path samples that explicitly need the legacy
            Bethe-Bloch momentum fallback.
        scint_range: Number of scintillator layers penetrated.
        total_energy: Total deposited energy in MeV.
        is_charged: Whether object left TPC track.
        track_length: TPC track length in cm.
        dedx_units: ``"e-/cm"`` for the thesis electron-count path or
            ``"MeV/cm"`` for the legacy eDep/path fallback.

    Returns:
        ParticleID result.
    """
    if not is_charged:
        # Neutral particle - assume photon
        return ParticleID(
            particle_type=ParticleType.PHOTON,
            confidence=0.8,
            dedx=0.0,
            scint_range=0,
            is_charged=False,
            mass_hypothesis=0.0,
            momentum_estimate=total_energy,  # E = p for photons
            beta_gamma=np.inf,
        )

    # Charged particle - use dE/dx and range
    particle_type, confidence = identify_pion_proton(dedx, scint_range, total_energy)

    # Get mass hypothesis
    if particle_type == ParticleType.PROTON:
        mass = 938.27
    else:
        mass = 139.57

    # Estimate momentum only for the legacy MeV/cm fallback.  The active
    # electron-count dE/dx path is intentionally not inverted as MeV/cm.
    momentum = momentum_from_dedx_if_legacy_mev_per_cm(dedx, mass, dedx_units)

    # Calculate βγ
    if mass > 0:
        energy = np.sqrt(momentum**2 + mass**2)
        gamma = energy / mass
        beta = momentum / energy
        beta_gamma = beta * gamma
    else:
        beta_gamma = 0.0

    return ParticleID(
        particle_type=particle_type,
        confidence=confidence,
        dedx=dedx,
        scint_range=scint_range,
        is_charged=True,
        mass_hypothesis=mass,
        momentum_estimate=momentum,
        beta_gamma=beta_gamma,
    )


# Lookup tables for dE/dx vs momentum (can be generated from Bethe-Bloch)
def generate_dedx_lookup_table(
    particle_mass: float,
    momentum_range: Tuple[float, float] = (50, 2000),
    n_points: int = 100,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate lookup table of dE/dx vs momentum.

    Args:
        particle_mass: Particle mass in MeV.
        momentum_range: (min, max) momentum in MeV/c.
        n_points: Number of points in table.

    Returns:
        Tuple of (momentum array, dE/dx array).
    """
    momenta = np.logspace(np.log10(momentum_range[0]), np.log10(momentum_range[1]), n_points)
    dedx_values = []

    for p in momenta:
        # Calculate βγ from momentum
        energy = np.sqrt(p**2 + particle_mass**2)
        gamma = energy / particle_mass
        beta = p / energy
        beta_gamma = beta * gamma

        dedx = bethe_bloch_dedx(beta_gamma, particle_mass)
        dedx_values.append(dedx)

    return momenta, np.array(dedx_values)


if __name__ == "__main__":
    # Test particle identification

    # Generate Bethe-Bloch curves
    import matplotlib.pyplot as plt

    momenta_pion, dedx_pion = generate_dedx_lookup_table(139.57)
    momenta_proton, dedx_proton = generate_dedx_lookup_table(938.27)

    print("Pion dE/dx at 300 MeV/c:", np.interp(300, momenta_pion, dedx_pion))
    print("Proton dE/dx at 300 MeV/c:", np.interp(300, momenta_proton, dedx_proton))

    # Test pion/proton identification
    # Low dE/dx, high range -> pion
    ptype, conf = identify_pion_proton(dedx=1.8, scint_range=4)
    print(f"dedx=1.8, range=4 -> {ptype.name}, confidence={conf:.2f}")

    # High dE/dx, low range -> proton
    ptype, conf = identify_pion_proton(dedx=4.0, scint_range=1)
    print(f"dedx=4.0, range=1 -> {ptype.name}, confidence={conf:.2f}")

    # Test pi0 identification
    candidate = identify_neutral_pion(
        photon1_energy=80.0,
        photon2_energy=60.0,
        opening_angle=np.radians(60),
        lg_energy1=60.0,
        lg_energy2=45.0,
    )
    print(f"Pi0 candidate: mass={candidate.invariant_mass:.1f} MeV, is_pi0={candidate.is_pi0}")
