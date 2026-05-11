"""
Charged Object Reconstruction.

Implements Section 7.4 from thesis:
- TPC dE/dx calculation using truncated mean
- Cone-based energy collection from calorimeters
- Momentum direction from vertex
- Scintillator range measurement
"""

import numpy as np
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import pandas as pd

from ..tracking.track_fitting import Track, compute_track_dedx
from ..utils.config import get_config, get_reconstruction_params
from .electron_pair import apply_electron_pair_labels
from ..utils.coordinates import (
    points_in_cone,
    compute_momentum_direction,
    normalize_vector,
)


@dataclass
class ChargedObject:
    """Reconstructed charged particle."""
    object_id: int
    track: Track                    # Associated TPC track

    # Kinematics
    energy: float                   # Total reconstructed energy (MeV)
    momentum: np.ndarray            # 3-momentum direction (unit vector)
    momentum_magnitude: float       # |p| estimate (MeV/c)

    # dE/dx
    dedx_truncated: float           # Truncated TPC dE/dx (e-/cm; legacy MeV/cm fallback)
    dedx_layers: np.ndarray         # Per-layer TPC dE/dx values in same units

    # Calorimeter
    scint_energy: float             # Energy in scintillator (MeV)
    lg_energy: float                # Energy in lead glass (MeV)
    scint_range: int                # Number of scintillator layers penetrated

    # Track properties
    tpc_entry: np.ndarray           # TPC entry point
    tpc_exit: np.ndarray            # TPC exit point

    # Particle ID (filled later)
    particle_type: Optional[str] = None
    pid_confidence: float = 0.0

    @property
    def total_energy(self) -> float:
        """Total energy from all detectors."""
        return self.energy

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'object_id': self.object_id,
            'track_id': self.track.track_id,
            'energy': self.energy,
            'momentum_x': self.momentum[0],
            'momentum_y': self.momentum[1],
            'momentum_z': self.momentum[2],
            'momentum_mag': self.momentum_magnitude,
            'dedx_truncated': self.dedx_truncated,
            'scint_energy': self.scint_energy,
            'lg_energy': self.lg_energy,
            'scint_range': self.scint_range,
            'particle_type': self.particle_type,
            'pid_confidence': self.pid_confidence,
        }


def calculate_truncated_dedx(
    track: Track,
    tpc_data: pd.DataFrame,
    truncation: Optional[float] = None,
) -> Tuple[float, np.ndarray]:
    """
    Calculate truncated mean dE/dx for a track.

    Implements the Chapter 7 thesis convention: use ionization electrons
    divided by layer path length, then the lower-60% truncated mean. The
    returned unit is e-/cm when the TPC table has an ``electrons`` column;
    samples without that column use the documented legacy eDep/path fallback
    in MeV/cm.

    Args:
        track: Track object.
        tpc_data: TPC hits DataFrame.
        truncation: Fraction of lowest values to keep.

    Returns:
        Tuple of (truncated mean, array of layer dE/dx).
    """
    if truncation is None:
        params = get_reconstruction_params()
        truncation = params.get('dedx_truncation', 0.6)

    return compute_track_dedx(track, tpc_data, truncation)


def collect_cone_energy(
    vertex: np.ndarray,
    direction: np.ndarray,
    scint_data: pd.DataFrame,
    lg_data: pd.DataFrame,
    cone_angle: Optional[float] = None,
) -> Tuple[float, float, np.ndarray, np.ndarray]:
    """
    Collect calorimeter energy within a cone from vertex.

    Args:
        vertex: Vertex position (x, y, z).
        direction: Track direction (unit vector).
        scint_data: Scintillator hits DataFrame.
        lg_data: Lead glass hits DataFrame.
        cone_angle: Half-opening angle in degrees.

    Returns:
        Tuple of (scint_energy, lg_energy, scint_mask, lg_mask).
    """
    if cone_angle is None:
        params = get_reconstruction_params()
        cone_angle = params.get('cone_angle', 25.0)

    scint_energy = 0.0
    lg_energy = 0.0
    scint_mask = np.zeros(len(scint_data), dtype=bool)
    lg_mask = np.zeros(len(lg_data), dtype=bool)

    # Scintillator
    if len(scint_data) > 0 and 'x' in scint_data.columns:
        scint_points = scint_data[['x', 'y', 'z']].values
        scint_mask = points_in_cone(vertex, direction, cone_angle, scint_points)

        if 'eDep' in scint_data.columns:
            scint_energy = scint_data.loc[scint_mask, 'eDep'].sum()

    # Lead glass
    if len(lg_data) > 0 and 'x' in lg_data.columns:
        lg_points = lg_data[['x', 'y', 'z']].values
        lg_mask = points_in_cone(vertex, direction, cone_angle, lg_points)

        if 'eDep' in lg_data.columns:
            lg_energy = lg_data.loc[lg_mask, 'eDep'].sum()

    return scint_energy, lg_energy, scint_mask, lg_mask


def count_scintillator_layers(
    track: Track,
    scint_data: pd.DataFrame,
    cone_angle: float = 25.0,
) -> int:
    """
    Count number of scintillator layers penetrated by track.

    Args:
        track: Track object.
        scint_data: Scintillator hits with 'Layer_ID' column.
        cone_angle: Cone angle for hit association.

    Returns:
        Number of unique valid layers with hits, capped by configuration.
    """
    if len(scint_data) == 0 or 'Layer_ID' not in scint_data.columns:
        return 0

    # Get hits in cone
    if 'x' not in scint_data.columns:
        return 0

    scint_points = scint_data[['x', 'y', 'z']].values
    mask = points_in_cone(track.head, track.direction, cone_angle, scint_points)

    # Count valid unique layers. GEANT4 replica ids are normally 0-based,
    # while the thesis text labels layers 1--10; accept either convention but
    # ignore negative/non-integral/out-of-range ids instead of inflating range.
    if mask.sum() > 0:
        n_layers = _configured_scintillator_layers()
        layer_ids = _valid_scintillator_layer_ids(
            scint_data.loc[mask, 'Layer_ID'],
            n_layers,
        )
        return int(layer_ids.nunique())

    return 0


def _configured_scintillator_layers() -> int:
    """Return the configured scintillator layer count."""
    n_layers = get_config('scintillator.n_layers', 10)
    try:
        n_layers = int(n_layers)
    except (TypeError, ValueError):
        return 0
    return max(0, n_layers)


def _valid_scintillator_layer_ids(layer_ids: pd.Series, n_layers: int) -> pd.Series:
    """Normalize valid scintillator layer ids to zero-based labels."""
    if n_layers <= 0:
        return pd.Series(dtype='int64')

    numeric = pd.to_numeric(layer_ids, errors='coerce').dropna()
    integral = numeric[np.isclose(numeric, np.rint(numeric))].astype(int)

    if (integral == 0).any():
        valid = integral[(integral >= 0) & (integral < n_layers)]
        return valid

    valid = integral[(integral >= 1) & (integral <= n_layers)]
    return valid - 1


def reconstruct_charged_object(
    track: Track,
    vertex: np.ndarray,
    tpc_data: pd.DataFrame,
    scint_data: pd.DataFrame,
    lg_data: pd.DataFrame,
    object_id: int,
) -> ChargedObject:
    """
    Reconstruct a single charged particle from track.

    Args:
        track: TPC track.
        vertex: Reconstructed vertex position.
        tpc_data: TPC hits DataFrame.
        scint_data: Scintillator hits DataFrame.
        lg_data: Lead glass hits DataFrame.
        object_id: ID to assign to this object.

    Returns:
        ChargedObject with reconstructed properties.
    """
    # Momentum direction from vertex (Eq. 7.7)
    momentum_dir = compute_momentum_direction(vertex, track.head)

    # Truncated mean dE/dx (Eq. 7.5)
    dedx, dedx_layers = calculate_truncated_dedx(track, tpc_data)

    # Cone-based energy collection
    scint_energy, lg_energy, _, _ = collect_cone_energy(
        vertex, momentum_dir, scint_data, lg_data
    )

    # Scintillator range
    scint_range = count_scintillator_layers(track, scint_data)

    # Total energy
    # For now, use calorimeter energy + TPC energy deposit
    total_energy = scint_energy + lg_energy + track.total_energy_dep

    # Momentum magnitude estimate from dE/dx is only dimensionally valid for
    # the legacy MeV/cm eDep/path fallback.  Current electron-count dE/dx is
    # e-/cm and must not be fed to the Bethe-Bloch MeV/cm inversion.
    from .charged_pid import CHARGED_PID_TN_UNITS
    from .object_identification import (
        LEGACY_DEDX_UNITS_MEV_PER_CM,
        momentum_from_dedx_if_legacy_mev_per_cm,
    )

    dedx_units = (
        CHARGED_PID_TN_UNITS
        if "electrons" in tpc_data.columns
        else LEGACY_DEDX_UNITS_MEV_PER_CM
    )
    momentum_mag = momentum_from_dedx_if_legacy_mev_per_cm(
        dedx,
        139.57,  # pion mass hypothesis for the legacy fallback
        dedx_units,
    )

    return ChargedObject(
        object_id=object_id,
        track=track,
        energy=total_energy,
        momentum=momentum_dir,
        momentum_magnitude=momentum_mag,
        dedx_truncated=dedx,
        dedx_layers=dedx_layers,
        scint_energy=scint_energy,
        lg_energy=lg_energy,
        scint_range=scint_range,
        tpc_entry=track.head,
        tpc_exit=track.tail,
    )


def reconstruct_charged_objects(
    tracks: List[Track],
    vertex: np.ndarray,
    tpc_data: pd.DataFrame,
    scint_data: pd.DataFrame,
    lg_data: pd.DataFrame,
) -> List[ChargedObject]:
    """
    Reconstruct all charged particles from tracks.

    Args:
        tracks: List of TPC tracks.
        vertex: Reconstructed vertex position.
        tpc_data: TPC hits DataFrame.
        scint_data: Scintillator hits DataFrame.
        lg_data: Lead glass hits DataFrame.

    Returns:
        List of ChargedObject.
    """
    objects = []

    for i, track in enumerate(tracks):
        obj = reconstruct_charged_object(
            track, vertex, tpc_data, scint_data, lg_data, object_id=i
        )
        objects.append(obj)

    return objects


def identify_charged_particles(
    objects: List[ChargedObject],
) -> List[ChargedObject]:
    """
    Apply particle identification to charged objects.

    Args:
        objects: List of ChargedObject.

    Returns:
        Same list with particle_type and pid_confidence filled.
    """
    from .object_identification import identify_pion_proton, ParticleType

    for obj in objects:
        ptype, confidence = identify_pion_proton(
            obj.dedx_truncated,
            obj.scint_range,
            obj.energy,
        )

        obj.particle_type = ptype.name
        obj.pid_confidence = confidence

    # Ch.8/plan-24 C.6: conversion-like e+/e- topology is a charged-object
    # rejection category, so pair rows must not flow into pion/proton counts.
    apply_electron_pair_labels(objects)

    return objects


if __name__ == "__main__":
    # Test charged reconstruction
    from ..tracking.track_fitting import Track

    # Mock track
    track = Track(
        track_id=0,
        center=np.array([150.0, 0.0, 50.0]),
        direction=np.array([0.8, 0.0, 0.6]),
        head=np.array([130.0, 0.0, 35.0]),
        tail=np.array([180.0, 0.0, 72.5]),
        length=55.9,
        n_hits=20,
        rms_residual=0.3,
        linearity=0.98,
        hit_indices=np.arange(20),
        is_signal=True,
        total_energy_dep=15.0,
    )

    # Mock vertex
    vertex = np.array([0.0, 0.0, 0.0])

    # Empty DataFrames for testing
    tpc_df = pd.DataFrame({'x': [], 'y': [], 'z': [], 'electrons': [], 'eDep': []})
    scint_df = pd.DataFrame({'x': [], 'y': [], 'z': [], 'eDep': [], 'Layer_ID': []})
    lg_df = pd.DataFrame({'x': [], 'y': [], 'z': [], 'eDep': []})

    obj = reconstruct_charged_object(track, vertex, tpc_df, scint_df, lg_df, object_id=0)

    print("Charged Object Reconstruction:")
    print(f"  Energy: {obj.energy:.1f} MeV")
    print(f"  Momentum direction: {obj.momentum}")
    print(f"  dE/dx: {obj.dedx_truncated:.2f} e-/cm (legacy MeV/cm if no electrons)")
