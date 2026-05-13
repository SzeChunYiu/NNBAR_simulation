"""
Coordinate transformations and geometric calculations for NNBAR reconstruction.

Provides functions for:
- Cartesian <-> Cylindrical coordinate transforms
- Angular calculations
- Distance computations
- Track projections

GPU Acceleration:
- Uses CuPy for GPU-accelerated array operations when available
- Transparent fallback to NumPy when GPU not available
- All functions work with both NumPy and CuPy arrays
"""

import numpy as np
from typing import Tuple, Union, Optional

from .event_quantities import (
    angular_distance_phi,
    compute_invariant_mass_2gamma,
    compute_sphericity,
    compute_total_invariant_mass,
    weighted_average_position,
)

try:
    # GPU backend is optional for formula-only event-variable callers.
    from .gpu_backend import get_backend
except ImportError:  # pragma: no cover - exercised only in minimal installs
    class _NumpyBackend:
        use_gpu = False
        xp = np

    def get_backend() -> _NumpyBackend:
        return _NumpyBackend()

# Type aliases
Vector3 = Union[np.ndarray, Tuple[float, float, float]]


def _get_array_module(x):
    """Get the array module (numpy or cupy) for the given array."""
    gpu = get_backend()
    if gpu.use_gpu:
        import cupy as cp
        if isinstance(x, cp.ndarray):
            return cp
    return np


def cartesian_to_cylindrical(
    x: Union[float, np.ndarray],
    y: Union[float, np.ndarray],
    z: Union[float, np.ndarray],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert Cartesian coordinates to cylindrical (r, phi, z).

    GPU-accelerated when input arrays are on GPU.

    Args:
        x, y, z: Cartesian coordinates (can be arrays).

    Returns:
        Tuple of (r, phi, z) where:
        - r: radial distance from z-axis
        - phi: azimuthal angle in [-pi, pi]
        - z: unchanged
    """
    gpu = get_backend()
    xp = _get_array_module(x) if hasattr(x, '__array__') else gpu.xp

    x = xp.asarray(x)
    y = xp.asarray(y)
    z = xp.asarray(z)

    r = xp.sqrt(x**2 + y**2)
    phi = xp.arctan2(y, x)

    return r, phi, z


def cylindrical_to_cartesian(
    r: Union[float, np.ndarray],
    phi: Union[float, np.ndarray],
    z: Union[float, np.ndarray],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert cylindrical coordinates to Cartesian (x, y, z).

    GPU-accelerated when input arrays are on GPU.

    Args:
        r: radial distance
        phi: azimuthal angle in radians
        z: z coordinate

    Returns:
        Tuple of (x, y, z) Cartesian coordinates.
    """
    gpu = get_backend()
    xp = _get_array_module(r) if hasattr(r, '__array__') else gpu.xp

    r = xp.asarray(r)
    phi = xp.asarray(phi)
    z = xp.asarray(z)

    x = r * xp.cos(phi)
    y = r * xp.sin(phi)

    return x, y, z


def compute_angle(v1: Vector3, v2: Vector3) -> float:
    """
    Compute angle between two vectors in radians.

    Args:
        v1, v2: 3D vectors.

    Returns:
        Angle in radians [0, pi].
    """
    v1 = np.asarray(v1)
    v2 = np.asarray(v2)

    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)

    return np.arccos(cos_angle)


def compute_angle_degrees(v1: Vector3, v2: Vector3) -> float:
    """Compute angle between two vectors in degrees."""
    return np.degrees(compute_angle(v1, v2))


def compute_distance(p1: Vector3, p2: Vector3) -> float:
    """
    Compute Euclidean distance between two points.

    Args:
        p1, p2: 3D points.

    Returns:
        Distance.
    """
    p1 = np.asarray(p1)
    p2 = np.asarray(p2)
    return np.linalg.norm(p1 - p2)


def compute_distance_to_line(
    point: Vector3,
    line_point: Vector3,
    line_direction: Vector3,
) -> float:
    """
    Compute perpendicular distance from a point to a line.

    Args:
        point: Point in 3D space.
        line_point: A point on the line.
        line_direction: Direction vector of the line (will be normalized).

    Returns:
        Perpendicular distance.
    """
    point = np.asarray(point)
    line_point = np.asarray(line_point)
    line_direction = np.asarray(line_direction)

    # Normalize direction
    d = line_direction / (np.linalg.norm(line_direction) + 1e-10)

    # Vector from line point to point
    v = point - line_point

    # Project v onto line direction
    projection = np.dot(v, d) * d

    # Perpendicular component
    perpendicular = v - projection

    return np.linalg.norm(perpendicular)


def project_to_plane(
    point: Vector3,
    direction: Vector3,
    plane_z: float = 0.0,
) -> Optional[np.ndarray]:
    """
    Project a point along a direction to a z-plane.

    Used for projecting tracks back to the target foil.

    Args:
        point: Starting point (x, y, z).
        direction: Direction vector (dx, dy, dz).
        plane_z: Z-coordinate of the target plane.

    Returns:
        Projected point (x, y, z) or None if no intersection.
    """
    point = np.asarray(point)
    direction = np.asarray(direction)

    # Avoid division by zero
    if abs(direction[2]) < 1e-10:
        return None

    # Parameter t for intersection: point + t * direction has z = plane_z
    t = (plane_z - point[2]) / direction[2]

    # Compute intersection point
    projected = point + t * direction

    return projected


def compute_opening_angle(
    vertex: Vector3,
    point1: Vector3,
    point2: Vector3,
) -> float:
    """
    Compute opening angle between two directions from a vertex.

    Used for photon pair invariant mass calculation.

    Args:
        vertex: Common vertex point.
        point1, point2: Two points defining directions from vertex.

    Returns:
        Opening angle in radians.
    """
    vertex = np.asarray(vertex)
    point1 = np.asarray(point1)
    point2 = np.asarray(point2)

    # Direction vectors from vertex
    d1 = point1 - vertex
    d2 = point2 - vertex

    return compute_angle(d1, d2)


def normalize_vector(v: Vector3) -> np.ndarray:
    """Normalize a vector to unit length."""
    v = np.asarray(v)
    norm = np.linalg.norm(v)
    if norm < 1e-10:
        return np.zeros(3)
    return v / norm


def compute_momentum_direction(
    vertex: Vector3,
    track_entry: Vector3,
) -> np.ndarray:
    """
    Compute momentum direction from vertex to track entry point.

    Implements Eq. 7.7 from thesis.

    Args:
        vertex: Reconstructed vertex position.
        track_entry: TPC entry point of track.

    Returns:
        Unit momentum direction vector.
    """
    vertex = np.asarray(vertex)
    track_entry = np.asarray(track_entry)

    direction = track_entry - vertex
    return normalize_vector(direction)


def cone_contains_point(
    apex: Vector3,
    axis: Vector3,
    half_angle: float,
    point: Vector3,
) -> bool:
    """
    Check if a point is within a cone.

    Used for collecting calorimeter hits associated with a track.

    Args:
        apex: Cone apex (vertex position).
        axis: Cone axis direction (track direction).
        half_angle: Half-opening angle in radians.
        point: Point to test.

    Returns:
        True if point is within the cone.
    """
    apex = np.asarray(apex)
    axis = normalize_vector(axis)
    point = np.asarray(point)

    # Direction from apex to point
    to_point = point - apex

    # Angle between axis and direction to point
    angle = compute_angle(axis, to_point)

    return angle <= half_angle


def points_in_cone(
    apex: Vector3,
    axis: Vector3,
    half_angle_deg: float,
    points: np.ndarray,
) -> np.ndarray:
    """
    Find indices of points within a cone.

    Args:
        apex: Cone apex.
        axis: Cone axis direction.
        half_angle_deg: Half-opening angle in degrees.
        points: Array of points (N, 3).

    Returns:
        Boolean mask for points within cone.
    """
    apex = np.asarray(apex)
    axis = normalize_vector(axis)
    half_angle = np.radians(half_angle_deg)

    # Direction from apex to each point
    to_points = points - apex

    # Normalize directions
    norms = np.linalg.norm(to_points, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-10)
    to_points_normalized = to_points / norms

    # Compute angles
    cos_angles = np.dot(to_points_normalized, axis)
    cos_angles = np.clip(cos_angles, -1.0, 1.0)
    angles = np.arccos(cos_angles)

    return angles <= half_angle
