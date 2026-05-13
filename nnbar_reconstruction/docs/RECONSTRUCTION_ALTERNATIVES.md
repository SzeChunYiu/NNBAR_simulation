# NNBAR Reconstruction: Alternative Strategies Comparison

**Version:** 1.0
**Date:** 2026-01-12
**Author:** Claude-Architect
**Status:** WP3.3 Deliverable

---

## 1. Executive Summary

This document evaluates alternative reconstruction strategies for the NNBAR detector, comparing them against the thesis baseline implementation. The goal is to identify approaches that may improve reconstruction quality for NNBAR-specific topologies, particularly multi-pion annihilation events with multiple scattering and decay topology changes.

### Key NNBAR Challenges
1. **Multi-track vertices**: ~5 pions per annihilation event
2. **Multiple scattering**: Low-energy pions (<200 MeV) deflect significantly in TPC
3. **Decay topology changes**: π⁰ → γγ, charged pion decays
4. **Overlapping tracks**: Dense track environment near vertex
5. **Mixed particle types**: π±, p, e±, γ requiring different reconstruction approaches

---

## 2. Baseline Implementation Summary

### 2.1 Current Pipeline

| Stage | Algorithm | Implementation | Compliance |
|-------|-----------|----------------|------------|
| Clustering | Adaptive DBSCAN | `clustering.py` | Thesis + HIBEAM |
| Track Fitting | PCA line fit | `track_fitting.py` | Thesis compliant |
| Vertex (Classical) | Weighted projection | `classical_vertex.py` | 93% compliant |
| Vertex (ML) | GNN attention | `gnn_model.py` | HIBEAM-adapted |
| Charged Reco | dE/dx + cone energy | `charged_reconstruction.py` | Thesis compliant |
| Neutral Reco | Angular clustering | `neutral_reconstruction.py` | Thesis compliant |

### 2.2 Baseline Performance Targets (from thesis)
- Trigger efficiency: >99%
- Vertex resolution: ~10 cm (TPC), ~2 cm (inner tracker)
- Pion ID: >90% π±, >98% protons
- π⁰ efficiency: >70%
- Signal acceptance: >68% after all cuts

---

## 3. Alternative Strategies

### 3.1 Clustering Alternatives

#### ALT-1: HDBSCAN (Hierarchical DBSCAN)

**Description:**
HDBSCAN extends DBSCAN by building a hierarchy of clusters at all density levels and extracting the most stable clusters. Unlike DBSCAN, it doesn't require a fixed epsilon parameter.

**Why it may help NNBAR:**
- Automatically handles varying track densities (dense near vertex, sparse at edges)
- Better at finding clusters of varying sizes (short vs long tracks)
- More robust to outliers from secondary interactions

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★★☆ | Better for varying densities |
| Speed | ★★★☆☆ | Slower than DBSCAN (~2x) |
| Complexity | ★★★☆☆ | Automatic epsilon selection |
| Tuning | ★★★★☆ | Fewer parameters (min_cluster_size, min_samples) |

**Required Inputs:**
- Hit positions (x, y, z)
- Optional: energy weights for stability scoring

**Implementation Status:** Available via `hdbscan` Python package, GPU via `cuml.cluster.HDBSCAN`

---

#### ALT-2: Graph-based Clustering (k-NN + Community Detection)

**Description:**
Build a k-nearest-neighbor graph from TPC hits, then apply community detection algorithms (Louvain, Leiden) to identify clusters as tightly connected subgraphs.

**Why it may help NNBAR:**
- Naturally handles non-convex cluster shapes (curved tracks)
- Can incorporate edge weights based on hit properties (charge, timing)
- Scalable to large hit counts via sparse graph representations

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★★☆ | Excellent for complex topologies |
| Speed | ★★★☆☆ | O(n log n) for graph construction |
| Complexity | ★★★★☆ | Requires graph library (networkx, igraph) |
| Tuning | ★★★☆☆ | k value, resolution parameter |

**Required Inputs:**
- Hit positions (x, y, z)
- Hit timing (for edge weighting)
- Hit charge/energy (for edge weighting)

**Implementation Status:** Requires new implementation using `networkx` or `python-igraph`

---

#### ALT-3: OPTICS (Ordering Points To Identify Clustering Structure)

**Description:**
OPTICS creates an ordering of points based on their density-reachability, producing a reachability plot that can be used to extract clusters at multiple density levels.

**Why it may help NNBAR:**
- Reveals hierarchical cluster structure (tracks within events)
- No need to specify epsilon a priori
- Produces interpretable visualization (reachability plot)

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★★☆ | Good for hierarchical structures |
| Speed | ★★☆☆☆ | Slower than DBSCAN (~3x) |
| Complexity | ★★★☆☆ | Simple concept, complex extraction |
| Tuning | ★★★☆☆ | min_samples, xi for extraction |

**Required Inputs:**
- Hit positions (x, y, z)

**Implementation Status:** Available via `sklearn.cluster.OPTICS`, GPU via custom implementation

---

### 3.2 Track Finding Alternatives

#### ALT-4: Hough Transform

**Description:**
Transform hit points to parameter space (e.g., ρ-θ for 2D lines) where each hit votes for all lines passing through it. Peaks in parameter space correspond to tracks.

**Why it may help NNBAR:**
- Robust to outliers and noise hits
- Can find tracks even with significant hit gaps
- Well-suited for straight tracks in TPC

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★☆☆ | Good for straight tracks only |
| Speed | ★★★★☆ | Fast with proper binning |
| Complexity | ★★☆☆☆ | Simple algorithm |
| Tuning | ★★☆☆☆ | Bin sizes, vote threshold |

**Required Inputs:**
- Hit positions (x, y, z) - applied to 2D projections (XY, XZ, YZ)

**Implementation Status:** Requires new implementation (OpenCV has 2D version)

---

#### ALT-5: RANSAC (Random Sample Consensus)

**Description:**
Iteratively fit line models to random subsets of hits, scoring by inlier count. Best-scoring model defines a track; repeat after removing inliers.

**Why it may help NNBAR:**
- Extremely robust to outliers (up to 50% noise tolerance)
- Works well when number of tracks is unknown
- Can be extended to curved models for scattered tracks

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★☆☆ | Good for dominant tracks, may miss faint ones |
| Speed | ★★☆☆☆ | Probabilistic, many iterations needed |
| Complexity | ★★☆☆☆ | Simple concept |
| Tuning | ★★★☆☆ | Inlier threshold, max iterations |

**Required Inputs:**
- Hit positions (x, y, z)

**Implementation Status:** Available via `sklearn.linear_model.RANSACRegressor`

---

#### ALT-6: Cellular Automaton

**Description:**
Build a graph where nodes are hit pairs (tracklets) and edges connect compatible tracklets. Propagate "track quality" signals through the graph to find connected track chains.

**Why it may help NNBAR:**
- Naturally handles track curvature through local compatibility
- Can incorporate direction and energy consistency
- Successfully used in high-multiplicity HEP environments (ALICE, LHCb)

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★★★ | Excellent for complex topologies |
| Speed | ★★★☆☆ | Depends on tracklet generation |
| Complexity | ★★★★★ | Complex implementation |
| Tuning | ★★★☆☆ | Compatibility criteria, propagation rules |

**Required Inputs:**
- Hit positions (x, y, z)
- Hit timing (for causality)
- Layer/region information

**Implementation Status:** Requires new implementation

---

### 3.3 Scattering-Aware Fitting Alternatives

#### ALT-7: Kalman Filter (with Multiple Scattering)

**Description:**
Sequential state estimation that propagates track parameters through the detector, updating with each hit measurement. Multiple scattering is incorporated as process noise.

**Why it may help NNBAR:**
- Explicitly models multiple scattering as physics process
- Provides per-point uncertainty estimates
- Standard in collider experiments (ATLAS, CMS, LHCb)

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★★★ | Best for tracks with scattering |
| Speed | ★★★★☆ | Linear in number of hits |
| Complexity | ★★★★☆ | Requires material model |
| Tuning | ★★★☆☆ | Process noise, measurement noise |

**Required Inputs:**
- Hit positions (x, y, z) with errors
- Detector material map (radiation lengths)
- Initial momentum estimate
- Magnetic field (if any)

**Implementation Status:** Requires new implementation (reference: acts-project/acts)

---

#### ALT-8: Deterministic Annealing Filter (DAF)

**Description:**
Extension of Kalman filter that assigns soft weights to hits based on their compatibility with the track. Weights are "annealed" from soft to hard assignments, helping resolve ambiguities.

**Why it may help NNBAR:**
- Robust to wrong hit assignments in dense environments
- Can handle overlapping tracks near vertex
- Self-resolves hit-to-track ambiguities

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★★★ | Best for dense environments |
| Speed | ★★★☆☆ | Multiple iterations needed |
| Complexity | ★★★★★ | Complex implementation |
| Tuning | ★★★☆☆ | Annealing schedule, cut-off weights |

**Required Inputs:**
- Same as Kalman filter
- Candidate hit-to-track associations

**Implementation Status:** Requires new implementation

---

### 3.4 Vertexing Alternatives

#### ALT-9: Adaptive Vertex Fitting (AVF)

**Description:**
Iteratively reweight tracks based on their χ² contribution to the vertex fit. Tracks with large residuals are downweighted, making the fit robust to outliers and secondary vertices.

**Why it may help NNBAR:**
- Robust to secondary interactions and decays
- Automatically handles outlier tracks
- Can identify multiple vertices in one event

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★★★ | Best for events with secondaries |
| Speed | ★★★★☆ | Few iterations typically |
| Complexity | ★★★☆☆ | Extension of weighted fit |
| Tuning | ★★★☆☆ | Temperature parameter, convergence |

**Required Inputs:**
- Track parameters (position, direction)
- Track covariance matrices
- Initial vertex seed

**Implementation Status:** Could extend `classical_vertex.py`

---

#### ALT-10: Graph-based Vertex Reconstruction

**Description:**
Build a graph where nodes are track intersection points and edges connect compatible intersections. Use graph algorithms to find vertex candidates as dense subgraphs.

**Why it may help NNBAR:**
- Can find multiple vertices simultaneously
- Natural handling of track-to-vertex associations
- Scalable to high track multiplicity

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★★☆ | Good for multi-vertex events |
| Speed | ★★★☆☆ | Depends on graph density |
| Complexity | ★★★★☆ | Requires graph algorithms |
| Tuning | ★★★☆☆ | Intersection threshold, subgraph criteria |

**Required Inputs:**
- Track parameters (position, direction)
- Pairwise intersection distances

**Implementation Status:** Requires new implementation

---

### 3.5 Fusion Approaches

#### ALT-11: Early TPC + Scintillator + Lead Glass Fusion

**Description:**
Instead of reconstructing subsystems independently and matching later, use information from all subsystems jointly in track finding. Scintillator timing constrains track directions; lead glass energy constrains track energies.

**Why it may help NNBAR:**
- Resolves ambiguities using complementary information early
- Better track-to-shower matching
- Can reject background at track level

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★★★ | Best overall physics performance |
| Speed | ★★☆☆☆ | More complex optimization |
| Complexity | ★★★★★ | Major architectural change |
| Tuning | ★★☆☆☆ | Many cross-subsystem parameters |

**Required Inputs:**
- TPC hits with timing
- Scintillator hits with positions and timing
- Lead glass deposits with positions and energies
- Detector geometry for matching

**Implementation Status:** Requires significant new development

---

### 3.6 Machine Learning Approaches

#### ALT-12: GNN Hit-to-Track Assignment

**Description:**
Formulate track finding as edge classification on a hit graph. A Graph Neural Network predicts which hit pairs belong to the same track, followed by clustering to extract tracks.

**Why it may help NNBAR:**
- Can learn complex patterns from simulation
- Naturally handles variable topology
- State-of-the-art in LHC tracking (TrackML challenge winners)

**Tradeoffs:**
| Aspect | Rating | Notes |
|--------|--------|-------|
| Accuracy | ★★★★★ | Best with sufficient training data |
| Speed | ★★★☆☆ | GPU acceleration essential |
| Complexity | ★★★★★ | Requires ML infrastructure |
| Tuning | ★★☆☆☆ | Hyperparameters, architecture |

**Required Inputs:**
- Hit features (x, y, z, charge, time)
- Training data with true track labels
- GPU for training and inference

**Implementation Status:** Partially implemented in GNN vertex model; could extend to tracking

---

## 4. Comparison Matrix

### 4.1 Clustering Alternatives

| Algorithm | Accuracy | Speed | Complexity | Tuning | NNBAR Suitability |
|-----------|----------|-------|------------|--------|-------------------|
| **DBSCAN (baseline)** | ★★★☆☆ | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | Good baseline |
| HDBSCAN (ALT-1) | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★★★☆ | **Recommended** |
| Graph-based (ALT-2) | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ★★★☆☆ | Good for complex shapes |
| OPTICS (ALT-3) | ★★★★☆ | ★★☆☆☆ | ★★★☆☆ | ★★★☆☆ | Good for hierarchy |

### 4.2 Track Finding Alternatives

| Algorithm | Accuracy | Speed | Complexity | Tuning | NNBAR Suitability |
|-----------|----------|-------|------------|--------|-------------------|
| **PCA line fit (baseline)** | ★★★☆☆ | ★★★★★ | ★☆☆☆☆ | ★★★★★ | Good for straight tracks |
| Hough (ALT-4) | ★★★☆☆ | ★★★★☆ | ★★☆☆☆ | ★★☆☆☆ | Fast alternative |
| RANSAC (ALT-5) | ★★★☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ | Robust to noise |
| Cellular Automaton (ALT-6) | ★★★★★ | ★★★☆☆ | ★★★★★ | ★★★☆☆ | **Recommended** for complex |

### 4.3 Scattering-Aware Fitting

| Algorithm | Accuracy | Speed | Complexity | Tuning | NNBAR Suitability |
|-----------|----------|-------|------------|--------|-------------------|
| Kalman Filter (ALT-7) | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★☆☆ | **Recommended** |
| DAF (ALT-8) | ★★★★★ | ★★★☆☆ | ★★★★★ | ★★★☆☆ | Best for dense |

### 4.4 Vertexing Alternatives

| Algorithm | Accuracy | Speed | Complexity | Tuning | NNBAR Suitability |
|-----------|----------|-------|------------|--------|-------------------|
| **Weighted projection (baseline)** | ★★★☆☆ | ★★★★★ | ★★☆☆☆ | ★★★☆☆ | Good baseline |
| **GNN attention (baseline)** | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ★★★☆☆ | Already implemented |
| AVF (ALT-9) | ★★★★★ | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | **Recommended** |
| Graph-based (ALT-10) | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ★★★☆☆ | Good for multi-vertex |

---

## 5. Evaluation Plan

### 5.1 Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Clustering Purity** | Fraction of clusters containing only one true track | >95% |
| **Clustering Efficiency** | Fraction of true track hits assigned to correct cluster | >95% |
| **Track Finding Efficiency** | Fraction of true tracks reconstructed | >90% |
| **Track Fake Rate** | Fraction of reconstructed tracks not matching truth | <5% |
| **Vertex Resolution (XY)** | RMS of (reco - true) vertex position | <10 cm |
| **Vertex Resolution (Z)** | RMS of (reco - true) vertex position | <10 cm |
| **π± ID Efficiency** | Fraction of true π± correctly identified | >90% |
| **Proton ID Efficiency** | Fraction of true protons correctly identified | >98% |
| **π⁰ Efficiency** | Fraction of true π⁰ reconstructed in mass window | >70% |
| **CPU Time/Event** | Processing time on reference CPU | Baseline |
| **GPU Time/Event** | Processing time with GPU acceleration | <0.1× CPU |

### 5.2 Stress Tests

| Test | Description | Purpose |
|------|-------------|---------|
| **High multiplicity** | Events with >10 tracks | Test scalability |
| **Dense vertex** | Multiple tracks within 5 cm | Test track separation |
| **Low energy tracks** | Pions <100 MeV | Test multiple scattering handling |
| **Overlapping showers** | Close π⁰ → γγ pairs | Test neutral clustering |
| **Mixed background** | Signal + cosmic overlay | Test robustness to noise |
| **Asymmetric events** | Large energy imbalance | Test algorithm stability |

### 5.3 Evaluation Dataset Requirements

| Dataset | Events | Purpose |
|---------|--------|---------|
| Signal (annihilation) | 10,000 | Performance measurement |
| Single particles | 1,000/type | Algorithm debugging |
| Cosmic background | 100,000 | Background rejection |
| Mixed (signal+cosmic) | 10,000 | Realistic conditions |

---

## 6. Recommended Implementation Path

### Phase 1: Quick Wins (1-2 weeks)
1. **HDBSCAN clustering** - Drop-in replacement, no architectural changes
2. **Adaptive Vertex Fitting** - Extend existing weighted vertex code
3. **Update angular sigma lookup** - Complete thesis compliance

### Phase 2: Medium-term Improvements (2-4 weeks)
4. **Kalman Filter with scattering** - Major accuracy improvement for low-E tracks
5. **Early timing fusion** - Use scintillator timing in track finding

### Phase 3: Research Exploration (4-8 weeks)
6. **Cellular Automaton track finder** - Best for complex topologies
7. **GNN hit-to-track** - If training data available

### Decision Matrix

| Priority | Alternative | Effort | Expected Gain | Recommendation |
|----------|-------------|--------|---------------|----------------|
| HIGH | HDBSCAN (ALT-1) | Low | Medium | **Implement** |
| HIGH | AVF (ALT-9) | Medium | High | **Implement** |
| HIGH | Kalman Filter (ALT-7) | High | High | **Implement** |
| MEDIUM | Cellular Automaton (ALT-6) | High | High | Prototype |
| MEDIUM | Early Fusion (ALT-11) | High | Very High | Research |
| LOW | Graph Clustering (ALT-2) | Medium | Medium | Optional |
| LOW | GNN Hit-to-Track (ALT-12) | Very High | High | Future work |

---

## 7. Conclusion

The current baseline implementation is **93% compliant** with thesis specifications and includes valuable HIBEAM adaptations. For further improvements, the recommended path forward is:

1. **Immediate**: Implement HDBSCAN and Adaptive Vertex Fitting as they require minimal changes and provide measurable improvements
2. **Near-term**: Add Kalman Filter with multiple scattering model for proper handling of low-energy tracks
3. **Research**: Explore Cellular Automaton and early fusion approaches for maximum performance

The GNN vertex model is already implemented and should be retained as an alternative to classical methods. Training data availability will determine whether GNN hit-to-track assignment is feasible.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-12 | Claude-Architect | Initial document |
