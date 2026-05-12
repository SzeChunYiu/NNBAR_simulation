"""Particle-counting helpers for event-variable rows."""

from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..reconstruction.charged_reconstruction import ChargedObject
    from ..reconstruction.neutral_reconstruction import NeutralObject


def count_particles(
    charged_objects: List["ChargedObject"],
    neutral_objects: List["NeutralObject"],
) -> Dict[str, int]:
    """Count charged and neutral reconstructed particles by analysis type.

    Args:
        charged_objects: List of charged particles.
        neutral_objects: List of neutral particles.

    Returns:
        Dictionary with charged, neutral, pion, proton, photon, and pi0 counts.
    """
    counts = {
        "charged": len(charged_objects),
        "neutral": len(neutral_objects),
        "pions": 0,
        "protons": 0,
        "photons": 0,
        "pi0": 0,
    }

    for obj in charged_objects:
        if obj.particle_type in ["PION_PLUS", "PION_MINUS"]:
            counts["pions"] += 1
        elif obj.particle_type == "PROTON":
            counts["protons"] += 1

    for obj in neutral_objects:
        if obj.is_pi0_candidate:
            counts["pi0"] += 1
        else:
            counts["photons"] += 1

    # Count pi0 as pions for the Ch. 9 pion multiplicity observable.
    counts["pions"] += counts["pi0"]

    return counts
