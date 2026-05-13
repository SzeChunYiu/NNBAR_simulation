"""
Timing Window of Acceptance.

Implements Section 7.3 from thesis:
- Scintillator timing window based on pion travel time
- Lead glass timing window based on photon travel time
"""

import numpy as np
from typing import Tuple, Optional
import pandas as pd
from types import SimpleNamespace

C_LIGHT_CM_PER_NS = 29.9792458
SCINTILLATOR_TIMING_RESOLUTION_NS = 1.0
LEADGLASS_TIMING_RESOLUTION_NS = 2.0
VALID_TIMING_DETECTORS = frozenset({"scintillator", "leadglass"})


def pion_travel_time(
    distance: float,
    kinetic_energy: float,
    mass: float = 139.57,
) -> float:
    """
    Calculate pion travel time for a given distance and energy.

    Args:
        distance: Distance in cm.
        kinetic_energy: Kinetic energy in MeV.
        mass: Pion mass in MeV.

    Returns:
        Travel time in ns.
    """
    c = C_LIGHT_CM_PER_NS

    total_energy = kinetic_energy + mass
    gamma = total_energy / mass
    beta = np.sqrt(1 - 1 / gamma**2)

    velocity = beta * c
    return distance / velocity


def photon_travel_time(distance: float) -> float:
    """
    Calculate photon travel time for a given distance.

    Args:
        distance: Distance in cm.

    Returns:
        Travel time in ns.
    """
    c = C_LIGHT_CM_PER_NS
    return distance / c


def scintillator_timing_window(
    vertex: np.ndarray,
    stave_position: np.ndarray,
    t0: float,
    sigma: Optional[float] = None,
    ke_range: Tuple[float, float] = (100.0, 1000.0),
    n_sigma: float = 2.0,
) -> Tuple[float, float]:
    """
    Calculate scintillator timing acceptance window.

    Window: [t_pi_1000MeV - n*sigma, t_pi_100MeV + n*sigma]

    Args:
        vertex: Vertex position (x, y, z).
        stave_position: Position of scintillator stave center.
        t0: Event time (trigger time).
        sigma: Timing resolution in ns. If None, uses config.
        ke_range: (min, max) kinetic energy range for pions.
        n_sigma: Number of sigma for window width.

    Returns:
        Tuple of (t_min, t_max) for acceptance window.
    """
    if sigma is None:
        sigma = SCINTILLATOR_TIMING_RESOLUTION_NS

    distance = np.linalg.norm(stave_position - vertex)

    # Travel time for fastest pions (highest KE)
    t_fast = pion_travel_time(distance, ke_range[1])

    # Travel time for slowest pions (lowest KE)
    t_slow = pion_travel_time(distance, ke_range[0])

    # Window
    t_min = t0 + t_fast - n_sigma * sigma
    t_max = t0 + t_slow + n_sigma * sigma

    return t_min, t_max


def leadglass_timing_window(
    vertex: np.ndarray,
    module_position: np.ndarray,
    t0: float,
    sigma: Optional[float] = None,
    n_sigma: float = 2.0,
) -> Tuple[float, float]:
    """
    Calculate lead glass timing acceptance window.

    Window: [t_gamma - n*sigma, t_gamma + n*sigma]

    Args:
        vertex: Vertex position (x, y, z).
        module_position: Position of lead glass module center.
        t0: Event time.
        sigma: Timing resolution in ns. If None, uses config.
        n_sigma: Number of sigma for window width.

    Returns:
        Tuple of (t_min, t_max) for acceptance window.
    """
    if sigma is None:
        sigma = LEADGLASS_TIMING_RESOLUTION_NS

    distance = np.linalg.norm(module_position - vertex)

    # Photon travel time
    t_gamma = photon_travel_time(distance)

    # Window
    t_min = t0 + t_gamma - n_sigma * sigma
    t_max = t0 + t_gamma + n_sigma * sigma

    return t_min, t_max


def apply_timing_cuts(
    hits: pd.DataFrame,
    vertex: np.ndarray,
    t0: float,
    detector: str = 'scintillator',
    n_sigma: float = 2.0,
    sigma: Optional[float] = None,
) -> pd.DataFrame:
    """
    Apply timing cuts to detector hits.

    Args:
        hits: DataFrame with 't', 'x', 'y', 'z' columns.
        vertex: Vertex position.
        t0: Event time.
        detector: 'scintillator' or 'leadglass'.
        n_sigma: Number of sigma for timing window.
        sigma: Optional detector timing resolution override in ns.

    Returns:
        Filtered DataFrame.
    """
    _validate_detector_name(detector)

    if len(hits) == 0 or 't' not in hits.columns:
        return hits

    if detector == 'scintillator':
        if sigma is None:
            sigma = SCINTILLATOR_TIMING_RESOLUTION_NS
        ke_range = (100.0, 1000.0)
    else:
        if sigma is None:
            sigma = LEADGLASS_TIMING_RESOLUTION_NS
        ke_range = None

    # Apply per-hit timing cut
    # Reset index to ensure contiguous integer indices for mask array
    hits = hits.reset_index(drop=True)
    mask = np.ones(len(hits), dtype=bool)

    for idx, row in hits.iterrows():
        hit_pos = np.array([row['x'], row['y'], row['z']])

        if detector == 'scintillator':
            t_min, t_max = scintillator_timing_window(vertex, hit_pos, t0, sigma, ke_range, n_sigma)
        else:
            t_min, t_max = leadglass_timing_window(vertex, hit_pos, t0, sigma, n_sigma)

        # Check if hit time is in window
        mask[idx] = t_min <= row['t'] <= t_max

    return hits[mask].copy()


def compute_out_of_time_energy(
    hits: pd.DataFrame,
    vertex: np.ndarray,
    t0: float,
    detector: str = 'scintillator',
    n_sigma: float = 2.0,
    sigma: Optional[float] = None,
) -> float:
    """
    Compute energy from hits outside timing window.

    Used for cosmic ray rejection.

    Args:
        hits: DataFrame with timing and energy information.
        vertex: Vertex position.
        t0: Event time.
        detector: Detector type.
        n_sigma: Timing window width.
        sigma: Optional detector timing resolution override in ns.

    Returns:
        Total energy outside timing window in MeV.
    """
    _validate_detector_name(detector)

    if len(hits) == 0 or 't' not in hits.columns or 'eDep' not in hits.columns:
        return 0.0

    # Work on a contiguous index so in-time/out-of-time bookkeeping is stable
    # for hemisphere-filtered inputs whose original indices are non-contiguous.
    hits = hits.reset_index(drop=True)
    in_time_hits = apply_timing_cuts(hits, vertex, t0, detector, n_sigma, sigma)
    in_time_indices = set(in_time_hits.index)

    out_of_time_energy = hits.loc[~hits.index.isin(in_time_indices), 'eDep'].sum()

    return float(out_of_time_energy)


def split_scintillator_hits_by_hemisphere(
    hits: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split scintillator hits into thesis upper/lower hemispheres.

    Chapter 9 defines the filtered scintillator observables by module
    y-coordinate: upper is y > 0 and lower is y < 0. Hits exactly on y == 0 are
    excluded from both hemispheres to avoid assigning them to either side.
    """
    if len(hits) == 0 or 'y' not in hits.columns:
        empty = hits.iloc[0:0].copy()
        return empty, empty

    upper = hits.loc[hits['y'] > 0].copy()
    lower = hits.loc[hits['y'] < 0].copy()
    return upper, lower


def compute_filtered_scintillator_hemisphere_energies(
    hits: pd.DataFrame,
    vertex: np.ndarray,
    t0: float,
    n_sigma: float = 2.0,
    sigma: Optional[float] = None,
) -> SimpleNamespace:
    """
    Compute out-of-time scintillator energy separately for y > 0 and y < 0.

    The timing acceptance is the Chapter 7 scintillator window
    [t_pi,1000 - 2 sigma_scint, t_pi,100 + 2 sigma_scint] evaluated per hit.
    """
    upper_hits, lower_hits = split_scintillator_hits_by_hemisphere(hits)

    upper_mev = compute_out_of_time_energy(
        upper_hits,
        vertex=vertex,
        t0=t0,
        detector='scintillator',
        n_sigma=n_sigma,
        sigma=sigma,
    )
    lower_mev = compute_out_of_time_energy(
        lower_hits,
        vertex=vertex,
        t0=t0,
        detector='scintillator',
        n_sigma=n_sigma,
        sigma=sigma,
    )

    return SimpleNamespace(upper_mev=upper_mev, lower_mev=lower_mev)


def _validate_detector_name(detector: str) -> None:
    """Reject misspelled detector names instead of applying lead-glass cuts."""
    if detector not in VALID_TIMING_DETECTORS:
        valid = ", ".join(sorted(VALID_TIMING_DETECTORS))
        raise ValueError(f"detector must be one of: {valid}")


if __name__ == "__main__":
    # Test timing windows
    vertex = np.array([0, 0, 0])
    t0 = 100.0  # ns

    # Scintillator at ~275 cm
    scint_pos = np.array([275, 0, 50])
    t_min, t_max = scintillator_timing_window(vertex, scint_pos, t0)
    print(f"Scintillator timing window: [{t_min:.1f}, {t_max:.1f}] ns")

    # Lead glass at ~335 cm
    lg_pos = np.array([0, 0, 335])
    t_min, t_max = leadglass_timing_window(vertex, lg_pos, t0)
    print(f"Lead glass timing window: [{t_min:.1f}, {t_max:.1f}] ns")

    # Expected: scintillator window ~10-30 ns after t0
    # Expected: lead glass window ~11 ns after t0 (photon at c)
