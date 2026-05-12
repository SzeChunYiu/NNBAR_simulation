"""Event-level geometric and invariant-mass quantities."""

import numpy as np


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
