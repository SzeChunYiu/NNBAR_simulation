"""
Neutral Object Reconstruction.

Implements Section 7.5 from thesis:
- Cluster unassigned calorimeter hits
- Energy from sum of deposits
- Direction from energy-weighted centroid
"""

import numpy as np
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import pandas as pd

from ..utils.config import get_config, get_reconstruction_params
from ..utils.coordinates import (
    normalize_vector,
    compute_opening_angle,
    compute_invariant_mass_2gamma,
)


@dataclass
class NeutralObject:
    """Reconstructed neutral particle (photon or neutral pion)."""
    object_id: int

    # Kinematics
    energy: float                   # Total energy (MeV)
    direction: np.ndarray           # Direction from vertex (unit vector)
    position: np.ndarray            # Energy-weighted centroid

    # Detector contributions
    scint_energy: float             # Energy in scintillator (MeV)
    lg_energy: float                # Energy in lead glass (MeV)
    n_scint_hits: int               # Number of scintillator hits
    n_lg_hits: int                  # Number of lead glass hits

    # Shower properties
    shower_width: float             # RMS spread of hits
    lg_fraction: float              # Fraction of energy in lead glass

    # Classification
    is_photon: bool = True
    is_pi0_candidate: bool = False

    @property
    def total_energy(self) -> float:
        return self.energy

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'object_id': self.object_id,
            'energy': self.energy,
            'direction_x': self.direction[0],
            'direction_y': self.direction[1],
            'direction_z': self.direction[2],
            'position_x': self.position[0],
            'position_y': self.position[1],
            'position_z': self.position[2],
            'scint_energy': self.scint_energy,
            'lg_energy': self.lg_energy,
            'n_scint_hits': self.n_scint_hits,
            'n_lg_hits': self.n_lg_hits,
            'shower_width': self.shower_width,
            'lg_fraction': self.lg_fraction,
            'is_photon': self.is_photon,
            'is_pi0_candidate': self.is_pi0_candidate,
        }


def cluster_neutral_hits(
    vertex: np.ndarray,
    scint_hits: pd.DataFrame,
    lg_hits: pd.DataFrame,
    assigned_scint_mask: np.ndarray,
    assigned_lg_mask: np.ndarray,
    cone_angle: Optional[float] = None,
    seed_min_energy: float = 0.1,
    cluster_min_energy: float = 10.0,
) -> List[NeutralObject]:
    """
    Cluster unassigned calorimeter hits into neutral objects.

    Algorithm from thesis Section 7.5:
    1. Sort unassigned hits by energy (descending)
    2. Take leading hit as seed
    3. Cluster hits within angular cone from vertex
    4. Compute energy and direction
    5. Keep clusters above the total-energy threshold
    6. Repeat until no seeds above threshold

    Args:
        vertex: Reconstructed vertex position.
        scint_hits: Scintillator hits DataFrame.
        lg_hits: Lead glass hits DataFrame.
        assigned_scint_mask: Boolean mask of scintillator hits assigned to charged objects.
        assigned_lg_mask: Boolean mask of lead glass hits assigned to charged objects.
        cone_angle: Clustering cone half-angle in degrees.
        seed_min_energy: Minimum seed-hit energy in MeV.
        cluster_min_energy: Minimum total cluster energy in MeV.

    Returns:
        List of NeutralObject.
    """
    if cone_angle is None:
        params = get_reconstruction_params()
        cone_angle = params.get('cone_angle', 25.0)

    cone_angle_rad = np.radians(cone_angle)

    # Get unassigned hits
    scint_unassigned = scint_hits[~assigned_scint_mask].copy() if len(scint_hits) > 0 else pd.DataFrame()
    lg_unassigned = lg_hits[~assigned_lg_mask].copy() if len(lg_hits) > 0 else pd.DataFrame()

    # Combine into single DataFrame
    combined_hits = []

    if len(scint_unassigned) > 0 and 'x' in scint_unassigned.columns:
        scint_unassigned = scint_unassigned.copy()
        scint_unassigned['detector'] = 'scint'
        scint_unassigned['orig_idx'] = scint_unassigned.index
        combined_hits.append(scint_unassigned[['x', 'y', 'z', 'eDep', 'detector', 'orig_idx']])

    if len(lg_unassigned) > 0 and 'x' in lg_unassigned.columns:
        lg_unassigned = lg_unassigned.copy()
        lg_unassigned['detector'] = 'lg'
        lg_unassigned['orig_idx'] = lg_unassigned.index
        combined_hits.append(lg_unassigned[['x', 'y', 'z', 'eDep', 'detector', 'orig_idx']])

    if len(combined_hits) == 0:
        return []

    all_hits = pd.concat(combined_hits, ignore_index=True)

    if len(all_hits) == 0:
        return []

    # Track which hits are still available
    available = np.ones(len(all_hits), dtype=bool)

    neutral_objects = []
    object_id = 0

    while True:
        # Find highest energy available hit as seed
        available_energies = all_hits.loc[available, 'eDep'].values
        if len(available_energies) == 0:
            break

        max_energy = available_energies.max()
        if max_energy < seed_min_energy:
            break

        # Get seed hit
        seed_idx = all_hits.loc[available, 'eDep'].idxmax()
        seed_pos = all_hits.loc[seed_idx, ['x', 'y', 'z']].values.astype(float)
        seed_dir = normalize_vector(seed_pos - vertex)

        # Find hits within cone
        hit_positions = all_hits.loc[available, ['x', 'y', 'z']].values
        hit_directions = hit_positions - vertex
        hit_directions = hit_directions / (np.linalg.norm(hit_directions, axis=1, keepdims=True) + 1e-10)

        # Compute angles
        cos_angles = np.dot(hit_directions, seed_dir)
        in_cone = cos_angles > np.cos(cone_angle_rad)

        # Get indices of hits in cone
        available_indices = all_hits.index[available].values
        cluster_indices = available_indices[in_cone]

        if len(cluster_indices) == 0:
            available[seed_idx] = False
            continue

        # Extract cluster hits
        cluster_hits = all_hits.loc[cluster_indices]

        # Compute properties
        energies = cluster_hits['eDep'].values
        positions = cluster_hits[['x', 'y', 'z']].values

        total_energy = energies.sum()
        if total_energy < cluster_min_energy:
            for idx in cluster_indices:
                available[idx] = False
            continue

        # Energy-weighted centroid
        if total_energy > 0:
            centroid = np.sum(positions * energies[:, np.newaxis], axis=0) / total_energy
        else:
            centroid = positions.mean(axis=0)

        # Direction from vertex
        direction = normalize_vector(centroid - vertex)

        # Shower width (RMS of hit positions around centroid)
        if len(positions) > 1:
            shower_width = np.sqrt(np.mean(np.sum((positions - centroid)**2, axis=1)))
        else:
            shower_width = 0.0

        # Detector contributions
        scint_mask = cluster_hits['detector'] == 'scint'
        lg_mask = cluster_hits['detector'] == 'lg'

        scint_energy = cluster_hits.loc[scint_mask, 'eDep'].sum() if scint_mask.any() else 0.0
        lg_energy = cluster_hits.loc[lg_mask, 'eDep'].sum() if lg_mask.any() else 0.0
        n_scint = scint_mask.sum()
        n_lg = lg_mask.sum()

        lg_fraction = lg_energy / (total_energy + 1e-10)

        # Create neutral object
        neutral_obj = NeutralObject(
            object_id=object_id,
            energy=total_energy,
            direction=direction,
            position=centroid,
            scint_energy=scint_energy,
            lg_energy=lg_energy,
            n_scint_hits=n_scint,
            n_lg_hits=n_lg,
            shower_width=shower_width,
            lg_fraction=lg_fraction,
        )

        neutral_objects.append(neutral_obj)
        object_id += 1

        # Mark hits as used
        for idx in cluster_indices:
            available[idx] = False

    return neutral_objects


def reconstruct_neutral_objects(
    vertex: np.ndarray,
    scint_data: pd.DataFrame,
    lg_data: pd.DataFrame,
    charged_scint_mask: Optional[np.ndarray] = None,
    charged_lg_mask: Optional[np.ndarray] = None,
) -> List[NeutralObject]:
    """
    Main function to reconstruct neutral objects.

    Args:
        vertex: Reconstructed vertex position.
        scint_data: Scintillator hits DataFrame.
        lg_data: Lead glass hits DataFrame.
        charged_scint_mask: Hits assigned to charged objects.
        charged_lg_mask: Hits assigned to charged objects.

    Returns:
        List of NeutralObject.
    """
    # Default: no hits assigned to charged objects
    if charged_scint_mask is None:
        charged_scint_mask = np.zeros(len(scint_data), dtype=bool)
    if charged_lg_mask is None:
        charged_lg_mask = np.zeros(len(lg_data), dtype=bool)

    return cluster_neutral_hits(
        vertex, scint_data, lg_data,
        charged_scint_mask, charged_lg_mask
    )


def find_pi0_candidates(
    neutral_objects: List[NeutralObject],
    vertex: np.ndarray,
) -> List[Tuple[NeutralObject, NeutralObject, float]]:
    """
    Find neutral pion candidates from photon pairs.

    Checks diphoton invariant mass against pi0 mass window.

    Args:
        neutral_objects: List of neutral objects (assumed photons).
        vertex: Vertex position for opening angle calculation.

    Returns:
        List of (photon1, photon2, invariant_mass) tuples for pi0 candidates.
    """
    from .object_identification import identify_neutral_pion

    candidates = []

    n_objects = len(neutral_objects)

    for i in range(n_objects):
        for j in range(i + 1, n_objects):
            obj1 = neutral_objects[i]
            obj2 = neutral_objects[j]

            # Compute opening angle
            opening_angle = compute_opening_angle(vertex, obj1.position, obj2.position)

            # Check pi0 criteria
            pi0_result = identify_neutral_pion(
                obj1.energy,
                obj2.energy,
                opening_angle,
                obj1.scint_energy,
                obj2.scint_energy,
                obj1.lg_energy,
                obj2.lg_energy,
            )

            if pi0_result.is_pi0:
                candidates.append((obj1, obj2, pi0_result.invariant_mass))
                obj1.is_pi0_candidate = True
                obj2.is_pi0_candidate = True

    return candidates


if __name__ == "__main__":
    # Test neutral reconstruction
    np.random.seed(42)

    # Create mock calorimeter hits
    n_hits = 20

    # Cluster 1: photon-like at phi=0
    pos1 = np.array([280, 20, 50])
    cluster1_x = pos1[0] + np.random.normal(0, 5, 10)
    cluster1_y = pos1[1] + np.random.normal(0, 5, 10)
    cluster1_z = pos1[2] + np.random.normal(0, 10, 10)
    cluster1_e = np.random.exponential(20, 10)

    # Cluster 2: photon-like at phi=180
    pos2 = np.array([-280, -10, 30])
    cluster2_x = pos2[0] + np.random.normal(0, 5, 10)
    cluster2_y = pos2[1] + np.random.normal(0, 5, 10)
    cluster2_z = pos2[2] + np.random.normal(0, 10, 10)
    cluster2_e = np.random.exponential(20, 10)

    # Combine
    lg_df = pd.DataFrame({
        'x': np.concatenate([cluster1_x, cluster2_x]),
        'y': np.concatenate([cluster1_y, cluster2_y]),
        'z': np.concatenate([cluster1_z, cluster2_z]),
        'eDep': np.concatenate([cluster1_e, cluster2_e]),
    })

    scint_df = pd.DataFrame({'x': [], 'y': [], 'z': [], 'eDep': []})

    vertex = np.array([0, 0, 0])

    objects = reconstruct_neutral_objects(vertex, scint_df, lg_df)

    print(f"Found {len(objects)} neutral objects:")
    for obj in objects:
        print(f"  Object {obj.object_id}: E={obj.energy:.1f} MeV, "
              f"pos=({obj.position[0]:.0f}, {obj.position[1]:.0f}, {obj.position[2]:.0f})")

    # Check for pi0 candidates
    candidates = find_pi0_candidates(objects, vertex)
    print(f"\nFound {len(candidates)} pi0 candidates")
