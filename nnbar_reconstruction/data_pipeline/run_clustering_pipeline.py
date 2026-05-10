"""Run adaptive DBSCAN clustering on TPC hits.

The pipeline uses the HIBEAM-style cylindrical coordinate transform from the
lane spec, computes a per-event adaptive DBSCAN epsilon, and summarises each
cluster with PCA-derived direction and shape features.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

from .load_simulation_data import load_dataset


_CANDIDATE_COLUMNS = [
    "Event_ID",
    "cluster_id",
    "n_hits",
    "center_x",
    "center_y",
    "center_z",
    "dir_x",
    "dir_y",
    "dir_z",
    "length",
    "rms",
    "linearity",
]


def transform_to_cylindrical(
    xyz: np.ndarray,
    phi_weight: float = 5.0,
    z_weight: float = 1.0,
) -> np.ndarray:
    """Transform Cartesian positions to weighted cylindrical coordinates."""
    xyz = np.asarray(xyz, dtype=float)
    if xyz.size == 0:
        return np.empty((0, 3), dtype=float)
    if xyz.ndim != 2 or xyz.shape[1] != 3:
        raise ValueError("xyz must have shape (N, 3)")

    x = xyz[:, 0]
    y = xyz[:, 1]
    z = xyz[:, 2]
    r = np.sqrt(x * x + y * y)
    phi = np.arctan2(y, x)
    return np.column_stack((r, phi * phi_weight, z * z_weight))


def adaptive_eps(X: np.ndarray, k: int = 6, alpha: float = 1.5) -> float:
    """Estimate DBSCAN epsilon as alpha times median k-neighbour distance."""
    X = np.asarray(X, dtype=float)
    if len(X) <= 1:
        return 0.1

    n_neighbors = min(k + 1, len(X))
    neighbor_index = n_neighbors - 1
    nearest = NearestNeighbors(n_neighbors=n_neighbors)
    nearest.fit(X)
    distances, _ = nearest.kneighbors(X)
    eps = alpha * float(np.median(distances[:, neighbor_index]))
    return max(eps, 0.1)


def cluster_event(
    tpc_hits: pd.DataFrame,
    phi_weight: float = 5.0,
    z_weight: float = 1.0,
    k: int = 6,
    alpha: float = 1.5,
) -> np.ndarray:
    """Cluster one event's TPC hits and return one label per hit."""
    if tpc_hits.empty:
        return np.empty(0, dtype=np.int32)
    if len(tpc_hits) < 3:
        return np.full(len(tpc_hits), -1, dtype=np.int32)

    xyz = tpc_hits[["x", "y", "z"]].to_numpy(dtype=float)
    transformed = transform_to_cylindrical(
        xyz,
        phi_weight=phi_weight,
        z_weight=z_weight,
    )
    eps = adaptive_eps(transformed, k=k, alpha=alpha)
    labels = DBSCAN(eps=eps, min_samples=3).fit_predict(transformed)
    return labels.astype(np.int32, copy=False)


def _cluster_shape(points: np.ndarray) -> dict[str, float]:
    """Compute center, principal direction, length, RMS, and linearity."""
    center = points.mean(axis=0)
    if len(points) < 2:
        direction = np.array([0.0, 0.0, 1.0])
        return _shape_row(center, direction, 0.0, 0.0, 0.0)

    centered = points - center
    try:
        _, singular_values, components = np.linalg.svd(centered, full_matrices=False)
    except np.linalg.LinAlgError:
        direction = np.array([0.0, 0.0, 1.0])
        return _shape_row(center, direction, 0.0, 0.0, 0.0)

    direction = components[0]
    projections = centered @ direction
    length = float(projections.max() - projections.min())
    residuals = centered - np.outer(projections, direction)
    rms = float(np.sqrt(np.mean(np.sum(residuals * residuals, axis=1))))

    eigenvalues = (singular_values * singular_values) / max(len(points) - 1, 1)
    total_variance = float(eigenvalues.sum())
    linearity = 0.0 if total_variance <= 0.0 else float(eigenvalues[0] / total_variance)
    return _shape_row(center, direction, length, rms, linearity)


def _shape_row(
    center: np.ndarray,
    direction: np.ndarray,
    length: float,
    rms: float,
    linearity: float,
) -> dict[str, float]:
    """Create a serialisable cluster-shape row fragment."""
    return {
        "center_x": float(center[0]),
        "center_y": float(center[1]),
        "center_z": float(center[2]),
        "dir_x": float(direction[0]),
        "dir_y": float(direction[1]),
        "dir_z": float(direction[2]),
        "length": float(length),
        "rms": float(rms),
        "linearity": float(linearity),
    }


def _candidate_rows(
    event_id: int,
    event_hits: pd.DataFrame,
    labels: np.ndarray,
) -> list[dict[str, float | int]]:
    """Build candidate rows for all non-noise clusters in one event."""
    rows: list[dict[str, float | int]] = []
    xyz = event_hits[["x", "y", "z"]].to_numpy(dtype=float)
    for cluster_id in sorted(label for label in np.unique(labels) if label >= 0):
        mask = labels == cluster_id
        shape = _cluster_shape(xyz[mask])
        row: dict[str, float | int] = {
            "Event_ID": int(event_id),
            "cluster_id": int(cluster_id),
            "n_hits": int(mask.sum()),
        }
        row.update(shape)
        rows.append(row)
    return rows


def run_clustering_pipeline(
    data_dir: Path,
    output_dir: Path | None = None,
) -> pd.DataFrame:
    """Run clustering for every TPC event in *data_dir*.

    If ``output_dir`` is provided, candidates are saved to
    ``output_dir/candidates.parquet``.
    """
    dataset = load_dataset(Path(data_dir))
    tpc_hits = dataset.get("tpc")
    if tpc_hits is None or tpc_hits.empty:
        candidates = pd.DataFrame(columns=_CANDIDATE_COLUMNS)
    else:
        rows: list[dict[str, float | int]] = []
        for event_id, event_hits in tpc_hits.groupby("Event_ID", sort=True):
            labels = cluster_event(event_hits)
            rows.extend(_candidate_rows(int(event_id), event_hits, labels))
        candidates = pd.DataFrame(rows, columns=_CANDIDATE_COLUMNS)

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        candidates.to_parquet(output_path / "candidates.parquet", index=False)
    return candidates
