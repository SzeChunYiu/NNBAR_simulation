"""Run the end-to-end NNBAR reconstruction data pipeline."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nnbar_reconstruction.data_pipeline.load_simulation_data import load_dataset
from nnbar_reconstruction.data_pipeline.prepare_gnn_training_data import (
    prepare_gnn_training_data,
)
from nnbar_reconstruction.data_pipeline.run_clustering_pipeline import (
    run_clustering_pipeline,
)
from nnbar_reconstruction.data_pipeline.synthetic import (
    TPC_COLUMNS,
    make_empty_tpc_hits,
    make_synthetic_tpc_hits,
)


SUMMARY_KEYS = (
    "n_events_loaded",
    "n_events_clustered",
    "n_tracks_total",
    "mean_tracks_per_event",
    "timing_seconds",
)


def load_tpc_hits(data_dir: Path, n_events: int | None = None) -> pd.DataFrame:
    """Load TPC hits from simulation parquet files, returning empty schema if absent."""
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        return make_empty_tpc_hits()

    dataset = load_dataset(data_dir)
    tpc_hits = dataset.get("tpc")
    if tpc_hits is None or tpc_hits.empty:
        return make_empty_tpc_hits()

    missing = [column for column in TPC_COLUMNS if column not in tpc_hits.columns]
    if missing:
        raise ValueError(f"TPC data is missing required columns: {missing}")

    return _limit_events(tpc_hits.copy(), n_events)


def cluster_tpc_hits(tpc_hits: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    """Run the existing clustering pipeline on an in-memory TPC hit table."""
    output_dir = Path(output_dir)
    staging_dir = output_dir / "_cluster_input"
    clustering_dir = output_dir / "clustering"
    _write_tpc_stage_input(tpc_hits, staging_dir)
    return run_clustering_pipeline(staging_dir, clustering_dir)


def run_pipeline(data_dir: Path, output_dir: Path, n_events: int = 100) -> dict[str, Any]:
    """Run load, clustering, and GNN-preparation stages and write summary JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timings: dict[str, float] = {}

    start = time.perf_counter()
    tpc_hits = load_tpc_hits(Path(data_dir), n_events=n_events)
    if tpc_hits.empty and n_events > 0:
        tpc_hits = make_synthetic_tpc_hits(n_events=n_events)
    timings["load"] = time.perf_counter() - start

    start = time.perf_counter()
    candidates = cluster_tpc_hits(tpc_hits, output_dir)
    timings["clustering"] = time.perf_counter() - start

    start = time.perf_counter()
    if tpc_hits.empty:
        gnn_result: dict[str, Any] = {
            "counts": {"train": 0, "val": 0, "test": 0, "total": 0},
            "files": {},
            "feature_columns": [],
        }
    else:
        gnn_input_dir = output_dir / "_gnn_input"
        _write_tpc_stage_input(tpc_hits, gnn_input_dir)
        _write_particle_truth(data_dir=Path(data_dir), tpc_hits=tpc_hits, output_dir=gnn_input_dir)
        gnn_result = prepare_gnn_training_data(gnn_input_dir, output_dir / "gnn")
    timings["gnn_prep"] = time.perf_counter() - start

    n_events_loaded = _n_unique_events(tpc_hits)
    n_events_clustered = _n_unique_events(candidates)
    n_tracks_total = int(len(candidates))
    mean_tracks_per_event = (
        float(n_tracks_total / n_events_clustered) if n_events_clustered else 0.0
    )
    summary: dict[str, Any] = {
        "n_events_loaded": n_events_loaded,
        "n_events_clustered": n_events_clustered,
        "n_tracks_total": n_tracks_total,
        "mean_tracks_per_event": mean_tracks_per_event,
        "timing_seconds": {
            stage: round(seconds, 6) for stage, seconds in timings.items()
        },
        "gnn": gnn_result,
    }

    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def _limit_events(tpc_hits: pd.DataFrame, n_events: int | None) -> pd.DataFrame:
    """Keep the first *n_events* Event_ID groups in stable sorted order."""
    if n_events is None or n_events < 0 or tpc_hits.empty:
        return tpc_hits
    event_ids = sorted(tpc_hits["Event_ID"].dropna().unique())[:n_events]
    return tpc_hits[tpc_hits["Event_ID"].isin(event_ids)].reset_index(drop=True)


def _write_tpc_stage_input(tpc_hits: pd.DataFrame, output_dir: Path) -> None:
    """Materialise TPC hits as a parquet input consumed by existing stages."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = tpc_hits.copy()
    if frame.empty:
        frame = make_empty_tpc_hits()
    frame.to_parquet(output_dir / "TPC_output_0.parquet", index=False)


def _write_particle_truth(data_dir: Path, tpc_hits: pd.DataFrame, output_dir: Path) -> None:
    """Write particle truth parquet, using real truth when present."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    particle_truth = _load_particle_truth(data_dir)
    event_ids = sorted(int(event_id) for event_id in tpc_hits["Event_ID"].unique())
    if particle_truth is None or particle_truth.empty:
        particle_truth = _synthetic_particle_truth(event_ids)
    else:
        particle_truth = particle_truth[particle_truth["Event_ID"].isin(event_ids)].copy()
        if particle_truth.empty:
            particle_truth = _synthetic_particle_truth(event_ids)
    particle_truth.to_parquet(output_dir / "Particle_output_0.parquet", index=False)


def _load_particle_truth(data_dir: Path) -> pd.DataFrame | None:
    """Load particle truth if the input directory provides it."""
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        return None
    return load_dataset(data_dir).get("particle")


def _synthetic_particle_truth(event_ids: list[int]) -> pd.DataFrame:
    """Create a minimal truth-vertex table for GNN preparation."""
    return pd.DataFrame(
        {
            "Event_ID": np.asarray(event_ids, dtype=np.int64),
            "vx": np.zeros(len(event_ids), dtype=np.float64),
            "vy": np.zeros(len(event_ids), dtype=np.float64),
            "vz": np.zeros(len(event_ids), dtype=np.float64),
        }
    )


def _n_unique_events(frame: pd.DataFrame) -> int:
    """Count unique Event_ID values in a frame."""
    if frame.empty or "Event_ID" not in frame:
        return 0
    return int(frame["Event_ID"].nunique())


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/signal_test"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/reco"))
    parser.add_argument("--n-events", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = _parse_args()
    summary = run_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        n_events=args.n_events,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
