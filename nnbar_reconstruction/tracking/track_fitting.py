"""
Track fitting using PCA and line fitting algorithms.

Extracts track parameters from clustered TPC hits:
- Center point
- Direction vector
- Head and tail endpoints
- Length
- Quality metrics (RMS residual, linearity)

GPU Acceleration:
- Uses CuPy for GPU-accelerated SVD and linear algebra
- Batched operations for fitting multiple tracks
- Transparent fallback to NumPy when GPU not available
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import pandas as pd

from ..utils.gpu_backend import get_backend
from ..utils.config import get_tracking_params, get_config
from ..utils.coordinates import (
    project_to_plane,
    compute_distance_to_line,
    normalize_vector,
)


@dataclass
class Track:
    """Reconstructed track from TPC hits."""
    track_id: int
    center: np.ndarray           # Center point [x, y, z]
    direction: np.ndarray        # Unit direction vector
    head: np.ndarray             # Endpoint closest to beampipe
    tail: np.ndarray             # Endpoint furthest from beampipe
    length: float                # Track length in cm
    n_hits: int                  # Number of hits
    rms_residual: float          # RMS perpendicular distance to line
    linearity: float             # Quality metric (0-1, 1=perfect line)
    hit_indices: np.ndarray      # Indices of hits in original DataFrame
    vertex_projection: Optional[np.ndarray] = None  # Projected vertex at z=0

    # Additional properties computed from hits
    total_electrons: float = 0.0
    total_energy_dep: float = 0.0
    mean_dedx: float = 0.0

    # Classification
    is_signal: Optional[bool] = None
    p_signal: float = 0.5        # Probability of being signal track

    @property
    def r_head(self) -> float:
        """Radial position of head (inner endpoint)."""
        return np.sqrt(self.head[0]**2 + self.head[1]**2)

    @property
    def r_tail(self) -> float:
        """Radial position of tail (outer endpoint)."""
        return np.sqrt(self.tail[0]**2 + self.tail[1]**2)

    @property
    def phi(self) -> float:
        """Azimuthal angle of track center."""
        return np.arctan2(self.center[1], self.center[0])

    @property
    def theta(self) -> float:
        """Polar angle of track direction (from z-axis)."""
        return np.arccos(abs(self.direction[2]))

    def project_to_z(self, z_target: float = 0.0) -> Optional[np.ndarray]:
        """Project track to a z-plane."""
        return project_to_plane(self.head, self.direction, z_target)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'track_id': self.track_id,
            'center_x': self.center[0],
            'center_y': self.center[1],
            'center_z': self.center[2],
            'dir_x': self.direction[0],
            'dir_y': self.direction[1],
            'dir_z': self.direction[2],
            'head_x': self.head[0],
            'head_y': self.head[1],
            'head_z': self.head[2],
            'tail_x': self.tail[0],
            'tail_y': self.tail[1],
            'tail_z': self.tail[2],
            'length': self.length,
            'n_hits': self.n_hits,
            'rms_residual': self.rms_residual,
            'linearity': self.linearity,
            'total_electrons': self.total_electrons,
            'total_energy_dep': self.total_energy_dep,
            'mean_dedx': self.mean_dedx,
            'is_signal': self.is_signal,
            'p_signal': self.p_signal,
        }


def pca_line_fit(points: np.ndarray, z_target: float = 0.0, use_gpu: bool = True) -> Dict[str, Any]:
    """
    Fit a line to points using PCA.

    GPU-accelerated SVD when CuPy is available.

    Args:
        points: (N, 3) array of [x, y, z] coordinates.
        z_target: Z-coordinate of target plane for vertex projection.
        use_gpu: Whether to use GPU acceleration if available.

    Returns:
        Dictionary with fit parameters:
        - center: Center of mass of points
        - direction: Principal direction (unit vector)
        - head: Endpoint with smaller r
        - tail: Endpoint with larger r
        - length: Distance between head and tail
        - rms: RMS perpendicular distance to fitted line
        - linearity: Ratio of first eigenvalue to total
        - vertex: Projected point at z=z_target
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 points for line fit")

    gpu = get_backend()

    # Use GPU if available and requested
    if use_gpu and gpu.use_gpu:
        points_gpu = gpu.to_gpu(points.astype(np.float32))

        # Center of mass
        center = gpu.mean(points_gpu, axis=0)

        # PCA via SVD on GPU
        centered = points_gpu - center
        _, s, Vt = gpu.svd(centered, full_matrices=False)

        # Principal direction
        direction = Vt[0]

        # Ensure direction points outward (increasing r)
        endpoint1 = center + direction * 50
        endpoint2 = center - direction * 50
        r1 = gpu.sqrt(endpoint1[0]**2 + endpoint1[1]**2)
        r2 = gpu.sqrt(endpoint2[0]**2 + endpoint2[1]**2)
        if float(gpu.to_numpy(r1)) < float(gpu.to_numpy(r2)):
            direction = -direction

        # Project points onto line to find endpoints
        projections = gpu.dot(centered, direction)
        t_min = float(gpu.to_numpy(gpu.min(projections)))
        t_max = float(gpu.to_numpy(gpu.max(projections)))

        head = center + direction * t_min
        tail = center + direction * t_max

        # Ensure head has smaller r
        r_head = float(gpu.to_numpy(gpu.sqrt(head[0]**2 + head[1]**2)))
        r_tail = float(gpu.to_numpy(gpu.sqrt(tail[0]**2 + tail[1]**2)))
        if r_head > r_tail:
            head, tail = tail, head

        # Track length
        length = float(gpu.to_numpy(gpu.norm(tail - head)))

        # RMS residual
        residuals = centered - gpu.outer(projections, direction)
        rms = float(gpu.to_numpy(gpu.sqrt(gpu.mean(gpu.sum(residuals**2, axis=1)))))

        # Linearity
        eigenvalues = s**2 / (len(points) - 1)
        linearity = float(gpu.to_numpy(eigenvalues[0] / (gpu.sum(eigenvalues) + 1e-10)))

        # Transfer results back to CPU
        center = gpu.to_numpy(center)
        direction = gpu.to_numpy(direction)
        head = gpu.to_numpy(head)
        tail = gpu.to_numpy(tail)
    else:
        # CPU path
        points = np.asarray(points)

        # Center of mass
        center = np.mean(points, axis=0)

        # PCA via SVD
        centered = points - center
        _, s, Vt = np.linalg.svd(centered, full_matrices=False)

        # Principal direction
        direction = Vt[0]

        # Ensure direction points outward (increasing r)
        endpoint1 = center + direction * 50
        endpoint2 = center - direction * 50
        r1 = np.sqrt(endpoint1[0]**2 + endpoint1[1]**2)
        r2 = np.sqrt(endpoint2[0]**2 + endpoint2[1]**2)
        if r1 < r2:
            direction = -direction

        # Project points onto line to find endpoints
        projections = np.dot(centered, direction)
        t_min, t_max = projections.min(), projections.max()

        head = center + direction * t_min
        tail = center + direction * t_max

        # Ensure head has smaller r
        r_head = np.sqrt(head[0]**2 + head[1]**2)
        r_tail = np.sqrt(tail[0]**2 + tail[1]**2)
        if r_head > r_tail:
            head, tail = tail, head

        # Track length
        length = np.linalg.norm(tail - head)

        # RMS residual (perpendicular distance to line)
        residuals = centered - np.outer(projections, direction)
        rms = np.sqrt(np.mean(np.sum(residuals**2, axis=1)))

        # Linearity (ratio of principal eigenvalue)
        eigenvalues = s**2 / (len(points) - 1)
        linearity = eigenvalues[0] / (eigenvalues.sum() + 1e-10)

    # Project to target z-plane for vertex using linear regression on INNER hits only
    # Using inner hits (closest to beampipe) reduces extrapolation distance and error
    if isinstance(points, np.ndarray):
        pts = points
    else:
        pts = np.asarray(points)

    # Compute radial distance for each hit
    r_vals = np.sqrt(pts[:, 0]**2 + pts[:, 1]**2)
    z_vals = pts[:, 2]
    x_vals = pts[:, 0]
    y_vals = pts[:, 1]

    # Use only the innermost portion of the track (lowest r values)
    # This reduces extrapolation distance to the vertex
    n_inner = max(5, len(pts) // 3)  # Use inner 1/3 of hits, minimum 5
    inner_indices = np.argsort(r_vals)[:n_inner]

    z_inner = z_vals[inner_indices]
    x_inner = x_vals[inner_indices]
    y_inner = y_vals[inner_indices]

    # Linear fit on inner hits: x = a*z + b, y = c*z + d
    # At z=z_target: x = a*z_target + b, y = c*z_target + d
    if np.std(z_inner) > 0.1 and len(inner_indices) >= 3:
        coef_x = np.polyfit(z_inner, x_inner, 1)
        coef_y = np.polyfit(z_inner, y_inner, 1)
        vertex_x = coef_x[0] * z_target + coef_x[1]
        vertex_y = coef_y[0] * z_target + coef_y[1]
        vertex = np.array([vertex_x, vertex_y, z_target])
    else:
        # Fall back to PCA projection for nearly horizontal tracks
        vertex = project_to_plane(head, -direction, z_target)

    return {
        'center': center,
        'direction': direction,
        'head': head,
        'tail': tail,
        'length': length,
        'rms': rms,
        'linearity': linearity,
        'vertex': vertex,
    }


def fit_track(
    hits: pd.DataFrame,
    track_id: int,
    hit_indices: np.ndarray,
    z_target: float = 0.0,
) -> Optional[Track]:
    """
    Create a Track object from clustered hits.

    Args:
        hits: DataFrame with hit data.
        track_id: ID to assign to this track.
        hit_indices: Indices of hits belonging to this track.
        z_target: Z-coordinate for vertex projection.

    Returns:
        Track object, or None if fitting fails.
    """
    if len(hit_indices) < 3:
        return None

    track_hits = hits.iloc[hit_indices]
    points = track_hits[['x', 'y', 'z']].values

    try:
        fit = pca_line_fit(points, z_target)
    except Exception:
        return None

    # Compute additional properties
    total_electrons = 0.0
    total_energy_dep = 0.0

    if 'electrons' in track_hits.columns:
        total_electrons = track_hits['electrons'].sum()
    if 'eDep' in track_hits.columns:
        total_energy_dep = track_hits['eDep'].sum()

    # Mean dE/dx (energy per unit length)
    mean_dedx = 0.0
    if fit['length'] > 0 and total_energy_dep > 0:
        mean_dedx = total_energy_dep / fit['length']

    return Track(
        track_id=track_id,
        center=fit['center'],
        direction=fit['direction'],
        head=fit['head'],
        tail=fit['tail'],
        length=fit['length'],
        n_hits=len(hit_indices),
        rms_residual=fit['rms'],
        linearity=fit['linearity'],
        hit_indices=hit_indices,
        vertex_projection=fit['vertex'],
        total_electrons=total_electrons,
        total_energy_dep=total_energy_dep,
        mean_dedx=mean_dedx,
    )


def fit_all_tracks(
    hits: pd.DataFrame,
    labels: np.ndarray,
    z_target: float = 0.0,
    min_length: Optional[float] = None,
    max_rms: Optional[float] = None,
    min_hits: int = 3,
    relaxed_mode: bool = False,
) -> List[Track]:
    """
    Fit tracks to all clusters.

    GPU-accelerated when CuPy is available.

    Args:
        hits: DataFrame with hit data.
        labels: Cluster labels for each hit.
        z_target: Z-coordinate for vertex projection.
        min_length: Minimum track length to keep (default: 5.0 cm in relaxed mode, else 15.0).
        max_rms: Maximum RMS residual to keep (default: 5.0 cm in relaxed mode, else 2.0).
        min_hits: Minimum number of hits for a track (default: 3).
        relaxed_mode: Use relaxed quality cuts for better track recovery.

    Returns:
        List of Track objects.
    """
    params = get_tracking_params()

    # Use relaxed defaults for better track recovery (based on HIBEAM analysis)
    if relaxed_mode:
        default_min_length = 5.0   # Relaxed from 15.0 - allows shorter tracks
        default_max_rms = 5.0      # Relaxed from 2.0 - allows less linear tracks
    else:
        default_min_length = params.get('min_track_length', 15.0)
        default_max_rms = params.get('max_rms_residual', 2.0)

    if min_length is None:
        min_length = default_min_length
    if max_rms is None:
        max_rms = default_max_rms

    tracks = []
    unique_labels = set(labels) - {-1}

    for cluster_id in unique_labels:
        hit_indices = np.where(labels == cluster_id)[0]

        if len(hit_indices) < min_hits:
            continue

        track = fit_track(hits, cluster_id, hit_indices, z_target)

        if track is None:
            continue

        # Apply quality cuts
        if track.length < min_length:
            continue
        if track.rms_residual > max_rms:
            continue

        tracks.append(track)

    return tracks


def fit_all_tracks_multiscale(
    hits: pd.DataFrame,
    labels: np.ndarray,
    z_target: float = 0.0,
    quality_levels: List[Dict] = None,
) -> List[Track]:
    """
    Fit tracks with multiple quality levels (HIBEAM-inspired).

    First tries strict cuts for high-quality tracks, then relaxes
    for remaining clusters to maximize track recovery.

    Args:
        hits: DataFrame with hit data.
        labels: Cluster labels for each hit.
        z_target: Z-coordinate for vertex projection.
        quality_levels: List of dicts with min_length, max_rms, min_hits.

    Returns:
        List of Track objects sorted by quality (best first).
    """
    if quality_levels is None:
        quality_levels = [
            # Strict - high quality tracks
            {'min_length': 15.0, 'max_rms': 1.5, 'min_hits': 5},
            # Medium - moderate quality
            {'min_length': 8.0, 'max_rms': 3.0, 'min_hits': 4},
            # Relaxed - recover remaining tracks
            {'min_length': 3.0, 'max_rms': 5.0, 'min_hits': 3},
        ]

    all_tracks = []
    used_clusters = set()
    unique_labels = set(labels) - {-1}

    for level in quality_levels:
        for cluster_id in unique_labels:
            if cluster_id in used_clusters:
                continue

            hit_indices = np.where(labels == cluster_id)[0]

            if len(hit_indices) < level['min_hits']:
                continue

            track = fit_track(hits, cluster_id, hit_indices, z_target)

            if track is None:
                continue

            # Check quality at this level
            if track.length >= level['min_length'] and track.rms_residual <= level['max_rms']:
                all_tracks.append(track)
                used_clusters.add(cluster_id)

    return all_tracks


# Quantities are implemented in a small helper module to keep this file under
# the 500-line cap while preserving the historical import surface.
from .track_quantities import (  # noqa: E402
    compute_track_dedx,
    compute_track_features,
    tracks_to_dataframe,
)
