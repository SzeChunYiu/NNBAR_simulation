"""
Event Pre-selection using Rolling Time Window Trigger.

Implements Section 7.1 from thesis:
- Scan global timeline in 10 ns increments
- Window width: 50 ns
- Trigger: >1 TPC track AND/OR calorimeter energy > 100 MeV
- Select window with highest energy deposition
- Return t0 (event time)
"""

import numpy as np
from typing import Tuple, Optional, Dict
import pandas as pd

from ..utils.config import get_reconstruction_params


def _count_unique_track_ids(track_ids: np.ndarray) -> int:
    """Count valid TPC track identifiers, ignoring negative/noise IDs."""
    if len(track_ids) == 0:
        return 0

    numeric_ids = pd.to_numeric(pd.Series(track_ids), errors="coerce")
    valid_ids = numeric_ids[(numeric_ids.notna()) & (numeric_ids >= 0)]
    return int(valid_ids.nunique())


def _track_id_column(tpc_data: pd.DataFrame) -> Optional[str]:
    """Return the supported TPC track-id column name, if present."""
    for column in ("track_id", "Track_ID"):
        if column in tpc_data.columns:
            return column
    return None


def find_event_time(
    tpc_times: np.ndarray,
    calo_times: np.ndarray,
    calo_energies: np.ndarray,
    window_width: Optional[float] = None,
    step_size: Optional[float] = None,
    min_tpc_tracks: Optional[int] = None,
    min_calo_energy: Optional[float] = None,
    tpc_track_ids: Optional[np.ndarray] = None,
) -> Tuple[float, float, int]:
    """
    Find the optimal event time using rolling window trigger.

    Args:
        tpc_times: Array of TPC hit times in ns.
        calo_times: Array of calorimeter hit times in ns.
        calo_energies: Array of calorimeter energy deposits in MeV.
        window_width: Width of trigger window in ns.
        step_size: Step size for scanning in ns.
        min_tpc_tracks: Minimum TPC track count for trigger.
        min_calo_energy: Minimum calorimeter energy for trigger.
        tpc_track_ids: Optional TPC track identifier per TPC hit. When omitted,
            the legacy times-only path counts TPC hits instead of tracks.

    Returns:
        Tuple of (t0, best_energy, n_triggers) where:
        - t0: Event time (start of best window)
        - best_energy: Total energy in best window
        - n_triggers: Number of windows that passed trigger
    """
    params = get_reconstruction_params()

    if window_width is None:
        window_width = params.get('trigger_window', 50.0)
    if step_size is None:
        step_size = params.get('trigger_step', 10.0)
    if min_tpc_tracks is None:
        min_tpc_tracks = params.get('min_tpc_tracks', 2)
    if min_calo_energy is None:
        min_calo_energy = params.get('min_calo_energy', 100.0)

    if tpc_track_ids is not None:
        tpc_track_ids = np.asarray(tpc_track_ids)
        if len(tpc_track_ids) != len(tpc_times):
            raise ValueError("tpc_track_ids must have the same length as tpc_times")

    # Combine all times
    all_times = np.concatenate([tpc_times, calo_times]) if len(calo_times) > 0 else tpc_times

    if len(all_times) == 0:
        return 0.0, 0.0, 0

    # Define scan range
    t_min = all_times.min() - window_width
    t_max = all_times.max()

    # Scan with rolling window
    best_t0 = t_min
    best_energy = 0.0
    n_triggers = 0
    found_trigger = False

    t = t_min
    while t <= t_max:
        # Thesis Ch. 7 event pre-selection activates on >1 TPC track. If this
        # legacy API receives only times, retain explicit hit-count fallback.
        tpc_mask = (tpc_times >= t) & (tpc_times < t + window_width)
        if tpc_track_ids is None:
            n_tpc = np.sum(tpc_mask)
        else:
            n_tpc = _count_unique_track_ids(tpc_track_ids[tpc_mask])

        # Sum calorimeter energy in window
        calo_mask = (calo_times >= t) & (calo_times < t + window_width)
        calo_energy = np.sum(calo_energies[calo_mask]) if len(calo_energies) > 0 else 0.0

        # Check trigger condition
        triggered = (n_tpc >= min_tpc_tracks) or (calo_energy >= min_calo_energy)

        if triggered:
            n_triggers += 1

            # Total energy in window (include TPC ionization if available)
            total_energy = calo_energy

            if not found_trigger or total_energy > best_energy:
                found_trigger = True
                best_energy = total_energy
                best_t0 = t

        t += step_size

    return best_t0, best_energy, n_triggers


def rolling_time_window_trigger(
    tpc_data: pd.DataFrame,
    scint_data: pd.DataFrame,
    leadglass_data: pd.DataFrame,
    window_width: Optional[float] = None,
    step_size: Optional[float] = None,
) -> Dict:
    """
    Apply rolling time window trigger to event data.

    Args:
        tpc_data: DataFrame with TPC hits (needs 't' column).
        scint_data: DataFrame with scintillator hits.
        leadglass_data: DataFrame with lead glass hits.
        window_width: Trigger window width in ns.
        step_size: Scan step size in ns.

    Returns:
        Dictionary with:
        - t0: Event time
        - tpc_mask: Boolean mask for TPC hits in window
        - scint_mask: Boolean mask for scintillator hits
        - lg_mask: Boolean mask for lead glass hits
        - triggered: Whether event passed trigger
        - total_energy: Energy in trigger window
    """
    params = get_reconstruction_params()

    if window_width is None:
        window_width = params.get('trigger_window', 50.0)
    if step_size is None:
        step_size = params.get('trigger_step', 10.0)

    # Extract times, optional track IDs, and energies.
    tpc_times = tpc_data['t'].values if 't' in tpc_data.columns and len(tpc_data) > 0 else np.array([])
    track_column = _track_id_column(tpc_data)
    tpc_track_ids = tpc_data[track_column].values if track_column and len(tpc_data) > 0 else None

    calo_times = []
    calo_energies = []

    if 't' in scint_data.columns and len(scint_data) > 0:
        calo_times.append(scint_data['t'].values)
        calo_energies.append(scint_data['eDep'].values if 'eDep' in scint_data.columns else np.zeros(len(scint_data)))

    if 't' in leadglass_data.columns and len(leadglass_data) > 0:
        calo_times.append(leadglass_data['t'].values)
        calo_energies.append(leadglass_data['eDep'].values if 'eDep' in leadglass_data.columns else np.zeros(len(leadglass_data)))

    calo_times = np.concatenate(calo_times) if calo_times else np.array([])
    calo_energies = np.concatenate(calo_energies) if calo_energies else np.array([])

    # Find best window
    t0, best_energy, n_triggers = find_event_time(
        tpc_times, calo_times, calo_energies,
        window_width, step_size, tpc_track_ids=tpc_track_ids
    )

    # Create masks for hits in window
    t1 = t0 + window_width

    tpc_mask = (tpc_data['t'] >= t0) & (tpc_data['t'] < t1) if 't' in tpc_data.columns else np.ones(len(tpc_data), dtype=bool)
    scint_mask = (scint_data['t'] >= t0) & (scint_data['t'] < t1) if 't' in scint_data.columns else np.ones(len(scint_data), dtype=bool)
    lg_mask = (leadglass_data['t'] >= t0) & (leadglass_data['t'] < t1) if 't' in leadglass_data.columns else np.ones(len(leadglass_data), dtype=bool)

    return {
        't0': t0,
        'window_width': window_width,
        'tpc_mask': tpc_mask.values if hasattr(tpc_mask, 'values') else tpc_mask,
        'scint_mask': scint_mask.values if hasattr(scint_mask, 'values') else scint_mask,
        'lg_mask': lg_mask.values if hasattr(lg_mask, 'values') else lg_mask,
        'triggered': n_triggers > 0,
        'n_trigger_windows': n_triggers,
        'total_energy': best_energy,
    }


def filter_hits_by_time(
    data: pd.DataFrame,
    t0: float,
    window_width: float,
) -> pd.DataFrame:
    """
    Filter DataFrame to hits within time window.

    Args:
        data: DataFrame with 't' column.
        t0: Start of time window.
        window_width: Width of time window.

    Returns:
        Filtered DataFrame.
    """
    if 't' not in data.columns or len(data) == 0:
        return data

    mask = (data['t'] >= t0) & (data['t'] < t0 + window_width)
    return data[mask].copy()


if __name__ == "__main__":
    # Test rolling window trigger
    np.random.seed(42)

    # Create synthetic event data
    # Main event at t=100 ns
    t_event = 100.0
    n_signal_hits = 50
    n_noise_hits = 20

    # Signal hits
    signal_times = t_event + np.random.normal(0, 5, n_signal_hits)
    signal_energies = np.random.exponential(10, n_signal_hits)

    # Noise hits
    noise_times = np.random.uniform(0, 500, n_noise_hits)
    noise_energies = np.random.exponential(2, n_noise_hits)

    all_times = np.concatenate([signal_times, noise_times])
    all_energies = np.concatenate([signal_energies, noise_energies])

    # Find event time
    t0, energy, n_trig = find_event_time(
        signal_times,  # TPC times
        all_times,     # Calo times
        all_energies,  # Calo energies
    )

    print(f"True event time: {t_event:.1f} ns")
    print(f"Found event time: {t0:.1f} ns")
    print(f"Error: {abs(t0 - t_event + 25):.1f} ns")  # +25 because t0 is start of window
    print(f"Energy in window: {energy:.1f} MeV")
    print(f"Number of trigger windows: {n_trig}")
