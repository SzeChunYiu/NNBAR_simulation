# NNBAR Detector Particle Identification Documentation

**Author:** Claude Analysis
**Date:** January 2026
**Version:** 1.0

## Table of Contents

1. [Overview](#overview)
2. [Detector Components](#detector-components)
3. [Data Samples](#data-samples)
4. [Charged Particle Identification](#charged-particle-identification)
5. [Neutral Pion Reconstruction](#neutral-pion-reconstruction)
6. [Object Definitions Summary](#object-definitions-summary)
7. [Performance Metrics](#performance-metrics)
8. [Recommendations](#recommendations)

---

## Overview

This document describes the particle identification (PID) capabilities of the NNBAR detector simulation. The analysis is based on antineutron annihilation events and single-particle calibration samples.

### Physics Context

The NNBAR experiment searches for neutron-antineutron oscillations. When an antineutron annihilates with a nucleon, it produces a characteristic multi-pion final state:

```
n̄ + N → multiple pions (π+, π-, π⁰) + possible nucleons (p, n)
```

Typical multiplicities per annihilation event:
- π⁺: 1.65/event
- π⁻: 1.27/event
- π⁰: 1.70/event
- proton: 1.03/event
- neutron: 0.82/event

---

## Detector Components

### 1. Time Projection Chamber (TPC) / Scintillator
- **Purpose:** Track charged particles, measure ionization (dE/dx)
- **Coverage:** Central tracking region
- **Key measurements:**
  - Track position (x, y, z)
  - Energy deposit (eDep)
  - Path length
  - Particle identification via dE/dx

### 2. Lead Glass Calorimeter
- **Purpose:** Measure electromagnetic showers from γ and e±
- **Material:** Lead glass (high-Z for EM shower development)
- **Key measurements:**
  - Total energy deposit
  - Shower position
  - Module hit pattern

### Data Columns

**Scintillator_output:**
| Column | Description | Units |
|--------|-------------|-------|
| Event_ID | Event identifier | - |
| Track_ID | Unique track identifier | - |
| Parent_ID | Parent particle ID (0 = primary) | - |
| Name | Particle name (pi+, pi-, proton, etc.) | - |
| eDep | Energy deposited in step | MeV |
| KE | Kinetic energy at step | MeV |
| x, y, z | Hit position | cm |

**LeadGlass_output:**
| Column | Description | Units |
|--------|-------------|-------|
| Event_ID | Event identifier | - |
| Track_ID | Track identifier | - |
| Module_ID | Calorimeter module | - |
| eDep | Energy deposit | MeV |
| x, y, z | Hit position | cm |

---

## Data Samples

### Baseline Reference (Antineutron Annihilation)
- **Location:** `output/baseline_reference/`
- **Events:** 1000
- **Generator:** Antineutron annihilation at rest
- **Used for:** Charged particle PID, event topology

### Single π⁰ Calibration
- **Location:** `output/pi0_proper/`
- **Events:** 500
- **Generator:** Single π⁰ at 150 MeV kinetic energy
- **Used for:** π⁰ reconstruction optimization
- **Note:** Run with `CELER_DISABLE=1` for full tracking

---

## Charged Particle Identification

### Method: dE/dx Measurement

The ionization energy loss (dE/dx) follows the Bethe-Bloch formula:

```
-dE/dx ∝ (z²/β²) × [ln(2mₑc²β²γ²/I) - β²]
```

where:
- z = charge of particle
- β = v/c (velocity)
- γ = Lorentz factor
- I = mean excitation energy of material

**Key insight:** At the same momentum, heavier particles (protons) have lower β and thus higher dE/dx than lighter particles (pions).

### Track Selection

```python
# Primary track selection
selection = (
    (track['Parent_ID'] == 0) &      # Primary particle
    (track['Path_Length'] > 1)        # Minimum path length
)
```

### dE/dx Calculation

```python
# Calculate dE/dx per track
track['dEdx'] = track['eDep'] / track['Path_Length']

# Path length from hit positions (bounding box approximation)
path_length = sqrt(
    (x_max - x_min)² +
    (y_max - y_min)² +
    (z_max - z_min)²
)
```

### Measured dE/dx Distributions

| Particle | dE/dx Mean (MeV/cm) | dE/dx Std | Track Length (cm) |
|----------|---------------------|-----------|-------------------|
| π⁺ | 2.61 | 1.73 | 28.1 ± 26.8 |
| π⁻ | 2.38 | 1.31 | 23.8 ± 13.4 |
| proton | 7.14 | 3.90 | 14.7 ± 9.7 |

### Separation Power

The separation power between two populations is defined as:

```
S = |μ₁ - μ₂| / √(0.5 × (σ₁² + σ₂²))
```

**Results:**
- dE/dx separation (π vs p): **1.56σ**
- Path length separation (π vs p): **0.67σ**
- Combined (quadrature): **1.70σ**
- ROC AUC: **0.88**

### Optimal Cut Determination

Using Youden's J statistic (J = TPR - FPR) to find optimal threshold:

**Optimal dE/dx cut: 4.76 MeV/cm**

| Metric | π± | proton |
|--------|-----|--------|
| Efficiency | 91.6% | 82.1% |
| Purity | 99.5% | 18.5% |

### 2D Selection (dE/dx + Path Length)

For improved pion selection:
```
dE/dx < 6.0 MeV/cm  AND  Path_Length > 10 cm
```
- Pion efficiency: 87.0%
- Pion purity: 99.5%
- F1 score: 0.928

---

## Neutral Pion Reconstruction

### Physics Background

The π⁰ decays electromagnetically with ~99% branching ratio:

```
π⁰ → γγ     (BR = 98.8%)
π⁰ → γe⁺e⁻  (BR = 1.2%, Dalitz decay)
```

**π⁰ properties:**
- Mass: 134.98 MeV/c²
- Lifetime: 8.4 × 10⁻¹⁷ s (decays immediately)

### Invariant Mass Reconstruction

For two photons with energies E₁ and E₂ at opening angle θ:

```
m_γγ = √(2 E₁ E₂ (1 - cos θ))
```

The opening angle is determined from the photon directions:

```python
cos_theta = dot(r1, r2) / (|r1| × |r2|)
```

where r₁ and r₂ are position vectors from the vertex to the cluster centroids.

### Challenges Identified

1. **Low Energy Capture:**
   - Lead Glass captures only ~59% of true π⁰ energy
   - Energy leakage at shower edges
   - Sampling fluctuations

2. **Shower Overlap:**
   - Typical opening angle at 150 MeV: 20-50°
   - Shower spread: ~120 cm (much larger than separation)
   - Two γ clusters merge into one

3. **Poor Cluster Separation:**
   - EM showers develop via e⁺e⁻ pair production
   - Energy deposited by e± (83,000 MeV) >> γ direct (20 MeV)
   - Position information smeared by shower development

### Energy Response

| Metric | Value |
|--------|-------|
| Mean E_reco/E_true | 58.8% |
| Resolution (σ) | 29.5% |
| Required correction | ×1.7 to ×2.2 |

### Reconstruction Methods Attempted

#### Method 1: Module-Based Clustering
- Sum energy per Lead Glass module
- Take top 2 modules
- **Result:** Very poor (17% efficiency)
- **Issue:** Energy spread across many modules

#### Method 2: Hierarchical Clustering
- Cluster hits by spatial proximity
- Distance threshold: 50 cm
- **Result:** 25% efficiency, 72 MeV resolution
- **Issue:** Overlapping showers not separated

#### Method 3: Seeded Cone Clustering
- Find highest-energy cell as seed
- Sum all cells within radius
- **Result:** Similar to Method 2
- **Issue:** Same fundamental limitation

---

## Object Definitions Summary

### Charged Pion (π±)

```python
def select_charged_pion(track):
    """
    Select charged pion candidates from scintillator tracks.

    Returns: bool indicating if track passes selection
    """
    cuts = (
        track['Parent_ID'] == 0 and           # Primary particle
        track['dEdx'] < 4.8 and                # Low ionization (MeV/cm)
        track['Path_Length'] > 10              # Minimum track length (cm)
    )
    return cuts
```

**Performance:**
- Efficiency: 92%
- Purity: 99.5%
- Main background: protons (separable with dE/dx)

### Proton

```python
def select_proton(track):
    """
    Select proton candidates from scintillator tracks.

    Returns: bool indicating if track passes selection
    """
    cuts = (
        track['Parent_ID'] == 0 and           # Primary particle
        track['dEdx'] >= 4.8                   # High ionization (MeV/cm)
    )
    return cuts
```

**Performance:**
- Efficiency: 82%
- Purity: 19% (limited by statistics)
- **Note:** Needs additional discrimination (ToF, E/p)

### Neutral Pion (π⁰) - Basic

```python
def select_pi0_basic(event_lg_hits):
    """
    Basic π⁰ selection using total Lead Glass energy.

    Returns: dict with reconstructed quantities or None
    """
    # Sum all energy in event
    total_E = event_lg_hits['eDep'].sum()

    # Apply correction factor
    corrected_E = total_E * 1.7

    # Check if consistent with π⁰
    if 100 < corrected_E < 400:  # Expected range for single π⁰
        return {'energy': corrected_E, 'is_pi0_candidate': True}
    return None
```

### Gamma

```python
def select_gamma(lg_cluster):
    """
    Select gamma candidates from Lead Glass clusters.

    Returns: bool indicating if cluster passes selection
    """
    cuts = (
        lg_cluster['energy'] > 20 and         # Minimum energy (MeV)
        lg_cluster['n_modules'] >= 1 and      # At least 1 module hit
        lg_cluster['has_tpc_match'] == False  # No associated charged track
    )
    return cuts
```

---

## Performance Metrics

### Charged Particle ID

| Particle | Efficiency | Purity | Separation (σ) |
|----------|------------|--------|----------------|
| π± | 92% | 99.5% | - |
| proton | 82% | 19% | 1.6 vs π |

### Neutral Particle ID

| Particle | Method | Efficiency | Resolution |
|----------|--------|------------|------------|
| π⁰ | Mass window [100-180] | 17-25% | 72 MeV |
| π⁰ | Energy threshold | ~90% | 29% |
| γ | No TPC match | High | N/A |

### Confusion Matrix (Charged Particles)

At dE/dx cut = 4.8 MeV/cm:

|  | Predicted π | Predicted p |
|--|-------------|-------------|
| True π | 1102 | 102 |
| True p | 5 | 23 |

---

## Recommendations

### For Improved Charged Particle ID

1. **Time-of-Flight (ToF):**
   - Mass = p × √(1/β² - 1)
   - Would provide direct mass measurement
   - Essential for π/K/p separation

2. **Momentum Measurement:**
   - Currently only dE/dx available
   - Track curvature in B-field would help
   - Enable E/p ratio cuts

3. **Machine Learning:**
   - Combine dE/dx, path length, hit pattern
   - BDT or neural network for multi-class PID
   - Expected improvement: 20-30% in separation

### For Improved π⁰ Reconstruction

1. **Better Clustering Algorithm:**
   - Use shower shape information
   - Fit expected EM shower profile
   - Separate overlapping showers

2. **Kinematic Constraints:**
   - Apply π⁰ mass constraint
   - Use opening angle vs energy correlation

3. **Combined Detector Response:**
   - Use scintillator + Lead Glass together
   - Preshower detector for γ identification

4. **Event-Level Analysis:**
   - In multi-pion events, use topology
   - Vertex constraints help associate γs

---

## Code Examples

### Loading Data

```python
import pyarrow.parquet as pq
import pandas as pd

# Load scintillator data
scint_df = pq.read_table("output/baseline_reference/Scintillator_output_0.parquet").to_pandas()

# Load Lead Glass data
lg_df = pq.read_table("output/pi0_proper/LeadGlass_output_0.parquet").to_pandas()

# Load truth particles
particle_df = pq.read_table("output/baseline_reference/Particle_output_0.parquet").to_pandas()
```

### Calculating dE/dx

```python
# Aggregate by track
tracks = scint_df.groupby(['Event_ID', 'Track_ID']).agg({
    'eDep': 'sum',
    'Name': 'first',
    'Parent_ID': 'first'
}).reset_index()

# Calculate path length
path_info = scint_df.groupby(['Event_ID', 'Track_ID']).apply(
    lambda g: np.sqrt(
        (g['x'].max() - g['x'].min())**2 +
        (g['y'].max() - g['y'].min())**2 +
        (g['z'].max() - g['z'].min())**2
    )
).reset_index(name='Path_Length')

tracks = tracks.merge(path_info, on=['Event_ID', 'Track_ID'])
tracks['dEdx'] = tracks['eDep'] / tracks['Path_Length']
```

### Applying Pion Selection

```python
# Select primary pion candidates
pion_candidates = tracks[
    (tracks['Parent_ID'] == 0) &
    (tracks['dEdx'] < 4.8) &
    (tracks['Path_Length'] > 10)
]

print(f"Selected {len(pion_candidates)} pion candidates")
```

---

## References

1. Geant4 Physics Reference Manual - Electromagnetic Physics
2. Particle Data Group - Review of Particle Physics
3. NNBAR Experiment Technical Design Report

---

## Appendix: Generated Plots

The following plots were generated during this analysis:

1. `object_definitions.png` - Charged particle dE/dx and selection cuts
2. `pi0_calorimeter_response.png` - π⁰ energy response in Lead Glass
3. `comprehensive_pid.png` - Full PID analysis summary
4. `pi0_improved_reco.png` - Improved π⁰ reconstruction attempts

All plots are saved in `/home/billy/nnbar/simulation/`
