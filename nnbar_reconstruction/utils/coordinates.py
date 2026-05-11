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


def compute_invariant_mass_2gamma(
    e1: float,
    e2: float,
    opening_angle: float,
) -> float:
    """
    Compute invariant mass of two photons.

    Implements Eq. 7.11 from thesis:
    m_0 = sqrt(2 * E1 * E2 * (1 - cos(theta)))

    Args:
        e1, e2: Energies of the two photons in MeV.
        opening_angle: Opening angle in radians.

    Returns:
        Invariant mass in MeV.
    """
    return np.sqrt(2 * e1 * e2 * (1 - np.cos(opening_angle)))


def compute_total_invariant_mass(
    energies: np.ndarray,
    momenta: np.ndarray,
) -> float:
    """
    Compute total invariant mass of a system of particles.

    Implements Eq. 9.1 from thesis:
    W = sqrt((sum E_i)^2 - (sum p_i)^2)

    Args:
        energies: Array of particle energies (N,) in MeV.
        momenta: Array of particle momenta (N, 3) in MeV/c.

    Returns:
        Total invariant mass in MeV.
    """
    total_energy = np.sum(energies)
    total_momentum = np.sum(momenta, axis=0)
    total_momentum_mag_sq = np.dot(total_momentum, total_momentum)

    mass_sq = total_energy**2 - total_momentum_mag_sq
    if mass_sq < 0:
        return 0.0

    return np.sqrt(mass_sq)


def compute_sphericity(momenta: np.ndarray) -> float:
    """
    Compute sphericity of a multi-particle system.

    Implements Eq. 9.2-9.4 from thesis:
    S = 3/2 * (lambda_2 + lambda_3)

    where lambda_i are normalized eigenvalues of momentum tensor.

    Args:
        momenta: Array of particle momenta (N, 3) in MeV/c.

    Returns:
        Sphericity in [0, 1]. 0 = pencil-like, 1 = isotropic.
    """
    momenta = np.asarray(momenta, dtype=float)
    if momenta.size == 0:
        return 0.0
    if momenta.ndim == 1:
        if momenta.shape[0] != 3:
            return 0.0
        momenta = momenta.reshape(1, 3)
    if len(momenta) < 2 or momenta.shape[1] != 3:
        return 0.0

    # Build and normalize the thesis momentum tensor:
    # S^{ab} = sum_i p_i^a p_i^b / sum_i |p_i|^2.
    momentum_norm_sq = np.einsum("ij,ij->i", momenta, momenta)
    denominator = float(np.sum(momentum_norm_sq))
    if denominator <= 1e-10:
        return 0.0

    S_tensor = (momenta.T @ momenta) / denominator

    # Eigenvalues sorted descending: lambda_1 >= lambda_2 >= lambda_3.
    eigenvalues = np.sort(np.linalg.eigvalsh(S_tensor))[::-1]
    lambda_2 = eigenvalues[1]
    lambda_3 = eigenvalues[2]

    return float(np.clip(1.5 * (lambda_2 + lambda_3), 0.0, 1.0))


def angular_distance_phi(phi1: float, phi2: float) -> float:
    """
    Compute angular distance between two azimuthal angles.

    Handles wraparound at +-pi.

    Args:
        phi1, phi2: Azimuthal angles in radians.

    Returns:
        Angular distance in [0, pi].
    """
    dphi = phi1 - phi2
    # Wrap to [-pi, pi]
    dphi = np.arctan2(np.sin(dphi), np.cos(dphi))
    return abs(dphi)


def weighted_average_position(
    positions: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    """
    Compute weighted average of positions.

    Args:
        positions: Array of positions (N, 3).
        weights: Array of weights (N,).

    Returns:
        Weighted average position (3,).
    """
    weights = np.asarray(weights)
    total_weight = np.sum(weights)
    if total_weight < 1e-10:
        return np.mean(positions, axis=0)
    return np.sum(positions * weights[:, np.newaxis], axis=0) / total_weight


if __name__ == "__main__":
    # Test coordinate transforms
    print("Testing coordinate transforms...")

    # Test cartesian to cylindrical
    x, y, z = 1.0, 1.0, 5.0
    r, phi, z_out = cartesian_to_cylindrical(x, y, z)
    print(f"Cartesian ({x}, {y}, {z}) -> Cylindrical ({r:.3f}, {np.degrees(phi):.1f}deg, {z_out})")

    # Test back conversion
    x2, y2, z2 = cylindrical_to_cartesian(r, phi, z_out)
    print(f"Back to Cartesian: ({x2:.3f}, {y2:.3f}, {z2:.3f})")

    # Test angle computation
    v1 = [1, 0, 0]
    v2 = [0, 1, 0]
    print(f"Angle between {v1} and {v2}: {compute_angle_degrees(v1, v2):.1f} degrees")

    # Test invariant mass
    m = compute_invariant_mass_2gamma(100, 100, np.radians(90))
    print(f"Invariant mass of two 100 MeV photons at 90 degrees: {m:.1f} MeV")
