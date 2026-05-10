"""Prepare clustered TPC candidates for vertex-GNN training.

The public entry point runs the spec pipeline: load parquet outputs, cluster
TPC hits, compute per-cluster features, attach the truth vertex, split by event,
and write train/validation/test NPZ files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .load_simulation_data import load_dataset
from .run_clustering_pipeline import cluster_event


FEATURE_COLUMNS = [
    "dx",
    "dy",
    "dz",
    "length",
    "linearity",
    "rms",
    "sphericity",
    "highland_theta0",
    "r_surface",
    "n_hits",
    "charge_sum",
    "mean_ke",
]


def extract_track_features(
    tpc_hits: pd.DataFrame,
    cluster_labels: np.ndarray,
) -> pd.DataFrame:
    """Extract the 12 spec features for each non-noise cluster.

    The returned table includes ``Event_ID`` and ``cluster_id`` metadata when
    available, followed by the 12 feature columns used for the NPZ ``X`` array.
    """
    labels = np.asarray(cluster_labels)
    if len(tpc_hits) != len(labels):
        raise ValueError("cluster_labels length must match tpc_hits rows")

    rows: list[dict[str, float | int]] = []
    event_id = _single_event_id(tpc_hits)
    xyz = tpc_hits[["x", "y", "z"]].to_numpy(dtype=float)

    for cluster_id in sorted(label for label in np.unique(labels) if label >= 0):
        mask = labels == cluster_id
        cluster_hits = tpc_hits.loc[mask]
        points = xyz[mask]
        row: dict[str, float | int] = {"cluster_id": int(cluster_id)}
        if event_id is not None:
            row["Event_ID"] = event_id
        row.update(_feature_row(points, cluster_hits))
        rows.append(row)

    columns = ["Event_ID", "cluster_id"] + FEATURE_COLUMNS
    return pd.DataFrame(rows, columns=columns)


def prepare_gnn_training_data(
    data_dir: Path,
    output_dir: Path,
    split: tuple[float, float, float] = (0.7, 0.15, 0.15),
) -> dict[str, object]:
    """Run load → cluster → feature extraction → split → NPZ export."""
    dataset = load_dataset(Path(data_dir))
    tpc_hits = dataset.get("tpc")
    particle_truth = dataset.get("particle")
    if tpc_hits is None or tpc_hits.empty:
        raise ValueError("TPC data is required to prepare GNN training data")
    if particle_truth is None or particle_truth.empty:
        raise ValueError("Particle truth data is required for vertex labels")

    truth_by_event = _truth_vertices(particle_truth)
    feature_frames: list[pd.DataFrame] = []
    for event_id, event_hits in tpc_hits.groupby("Event_ID", sort=True):
        labels = cluster_event(event_hits)
        features = extract_track_features(event_hits, labels)
        if features.empty or int(event_id) not in truth_by_event:
            continue
        features["Event_ID"] = int(event_id)
        feature_frames.append(features)

    features = _combine_feature_frames(feature_frames)
    features = features[features["Event_ID"].isin(truth_by_event)].reset_index(drop=True)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    event_splits = _split_events(features["Event_ID"].to_numpy(dtype=int), split)
    files = {
        "train": output_dir / "train.npz",
        "val": output_dir / "val.npz",
        "test": output_dir / "test.npz",
    }

    counts: dict[str, int] = {}
    for split_name, event_ids in event_splits.items():
        mask = features["Event_ID"].isin(event_ids)
        split_frame = features.loc[mask]
        X = split_frame[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
        y = np.vstack([truth_by_event[int(eid)] for eid in split_frame["Event_ID"]]).astype(
            np.float32,
            copy=False,
        ) if len(split_frame) else np.empty((0, 3), dtype=np.float32)
        event_array = split_frame["Event_ID"].to_numpy(dtype=np.int64)
        np.savez(files[split_name], X=X, y=y, event_id=event_array)
        counts[split_name] = int(len(split_frame))

    counts["total"] = int(len(features))
    return {
        "counts": counts,
        "files": {name: str(path) for name, path in files.items()},
        "feature_columns": list(FEATURE_COLUMNS),
    }


def _single_event_id(tpc_hits: pd.DataFrame) -> int | None:
    """Return the unique Event_ID for an event-level hit table."""
    if "Event_ID" not in tpc_hits or tpc_hits.empty:
        return None
    values = tpc_hits["Event_ID"].unique()
    return int(values[0]) if len(values) == 1 else None


def _feature_row(points: np.ndarray, hits: pd.DataFrame) -> dict[str, float | int]:
    """Compute one 12-feature row for a cluster."""
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    spans = maxs - mins
    center = points.mean(axis=0)
    shape = _pca_shape(points)
    mean_ke = _mean_column(hits, "KE")
    length = max(shape["length"], 0.0)
    if mean_ke > 0.0 and length > 0.0:
        highland = 13.6 / (mean_ke * np.sqrt(length))
    else:
        highland = 0.0

    return {
        "dx": float(spans[0]),
        "dy": float(spans[1]),
        "dz": float(spans[2]),
        "length": float(shape["length"]),
        "linearity": float(shape["linearity"]),
        "rms": float(shape["rms"]),
        "sphericity": float(shape["sphericity"]),
        "highland_theta0": float(highland),
        "r_surface": float(np.sqrt(center[0] * center[0] + center[1] * center[1])),
        "n_hits": int(len(hits)),
        "charge_sum": float(hits["electrons"].sum()) if "electrons" in hits else 0.0,
        "mean_ke": float(mean_ke),
    }


def _pca_shape(points: np.ndarray) -> dict[str, float]:
    """Return PCA length, linearity, transverse RMS, and sphericity."""
    if len(points) < 2:
        return {"length": 0.0, "linearity": 0.0, "rms": 0.0, "sphericity": 0.0}

    centered = points - points.mean(axis=0)
    try:
        _, singular_values, components = np.linalg.svd(centered, full_matrices=False)
    except np.linalg.LinAlgError:
        return {"length": 0.0, "linearity": 0.0, "rms": 0.0, "sphericity": 0.0}

    direction = components[0]
    projections = centered @ direction
    residuals = centered - np.outer(projections, direction)
    eigenvalues = (singular_values * singular_values) / max(len(points) - 1, 1)
    total = float(eigenvalues.sum())
    if total <= 0.0:
        linearity = 0.0
        sphericity = 0.0
    else:
        linearity = float(eigenvalues[0] / total)
        sphericity = float(eigenvalues[-1] / total)

    return {
        "length": float(projections.max() - projections.min()),
        "linearity": linearity,
        "rms": float(np.sqrt(np.mean(np.sum(residuals * residuals, axis=1)))),
        "sphericity": sphericity,
    }


def _mean_column(frame: pd.DataFrame, column: str) -> float:
    """Return finite mean for a column, or 0.0 if unavailable."""
    if column not in frame or frame.empty:
        return 0.0
    value = frame[column].mean()
    return 0.0 if pd.isna(value) else float(value)


def _truth_vertices(particle_truth: pd.DataFrame) -> dict[int, np.ndarray]:
    """Build Event_ID → truth vertex lookup from Particle output."""
    if {"vx", "vy", "vz"}.issubset(particle_truth.columns):
        vertex_cols = ["vx", "vy", "vz"]
    elif {"x", "y", "z"}.issubset(particle_truth.columns):
        vertex_cols = ["x", "y", "z"]
    else:
        raise ValueError("Particle table must contain vx/vy/vz or x/y/z truth vertex columns")

    truth: dict[int, np.ndarray] = {}
    for event_id, rows in particle_truth.groupby("Event_ID", sort=True):
        truth[int(event_id)] = rows.iloc[0][vertex_cols].to_numpy(dtype=float)
    return truth


def _combine_feature_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate feature frames while preserving the expected columns."""
    columns = ["Event_ID", "cluster_id"] + FEATURE_COLUMNS
    if not frames:
        return pd.DataFrame(columns=columns)
    return pd.concat(frames, ignore_index=True)[columns]


def _split_events(
    event_ids: np.ndarray,
    split: tuple[float, float, float],
) -> dict[str, np.ndarray]:
    """Create deterministic train/validation/test event-id splits."""
    if len(split) != 3 or not np.isclose(sum(split), 1.0):
        raise ValueError("split must contain three fractions summing to 1.0")

    unique_events = np.array(sorted(set(int(eid) for eid in event_ids)), dtype=np.int64)
    n_events = len(unique_events)
    n_train = int(n_events * split[0])
    n_val = int(n_events * split[1])
    if n_events and n_train == 0:
        n_train = 1
    if n_events >= 3 and n_val == 0:
        n_val = 1
    if n_train + n_val > n_events:
        n_val = max(0, n_events - n_train)

    return {
        "train": unique_events[:n_train],
        "val": unique_events[n_train : n_train + n_val],
        "test": unique_events[n_train + n_val :],
    }
