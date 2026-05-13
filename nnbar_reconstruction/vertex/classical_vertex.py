"""
Classical vertex reconstruction based on thesis Chapter 7.2.

Implements:
- Track projection to target plane (Eq. 7.1-7.3)
- Weighted vertex averaging (Eq. 7.4)
- Angular uncertainty estimation
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Sequence
from dataclasses import dataclass

from ..tracking.track_fitting import Track
from ..utils.config import get_config
from ..utils.coordinates import project_to_plane, compute_distance


@dataclass
class VertexResult:
    """Result of vertex reconstruction."""
    position: np.ndarray         # (x, y, z) vertex position
    uncertainty: np.ndarray      # (sigma_x, sigma_y, sigma_z) uncertainties
    n_tracks: int                # Number of tracks used
    chi2: float                  # Goodness of fit
    track_weights: np.ndarray    # Weights assigned to each track
    track_projections: np.ndarray  # Individual track projections
    is_valid: bool               # Whether reconstruction succeeded

    @property
    def r(self) -> float:
        """Radial distance from z-axis."""
        return np.sqrt(self.position[0]**2 + self.position[1]**2)

    @property
    def phi(self) -> float:
        """Azimuthal angle."""
        return np.arctan2(self.position[1], self.position[0])


def project_track_to_target(
    track: Track,
    target_z: float = 0.0,
) -> Optional[np.ndarray]:
    """
    Project a track back to the target plane.

    Uses the pre-computed vertex_projection from linear regression fit
    if available (more accurate for curved tracks), otherwise falls back
    to geometric projection from track head.

    Args:
        track: Track object with fitted parameters.
        target_z: Z-coordinate of target plane.

    Returns:
        Projected point (x, y, z) or None if projection fails.
    """
    # Use pre-computed vertex projection if available (linear regression based)
    if hasattr(track, 'vertex_projection') and track.vertex_projection is not None:
        proj = track.vertex_projection
        # Check if it was computed for the same target_z
        if abs(proj[2] - target_z) < 0.1:
            return proj.copy()

    # Fall back to geometric projection from track head
    point = track.head
    direction = -track.direction

    return project_to_plane(point, direction, target_z)


def estimate_angular_uncertainty(
    track: Track,
    method: str = 'empirical',
) -> float:
    """
    Estimate uncertainty in track angle for vertex weighting.

    Args:
        track: Track object.
        method: 'empirical' for data-driven, 'analytic' for formula-based.

    Returns:
        Angular uncertainty sigma_theta in radians.
    """
    if method == 'empirical':
        # Empirical formula based on track quality
        # Better tracks (lower RMS, longer) have smaller uncertainty

        # Base uncertainty
        sigma_base = 0.05  # radians (~3 degrees)

        # Scale by track quality
        length_factor = np.exp(-track.length / 50)  # Longer = better
        rms_factor = track.rms_residual / 0.5       # Lower RMS = better
        hits_factor = np.exp(-track.n_hits / 20)    # More hits = better

        sigma = sigma_base * (1 + length_factor + rms_factor + hits_factor)

        return np.clip(sigma, 0.01, 0.5)

    else:
        # Analytic formula based on multiple scattering
        # Highland formula: theta_0 = (13.6 MeV / p) * sqrt(L/X0) * (1 + 0.038*ln(L/X0))

        # Approximate values
        p = 300.0  # MeV, typical pion momentum
        L_over_X0 = track.length / 1000  # Approximate radiation lengths in gas

        if L_over_X0 > 0:
            sigma = (13.6 / p) * np.sqrt(L_over_X0) * (1 + 0.038 * np.log(L_over_X0))
        else:
            sigma = 0.1

        return np.clip(sigma, 0.01, 0.5)


def theta_binned_projected_sigma_cm(
    track: Track,
    sigma_table_cm: Sequence[float],
    bin_width_deg: float = 20.0,
) -> float:
    """
    Look up thesis-style projected vertex uncertainty by track polar angle.

    Chapter 7 weights each projected vertex by sigma(theta)=mean d0(theta),
    with d0 means tabulated in 20-degree theta bins over 0--180 degrees.
    The table values are projected-position uncertainties in centimeters,
    not angular uncertainties in radians.

    Args:
        track: Track object.
        sigma_table_cm: Positive sigma values ordered by theta bin.
        bin_width_deg: Theta bin width in degrees. The thesis uses 20.

    Returns:
        Projected vertex uncertainty sigma(theta) in centimeters.
    """
    if bin_width_deg <= 0:
        raise ValueError("bin_width_deg must be positive")

    expected_bins = int(np.ceil(180.0 / bin_width_deg))
    if len(sigma_table_cm) != expected_bins:
        raise ValueError(
            f"sigma_table_cm must contain {expected_bins} values "
            f"for {bin_width_deg:g}-degree bins over 0--180 degrees"
        )

    table = np.asarray(sigma_table_cm, dtype=float)
    if np.any(~np.isfinite(table)) or np.any(table <= 0.0):
        raise ValueError("sigma_table_cm values must be positive finite numbers")

    direction = np.asarray(track.direction, dtype=float)
    norm = np.linalg.norm(direction)
    if norm == 0.0:
        raise ValueError("track.direction must be non-zero")

    cos_theta = np.clip(direction[2] / norm, -1.0, 1.0)
    theta_deg = np.degrees(np.arccos(cos_theta))
    bin_index = min(int((theta_deg + 1e-9) // bin_width_deg), expected_bins - 1)
    return float(table[bin_index])


def weighted_vertex_reconstruction(
    tracks: List[Track],
    target_z: float = 0.0,
    weight_by_angle: bool = True,
    weight_by_r_head: bool = True,
    max_r_head: float = 160.0,
    min_tracks: int = 1,
    theta_sigma_table_cm: Optional[Sequence[float]] = None,
) -> VertexResult:
    """
    Reconstruct vertex using weighted average of track projections.

    Implements Eq. 7.4 from thesis:
    (xc, yc) = sum(xv/sigma^2) / sum(1/sigma^2)

    Args:
        tracks: List of Track objects.
        target_z: Z-coordinate of target plane.
        weight_by_angle: Whether to weight by angular uncertainty.
        weight_by_r_head: Whether to weight by 1/r_head (prefer inner tracks).
        max_r_head: Maximum r_head to include track (exclude outer tracks).
        min_tracks: Minimum number of tracks required.
        theta_sigma_table_cm: Optional thesis-style projected-position
            uncertainties in cm, ordered in 20-degree theta bins over
            0--180 degrees. When omitted, the empirical angular fallback is
            unchanged.

    Returns:
        VertexResult with reconstructed vertex.
    """
    if len(tracks) < min_tracks:
        return VertexResult(
            position=np.array([0.0, 0.0, target_z]),
            uncertainty=np.array([np.inf, np.inf, 0.0]),
            n_tracks=0,
            chi2=np.inf,
            track_weights=np.array([]),
            track_projections=np.array([]),
            is_valid=False,
        )

    # Project all tracks to target plane
    projections = []
    weights = []
    valid_tracks = []
    projected_sigmas_cm = []

    for track in tracks:
        proj = project_track_to_target(track, target_z)

        if proj is None:
            continue

        # Check if projection is reasonable (not too far from beam axis)
        r_proj = np.sqrt(proj[0]**2 + proj[1]**2)
        if r_proj > 200:  # cm, reasonable limit
            continue

        # Prefer tracks with smaller r_head (closer to vertex)
        r_head = track.r_head
        if r_head > max_r_head:
            continue

        projections.append(proj)

        # Compute weight
        w = 1.0

        if weight_by_angle:
            if theta_sigma_table_cm is None:
                sigma = estimate_angular_uncertainty(track)
                projected_sigmas_cm.append(None)
            else:
                sigma = theta_binned_projected_sigma_cm(track, theta_sigma_table_cm)
                projected_sigmas_cm.append(sigma)
            # Weight by 1/sigma^2
            w *= 1.0 / (sigma**2 + 1e-10)
        else:
            projected_sigmas_cm.append(None)

        if weight_by_r_head:
            # Weight by 1/r_head^2 (tracks closer to beampipe are more reliable)
            w *= 1.0 / (r_head**2 + 1.0)

        weights.append(w)
        valid_tracks.append(track)

    if len(projections) < min_tracks:
        return VertexResult(
            position=np.array([0.0, 0.0, target_z]),
            uncertainty=np.array([np.inf, np.inf, 0.0]),
            n_tracks=0,
            chi2=np.inf,
            track_weights=np.array([]),
            track_projections=np.array([]),
            is_valid=False,
        )

    projections = np.array(projections)
    weights = np.array(weights)

    # Normalize weights
    weights = weights / weights.sum()

    # Weighted average (Eq. 7.4)
    vertex = np.sum(projections * weights[:, np.newaxis], axis=0)

    # Uncertainty estimate
    # Standard error of weighted mean
    if len(projections) > 1:
        residuals = projections - vertex
        weighted_var = np.sum(weights[:, np.newaxis] * residuals**2, axis=0)
        uncertainty = np.sqrt(weighted_var / (1 - np.sum(weights**2) + 1e-10))
    else:
        # Single track - use projected-position sigma when explicitly supplied.
        if projected_sigmas_cm[0] is None:
            sigma = estimate_angular_uncertainty(valid_tracks[0])
            uncertainty = np.array([sigma * 100, sigma * 100, 0.0])  # Scale to cm
        else:
            sigma = projected_sigmas_cm[0]
            uncertainty = np.array([sigma, sigma, 0.0])

    # Chi-squared: sum of weighted squared residuals
    residuals = projections - vertex
    chi2 = np.sum(weights * np.sum(residuals**2, axis=1))

    return VertexResult(
        position=vertex,
        uncertainty=uncertainty,
        n_tracks=len(projections),
        chi2=chi2,
        track_weights=weights,
        track_projections=projections,
        is_valid=True,
    )


def reconstruct_vertex(
    tracks: List[Track],
    target_z: Optional[float] = None,
    method: str = 'median',
    signal_only: bool = True,
) -> VertexResult:
    """
    Main vertex reconstruction function.

    Args:
        tracks: List of Track objects.
        target_z: Z-coordinate of target. If None, uses config.
        method: 'median' for robust median (default), 'weighted' for weighted average.
        signal_only: If True, only use tracks classified as signal.

    Returns:
        VertexResult with reconstructed vertex.
    """
    if target_z is None:
        target_z = get_config('target.z_position', 0.0)

    # Filter to signal tracks if requested
    if signal_only:
        tracks = [t for t in tracks if t.is_signal or t.p_signal > 0.5]

    if len(tracks) == 0:
        return VertexResult(
            position=np.array([0.0, 0.0, target_z]),
            uncertainty=np.array([np.inf, np.inf, 0.0]),
            n_tracks=0,
            chi2=np.inf,
            track_weights=np.array([]),
            track_projections=np.array([]),
            is_valid=False,
        )

    if method == 'weighted':
        return weighted_vertex_reconstruction(tracks, target_z)

    elif method == 'median':
        # Median-based reconstruction (more robust to outliers)
        projections = []
        for track in tracks:
            proj = project_track_to_target(track, target_z)
            if proj is not None:
                r_proj = np.sqrt(proj[0]**2 + proj[1]**2)
                if r_proj < 200:
                    projections.append(proj)

        if len(projections) == 0:
            return VertexResult(
                position=np.array([0.0, 0.0, target_z]),
                uncertainty=np.array([np.inf, np.inf, 0.0]),
                n_tracks=0,
                chi2=np.inf,
                track_weights=np.array([]),
                track_projections=np.array([]),
                is_valid=False,
            )

        projections = np.array(projections)
        vertex = np.median(projections, axis=0)

        # MAD-based uncertainty
        mad = np.median(np.abs(projections - vertex), axis=0)
        uncertainty = 1.4826 * mad  # Scale MAD to standard deviation

        # Chi-squared
        residuals = projections - vertex
        chi2 = np.sum(np.sum(residuals**2, axis=1))

        return VertexResult(
            position=vertex,
            uncertainty=uncertainty,
            n_tracks=len(projections),
            chi2=chi2,
            track_weights=np.ones(len(projections)) / len(projections),
            track_projections=projections,
            is_valid=True,
        )

    else:
        raise ValueError(f"Unknown method: {method}")


def iterative_vertex_reconstruction(
    tracks: List[Track],
    target_z: Optional[float] = None,
    max_iterations: int = 5,
    outlier_threshold: float = 3.0,
) -> VertexResult:
    """
    Iterative vertex reconstruction with outlier rejection.

    Repeatedly reconstructs vertex and removes tracks with large residuals.

    Args:
        tracks: List of Track objects.
        target_z: Z-coordinate of target.
        max_iterations: Maximum refinement iterations.
        outlier_threshold: Number of sigma for outlier rejection.

    Returns:
        VertexResult after outlier rejection.
    """
    if target_z is None:
        target_z = get_config('target.z_position', 0.0)

    remaining_tracks = list(tracks)

    for iteration in range(max_iterations):
        result = reconstruct_vertex(remaining_tracks, target_z, method='weighted', signal_only=False)

        if not result.is_valid or result.n_tracks < 2:
            break

        # Compute residuals
        residuals = result.track_projections - result.position
        r_residuals = np.sqrt(np.sum(residuals**2, axis=1))

        # Identify outliers
        mean_r = np.mean(r_residuals)
        std_r = np.std(r_residuals)
        outlier_mask = r_residuals > mean_r + outlier_threshold * std_r

        if not np.any(outlier_mask):
            break

        # Remove outliers
        keep_indices = ~outlier_mask
        remaining_tracks = [remaining_tracks[i] for i in range(len(remaining_tracks))
                           if keep_indices[i]]

        if len(remaining_tracks) < 1:
            break

    return reconstruct_vertex(remaining_tracks, target_z, method='weighted', signal_only=False)
