# NNBAR Reconstruction Improvement Task

## Project Overview

Improve the NNBAR particle physics reconstruction pipeline, focusing on TPC track reconstruction and vertex finding using GNN and ML algorithms. The goal is to enhance reconstruction efficiency and accuracy for multi-pion annihilation events.

## Current State

### Available Simulation Data
- **baseline_reference**: 980 events (primary dataset at `/home/billy/nnbar/simulation/NNBAR_Detector/build/output/baseline_reference/`)
- **sig_pip_test**: 87 events
- **test_signal**: 5 events
- **test_gun**: 6 events

### How to Generate More Data
The MCPL input file contains 100,000 annihilation events. To generate more:
```bash
cd /home/billy/nnbar/simulation/NNBAR_Detector/build
# Edit macro/signal/run_signal_100k.mac to change folder_name and beamOn count
./nnbar-detector-simulation macro/signal/run_signal_100k.mac
```

### Typical Event Structure (Event 967 example)
- TPC hits: 1075 total
- Unique tracks: 20
- Primary pions (Parent_ID=0): 5 tracks (pi+, pi-)
- Truth vertex: (-2.2, -12.1, 0.0) cm
- Signal tracks: pi+, pi- with Parent_ID=0 point back to vertex
- Background: secondary protons, spallation products (Mg26, Al27)
- Key insight: Only use Parent_ID=0 charged particles for vertex fit

### Data Format (Parquet files per dataset)
- `TPC_output_0.parquet`: Columns = Event_ID, Track_ID, Parent_ID, Name, Proc, Step_info, Origin, Current_Vol, Module_ID, Layer_ID, x, y, z, px, py, pz, t, KE, eDep, trackl, electrons
- `Particle_output_0.parquet`: Primary particle info with truth vertex
- `Scintillator_output_0.parquet`: Scintillator hits
- `LeadGlass_output_0.parquet`: Lead glass calorimeter hits

### Existing Implementation (in nnbar_reconstruction/)
- `tracking/clustering.py`: Adaptive DBSCAN clustering (831 lines)
- `tracking/track_fitting.py`: PCA line fitting (634 lines)
- `vertex/gnn_model.py`: GNN vertex model (689 lines)
- `vertex/classical_vertex.py`: Weighted projection vertex (425 lines)
- `training/prepare_training_data.py`: Basic data prep (486 lines)
- `models/psignal/best.ckpt`: Trained signal classifier (120KB)
- `models/vertex_gnn/best.ckpt`: Trained vertex GNN (2.1MB)

### HIBEAM Reference (at /home/billy/nnbar/simulation/HIBEAM_Clustering_and_Vertex/)
The HIBEAM project provides proven algorithms that should be adapted:
- `run_nnbar_clustering.py`: Complete clustering pipeline with refinement
- `config_nnbar.yaml`: NNBAR-specific configuration
- `gnn_pipeline/`: GNN model architecture and training
- Key techniques: cylindrical coordinate transform, bimodality splitting, collinear merging

## Tasks to Complete

### Phase 1: Enhanced Data Preparation Pipeline

Create `/home/billy/nnbar/simulation/nnbar_reconstruction/data_pipeline/` with:

1. **`load_simulation_data.py`**
   - Load all available simulation datasets
   - Combine baseline_reference (980 events) + sig_pip_test (87 events)
   - Proper event ID management across datasets
   - Output: Combined parquet files ready for processing

2. **`run_clustering_pipeline.py`**
   - Implement HIBEAM-style clustering with refinements
   - Use cylindrical coordinate transform (phi_weight=5.0, z_weight=1.0)
   - Apply z-gap splitting, perpendicular bimodality splitting
   - Apply collinear fragment merging
   - Generate candidates.parquet with: cluster_id, n_hits, vx, vy, vz, length, rms, linearity, center_x/y/z, dir_x/y/z
   - Save clustering labels for evaluation

3. **`prepare_gnn_training_data.py`**
   - Process clustered data into GNN training format
   - Extract 12+ features per track candidate (from HIBEAM):
     - Spatial: dx, dy, dz, length
     - Shape: linearity, rms, sphericity
     - Physics: highland_theta0, r_surface
   - Create train/val/test splits (70/15/15)
   - Save as NPZ and/or PyTorch .pt files
   - Target: process ALL 1067 events

4. **`evaluate_clustering.py`**
   - Compute clustering metrics vs true Track_ID labels:
     - Purity: fraction of clusters with single true track
     - Efficiency: fraction of true track hits in correct cluster
     - Adjusted Rand Index
     - V-measure
   - Output summary report

### Phase 2: Enhanced GNN Vertex Model

Update `/home/billy/nnbar/simulation/nnbar_reconstruction/vertex/`:

5. **Update `gnn_model.py`** (or create `gnn_model_v2.py`)
   - Add uncertainty estimation heads (predict sigma for vx, vy, vz)
   - Add coordinate-specific loss weighting (x/y typically less certain than z)
   - Implement log-cosh loss (more robust than MSE)
   - Support for mixed-precision training (AMP)
   - Architecture: Multi-head cross-attention with residual MLPs (keep existing, enhance)

6. **Create `train_vertex_gnn.py`**
   - Load prepared training data
   - Train with proper hyperparameters:
     - batch_size: 64
     - learning_rate: 0.001 with cosine schedule
     - epochs: 100 with early stopping (patience=20)
     - loss: log-cosh
   - Save best model checkpoint
   - Generate training curves

7. **Create `evaluate_vertex.py`**
   - Compute vertex resolution: RMS of (pred - true) for x, y, z
   - Generate residual plots
   - Compute metrics on test set
   - Compare GNN vs classical method

### Phase 3: Clustering Improvements

Update `/home/billy/nnbar/simulation/nnbar_reconstruction/tracking/`:

8. **Update `clustering.py`**
   - Add HDBSCAN as alternative algorithm (via sklearn or cuml)
   - Implement multi-scale clustering for varying track densities
   - Add proper logging and progress bars
   - GPU acceleration via cuML when available

9. **Create `clustering_config.yaml`**
   - Centralized configuration for clustering parameters
   - DBSCAN: alpha, min_samples, k, phi_weight, z_weight
   - HDBSCAN: min_cluster_size, min_samples
   - Refinement: gap_threshold, d_thresh, angle_thresh_deg

### Phase 4: Integration and Evaluation

10. **Create `scripts/run_full_pipeline.py`**
    - End-to-end reconstruction pipeline:
      1. Load simulation data
      2. Run clustering
      3. Run track fitting
      4. Run vertex reconstruction (classical + GNN)
      5. Compute all metrics
    - Output comprehensive results report

11. **Create `scripts/benchmark.py`**
    - Compare reconstruction approaches:
      - DBSCAN vs HDBSCAN clustering
      - Classical vs GNN vertex
      - With/without refinement steps
    - Generate comparison tables and plots

## Quality Gates

The implementation is considered successful if:

1. **Data Pipeline**: Processes all 1067 events without errors
2. **Clustering Purity**: > 90% (fraction of pure clusters)
3. **Clustering Efficiency**: > 90% (fraction of hits correctly assigned)
4. **Vertex Resolution (GNN)**: < 15 cm RMS in each coordinate
5. **Code Quality**: All Python files pass syntax check, proper docstrings

## File Structure

```
nnbar_reconstruction/
├── data_pipeline/           # NEW
│   ├── __init__.py
│   ├── load_simulation_data.py
│   ├── run_clustering_pipeline.py
│   ├── prepare_gnn_training_data.py
│   └── evaluate_clustering.py
├── tracking/
│   ├── clustering.py        # ENHANCE
│   └── clustering_config.yaml  # NEW
├── vertex/
│   ├── gnn_model.py         # ENHANCE
│   ├── train_vertex_gnn.py  # NEW
│   └── evaluate_vertex.py   # NEW
├── scripts/
│   ├── run_full_pipeline.py # NEW
│   └── benchmark.py         # NEW
└── config/
    └── nnbar_geometry.yaml  # EXISTS
```

## Important Notes

1. **Use HIBEAM as reference** - The patterns in `/home/billy/nnbar/simulation/HIBEAM_Clustering_and_Vertex/` are proven to work
2. **Process the large dataset** - baseline_reference has 980 events, this is the primary training data
3. **Track ID is truth label** - In simulation data, Track_ID defines the true cluster
4. **Parent_ID = 0 means primary** - Primary particles from annihilation have Parent_ID = 0
5. **Signal particles**: pi+, pi-, proton, K+, K- with Parent_ID = 0
6. **Target z=0** - Vertex is at z=0 (target plane)
7. **Python 3.9+** compatible code

## Example Code Patterns

### Loading TPC data:
```python
import pandas as pd
from pathlib import Path

data_dir = Path("/home/billy/nnbar/simulation/NNBAR_Detector/build/output/baseline_reference")
tpc_data = pd.read_parquet(data_dir / "TPC_output_0.parquet")
particle_data = pd.read_parquet(data_dir / "Particle_output_0.parquet")
```

### Cylindrical transform (from HIBEAM):
```python
def transform_to_cylindrical(xyz, phi_weight=5.0, z_weight=1.0):
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    r = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return np.column_stack([r, phi * phi_weight, z * z_weight])
```

### Adaptive epsilon:
```python
from sklearn.neighbors import NearestNeighbors

def adaptive_eps(X, k=6, alpha=1.5):
    nbrs = NearestNeighbors(n_neighbors=k+1).fit(X)
    dists, _ = nbrs.kneighbors(X)
    return alpha * np.median(dists[:, 1:])
```
