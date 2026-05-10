"""Feature extraction for the NNBAR Random Forest Classifier."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from nnbar_reconstruction.data_pipeline.load_simulation_data import load_dataset


RFC_FEATURE_COLUMNS = [
    "total_energy", "scintillator_energy", "leadglass_energy",
    "n_charged_tracks", "n_pi0", "sphericity", "invariant_mass",
    "vertex_x", "vertex_y", "vertex_z", "energy_asymmetry",
    "n_hits_tpc", "leading_track_dedx",
]
_ENERGY_COLUMNS = ("edep", "energy", "Energy", "Edep", "edep_MeV")


def extract_rfc_features(parquet_dir: Path, n_events: int = -1) -> pd.DataFrame:
    """Load Parquet files and extract RFC feature columns, filling missing values."""
    parquet_dir = Path(parquet_dir)
    if not parquet_dir.is_dir():
        return _empty()
    try:
        dataset = load_dataset(parquet_dir)
    except FileNotFoundError:
        return _empty()

    event_ids = sorted(
        {
            int(event_id)
            for frame in dataset.values()
            if "Event_ID" in frame
            for event_id in frame["Event_ID"].dropna().unique()
        }
    )
    if not event_ids:
        return _generic_feature_parquet(parquet_dir, n_events)
    if n_events >= 0:
        event_ids = event_ids[:n_events]

    features = pd.DataFrame(
        0.0,
        index=pd.Index(event_ids, name="Event_ID"),
        columns=RFC_FEATURE_COLUMNS,
    )
    tpc = dataset.get("tpc", pd.DataFrame())
    scintillator = dataset.get("scintillator", pd.DataFrame())
    leadglass = dataset.get("leadglass", pd.DataFrame())

    tpc_energy = _energy_sum(tpc)
    scint_energy = _energy_sum(scintillator)
    lead_energy = _energy_sum(leadglass)
    _put(features, "total_energy", tpc_energy.add(scint_energy, fill_value=0.0).add(lead_energy, fill_value=0.0))
    _put(features, "scintillator_energy", scint_energy)
    _put(features, "leadglass_energy", lead_energy)
    if "Event_ID" in tpc:
        _put(features, "n_hits_tpc", tpc.groupby("Event_ID").size())
    if {"Event_ID", "track_id"}.issubset(tpc.columns):
        _put(features, "n_charged_tracks", tpc.groupby("Event_ID")["track_id"].nunique())
        energy_col = _energy_column(tpc)
        if energy_col is not None:
            per_track = tpc.groupby(["Event_ID", "track_id"])[energy_col].sum()
            _put(features, "leading_track_dedx", per_track.groupby("Event_ID").max())
    if {"Event_ID", "x", "y", "z"}.issubset(tpc.columns):
        means = tpc.groupby("Event_ID")[["x", "y", "z"]].mean() / 10.0
        for source, target in zip(["x", "y", "z"], ["vertex_x", "vertex_y", "vertex_z"]):
            _put(features, target, means[source])
        _put(features, "sphericity", pd.Series({
            int(event_id): _sphericity(hits[["x", "y", "z"]].to_numpy(float))
            for event_id, hits in tpc.groupby("Event_ID", sort=True)
        }))
    _put(features, "energy_asymmetry", _energy_asymmetry(scintillator, leadglass))
    for frame in dataset.values():
        if "Event_ID" not in frame:
            continue
        for column in RFC_FEATURE_COLUMNS:
            if column in frame:
                _put(features, column, frame.groupby("Event_ID")[column].first())
    return features.reset_index(drop=True).astype(float)


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=RFC_FEATURE_COLUMNS, dtype=float)


def _generic_feature_parquet(parquet_dir: Path, n_events: int) -> pd.DataFrame:
    frames = [
        pd.read_parquet(path)
        for path in sorted(Path(parquet_dir).glob("*.parquet"))
    ]
    frames = [frame for frame in frames if any(col in frame for col in RFC_FEATURE_COLUMNS)]
    if not frames:
        return _empty()
    combined = pd.concat(frames, ignore_index=True)
    if n_events >= 0:
        combined = combined.head(n_events)
    return pd.DataFrame({
        col: pd.to_numeric(combined.get(col, 0.0), errors="coerce").fillna(0.0)
        for col in RFC_FEATURE_COLUMNS
    }).astype(float)


def _energy_column(frame: pd.DataFrame) -> str | None:
    return next((column for column in _ENERGY_COLUMNS if column in frame), None)


def _energy_sum(frame: pd.DataFrame) -> pd.Series:
    column = _energy_column(frame)
    if frame.empty or "Event_ID" not in frame or column is None:
        return pd.Series(dtype=float)
    return frame.groupby("Event_ID")[column].sum().astype(float)


def _energy_asymmetry(*frames: pd.DataFrame) -> pd.Series:
    top = pd.Series(dtype=float)
    bottom = pd.Series(dtype=float)
    for frame in frames:
        column = _energy_column(frame)
        if frame.empty or "Event_ID" not in frame or "y" not in frame or column is None:
            continue
        top = top.add(frame.loc[frame["y"] > 0].groupby("Event_ID")[column].sum(), fill_value=0.0)
        bottom = bottom.add(frame.loc[frame["y"] < 0].groupby("Event_ID")[column].sum(), fill_value=0.0)
    total = top.add(bottom, fill_value=0.0)
    return top.sub(bottom, fill_value=0.0).divide(total.replace(0.0, np.nan)).fillna(0.0)


def _sphericity(points: np.ndarray) -> float:
    if len(points) < 3:
        return 0.0
    centered = points - points.mean(axis=0)
    tensor = centered.T @ centered
    trace = float(np.trace(tensor))
    if trace <= 0.0:
        return 0.0
    eigenvalues = np.sort(np.linalg.eigvalsh(tensor) / trace)[::-1]
    return float(np.clip(1.5 * (eigenvalues[1] + eigenvalues[2]), 0.0, 1.0))


def _put(features: pd.DataFrame, column: str, values: pd.Series) -> None:
    if not values.empty:
        features.loc[features.index.intersection(values.index), column] = values
