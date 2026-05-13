# NNBAR Reconstruction Model Training Plan

**Date:** 2026-01-12
**Author:** Claude-Architect
**Status:** Planning

---

## 1. Overview

The current reconstruction pipeline includes three components that require training/tuning on NNBAR-specific data:

| Component | Type | Current Status | Training Data Needed |
|-----------|------|----------------|---------------------|
| DBSCAN Clustering | Parameter-based | Default params | Labeled clusters from truth |
| P-Signal Classifier | Neural Network | Model structure only, no weights | Signal/background track labels |
| Vertex GNN | Neural Network | Model structure only, no weights | Truth vertex positions |

### 1.1 Key Physics Considerations

**Beampipe Interactions (Critical):**
- Primary particles (pions, protons) may decay or scatter in the beampipe before reaching TPC
- Charged pions: τ = 26 ns, cτ = 7.8 m (may decay to μ + ν)
- Multiple scattering in Al beampipe (2 cm thick): θ₀ ≈ 13.6/p × √(x/X₀)
- Direction at TPC entry may differ from direction at annihilation vertex

**Signal Characteristics:**
- Annihilation vertex at z ≈ 0 (target foil)
- Radial position r ≈ 0-10 cm (inside beampipe)
- Multiple charged tracks (typically 3-7 pions)
- Total energy ≈ 2 × 939 MeV = 1878 MeV
- Spherical topology (isotropic in CM frame)

---

## 2. Training Dataset Preparation

### 2.1 Dataset Sources

**Baseline Dataset:** `/home/billy/nnbar/simulation/NNBAR_Detector/build/output/baseline_reference/`
- 1000 annihilation events
- TPC, Scintillator, Lead Glass hits
- Particle truth information (Name, Track_ID, Parent_ID, Origin)

### 2.2 Truth Information Extraction

From the Parquet output files, we can extract:

```python
# TPC hits with truth labels
TPC_output_0.parquet columns:
- Event_ID, Track_ID, Parent_ID: Particle identification
- Name: Particle type (pi+, pi-, proton, e-, etc.)
- Proc: Creation process
- Origin: Origin volume
- x, y, z, t: Position and time
- KE, eDep: Kinematics
- Module_ID, Layer_ID: Detector indices

# Primary particles (for vertex truth)
Particle_output_0.parquet columns:
- Event_ID, PID, Name
- x, y, z, t: Vertex position (TRUTH VERTEX)
- KE, angle: Kinematics
```

### 2.3 Truth Labeling Strategy

#### For Clustering:
- **True cluster** = all hits from the same Track_ID
- **Cluster quality metrics:**
  - Purity = hits from dominant Track_ID / total hits
  - Completeness = cluster hits / all hits from that Track_ID

#### For P-Signal:
- **Signal track** = Track originates from annihilation (Parent_ID == 0 OR Origin near beampipe center)
- **Background track** = Compton scatters, δ-rays, secondaries from material interactions
- **Edge case:** Decay products of primary pions (μ from π→μν) - classify as signal since they carry kinematic information

#### For Vertex:
- **Truth vertex** = (x, y, z) from Particle_output where Event_ID matches and parent is the annihilation
- Typically should be at z ≈ 0, r < 10 cm

---

## 3. Beampipe Interaction Study

### 3.1 Effects to Quantify

| Effect | Observable | Expected Magnitude |
|--------|------------|-------------------|
| Pion decay | μ track with kink | ~5% of π± before TPC |
| Multiple scattering | Direction spread | θ₀ ~ 0.5-5° depending on p |
| Energy loss | dE/dx in beampipe | ~2-10 MeV |
| Nuclear interactions | Hadronic shower | ~10% of pions |
| Secondary production | Extra tracks | Variable |

### 3.2 Study Methodology

1. **Compare track direction at TPC entry vs truth vertex direction**
   ```python
   # For each primary track:
   truth_direction = (TPC_entry_point - vertex) / |...|
   track_direction = PCA_direction_from_TPC_hits
   angle_deviation = arccos(dot(truth_direction, track_direction))
   ```

2. **Track integrity check**
   - Count hits per primary particle
   - Identify tracks that are split or missing hits

3. **Backprojection study**
   - Project tracks back to z=0
   - Measure miss distance from truth vertex

### 3.3 Algorithm Adaptations

Based on beampipe effects, the algorithms may need:

1. **Clustering:**
   - Larger tolerance for direction changes
   - Don't split clusters at kinks (could be scattering)
   - Consider hits in beampipe region separately

2. **P-Signal:**
   - Features should be robust to direction changes
   - Include track origin volume as feature
   - Consider μ from π decay as signal

3. **Vertex:**
   - Weighted fit with uncertainty from scattering
   - Constrain to beampipe volume
   - Use multiple-track intersection robustly

---

## 4. Clustering Parameter Optimization

### 4.1 Parameters to Optimize

| Parameter | Current | Purpose | Range |
|-----------|---------|---------|-------|
| `phi_weight` | 5.0 | Angular separation | [1.0, 10.0] |
| `z_weight` | 1.0 | Z separation | [0.5, 2.0] |
| `min_samples` | 3 | Core point threshold | [2, 5] |
| `alpha` | 1.5 | Adaptive epsilon scale | [1.0, 3.0] |
| `k` | 6 | k-NN for adaptive eps | [4, 10] |
| `gap_threshold` | 6.0 cm | Z-gap splitting | [3.0, 10.0] |
| `angle_threshold` | 0.7 | Direction splitting | [0.5, 0.9] |
| `ashman_threshold` | 2.0 | Bimodality split | [1.5, 3.0] |

### 4.2 Optimization Metric

```python
def clustering_score(labels_pred, labels_true):
    """
    Combined metric balancing purity and completeness.

    Purity: Fraction of hits correctly assigned within each cluster
    Completeness: Fraction of true clusters recovered
    """
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

    # Adjusted Rand Index ([-1, 1], 1 = perfect)
    ari = adjusted_rand_score(labels_true, labels_pred)

    # Normalized Mutual Information ([0, 1], 1 = perfect)
    nmi = normalized_mutual_info_score(labels_true, labels_pred)

    # Combined score
    return 0.5 * (ari + 1) + 0.5 * nmi  # [0, 1]
```

### 4.3 Optimization Strategy

1. **Grid search** on baseline dataset for initial values
2. **Bayesian optimization** (Optuna) for fine-tuning
3. **Cross-validation** across different event types

---

## 5. P-Signal Model Training

### 5.1 Model Architecture

Use **PointNetMini** (simpler, sufficient for mostly-linear tracks):
- Input: (N, 3) normalized hit coordinates
- Per-point MLP: 3 → 64 → 64 → 128
- Global max pooling
- Classification head: 128 → 128 → 1

### 5.2 Training Data Format

```python
@dataclass
class TrackSample:
    event_id: int
    track_id: int
    hits: np.ndarray  # (N, 3) coordinates
    label: int  # 1 = signal, 0 = background

    # Optional metadata
    particle_type: str
    parent_id: int
    ke: float
    origin: str
```

### 5.3 Training Pipeline

```python
# Pseudocode for training
def prepare_psignal_dataset(baseline_dir):
    """Extract labeled tracks from simulation output."""

    tpc_data = pd.read_parquet(f"{baseline_dir}/TPC_output_0.parquet")
    particle_data = pd.read_parquet(f"{baseline_dir}/Particle_output_0.parquet")

    samples = []
    for event_id in tpc_data['Event_ID'].unique():
        event_tpc = tpc_data[tpc_data['Event_ID'] == event_id]

        for track_id in event_tpc['Track_ID'].unique():
            track_hits = event_tpc[event_tpc['Track_ID'] == track_id]

            if len(track_hits) < 3:
                continue

            # Determine if signal or background
            parent_id = track_hits.iloc[0]['Parent_ID']
            origin = track_hits.iloc[0]['Origin']

            # Signal: primary particles or their immediate decay products
            is_signal = (parent_id == 0) or (origin in ['Carbon_target', 'Beampipe'])

            samples.append(TrackSample(
                event_id=event_id,
                track_id=track_id,
                hits=track_hits[['x', 'y', 'z']].values,
                label=1 if is_signal else 0,
                ...
            ))

    return samples

# Training loop
def train_psignal_model(samples, epochs=100):
    model = PointNetMini(hidden=64, emb=128)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.BCEWithLogitsLoss()

    for epoch in range(epochs):
        for batch in dataloader(samples):
            optimizer.zero_grad()
            logits = model(batch.hits, batch.mask)
            loss = criterion(logits, batch.labels)
            loss.backward()
            optimizer.step()
```

### 5.4 Training Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Learning rate | 1e-3 | With cosine decay |
| Batch size | 64 | Tracks per batch |
| Epochs | 100 | Early stopping |
| Hidden dim | 64 | |
| Embedding dim | 128 | |
| Dropout | 0.1 | |
| Weight decay | 1e-4 | |

---

## 6. Vertex GNN Training

### 6.1 Model Architecture

Use **NNBARVertexGNN** (v1):
- Candidate encoder: Residual MLP (12 → 128)
- Cross-attention pooling (4 heads)
- Position encoding for anchor
- Separate coordinate heads (x, y, z)

### 6.2 Training Data Format

```python
@dataclass
class VertexSample:
    event_id: int
    cand_vxyz: np.ndarray  # (C, 3) candidate vertices
    cand_feat: np.ndarray  # (C, 12) candidate features
    cand_mask: np.ndarray  # (C,) valid mask
    truth_vertex: np.ndarray  # (3,) truth position
```

### 6.3 Feature Extraction (12 features)

```python
def extract_candidate_features(track_hits):
    """Extract 12 features for vertex GNN input."""
    # Spatial extent (3)
    dx = hits[:, 0].max() - hits[:, 0].min()
    dy = hits[:, 1].max() - hits[:, 1].min()
    dz = hits[:, 2].max() - hits[:, 2].min()

    # PCA shape (4)
    eigvals = pca_eigenvalues(hits)
    elongation_1 = (eigvals[0] - eigvals[1]) / eigvals[0]
    elongation_2 = (eigvals[1] - eigvals[2]) / eigvals[0]
    sphericity = eigvals[2] / eigvals[0]
    dominant_mode = eigvals[0] / eigvals.sum()

    # Density (1)
    volume = dx * dy * dz
    density = np.log(len(hits) / volume)

    # Time spread (1) - set to 0 if no timing
    time_std = 0.0

    # Physics (3)
    x_over_X0 = 0.0  # Material info
    highland_theta0 = scattering_angle_estimate(hits)
    r_surface = np.sqrt(centroid[0]**2 + centroid[1]**2)

    return np.array([dx, dy, dz, elongation_1, elongation_2, sphericity,
                     dominant_mode, density, time_std, x_over_X0,
                     highland_theta0, r_surface])
```

### 6.4 Training Pipeline

```python
def prepare_vertex_dataset(baseline_dir):
    """Prepare vertex training samples."""

    tpc_data = pd.read_parquet(f"{baseline_dir}/TPC_output_0.parquet")
    particle_data = pd.read_parquet(f"{baseline_dir}/Particle_output_0.parquet")

    samples = []
    for event_id in tpc_data['Event_ID'].unique():
        # Get truth vertex from primary particles
        primaries = particle_data[
            (particle_data['Event_ID'] == event_id)
        ]
        if len(primaries) == 0:
            continue

        truth_vertex = primaries[['x', 'y', 'z']].iloc[0].values

        # Cluster hits and fit tracks
        event_tpc = tpc_data[tpc_data['Event_ID'] == event_id]
        labels, clustered = cluster_tpc_hits(event_tpc)
        tracks = fit_all_tracks(clustered, labels)

        if len(tracks) < 2:
            continue

        # Extract candidates
        cand_vxyz = []
        cand_feat = []
        for track in tracks:
            # Project track to z=0
            projected_vertex = project_track_to_z(track, z=0)
            cand_vxyz.append(projected_vertex)
            cand_feat.append(extract_candidate_features(track.hits))

        samples.append(VertexSample(
            event_id=event_id,
            cand_vxyz=np.array(cand_vxyz),
            cand_feat=np.array(cand_feat),
            cand_mask=np.ones(len(cand_vxyz), dtype=bool),
            truth_vertex=truth_vertex,
        ))

    return samples
```

### 6.5 Loss Function

```python
# Log-cosh loss (smooth, robust to outliers)
def log_cosh_loss(pred, target):
    diff = pred - target
    return torch.mean(torch.log(torch.cosh(diff + 1e-12)))

# Per-coordinate weighted loss (x/y harder than z)
loss = 1.0 * log_cosh(pred_x, truth_x) +
       1.0 * log_cosh(pred_y, truth_y) +
       0.5 * log_cosh(pred_z, truth_z)
```

---

## 7. Implementation Plan

### Phase 1: Dataset Preparation
1. [ ] Load baseline Parquet files
2. [ ] Extract truth labels for clustering
3. [ ] Extract signal/background labels for P-Signal
4. [ ] Extract truth vertices for Vertex GNN
5. [ ] Split into train/val/test (70/15/15)

### Phase 2: Beampipe Study
1. [ ] Compute direction deviations at TPC entry
2. [ ] Quantify track splitting/loss
3. [ ] Measure backprojection accuracy
4. [ ] Document findings

### Phase 3: Clustering Optimization
1. [ ] Implement evaluation metrics (ARI, NMI)
2. [ ] Grid search parameter sweep
3. [ ] Fine-tune with Optuna
4. [ ] Validate on test set

### Phase 4: P-Signal Training
1. [ ] Implement data loader
2. [ ] Train PointNetMini
3. [ ] Validate on test set
4. [ ] Save checkpoint

### Phase 5: Vertex GNN Training
1. [ ] Implement data loader
2. [ ] Train NNBARVertexGNN
3. [ ] Validate on test set
4. [ ] Save checkpoint

### Phase 6: End-to-End Validation
1. [ ] Run full reconstruction with trained models
2. [ ] Measure stage-wise efficiency
3. [ ] Compare to heuristic baseline
4. [ ] Document results

---

## 8. Expected Outputs

| Artifact | Path | Purpose |
|----------|------|---------|
| Training data | `training_data/psignal_dataset.npz` | P-Signal training |
| Training data | `training_data/vertex_dataset.npz` | Vertex GNN training |
| P-Signal checkpoint | `models/psignal_nnbar.ckpt` | Trained P-Signal model |
| Vertex checkpoint | `models/vertex_gnn_nnbar.ckpt` | Trained Vertex GNN |
| Clustering config | `config/clustering_optimized.yaml` | Tuned clustering params |
| Validation report | `validation_results/reconstruction_metrics.json` | Stage-wise efficiency |

---

## 9. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Insufficient training data | Medium | High | Generate more events, data augmentation |
| Beampipe effects too severe | Low | High | Constrain vertex to beampipe, use timing |
| Model overfitting | Medium | Medium | Regularization, early stopping |
| GPU memory limits | Low | Medium | Reduce batch size, gradient accumulation |

---

*This plan will be executed iteratively with validation at each phase.*
