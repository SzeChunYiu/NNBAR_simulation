# Comprehensive Particle Identification Strategy for NNBAR

**Author:** Claude Analysis
**Date:** January 2026
**Version:** 2.0 (Multi-Detector + Decay)

---

## Executive Summary

### Available Detectors
| Detector | Primary Role | Key Measurements |
|----------|-------------|------------------|
| **TPC** | Tracking | dE/dx, path, momentum, kink angle |
| **Scintillator** | Energy + Timing | eDep, layer penetration, TOF |
| **Lead Glass** | EM Calorimetry | Gamma/electron showers |

### Particle Signatures
| Particle | dE/dx (TPC) | Penetration | Special Features |
|----------|-------------|-------------|------------------|
| **Proton** | HIGH (~0.6) | Short (2.6 layers) | Stops quickly |
| **Pion (pi+/-)** | MEDIUM (~0.05) | Long (4.1 layers) | May decay to muon |
| **Muon (mu+/-)** | MEDIUM (~0.11) | Very long | From pion decay |
| **Electron** | Variable | Short (EM shower) | From gamma conversion |

### Performance Summary
| Task | Method | Accuracy |
|------|--------|----------|
| pi vs proton | TPC dE/dx + ML | **96.0%** |
| pi0 reconstruction | PCA + ML correction | **82-87%** |
| Pion decay ID | TPC kink + timing | **6.6% detected** |

---

## 1. Key Findings

### 1.1 Gamma Interactions in Scintillator

**Critical insight**: 88.5% of scintillator energy in pi0 events comes from gamma interactions!

```
Gamma interaction processes in scintillator:
├── compt (144k hits): Compton scattering
├── conv (92k hits):   Pair production (gamma -> e+e-)
├── phot (6k hits):    Photoelectric effect
└── eIoni (63k hits):  Secondary electron ionization
```

**Implication**: We cannot distinguish gamma-converted electrons from direct charged particles using scintillator alone. Must use:
- Pattern recognition (shower vs track)
- TPC information (no track for gamma/neutral)
- Lead Glass energy (most gamma energy there)

### 1.2 Pion Decay (pi -> mu + nu)

| Property | Value |
|----------|-------|
| Lifetime | tau = 26 ns |
| c*tau | 7.8 m |
| Branching ratio | 99.99% to mu + nu |
| Decay signature | Kink in track, muon appears |

**Detection method**:
1. Look for track endpoint (pion stops)
2. Find muon starting at same point
3. Check time delay (~26 ns)
4. Measure kink angle (direction change)

**Current detection rate**: 6.6% of pions with detected muon daughter
- Limited by: Decay outside detector volume, muon escapes

---

## 2. Updated Reconstruction Methods

### 2.1 Charged Particle ID (pi vs proton)

**Best approach**: Combine TPC + Scintillator features

```python
features = [
    # TPC (most important)
    'tpc_dEdx',        # 38.2% importance - PRIMARY DISCRIMINATOR
    'tpc_n_hits',      # 36.5% importance
    'kink_angle',      # 10.6% importance - for decay ID
    'tpc_path',        # 5.4% importance

    # Scintillator (supporting)
    'scint_eDep',      # 3.5% importance
    'scint_n_layers',  # 3.3% importance
    'scint_n_hits',    # 2.5% importance
]
```

**Performance**: 96.0% accuracy (cross-validated)

### 2.2 Pi0 Reconstruction

**Updated algorithm accounting for scintillator gamma interactions**:

1. **Lead Glass**: Primary gamma detection (PCA cluster splitting)
2. **Scintillator**: Add energy from gamma conversion (it's signal, not background!)
3. **ML correction**: Gradient Boosting on combined features

```python
# Energy calculation
E_gamma1 = lg_cluster1_photons * calibration
E_gamma2 = lg_cluster2_photons * calibration

# Scintillator contribution (from gamma conversion)
scint_gamma_E = scint_total_photons * scint_calibration
E_gamma1 += scint_gamma_E * fraction1
E_gamma2 += scint_gamma_E * fraction2

# Invariant mass
mass = sqrt(2 * E_gamma1 * E_gamma2 * (1 - cos_theta))
```

### 2.3 Electron vs Pion Distinction

| Feature | Electron | Pion |
|---------|----------|------|
| TPC track | Often no track (from gamma) | Clear track |
| dE/dx | Variable (shower) | ~0.05 consistent |
| Lead Glass | Large shower | Minimal |
| Origin | Secondary (Parent_ID != 0) | Primary (Parent_ID = 0) |

**Key discriminator**: Check if particle is PRIMARY (Parent_ID = 0)
- Primary charged track -> likely pion/proton
- Secondary from gamma -> electron

### 2.4 Muon Identification (from Pion Decay)

```python
def identify_pion_decay(tpc_data, event_id, pion_track_id):
    """
    Identify pion -> muon decay.

    Returns: (is_decay, muon_track_id, decay_time, kink_angle)
    """
    pion_track = tpc_data[(tpc_data['Event_ID'] == event_id) &
                          (tpc_data['Track_ID'] == pion_track_id)]

    # Find muon daughter
    muon_tracks = tpc_data[(tpc_data['Event_ID'] == event_id) &
                           (tpc_data['Parent_ID'] == pion_track_id) &
                           (tpc_data['Name'].isin(['mu+', 'mu-']))]

    if len(muon_tracks) == 0:
        return False, None, None, None

    # Get decay time
    pion_end_t = pion_track.sort_values('t')['t'].iloc[-1]
    muon_start_t = muon_tracks.sort_values('t')['t'].iloc[0]
    decay_time = muon_start_t - pion_end_t

    # Calculate kink angle
    # ... (direction change at decay vertex)

    return True, muon_tracks['Track_ID'].iloc[0], decay_time, kink_angle
```

---

## 3. Real Experiment Compatibility

### 3.1 What We Have vs What We Need

| Information | Simulation | Real Experiment | Solution |
|-------------|------------|-----------------|----------|
| Particle type | Name column | NOT available | ML prediction |
| Track_ID | Automatic | Pattern recognition | TPC reconstruction |
| Hit positions | (x,y,z) per hit | Module-level | Use module positions |
| Energy | eDep | Photon counts | Calibration |
| Timing | t column | PMT timing | Requires good resolution |

### 3.2 TPC in Real Experiment

The TPC provides **crucial tracking information**:
- 3D hit positions with good resolution
- Track reconstruction possible
- dE/dx measurement for PID
- Decay vertex detection

**Key requirement**: TPC readout and track reconstruction algorithm

### 3.3 Module-Level Algorithm (No hit positions)

If TPC tracking is not available:

```python
# Use module-level features only
features_real_experiment = [
    'total_photons',      # Sum of PMT signals
    'n_modules_hit',      # Number of modules fired
    'n_layers',           # Layer penetration
    'time_spread',        # Timing information
    'spatial_extent',     # From module positions (geometry)
    'pseudo_dEdx',        # photons / spatial_extent
]
```

**Performance**: ~82-87% for pi0, ~95% for charged PID

---

## 4. Implementation Workflow

### 4.1 Event Reconstruction Pipeline

```
Event Data
    │
    ├── TPC Hits ──────────► Track Reconstruction
    │                              │
    │                              ├── Primary tracks
    │                              ├── dE/dx per track
    │                              └── Decay vertex search
    │
    ├── Scintillator ──────► Energy + Timing
    │       │                      │
    │       │                      ├── Layer penetration
    │       │                      └── TOF measurement
    │       │
    │       └── (NOTE: Contains gamma-converted electrons!)
    │
    └── Lead Glass ────────► Calorimetry
                                   │
                                   ├── Gamma clusters
                                   └── Pi0 mass reconstruction

                    ▼
           Combined ML Classification
                    │
                    ├── Charged: pion / proton / muon
                    ├── Neutral: pi0 / gamma / neutron
                    └── Decay: pion with muon daughter
```

### 4.2 Classification Decision Tree

```
Is there a TPC track?
    │
    ├── YES (charged particle)
    │       │
    │       └── Check dE/dx
    │               │
    │               ├── HIGH (>0.3) ──► PROTON
    │               │
    │               └── LOW (<0.3)
    │                       │
    │                       └── Check for muon daughter
    │                               │
    │                               ├── YES ──► PION (decayed)
    │                               └── NO  ──► PION or MUON
    │                                               │
    │                                               └── Check Parent_ID
    │                                                       │
    │                                                       ├── Primary ──► PION
    │                                                       └── From pion ──► MUON
    │
    └── NO (neutral particle)
            │
            └── Check Lead Glass
                    │
                    ├── Large EM shower ──► GAMMA or ELECTRON
                    │       │
                    │       └── Reconstruct pi0 mass
                    │               │
                    │               ├── [100-180] MeV ──► PI0
                    │               └── Other ──► Single GAMMA
                    │
                    └── Hadronic pattern ──► NEUTRON
```

---

## 5. Summary Tables

### 5.1 Particle Properties

| Particle | Mass (MeV) | Charge | Lifetime | Decay Mode |
|----------|------------|--------|----------|------------|
| pi+ | 139.6 | +1 | 26 ns | mu+ nu |
| pi- | 139.6 | -1 | 26 ns | mu- nu |
| pi0 | 135.0 | 0 | 8.4e-17 s | gamma gamma |
| proton | 938.3 | +1 | stable | - |
| mu+ | 105.7 | +1 | 2.2 us | e+ nu nu |
| mu- | 105.7 | -1 | 2.2 us | e- nu nu |
| e- | 0.511 | -1 | stable | - |
| gamma | 0 | 0 | stable | - |

### 5.2 Detector Response

| Particle | TPC | Scintillator | Lead Glass |
|----------|-----|--------------|------------|
| pi+/- | Track, dE/dx~0.05 | 4 layers, 2 MeV/cm | Minimal |
| proton | Track, dE/dx~0.6 | 2.6 layers, 6.5 MeV/cm | Minimal |
| mu+/- | Track, dE/dx~0.1 | 4.3 layers | Minimal |
| e+/- | Short track | Part of shower | EM shower |
| gamma | No track | Converted e+e- | EM shower |
| pi0 | No track | Converted e+e- | Two EM showers |

---

## Appendix: Updated Documentation Files

- `docs/optimized_pid_algorithms.md` - ML algorithms and performance
- `docs/real_experiment_algorithms.md` - Real experiment compatible methods
- `docs/comprehensive_pid_strategy.md` - This file (complete strategy)
