"""
Signal vs Compton track separation.

Signal tracks: Originate from the target foil, radially outward
Compton tracks: Originate at TPC cathode from gamma interactions, scattered directions

Methods:
1. Geometric: Track extrapolation to target plane
2. ML-based: PointNet/GNN classifier on track point cloud
"""

import numpy as np
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass
from pathlib import Path

from .track_fitting import Track
from ..utils.config import get_config
from ..utils.coordinates import project_to_plane, compute_distance

# Optional: ML-based P-Signal model
_PSIGNAL_PREDICTOR = None


def classify_track_origin(
    track: Track,
    beampipe_radius: Optional[float] = None,
    target_z: Optional[float] = None,
    max_extrapolation_r: float = 50.0,
) -> Tuple[bool, float, float]:
    """
    Classify track as signal or Compton based on geometry.

    Signal tracks should extrapolate back to near the beampipe/target.
    Compton tracks originate at the TPC cathode (outer radius).

    Args:
        track: Track object with fitted parameters.
        beampipe_radius: Radius of beampipe in cm.
        target_z: Z position of target foil.
        max_extrapolation_r: Maximum r at target plane to classify as signal.

    Returns:
        Tuple of (is_signal, extrapolated_r, radial_alignment_score)
    """
    if beampipe_radius is None:
        beampipe_radius = get_config('beampipe.inner_radius', 112.0)
    if target_z is None:
        target_z = get_config('target.z_position', 0.0)

    # Project track backward to target z-plane
    # Use the inner endpoint (head) as starting point
    vertex = project_to_plane(track.head, -track.direction, target_z)

    if vertex is None:
        # Track is parallel to z=0 plane
        return False, np.inf, 0.0

    # Radial distance of extrapolated vertex
    extrapolated_r = np.sqrt(vertex[0]**2 + vertex[1]**2)

    # Radial alignment: how well does track direction point radially outward?
    # For signal tracks from target, direction should be radially outward
    radial_direction = np.array([track.center[0], track.center[1], 0])
    radial_direction = radial_direction / (np.linalg.norm(radial_direction) + 1e-10)

    # Take horizontal component of track direction
    track_dir_horiz = np.array([track.direction[0], track.direction[1], 0])
    track_dir_horiz = track_dir_horiz / (np.linalg.norm(track_dir_horiz) + 1e-10)

    radial_alignment = np.dot(radial_direction, track_dir_horiz)

    # Classification criteria
    # Signal: extrapolates to small r and is radially aligned
    is_signal = (extrapolated_r < max_extrapolation_r) and (radial_alignment > 0.5)

    return is_signal, extrapolated_r, radial_alignment


def separate_signal_compton(
    tracks: List[Track],
    beampipe_radius: Optional[float] = None,
    target_z: Optional[float] = None,
    max_extrapolation_r: float = 50.0,
    min_radial_alignment: float = 0.5,
) -> Tuple[List[Track], List[Track]]:
    """
    Separate tracks into signal and Compton categories.

    Args:
        tracks: List of Track objects.
        beampipe_radius: Radius of beampipe.
        target_z: Z position of target.
        max_extrapolation_r: Maximum r for signal classification.
        min_radial_alignment: Minimum radial alignment score.

    Returns:
        Tuple of (signal_tracks, compton_tracks)
    """
    signal_tracks = []
    compton_tracks = []

    for track in tracks:
        is_signal, extrap_r, alignment = classify_track_origin(
            track, beampipe_radius, target_z, max_extrapolation_r
        )

        track.is_signal = is_signal
        track.p_signal = 1.0 if is_signal else 0.0

        if is_signal:
            signal_tracks.append(track)
        else:
            compton_tracks.append(track)

    return signal_tracks, compton_tracks


def compute_signal_probability(
    track: Track,
    beampipe_radius: Optional[float] = None,
    target_z: Optional[float] = None,
) -> float:
    """
    Compute probability that a track is signal (soft classification).

    Uses geometric features to estimate signal probability:
    - Distance from extrapolated vertex to target center
    - Radial alignment score
    - Track length (longer = more likely signal)
    - Track quality (lower RMS = better)

    Args:
        track: Track object.
        beampipe_radius: Radius of beampipe.
        target_z: Z position of target.

    Returns:
        Probability in [0, 1].
    """
    is_signal, extrap_r, alignment = classify_track_origin(
        track, beampipe_radius, target_z
    )

    # Component scores (each in [0, 1])

    # 1. Extrapolation score: small r is good
    # Sigmoid-like function centered at r=50
    r_score = 1.0 / (1.0 + np.exp((extrap_r - 50) / 20))

    # 2. Radial alignment score
    # Already in [-1, 1], transform to [0, 1]
    alignment_score = (alignment + 1) / 2

    # 3. Track length score: longer is better, saturates at ~30 cm
    length_score = 1.0 - np.exp(-track.length / 30)

    # 4. Quality score: lower RMS is better
    quality_score = np.exp(-track.rms_residual / 0.5)

    # Combined score (weighted average)
    weights = [0.4, 0.3, 0.15, 0.15]  # r, alignment, length, quality
    scores = [r_score, alignment_score, length_score, quality_score]

    p_signal = sum(w * s for w, s in zip(weights, scores))

    return np.clip(p_signal, 0.0, 1.0)


def filter_tracks_by_signal_probability(
    tracks: List[Track],
    threshold: float = 0.5,
) -> List[Track]:
    """
    Filter tracks to keep only those likely to be signal.

    Args:
        tracks: List of tracks.
        threshold: Minimum signal probability.

    Returns:
        Filtered list of tracks.
    """
    signal_tracks = []

    for track in tracks:
        p_signal = compute_signal_probability(track)
        track.p_signal = p_signal

        if p_signal >= threshold:
            track.is_signal = True
            signal_tracks.append(track)
        else:
            track.is_signal = False

    return signal_tracks


def estimate_track_momentum(
    track: Track,
    dedx: float,
    particle_mass: float = 139.57,  # pion mass in MeV
) -> float:
    """
    Estimate track momentum from dE/dx using Bethe-Bloch.

    This is an approximate inversion of the Bethe-Bloch formula.

    Args:
        track: Track object.
        dedx: Measured dE/dx in MeV/cm.
        particle_mass: Assumed particle mass in MeV.

    Returns:
        Estimated momentum in MeV/c.
    """
    # Approximate Bethe-Bloch parameters for argon
    # dE/dx = K * (1/beta^2) * [ln(2*m_e*c^2*beta^2*gamma^2/I) - beta^2]
    # For a rough estimate, use empirical scaling

    if dedx <= 0:
        return 0.0

    # Minimum ionizing: ~1.5 MeV/cm in argon
    # Higher dE/dx = lower momentum

    # Empirical relation for pions in argon:
    # p ~ 200 / sqrt(dE/dx / 1.5) for dE/dx > 1.5 MeV/cm

    if dedx < 1.5:
        # Near minimum ionizing - high momentum
        return 500.0 * (1.5 / dedx)
    else:
        # Below minimum - lower momentum
        return 200.0 / np.sqrt(dedx / 1.5)


# ============================================================================
# ML-Based P-Signal Classification
# ============================================================================

def load_psignal_model(checkpoint_path: str, device: str = None) -> bool:
    """
    Load a trained P-Signal model for ML-based track classification.

    Args:
        checkpoint_path: Path to model checkpoint (.ckpt file)
        device: Device to run inference on ('cuda' or 'cpu')

    Returns:
        True if model loaded successfully, False otherwise
    """
    global _PSIGNAL_PREDICTOR

    try:
        from ..vertex.psignal_model import PSignalPredictor
        import torch

        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            device = torch.device(device)

        _PSIGNAL_PREDICTOR = PSignalPredictor.from_checkpoint(checkpoint_path, device)
        print(f"[P-Signal] Loaded model from {checkpoint_path}")
        print(f"[P-Signal] Model type: {_PSIGNAL_PREDICTOR.config.model_type}")
        return True

    except Exception as e:
        print(f"[P-Signal] Failed to load model: {e}")
        _PSIGNAL_PREDICTOR = None
        return False


def is_psignal_model_loaded() -> bool:
    """Check if a P-Signal model is loaded."""
    return _PSIGNAL_PREDICTOR is not None


def compute_signal_probability_ml(
    track: Track,
    tpc_hits: np.ndarray = None,
) -> float:
    """
    Compute signal probability using the ML model.

    Falls back to heuristic if no model is loaded.

    Args:
        track: Track object
        tpc_hits: (N, 3) hit coordinates (optional if track has hit_indices)

    Returns:
        Signal probability in [0, 1]
    """
    global _PSIGNAL_PREDICTOR

    # Get hit coordinates
    if tpc_hits is None and hasattr(track, 'hits'):
        tpc_hits = track.hits
    elif tpc_hits is None:
        # Fall back to heuristic
        return compute_signal_probability(track)

    # Use ML model if available
    if _PSIGNAL_PREDICTOR is not None:
        try:
            return _PSIGNAL_PREDICTOR.predict_single(tpc_hits)
        except Exception as e:
            print(f"[P-Signal] ML prediction failed: {e}")
            # Fall back to heuristic
            pass

    # Fall back to heuristic
    from ..vertex.psignal_model import heuristic_psignal
    return heuristic_psignal(tpc_hits)


def separate_signal_compton_ml(
    tracks: List[Track],
    tpc_data: np.ndarray = None,
    threshold: float = 0.5,
) -> Tuple[List[Track], List[Track]]:
    """
    Separate tracks using ML-based P-Signal classification.

    Args:
        tracks: List of Track objects
        tpc_data: (N, 3+) array with all TPC hits (for extracting track hits)
        threshold: Classification threshold (default 0.5)

    Returns:
        Tuple of (signal_tracks, compton_tracks)
    """
    global _PSIGNAL_PREDICTOR

    signal_tracks = []
    compton_tracks = []

    # Batch prediction if model available
    if _PSIGNAL_PREDICTOR is not None and tpc_data is not None:
        # Extract hit arrays for each track
        hits_list = []
        for track in tracks:
            if hasattr(track, 'hit_indices') and track.hit_indices is not None:
                track_hits = tpc_data[track.hit_indices, :3]
            elif hasattr(track, 'hits') and track.hits is not None:
                track_hits = track.hits[:, :3]
            else:
                # Use track geometry to reconstruct approximate hits
                track_hits = np.array([track.head, track.center, track.tail])

            hits_list.append(track_hits)

        # Batch prediction
        try:
            probs = _PSIGNAL_PREDICTOR.predict_batch(hits_list)

            for track, p_signal in zip(tracks, probs):
                track.p_signal = p_signal
                track.is_signal = p_signal >= threshold

                if track.is_signal:
                    signal_tracks.append(track)
                else:
                    compton_tracks.append(track)

            return signal_tracks, compton_tracks

        except Exception as e:
            print(f"[P-Signal] Batch prediction failed: {e}")
            # Fall through to single prediction

    # Single prediction (heuristic or ML)
    for track in tracks:
        if tpc_data is not None and hasattr(track, 'hit_indices') and track.hit_indices is not None:
            track_hits = tpc_data[track.hit_indices, :3]
        elif hasattr(track, 'hits') and track.hits is not None:
            track_hits = track.hits[:, :3]
        else:
            track_hits = None

        p_signal = compute_signal_probability_ml(track, track_hits)
        track.p_signal = p_signal
        track.is_signal = p_signal >= threshold

        if track.is_signal:
            signal_tracks.append(track)
        else:
            compton_tracks.append(track)

    return signal_tracks, compton_tracks


def compute_signal_probabilities_batch(
    tracks: List[Track],
    tpc_data: np.ndarray = None,
) -> List[float]:
    """
    Compute signal probabilities for a batch of tracks.

    Args:
        tracks: List of Track objects
        tpc_data: (N, 3+) array with all TPC hits

    Returns:
        List of signal probabilities
    """
    global _PSIGNAL_PREDICTOR

    # Extract hits for each track
    hits_list = []
    for track in tracks:
        if tpc_data is not None and hasattr(track, 'hit_indices') and track.hit_indices is not None:
            track_hits = tpc_data[track.hit_indices, :3]
        elif hasattr(track, 'hits') and track.hits is not None:
            track_hits = track.hits[:, :3]
        else:
            track_hits = np.array([track.head, track.center, track.tail])

        hits_list.append(track_hits)

    # Use ML model if available
    if _PSIGNAL_PREDICTOR is not None:
        try:
            return _PSIGNAL_PREDICTOR.predict_batch(hits_list)
        except Exception as e:
            print(f"[P-Signal] Batch prediction failed: {e}")

    # Fall back to heuristic
    from ..vertex.psignal_model import heuristic_psignal
    return [heuristic_psignal(hits) for hits in hits_list]


if __name__ == "__main__":
    # Test signal separation
    from .track_fitting import Track

    # Create mock signal track (radially outward from target)
    signal_track = Track(
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
    )

    # Create mock Compton track (tangential, originates at cathode)
    compton_track = Track(
        track_id=1,
        center=np.array([200.0, 50.0, 30.0]),
        direction=np.array([0.0, 0.9, 0.44]),
        head=np.array([200.0, 20.0, 15.0]),
        tail=np.array([200.0, 80.0, 45.0]),
        length=67.1,
        n_hits=25,
        rms_residual=0.5,
        linearity=0.95,
        hit_indices=np.arange(25),
    )

    # Test classification
    is_sig, r_ext, align = classify_track_origin(signal_track)
    print(f"Signal track: is_signal={is_sig}, extrap_r={r_ext:.1f}, alignment={align:.2f}")

    is_sig, r_ext, align = classify_track_origin(compton_track)
    print(f"Compton track: is_signal={is_sig}, extrap_r={r_ext:.1f}, alignment={align:.2f}")

    # Test probability
    p_sig = compute_signal_probability(signal_track)
    p_comp = compute_signal_probability(compton_track)
    print(f"Signal probability: signal_track={p_sig:.3f}, compton_track={p_comp:.3f}")
