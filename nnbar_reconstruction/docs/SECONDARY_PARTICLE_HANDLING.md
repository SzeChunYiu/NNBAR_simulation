# Secondary Particle Handling Strategy for NNBAR Reconstruction

**Date:** 2026-01-12
**Author:** Claude-Architect
**Status:** Analysis Complete

---

## 1. Executive Summary

Analysis of 1000 baseline annihilation events reveals that **secondary particles dominate TPC track content**:
- 53.4% of TPC tracks are from secondary particles
- ~52% of pion decays occur inside the beampipe (r < 112 cm)
- 1656 pion inelastic interactions in the beampipe region

This document defines the strategy for handling secondary particles in reconstruction to maximize vertex resolution and signal efficiency.

---

## 2. Particle Flow Analysis

### 2.1 Primary Particle Production (from annihilation)

| Particle | Count | Fraction |
|----------|-------|----------|
| π⁰ | 1700 | 21.2% |
| π⁺ | 1652 | 20.6% |
| π⁻ | 1270 | 15.8% |
| proton | 1032 | 12.8% |
| neutron | 824 | 10.3% |
| alpha | 352 | 4.4% |
| Others | 1208 | 15.0% |
| **Total** | **8038** | **100%** |

### 2.2 Pion Fate Statistics

```
Primary charged pions: 2922
├── Reach TPC directly: 1804 (62%)
├── Decay (π → μ + ν): ~2400 muons produced
│   ├── Inside beampipe (r < 112 cm): 51.6%
│   ├── In beampipe wall (112-114 cm): 3.4%
│   └── After beampipe (r > 114 cm): 45.0%
└── Inelastic in beampipe: 1656 interactions
    └── Products: neutrons, protons, π±, deuterons
```

### 2.3 TPC Track Composition

| Particle | Hits | Fraction | Tracks/Event | Hits/Track |
|----------|------|----------|--------------|------------|
| π⁺ | 155,107 | 44.6% | 1.4 | 139.2 |
| π⁻ | 116,664 | 33.5% | 1.2 | 139.6 |
| proton | 35,912 | 10.3% | 1.5 | 94.3 |
| μ⁺ | 22,187 | 6.4% | 1.1 | 108.2 |
| μ⁻ | 16,122 | 4.6% | 1.0 | 116.0 |
| Others | ~2k | 0.6% | - | - |

---

## 3. Track Classification Scheme

### 3.1 Three-Tier Classification

```
SIGNAL (use for vertex)
└── PRIMARY: Parent_ID = 0, charged particle from annihilation
    - π±, proton, K±, etc.
    - Direct kinematic information from annihilation
    - 82.8% have <5 deg direction deviation at TPC entry
    - 96.1% have >20 TPC hits

QUASI-SIGNAL (use with extreme caution)
└── DECAY MUONS: μ± from π± → μ± + ν
    - Mean decay angle: ~60 deg from parent pion direction!
    - Only 22% within 10 deg of parent pion
    - RECOMMENDATION: EXCLUDE from vertex fit
    - Use only for secondary analysis (kink finding)

BACKGROUND (exclude from vertex)
├── MATERIAL: Origin in detector material volumes
│   - Al27, Mg26, etc. (spallation products)
│   - δ-rays (high-energy electrons)
│   - Produced by interactions in beampipe/TPC walls
│
├── COMPTON: Low-energy electrons from γ interactions
│   - Short tracks, typically < 20 hits
│   - No vertex information
│
└── HADRONIC SECONDARY: Products of hadronic interactions
    - Secondary pions from inelastic scattering
    - Protons/neutrons from nuclear breakup
    - Direction uncorrelated with annihilation vertex
```

### 3.2 Classification Algorithm

```python
def classify_track(track_hits):
    """
    Classify a TPC track as SIGNAL, SIGNAL_LIKE, or BACKGROUND.

    Args:
        track_hits: DataFrame with columns:
            - Parent_ID: Parent particle ID (0 = primary)
            - Origin: Volume where particle was created
            - Name: Particle type
            - Proc: Creation process

    Returns:
        str: 'SIGNAL', 'SIGNAL_LIKE', or 'BACKGROUND'
    """
    first_hit = track_hits.iloc[0]

    parent_id = first_hit['Parent_ID']
    origin = first_hit['Origin']
    name = first_hit['Name']
    proc = first_hit['Proc']

    # PRIMARY: Direct from annihilation
    if parent_id == 0:
        return 'SIGNAL'

    # SIGNAL-LIKE: Muon from pion decay
    if name in ['mu+', 'mu-'] and proc == 'Decay':
        # Check if parent was a primary pion
        # Parent_ID 1-10 are typically primaries
        if parent_id <= 10:
            return 'SIGNAL_LIKE'

    # BACKGROUND: Material interactions
    material_origins = [
        'Beampipe_5_wall_PV', 'Beampipe_5_coating_PV',
        'TPCPV', 'TPC_1_layer_PV', 'TPC_2_layer_PV',
        'siliconPV', 'LeadGlassPV', 'Scint_barPV'
    ]
    if any(mat in str(origin) for mat in material_origins):
        if name not in ['pi+', 'pi-', 'proton', 'mu+', 'mu-']:
            return 'BACKGROUND'

    # BACKGROUND: Short tracks (likely Compton/delta-rays)
    if len(track_hits) < 15:
        return 'BACKGROUND'

    # BACKGROUND: Low-energy electrons
    if name in ['e-', 'e+'] and first_hit.get('KE', 0) < 10:
        return 'BACKGROUND'

    # DEFAULT: Treat as background for safety
    return 'BACKGROUND'
```

---

## 4. Handling Strategies by Particle Type

### 4.1 Muons from Pion Decay

**Challenge:** 52% of pions decay before TPC, producing muons that carry directional information but emerge from a different position than the annihilation vertex.

**Strategy:**
1. **Identify μ tracks** via dE/dx (MIP-like, ~2 MeV/cm)
2. **Trace back to decay point** using track extrapolation
3. **Link to parent pion** if possible (via timing or position)
4. **Weight muon tracks** lower in vertex fit (uncertainty from decay kinematics)

```python
def weight_muon_for_vertex(muon_track, decay_radius):
    """
    Compute weight for muon track in vertex fit.

    Muon direction differs from pion direction by:
    - Decay angle (up to ~30° in lab frame for boosted pion)
    - Multiple scattering in any traversed material

    Weight decreases with:
    - Decay radius (more material traversed)
    - Decay angle uncertainty
    """
    base_weight = 1.0

    # Penalty for decay radius
    if decay_radius < 50:
        weight = base_weight * 0.9  # Decayed early, good direction
    elif decay_radius < 112:
        weight = base_weight * 0.7  # Decayed in flight
    else:
        weight = base_weight * 0.5  # Decayed after beampipe

    return weight
```

### 4.2 Secondary Pions (from hadronic interactions)

**Challenge:** Pion inelastic interactions in beampipe produce secondary pions with different directions.

**Strategy:**
1. **Identify by origin volume** (Beampipe_* volumes)
2. **Check Parent_ID** (non-zero indicates secondary)
3. **Exclude from vertex fit** (direction is uncorrelated)
4. **Include in energy sum** (they still carry energy from event)

### 4.3 Spallation Products

**Challenge:** Al27, Mg26, deuterons from beampipe material have no relation to annihilation vertex.

**Strategy:**
1. **Exclude completely** from all reconstruction
2. **Identify by:**
   - Particle name (Al27, Mg*, Be*, Li*, etc.)
   - Origin volume (Beampipe_*_wall_PV)
   - Low momentum (< 100 MeV/c typically)

### 4.4 Compton/Delta-ray Electrons

**Challenge:** Low-energy electrons from photon interactions create short, wandering tracks.

**Strategy:**
1. **Exclude from clustering** (or mark as noise)
2. **Identify by:**
   - Short track length (< 15 hits)
   - Curving trajectory (small gyroradius)
   - Creation process (compt, phot, eIoni)

---

## 5. Clustering Modifications

### 5.1 Pre-clustering Filtering

```python
def filter_hits_for_clustering(tpc_data):
    """
    Remove obvious background hits before clustering.
    """
    # Remove spallation products
    spallation = ['Al27', 'Mg26', 'Mg25', 'Ar40', 'O16', 'Si28']
    mask = ~tpc_data['Name'].isin(spallation)

    # Remove hits from detector material origins
    material_origins = ['siliconPV', 'LeadGlassPV']
    for mat in material_origins:
        mask &= ~tpc_data['Origin'].str.contains(mat, na=False)

    return tpc_data[mask]
```

### 5.2 Cluster Labeling

After clustering, label each cluster with truth information:

```python
def label_cluster(cluster_hits):
    """
    Assign truth label to cluster for training.

    Returns:
        - cluster_id
        - purity: fraction of hits from dominant particle
        - dominant_particle: (Track_ID, Name)
        - classification: SIGNAL, SIGNAL_LIKE, BACKGROUND
    """
    track_counts = cluster_hits['Track_ID'].value_counts()
    dominant_track = track_counts.index[0]
    purity = track_counts.iloc[0] / len(cluster_hits)

    # Get particle info for dominant track
    dominant_hits = cluster_hits[cluster_hits['Track_ID'] == dominant_track]
    particle_name = dominant_hits.iloc[0]['Name']
    parent_id = dominant_hits.iloc[0]['Parent_ID']

    # Classify
    if parent_id == 0:
        classification = 'SIGNAL'
    elif particle_name in ['mu+', 'mu-'] and parent_id <= 10:
        classification = 'SIGNAL_LIKE'
    else:
        classification = 'BACKGROUND'

    return {
        'dominant_track': dominant_track,
        'particle_name': particle_name,
        'purity': purity,
        'classification': classification,
    }
```

---

## 6. Vertex Reconstruction Modifications

### 6.1 Track Weighting

```python
def compute_track_weight(track, classification):
    """
    Compute weight for track in vertex fit.
    """
    weights = {
        'SIGNAL': 1.0,       # Primary particles - full weight
        'SIGNAL_LIKE': 0.6,  # Muons from decay - reduced weight
        'BACKGROUND': 0.0,   # Background - excluded
    }

    base_weight = weights.get(classification, 0.0)

    # Additional weight factors
    n_hits = track.n_hits
    hit_weight = min(1.0, n_hits / 50)  # More hits = more reliable

    # Track fit quality
    chi2_weight = np.exp(-track.chi2_ndf / 5.0)

    return base_weight * hit_weight * chi2_weight
```

### 6.2 Vertex Constraint

```python
def constrain_vertex_to_beampipe(vertex_estimate, uncertainty):
    """
    Constrain vertex to be inside beampipe region.

    Beampipe geometry:
    - Inner radius: 112 cm
    - Target at z ≈ 0
    """
    x, y, z = vertex_estimate
    r = np.sqrt(x**2 + y**2)

    # If outside beampipe, project back
    if r > 110:  # 2 cm margin
        scale = 110 / r
        x *= scale
        y *= scale
        # Increase uncertainty
        uncertainty *= 1.5

    # Z should be near target
    if abs(z) > 50:
        z = np.sign(z) * 50
        uncertainty *= 1.5

    return np.array([x, y, z]), uncertainty
```

---

## 7. Training Data Preparation

### 7.1 Signal Definition for P-Signal Model

```python
def create_psignal_labels(tpc_data):
    """
    Create binary labels for P-Signal training.

    Labels:
        1 = SIGNAL or SIGNAL_LIKE (use for vertex)
        0 = BACKGROUND (exclude from vertex)
    """
    labels = []

    for (event_id, track_id), track_hits in tpc_data.groupby(['Event_ID', 'Track_ID']):
        first_hit = track_hits.iloc[0]

        parent_id = first_hit['Parent_ID']
        name = first_hit['Name']
        proc = first_hit['Proc']

        # SIGNAL: Primary particles
        if parent_id == 0:
            label = 1
        # SIGNAL_LIKE: Muons from pion decay
        elif name in ['mu+', 'mu-'] and proc == 'Decay' and parent_id <= 10:
            label = 1
        # BACKGROUND
        else:
            label = 0

        labels.append({
            'event_id': event_id,
            'track_id': track_id,
            'label': label,
            'particle': name,
            'parent_id': parent_id,
            'n_hits': len(track_hits),
        })

    return pd.DataFrame(labels)
```

### 7.2 Truth Vertex Extraction

```python
def extract_truth_vertices(particle_data, tpc_data):
    """
    Extract truth vertex positions for Vertex GNN training.

    The annihilation vertex is defined as the mean position
    of primary particle origins.
    """
    vertices = []

    for event_id in particle_data['Event_ID'].unique():
        event_particles = particle_data[particle_data['Event_ID'] == event_id]

        # Primary particles have their creation point at vertex
        # Use mean of all primary positions
        x = event_particles['x'].mean()
        y = event_particles['y'].mean()
        z = event_particles['z'].mean()

        vertices.append({
            'event_id': event_id,
            'truth_x': x,
            'truth_y': y,
            'truth_z': z,
            'n_primaries': len(event_particles),
        })

    return pd.DataFrame(vertices)
```

---

## 8. Implementation Checklist

- [ ] Add track classification to clustering pipeline
- [ ] Implement pre-clustering hit filtering
- [ ] Add track weighting to vertex reconstruction
- [ ] Implement beampipe vertex constraint
- [ ] Create P-Signal training dataset with proper labels
- [ ] Create Vertex GNN training dataset with truth vertices
- [ ] Validate classification accuracy on test set
- [ ] Measure impact on vertex resolution

---

## 9. Expected Impact

| Metric | Without Strategy | With Strategy |
|--------|-----------------|---------------|
| Background tracks in vertex | ~50% | <10% |
| Vertex resolution (r) | ~15 cm | ~5-8 cm |
| Signal efficiency | ~95% | ~90% (stricter cuts) |
| Track purity | ~50% | >90% |

---

*This document should be updated as the reconstruction is refined and validated.*
