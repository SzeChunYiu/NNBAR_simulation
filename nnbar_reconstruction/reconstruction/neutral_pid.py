"""Neutral-pion particle identification helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .pi0_cuts import (
    PI0_MAX_TOTAL_ENERGY_MEV,
    PI0_MIN_LEADGLASS_FRACTION,
    PI0_MIN_OPENING_ANGLE_DEG,
    evaluate_pi0_candidate,
)


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

    # Apply the canonical thesis Ch.8 cuts from pi0_cuts.py. Keeping the cut
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

    # Compute confidence based on how well criteria are satisfied.
    confidence_scores = []

    # Mass score (Gaussian around pi0 mass).
    pi0_mass = 134.977  # MeV
    mass_score = np.exp(-0.5 * ((inv_mass - pi0_mass) / 20) ** 2)
    confidence_scores.append(mass_score)

    # Energy score (prefer moderate energies).
    energy_score = (
        1.0
        if total_energy < PI0_MAX_TOTAL_ENERGY_MEV
        else np.exp(-(total_energy - PI0_MAX_TOTAL_ENERGY_MEV) / 100)
    )
    confidence_scores.append(energy_score)

    # LG fraction score.
    frac_score = (
        min(1.0, lg_fraction / PI0_MIN_LEADGLASS_FRACTION)
        if lg_fraction > PI0_MIN_LEADGLASS_FRACTION
        else lg_fraction / PI0_MIN_LEADGLASS_FRACTION
    )
    confidence_scores.append(frac_score)

    # Opening angle score.
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
