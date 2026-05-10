from __future__ import annotations

import json

from nnbar_reconstruction.data_pipeline.synthetic import make_synthetic_tpc_hits
from scripts.run_reco_pipeline import (
    SUMMARY_KEYS,
    cluster_tpc_hits,
    load_tpc_hits,
    run_pipeline,
)


def test_load_empty_returns_empty_dataframe(tmp_path):
    hits = load_tpc_hits(tmp_path)

    assert hits.shape == (0, 8)
    assert list(hits.columns) == [
        "Event_ID",
        "x",
        "y",
        "z",
        "time",
        "edep",
        "particle_id",
        "track_id",
    ]


def test_clustering_on_synthetic_hits(tmp_path):
    hits = make_synthetic_tpc_hits(n_events=1, hits_per_event=50)

    candidates = cluster_tpc_hits(hits, tmp_path)

    assert "cluster_id" in candidates.columns
    assert len(candidates) >= 1


def test_pipeline_produces_summary(tmp_path):
    output_dir = tmp_path / "output"

    summary = run_pipeline(tmp_path / "missing-data", output_dir, n_events=10)

    summary_path = output_dir / "summary.json"
    assert summary_path.is_file()
    assert set(SUMMARY_KEYS).issubset(summary)
    assert set(SUMMARY_KEYS).issubset(json.loads(summary_path.read_text()))
    assert summary["n_events_loaded"] == 10
    assert set(summary["timing_seconds"]) == {"load", "clustering", "gnn_prep"}
