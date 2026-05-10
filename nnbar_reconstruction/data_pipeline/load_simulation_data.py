"""Load Geant4 simulation parquet outputs for reconstruction studies.

The simulation writes one parquet file per detector subsystem in each run
folder.  This module recognises the four subsystems required by the lane spec
and leaves all paths under caller control.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


_SUBSYSTEM_FILES: dict[str, str] = {
    "tpc": "TPC_output_*.parquet",
    "particle": "Particle_output_*.parquet",
    "scintillator": "Scintillator_output_*.parquet",
    "leadglass": "LeadGlass_output_*.parquet",
}


def _read_parquet_group(data_dir: Path, pattern: str) -> pd.DataFrame | None:
    """Read all parquet files matching *pattern* in *data_dir*."""
    paths = sorted(data_dir.glob(pattern))
    if not paths:
        return None

    frames = [pd.read_parquet(path) for path in paths]
    if len(frames) == 1:
        return frames[0]
    return pd.concat(frames, ignore_index=True)


def load_dataset(data_dir: Path) -> dict[str, pd.DataFrame]:
    """Load available subsystem parquet tables from one run directory.

    Missing subsystem files are skipped without warning.  Returned keys are a
    subset of ``tpc``, ``particle``, ``scintillator``, and ``leadglass``.
    """
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Simulation data directory not found: {data_dir}")

    dataset: dict[str, pd.DataFrame] = {}
    for subsystem, pattern in _SUBSYSTEM_FILES.items():
        frame = _read_parquet_group(data_dir, pattern)
        if frame is not None:
            dataset[subsystem] = frame
    return dataset


def load_all_datasets(
    base_dir: Path,
    dataset_names: list[str] | None = None,
) -> dict[str, dict[str, pd.DataFrame]]:
    """Load multiple named run subdirectories under *base_dir*.

    If ``dataset_names`` is omitted, every immediate child directory with at
    least one ``*.parquet`` file is loaded.
    """
    base_dir = Path(base_dir)
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Simulation base directory not found: {base_dir}")

    if dataset_names is None:
        dataset_names = [
            child.name
            for child in sorted(base_dir.iterdir())
            if child.is_dir() and any(child.glob("*.parquet"))
        ]

    datasets: dict[str, dict[str, pd.DataFrame]] = {}
    for name in dataset_names:
        run_dir = base_dir / name
        if run_dir.is_dir():
            datasets[name] = load_dataset(run_dir)
        else:
            datasets[name] = {}
    return datasets


def _event_id_range(run_data: dict[str, pd.DataFrame]) -> tuple[int, int] | None:
    """Return the min/max Event_ID present in any subsystem for one run."""
    mins: list[int] = []
    maxs: list[int] = []
    for frame in run_data.values():
        if "Event_ID" not in frame or frame.empty:
            continue
        ids = frame["Event_ID"]
        mins.append(int(ids.min()))
        maxs.append(int(ids.max()))
    if not mins:
        return None
    return min(mins), max(maxs)


def combine_datasets(
    datasets: dict[str, dict[str, pd.DataFrame]],
    offset_ids: bool = True,
) -> dict[str, pd.DataFrame]:
    """Merge run dictionaries into one DataFrame per subsystem.

    With ``offset_ids=True``, Event_ID values for later runs are shifted so
    that each combined subsystem table has globally unique event IDs while
    preserving cross-subsystem alignment inside a run.
    """
    if not datasets:
        return {}

    run_offsets: dict[str, int] = {}
    next_event_id: int | None = None

    for run_name, run_data in datasets.items():
        event_range = _event_id_range(run_data)
        if not offset_ids or event_range is None:
            run_offsets[run_name] = 0
            continue

        min_id, max_id = event_range
        shift = 0 if next_event_id is None else next_event_id - min_id
        run_offsets[run_name] = shift
        next_event_id = max_id + shift + 1

    by_subsystem: dict[str, list[pd.DataFrame]] = {}
    for run_name, run_data in datasets.items():
        shift = run_offsets[run_name]
        for subsystem, frame in run_data.items():
            if frame.empty:
                continue
            copy = frame.copy()
            if offset_ids and shift and "Event_ID" in copy:
                copy["Event_ID"] = copy["Event_ID"] + shift
            by_subsystem.setdefault(subsystem, []).append(copy)

    return {
        subsystem: pd.concat(frames, ignore_index=True)
        for subsystem, frames in by_subsystem.items()
        if frames
    }
