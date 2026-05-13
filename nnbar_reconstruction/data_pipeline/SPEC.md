# Spec: data_pipeline package

## Goal

Create `nnbar_reconstruction/data_pipeline/` — a new Python package for loading
simulation output, running clustering, and preparing GNN training data.

## Data Format

Parquet files written by the Geant4 simulation. One set per run directory:

- `TPC_output_0.parquet` — columns: Event_ID, Track_ID, Parent_ID, Name, Proc,
  Step_info, Origin, Current_Vol, Module_ID, Layer_ID, x, y, z, px, py, pz, t,
  KE, eDep, trackl, electrons
- `Particle_output_0.parquet` — primary particle truth: Event_ID, Track_ID,
  Parent_ID, Name, px, py, pz, KE, vx, vy, vz (truth vertex)
- `Scintillator_output_0.parquet` — scintillator hits (same spatial columns)
- `LeadGlass_output_0.parquet` — lead-glass calorimeter hits

Example local data (1 run, small): `/Volumes/MyDrive/nnbar/nnbar/simulation/NNBAR_Detector/output/`
LUNARC production will be at: `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc/output/`

## Files to Create

### `__init__.py`
Exports all public functions from the three modules below.

### `load_simulation_data.py`
- `load_dataset(data_dir: Path) -> dict[str, pd.DataFrame]`
  Loads all parquet files from a single run directory. Keys: `tpc`, `particle`,
  `scintillator`, `leadglass`. Silently skips missing subsystems.
- `load_all_datasets(base_dir: Path, dataset_names: list[str] | None = None) -> dict[str, dict]`
  Loads multiple named run sub-directories under `base_dir`.
- `combine_datasets(datasets: dict, offset_ids: bool = True) -> dict[str, pd.DataFrame]`
  Merges all runs into single DataFrames. When `offset_ids=True`, shifts Event_ID
  in each run so IDs stay unique across the combined set.

### `run_clustering_pipeline.py`
Implements HIBEAM-style adaptive DBSCAN with cylindrical transform.

- `transform_to_cylindrical(xyz, phi_weight=5.0, z_weight=1.0) -> np.ndarray`
- `adaptive_eps(X, k=6, alpha=1.5) -> float`  
  k-NN median distance scaled by alpha.
- `cluster_event(tpc_hits: pd.DataFrame, phi_weight=5.0, z_weight=1.0, k=6, alpha=1.5) -> np.ndarray`
  Returns cluster label array (length = len(tpc_hits)). Label -1 = noise.
- `run_clustering_pipeline(data_dir: Path, output_dir: Path | None = None) -> pd.DataFrame`
  Runs clustering on every event in `data_dir`. Returns candidates DataFrame with
  columns: Event_ID, cluster_id, n_hits, center_x, center_y, center_z,
  dir_x, dir_y, dir_z, length, rms, linearity.
  Saves to `output_dir/candidates.parquet` if output_dir given.

Direction and shape features per cluster come from PCA on the hit positions.

### `prepare_gnn_training_data.py`
- `extract_track_features(tpc_hits: pd.DataFrame, cluster_labels: np.ndarray) -> pd.DataFrame`
  12 features per cluster: dx, dy, dz (bounding box), length (PCA), linearity
  (ratio of first eigenvalue), rms (transverse spread), sphericity (trace ratio),
  highland_theta0 (estimated angular scatter = 13.6 MeV / (KE * sqrt(length))),
  r_surface (radial distance of cluster centroid from beam axis), n_hits,
  charge_sum (sum of electrons column), mean_ke.
- `prepare_gnn_training_data(data_dir: Path, output_dir: Path, split=(0.7,0.15,0.15)) -> dict`
  Full pipeline: load → cluster → extract features → train/val/test split → save NPZ.
  NPZ files: `train.npz`, `val.npz`, `test.npz` each with arrays `X` (features),
  `y` (truth vertex from Particle table), `event_id`.
  Returns dict with counts and file paths.

## Rules

- Each file under 500 lines
- No hardcoded paths — all paths passed as arguments
- Python 3.9+, uses pandas, numpy, scikit-learn (all in hibeam_env)
- No new dependencies
- Reference existing clustering code for style:
  `nnbar_reconstruction/tracking/clustering.py`
