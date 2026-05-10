# Lane: reco-pipeline

## Goal

Write an end-to-end reconstruction pipeline runner and a validation test that
exercises the signal Parquet data through all reconstruction stages.

## Repo

Work in: `/Volumes/MyDrive/nnbar/nnbar/simulation/`
Branch: `lane/reco-pipeline`

## What exists already (read these before writing anything)

- `nnbar_reconstruction/data_pipeline/load_simulation_data.py` — loads Parquet files
- `nnbar_reconstruction/data_pipeline/run_clustering_pipeline.py` — runs clustering
- `nnbar_reconstruction/data_pipeline/prepare_gnn_training_data.py` — prepares GNN data
- `nnbar_reconstruction/tracking/clustering.py` — HDBSCAN + GPU DBSCAN clustering
- `nnbar_reconstruction/tracking/clustering_config.yaml` — clustering parameters

## Signal data location (local copy, rsync from LUNARC)

Data will be at: `data/signal_test/` (relative to repo root).
If the directory doesn't exist, write the script to accept a `--data-dir` CLI argument
and use a synthetic test dataset when no real data is available.

## Files to produce

### 1. `scripts/run_reco_pipeline.py`

End-to-end runner. CLI:
```
python scripts/run_reco_pipeline.py \
    --data-dir data/signal_test/ \
    --output-dir output/reco/ \
    --n-events 100
```

Steps:
1. Load signal Parquet files from `--data-dir` using `load_simulation_data.py`
2. Run clustering on TPC hits using `run_clustering_pipeline.py`
3. Prepare GNN training data using `prepare_gnn_training_data.py`
4. Write summary JSON: `output/reco/summary.json` with:
   - n_events_loaded, n_events_clustered, n_tracks_total, mean_tracks_per_event
   - Timing: seconds per stage

### 2. `tests/test_reco_pipeline.py`

Pytest tests that run with synthetic data (no real Parquet files needed):
- `test_load_empty_returns_empty_dataframe()` — load from empty dir, check shape
- `test_clustering_on_synthetic_hits()` — create 50 synthetic TPC hits, run clustering, check output has 'cluster_id' column
- `test_pipeline_produces_summary()` — run full pipeline on 10 synthetic events, check summary.json keys

### 3. `nnbar_reconstruction/data_pipeline/synthetic.py`

Synthetic data generator for tests:
```python
def make_synthetic_tpc_hits(n_events: int, hits_per_event: int = 20) -> pd.DataFrame:
    """Generate random TPC hits for pipeline testing."""
```

Columns must match real TPC_output_*.parquet schema:
`Event_ID, x, y, z, time, edep, particle_id, track_id`

## Synthetic data schema (from actual Parquet output on LUNARC)

The signal run produced these files: `TPC_output_0.parquet`, `Silicon_output_0.parquet`,
`Scintillator_output_0.parquet`, `LeadGlass_output_0.parquet`, etc.
Use the TPC file as the primary reconstruction input.

Minimal column set needed for clustering:
- `Event_ID` (int64)
- `x`, `y`, `z` (float64, mm)
- `time` (float64, ns)
- `edep` (float64, MeV)

## Iteration cycle

1. Read the existing reconstruction modules listed above
2. Write the three files
3. Run: `python -m pytest tests/test_reco_pipeline.py -v 2>&1 | tail -20`
4. Fix until all tests pass
5. Commit on `lane/reco-pipeline`, then merge to main via:
   `bash /Volumes/MyDrive/nnbar/nnbar/simulation/scripts/codex-supervisor/merge.sh lane/reco-pipeline`

## Commit format

```
feat(reco): add end-to-end pipeline runner and pytest suite

Lane: reco-pipeline
```

## Stop condition

Stop when all tests pass and commit is merged. Write "DONE: reco-pipeline merged to main" to stdout.

## Constraints

- Max 500 lines per file
- No GPU required — clustering falls back to CPU HDBSCAN if no CUDA device
- Use pathlib everywhere, not os.path
- No hardcoded LUNARC paths
