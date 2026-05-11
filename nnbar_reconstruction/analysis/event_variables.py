"""
Event Variables for NNBAR analysis.

Implements Chapter 9 from thesis:
- Invariant mass (Eq. 9.1)
- Sphericity (Eq. 9.2-9.4)
- Longitudinal energy (Eq. 9.5)
- Transverse energy (Eq. 9.7)
- Additional variables for event selection
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, TYPE_CHECKING
from dataclasses import dataclass

from ..utils.coordinates import (
    compute_sphericity,
    compute_total_invariant_mass,
    normalize_vector,
)

if TYPE_CHECKING:
    from ..reconstruction.charged_reconstruction import ChargedObject
    from ..reconstruction.neutral_reconstruction import NeutralObject


@dataclass
class EventVariables:
    """Collection of event-level variables."""
    # Invariant mass (target: 1.88 GeV = 2 * nucleon mass)
    invariant_mass: float           # Total invariant mass (MeV)

    # Event shape
    sphericity: float               # Sphericity [0, 1]

    # Energy variables
    total_energy: float             # Total reconstructed energy (MeV)
    scint_energy: float             # Total scintillator energy (MeV)
    lg_energy: float                # Total lead glass energy (MeV)
    longitudinal_energy: float      # Energy along beam axis (MeV)
    transverse_energy: float        # Energy perpendicular to beam (MeV)

    # Asymmetries
    top_bottom_asymmetry: float     # (E_top - E_bottom) / (E_top + E_bottom)
    forward_backward_asymmetry: float  # (E_forward - E_backward) / E_total

    # Multiplicities
    n_charged: int                  # Number of charged objects
    n_neutral: int                  # Number of neutral objects
    n_pions: int                    # Number of identified pions (charged + neutral)
    n_protons: int                  # Number of identified protons

    # Vertex quality
    vertex_r: float                 # Radial distance of vertex from z-axis
    n_tracks_to_vertex: int         # Tracks used in vertex reconstruction

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'invariant_mass': self.invariant_mass,
            'sphericity': self.sphericity,
            'total_energy': self.total_energy,
            'scint_energy': self.scint_energy,
            'lg_energy': self.lg_energy,
            'longitudinal_energy': self.longitudinal_energy,
            'transverse_energy': self.transverse_energy,
            'top_bottom_asymmetry': self.top_bottom_asymmetry,
            'forward_backward_asymmetry': self.forward_backward_asymmetry,
            'n_charged': self.n_charged,
            'n_neutral': self.n_neutral,
            'n_pions': self.n_pions,
            'n_protons': self.n_protons,
            'vertex_r': self.vertex_r,
            'n_tracks_to_vertex': self.n_tracks_to_vertex,
        }


def compute_invariant_mass(
    charged_objects: List[ChargedObject],
    neutral_objects: List[NeutralObject],
    vertex: np.ndarray,
) -> float:
    """
    Compute total invariant mass of the event.

    Implements Eq. 9.1 from thesis:
    W = sqrt((sum E_i)^2 - (sum p_i)^2)

    For this to peak at 1.88 GeV (2 * nucleon mass), we need good
    energy and momentum reconstruction.

    Args:
        charged_objects: List of reconstructed charged particles.
        neutral_objects: List of reconstructed neutral particles.
        vertex: Reconstructed vertex position.

    Returns:
        Invariant mass in MeV.
    """
    energies = []
    momenta = []

    # Charged objects
    for obj in charged_objects:
        energies.append(obj.energy)
        # p = E * direction (assuming relativistic, E >> m)
        # For better accuracy, use momentum magnitude estimate
        p_mag = obj.momentum_magnitude if obj.momentum_magnitude > 0 else obj.energy
        momenta.append(obj.momentum * p_mag)

    # Neutral objects (photons: E = |p|)
    for obj in neutral_objects:
        energies.append(obj.energy)
        momenta.append(obj.direction * obj.energy)

    if len(energies) == 0:
        return 0.0

    energies = np.array(energies)
    momenta = np.array(momenta)

    return compute_total_invariant_mass(energies, momenta)


def compute_event_sphericity(
    charged_objects: List[ChargedObject],
    neutral_objects: List[NeutralObject],
) -> float:
    """
    Compute event sphericity.

    Implements Eq. 9.2-9.4 from thesis:
    S = 3/2 * (lambda_2 + lambda_3)

    where lambda_i are normalized eigenvalues of momentum tensor.
    S = 0 for pencil-like events, S = 1 for isotropic events.

    Signal events should have high sphericity (isotropic decay).

    Args:
        charged_objects: List of charged particles.
        neutral_objects: List of neutral particles.

    Returns:
        Sphericity in [0, 1].
    """
    momenta = []

    for obj in charged_objects:
        p_mag = obj.momentum_magnitude if obj.momentum_magnitude > 0 else obj.energy
        momenta.append(obj.momentum * p_mag)

    for obj in neutral_objects:
        momenta.append(obj.direction * obj.energy)

    if len(momenta) < 2:
        return 0.0

    return compute_sphericity(np.array(momenta))


def compute_longitudinal_energy(
    charged_objects: List[ChargedObject],
    neutral_objects: List[NeutralObject],
    vertex: np.ndarray,
    beam_axis: np.ndarray = np.array([0, 0, 1]),
) -> float:
    """
    Compute longitudinal energy (along beam axis).

    Implements Eq. 9.5 from thesis:
    E_L = sum(E_i * cos(alpha_i))

    where alpha_i is angle between particle direction and beam axis.

    Args:
        charged_objects: List of charged particles.
        neutral_objects: List of neutral particles.
        vertex: Vertex position.
        beam_axis: Beam direction (default: z-axis).

    Returns:
        Longitudinal energy in MeV.
    """
    beam_axis = normalize_vector(beam_axis)
    e_long = 0.0

    for obj in charged_objects:
        direction = normalize_vector(obj.momentum)
        cos_alpha = np.clip(np.dot(direction, beam_axis), -1.0, 1.0)
        e_long += obj.energy * cos_alpha

    for obj in neutral_objects:
        direction = normalize_vector(obj.direction)
        cos_alpha = np.clip(np.dot(direction, beam_axis), -1.0, 1.0)
        e_long += obj.energy * cos_alpha

    return float(e_long)


def compute_transverse_energy(
    charged_objects: List[ChargedObject],
    neutral_objects: List[NeutralObject],
    vertex: np.ndarray,
    beam_axis: np.ndarray = np.array([0, 0, 1]),
) -> float:
    """
    Compute transverse energy (perpendicular to beam axis).

    Implements Eq. 9.7 from thesis:
    E_T = sum(E_i * sin(alpha_i))

    Args:
        charged_objects: List of charged particles.
        neutral_objects: List of neutral particles.
        vertex: Vertex position.
        beam_axis: Beam direction.

    Returns:
        Transverse energy in MeV.
    """
    beam_axis = normalize_vector(beam_axis)
    e_trans = 0.0

    for obj in charged_objects:
        direction = normalize_vector(obj.momentum)
        cos_alpha = np.clip(np.dot(direction, beam_axis), -1.0, 1.0)
        sin_alpha = np.sqrt(max(0.0, 1.0 - cos_alpha**2))
        e_trans += obj.energy * sin_alpha

    for obj in neutral_objects:
        direction = normalize_vector(obj.direction)
        cos_alpha = np.clip(np.dot(direction, beam_axis), -1.0, 1.0)
        sin_alpha = np.sqrt(max(0.0, 1.0 - cos_alpha**2))
        e_trans += obj.energy * sin_alpha

    return float(e_trans)


def compute_top_bottom_asymmetry(
    charged_objects: List[ChargedObject],
    neutral_objects: List[NeutralObject],
) -> float:
    """
    Compute top-bottom energy asymmetry.

    A = (E_top - E_bottom) / (E_top + E_bottom)

    where top = y > 0, bottom = y < 0.

    Signal events should have small asymmetry (isotropic).
    Cosmic rays tend to come from above (large asymmetry).

    Args:
        charged_objects: List of charged particles.
        neutral_objects: List of neutral particles.

    Returns:
        Asymmetry in [-1, 1].
    """
    e_top = 0.0
    e_bottom = 0.0

    for obj in charged_objects:
        if obj.track.center[1] > 0:
            e_top += obj.energy
        else:
            e_bottom += obj.energy

    for obj in neutral_objects:
        if obj.position[1] > 0:
            e_top += obj.energy
        else:
            e_bottom += obj.energy

    total = e_top + e_bottom
    if total < 1e-10:
        return 0.0

    return (e_top - e_bottom) / total


def compute_forward_backward_asymmetry(
    charged_objects: List[ChargedObject],
    neutral_objects: List[NeutralObject],
) -> float:
    """
    Compute forward-backward energy asymmetry.

    A = (E_forward - E_backward) / (E_forward + E_backward)

    where forward = z > 0, backward = z < 0.

    Args:
        charged_objects: List of charged particles.
        neutral_objects: List of neutral particles.

    Returns:
        Asymmetry in [-1, 1].
    """
    e_forward = 0.0
    e_backward = 0.0

    for obj in charged_objects:
        if obj.track.center[2] > 0:
            e_forward += obj.energy
        else:
            e_backward += obj.energy

    for obj in neutral_objects:
        if obj.position[2] > 0:
            e_forward += obj.energy
        else:
            e_backward += obj.energy

    total = e_forward + e_backward
    if total < 1e-10:
        return 0.0

    return (e_forward - e_backward) / total


def count_particles(
    charged_objects: List[ChargedObject],
    neutral_objects: List[NeutralObject],
) -> Dict[str, int]:
    """
    Count particles by type.

    Args:
        charged_objects: List of charged particles.
        neutral_objects: List of neutral particles.

    Returns:
        Dictionary with counts.
    """
    counts = {
        'charged': len(charged_objects),
        'neutral': len(neutral_objects),
        'pions': 0,
        'protons': 0,
        'photons': 0,
        'pi0': 0,
    }

    for obj in charged_objects:
        if obj.particle_type in ['PION_PLUS', 'PION_MINUS']:
            counts['pions'] += 1
        elif obj.particle_type == 'PROTON':
            counts['protons'] += 1

    for obj in neutral_objects:
        if obj.is_pi0_candidate:
            counts['pi0'] += 1
        else:
            counts['photons'] += 1

    # Count pi0 as pions
    counts['pions'] += counts['pi0']

    return counts


def compute_event_variables(
    charged_objects: List[ChargedObject],
    neutral_objects: List[NeutralObject],
    vertex: np.ndarray,
    n_tracks_to_vertex: int = 0,
) -> EventVariables:
    """
    Compute all event-level variables.

    Args:
        charged_objects: List of reconstructed charged particles.
        neutral_objects: List of reconstructed neutral particles.
        vertex: Reconstructed vertex position.
        n_tracks_to_vertex: Number of tracks used in vertex reconstruction.

    Returns:
        EventVariables dataclass.
    """
    # Invariant mass
    inv_mass = compute_invariant_mass(charged_objects, neutral_objects, vertex)

    # Sphericity
    sphericity = compute_event_sphericity(charged_objects, neutral_objects)

    # Energy sums
    total_energy = sum(obj.energy for obj in charged_objects) + \
                   sum(obj.energy for obj in neutral_objects)

    scint_energy = sum(obj.scint_energy for obj in charged_objects) + \
                   sum(obj.scint_energy for obj in neutral_objects)

    lg_energy = sum(obj.lg_energy for obj in charged_objects) + \
                sum(obj.lg_energy for obj in neutral_objects)

    # Longitudinal and transverse energy
    e_long = compute_longitudinal_energy(charged_objects, neutral_objects, vertex)
    e_trans = compute_transverse_energy(charged_objects, neutral_objects, vertex)

    # Asymmetries
    tb_asym = compute_top_bottom_asymmetry(charged_objects, neutral_objects)
    fb_asym = compute_forward_backward_asymmetry(charged_objects, neutral_objects)

    # Particle counts
    counts = count_particles(charged_objects, neutral_objects)

    # Vertex quality
    vertex_r = np.sqrt(vertex[0]**2 + vertex[1]**2)

    return EventVariables(
        invariant_mass=inv_mass,
        sphericity=sphericity,
        total_energy=total_energy,
        scint_energy=scint_energy,
        lg_energy=lg_energy,
        longitudinal_energy=e_long,
        transverse_energy=e_trans,
        top_bottom_asymmetry=tb_asym,
        forward_backward_asymmetry=fb_asym,
        n_charged=counts['charged'],
        n_neutral=counts['neutral'],
        n_pions=counts['pions'],
        n_protons=counts['protons'],
        vertex_r=vertex_r,
        n_tracks_to_vertex=n_tracks_to_vertex,
    )


if __name__ == "__main__":
    # Test event variables
    from ..reconstruction.charged_reconstruction import ChargedObject
    from ..reconstruction.neutral_reconstruction import NeutralObject
    from ..tracking.track_fitting import Track

    # Create mock event
    vertex = np.array([0, 0, 0])

    # Mock tracks
    tracks = []
    for i in range(3):
        theta = np.random.uniform(0.5, 1.5)
        phi = np.random.uniform(0, 2 * np.pi)
        direction = np.array([np.sin(theta) * np.cos(phi),
                              np.sin(theta) * np.sin(phi),
                              np.cos(theta)])

        track = Track(
            track_id=i,
            center=vertex + direction * 150,
            direction=direction,
            head=vertex + direction * 120,
            tail=vertex + direction * 180,
            length=60.0,
            n_hits=20,
            rms_residual=0.3,
            linearity=0.97,
            hit_indices=np.arange(20),
            is_signal=True,
        )
        tracks.append(track)

    # Create charged objects
    charged = []
    for i, track in enumerate(tracks):
        obj = ChargedObject(
            object_id=i,
            track=track,
            energy=300.0,
            momentum=track.direction,
            momentum_magnitude=280.0,
            dedx_truncated=1.8,
            dedx_layers=np.array([]),
            scint_energy=50.0,
            lg_energy=200.0,
            scint_range=3,
            tpc_entry=track.head,
            tpc_exit=track.tail,
            particle_type='PION_PLUS',
            pid_confidence=0.85,
        )
        charged.append(obj)

    # Create neutral objects
    neutral = []
    for i in range(2):
        direction = np.random.randn(3)
        direction = direction / np.linalg.norm(direction)

        obj = NeutralObject(
            object_id=i,
            energy=150.0,
            direction=direction,
            position=vertex + direction * 300,
            scint_energy=30.0,
            lg_energy=120.0,
            n_scint_hits=5,
            n_lg_hits=10,
            shower_width=5.0,
            lg_fraction=0.8,
        )
        neutral.append(obj)

    # Compute event variables
    ev = compute_event_variables(charged, neutral, vertex, n_tracks_to_vertex=3)

    print("Event Variables:")
    print(f"  Invariant mass: {ev.invariant_mass:.1f} MeV ({ev.invariant_mass/1000:.3f} GeV)")
    print(f"  Sphericity: {ev.sphericity:.3f}")
    print(f"  Total energy: {ev.total_energy:.1f} MeV")
    print(f"  N charged: {ev.n_charged}, N neutral: {ev.n_neutral}")
    print(f"  N pions: {ev.n_pions}")
