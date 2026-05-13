"""
Data loader for NNBAR simulation output (Parquet files).

Loads and merges detector data from GEANT4 simulation output.

Usage:
    from nnbar_reconstruction.utils import load_event_data, load_parquet_files

    # Load all detector data for a run
    data = load_parquet_files('/path/to/simulation/output/')

    # Load specific event
    event = load_event_data(data, event_id=42)
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass

import numpy as np
import pandas as pd

try:
    import pyarrow.parquet as pq
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False


@dataclass
class EventData:
    """Container for all detector data from a single event."""
    event_id: int
    tpc: pd.DataFrame
    scintillator: pd.DataFrame
    leadglass: pd.DataFrame
    silicon: Optional[pd.DataFrame] = None
    carbon: Optional[pd.DataFrame] = None
    particles: Optional[pd.DataFrame] = None
    interactions: Optional[pd.DataFrame] = None

    @property
    def has_tpc_hits(self) -> bool:
        return len(self.tpc) > 0

    @property
    def has_scint_hits(self) -> bool:
        return len(self.scintillator) > 0

    @property
    def has_calo_hits(self) -> bool:
        return len(self.leadglass) > 0

    @property
    def n_tpc_hits(self) -> int:
        return len(self.tpc)

    @property
    def total_scint_energy(self) -> float:
        if len(self.scintillator) == 0:
            return 0.0
        return self.scintillator['eDep'].sum()

    @property
    def total_calo_energy(self) -> float:
        if len(self.leadglass) == 0:
            return 0.0
        return self.leadglass['eDep'].sum()


def find_parquet_files(directory: Union[str, Path]) -> Dict[str, Path]:
    """
    Find all Parquet output files in a directory.

    Args:
        directory: Path to simulation output directory.

    Returns:
        Dictionary mapping detector name to file path.
    """
    directory = Path(directory)

    # Expected file patterns
    patterns = {
        'tpc': 'TPC_output*.parquet',
        'scintillator': 'Scintillator_output*.parquet',
        'leadglass': 'LeadGlass_output*.parquet',
        'silicon': 'Silicon_output*.parquet',
        'carbon': 'Carbon_output*.parquet',
        'particles': 'Particle_output*.parquet',
        'interactions': 'Interaction_output*.parquet',
        'beampipe': 'Beampipe_output*.parquet',
    }

    found_files = {}
    for detector, pattern in patterns.items():
        matches = list(directory.glob(pattern))
        if matches:
            # Take the most recent file if multiple exist
            found_files[detector] = sorted(matches)[-1]

    return found_files


def load_parquet_files(
    directory: Union[str, Path],
    detectors: Optional[List[str]] = None,
    columns: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Load Parquet files from simulation output.

    Args:
        directory: Path to simulation output directory.
        detectors: List of detectors to load. If None, loads all available.
        columns: Dictionary mapping detector to columns to load.

    Returns:
        Dictionary mapping detector name to DataFrame.
    """
    if not HAS_PYARROW:
        raise ImportError("pyarrow required. Install with: pip install pyarrow")

    files = find_parquet_files(directory)

    if detectors is None:
        detectors = list(files.keys())

    data = {}
    for detector in detectors:
        if detector in files:
            cols = columns.get(detector) if columns else None
            try:
                if cols:
                    data[detector] = pd.read_parquet(files[detector], columns=cols)
                else:
                    data[detector] = pd.read_parquet(files[detector])
            except Exception as e:
                print(f"[WARNING] Failed to load {detector}: {e}")
                data[detector] = pd.DataFrame()
        else:
            data[detector] = pd.DataFrame()

    return data


def load_event_data(
    data: Dict[str, pd.DataFrame],
    event_id: int,
) -> EventData:
    """
    Extract data for a specific event.

    Args:
        data: Dictionary of DataFrames from load_parquet_files.
        event_id: Event ID to extract.

    Returns:
        EventData object containing all detector data for the event.
    """
    def filter_event(df: pd.DataFrame, eid: int) -> pd.DataFrame:
        if df is None or len(df) == 0:
            return pd.DataFrame()
        if 'Event_ID' in df.columns:
            return df[df['Event_ID'] == eid].copy()
        return pd.DataFrame()

    return EventData(
        event_id=event_id,
        tpc=filter_event(data.get('tpc'), event_id),
        scintillator=filter_event(data.get('scintillator'), event_id),
        leadglass=filter_event(data.get('leadglass'), event_id),
        silicon=filter_event(data.get('silicon'), event_id),
        carbon=filter_event(data.get('carbon'), event_id),
        particles=filter_event(data.get('particles'), event_id),
        interactions=filter_event(data.get('interactions'), event_id),
    )


def get_event_ids(data: Dict[str, pd.DataFrame]) -> np.ndarray:
    """
    Get list of all event IDs in the data.

    Args:
        data: Dictionary of DataFrames from load_parquet_files.

    Returns:
        Sorted array of unique event IDs.
    """
    all_ids = set()

    for detector, df in data.items():
        if df is not None and len(df) > 0 and 'Event_ID' in df.columns:
            all_ids.update(df['Event_ID'].unique())

    return np.array(sorted(all_ids))


def get_truth_vertex(event: EventData) -> Optional[np.ndarray]:
    """
    Get truth vertex position from carbon target hits.

    Args:
        event: EventData object.

    Returns:
        Vertex position [x, y, z] in cm, or None if not available.
    """
    if event.carbon is None or len(event.carbon) == 0:
        return None

    # Use first interaction point on carbon foil
    carbon = event.carbon
    if 'x' in carbon.columns:
        return np.array([
            carbon['x'].iloc[0],
            carbon['y'].iloc[0],
            carbon['z'].iloc[0],
        ])
    return None


def get_truth_particles(event: EventData) -> pd.DataFrame:
    """
    Get truth-level particle information.

    Args:
        event: EventData object.

    Returns:
        DataFrame with particle truth information.
    """
    if event.particles is None:
        return pd.DataFrame()
    return event.particles


def compute_event_statistics(data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Compute summary statistics for loaded data.

    Args:
        data: Dictionary of DataFrames.

    Returns:
        Dictionary of statistics.
    """
    stats = {
        'n_events': len(get_event_ids(data)),
    }

    for detector, df in data.items():
        if df is not None and len(df) > 0:
            stats[f'{detector}_hits'] = len(df)
            if 'Event_ID' in df.columns:
                stats[f'{detector}_events'] = df['Event_ID'].nunique()
            if 'eDep' in df.columns:
                stats[f'{detector}_total_energy'] = df['eDep'].sum()

    return stats


class EventIterator:
    """Iterator over events in simulation data."""

    def __init__(
        self,
        data: Dict[str, pd.DataFrame],
        event_ids: Optional[List[int]] = None,
    ):
        """
        Initialize event iterator.

        Args:
            data: Dictionary of DataFrames from load_parquet_files.
            event_ids: Specific events to iterate. If None, iterates all.
        """
        self.data = data
        if event_ids is None:
            self.event_ids = get_event_ids(data)
        else:
            self.event_ids = np.array(event_ids)
        self._index = 0

    def __len__(self) -> int:
        return len(self.event_ids)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> EventData:
        if self._index >= len(self.event_ids):
            raise StopIteration
        event_id = self.event_ids[self._index]
        self._index += 1
        return load_event_data(self.data, event_id)


def preprocess_tpc_data(tpc_df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess TPC data for reconstruction.

    Adds derived columns and filters invalid hits.

    Args:
        tpc_df: Raw TPC DataFrame.

    Returns:
        Preprocessed DataFrame.
    """
    if len(tpc_df) == 0:
        return tpc_df

    df = tpc_df.copy()

    # Compute cylindrical coordinates
    df['r'] = np.sqrt(df['x']**2 + df['y']**2)
    df['phi'] = np.arctan2(df['y'], df['x'])

    # Filter out hits with zero energy deposit
    if 'eDep' in df.columns:
        df = df[df['eDep'] > 0]

    # Sort by time
    if 't' in df.columns:
        df = df.sort_values('t')

    return df


def preprocess_scintillator_data(scint_df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess scintillator data for reconstruction.

    Args:
        scint_df: Raw scintillator DataFrame.

    Returns:
        Preprocessed DataFrame.
    """
    if len(scint_df) == 0:
        return scint_df

    df = scint_df.copy()

    # Compute cylindrical coordinates
    df['r'] = np.sqrt(df['x']**2 + df['y']**2)
    df['phi'] = np.arctan2(df['y'], df['x'])

    # Filter hits with energy deposit
    if 'eDep' in df.columns:
        df = df[df['eDep'] > 0]

    return df


def preprocess_leadglass_data(lg_df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess lead glass data for reconstruction.

    Args:
        lg_df: Raw lead glass DataFrame.

    Returns:
        Preprocessed DataFrame.
    """
    if len(lg_df) == 0:
        return lg_df

    df = lg_df.copy()

    # Compute distance from beam axis
    df['r'] = np.sqrt(df['x']**2 + df['y']**2)

    # Filter hits with energy deposit
    if 'eDep' in df.columns:
        df = df[df['eDep'] > 0]

    return df


if __name__ == "__main__":
    # Test data loading
    import sys

    if len(sys.argv) > 1:
        directory = sys.argv[1]
        print(f"Loading data from: {directory}")
        data = load_parquet_files(directory)
        stats = compute_event_statistics(data)
        print("Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print("Usage: python data_loader.py <path_to_simulation_output>")
