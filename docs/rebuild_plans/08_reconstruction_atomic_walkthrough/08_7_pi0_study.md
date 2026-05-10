---
id: 08_7
title: Reconstruction atomic walkthrough — pi0 study
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/pi0_study.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_7_pi0_study.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# π⁰ study — split from plan 08

This split file preserves and deepens plan 08 §7 so the main walkthrough
stays below the 500-line cap.

## 7. π⁰ study (pi0_study.py, 1974 lines)

The 2 KLOC file implements the truth-vs-reco π⁰ mass ladder used to
explain the thesis Chapter 8 selection and to prototype plan 38's
truth-substitution ladder. It is being documented in multiple logical
units.

Public surface currently detected from source:

- `two_photon_mass_mev(energy1, direction1, energy2, direction2)`
- `evaluate_pi0_mass_ladder(output_dir, run, reconstruction)`
- `event_rows(report)`

### 7.1 Constants and stage schema

- `PI0_MASS_MEV = 134.9768` (`pi0_study.py:16`) is the reference mass
  used by stage summaries.
- `MASS_STAGE_COLUMNS` maps ladder stage names to row columns for truth
  daughters, truth-direction/reco-energy, reco-direction/truth-energy,
  full reco, truth-matched full reco, global and cross-validated energy
  scales, photon-response scales, and containment-binned scales
  (`pi0_study.py:17–31`). These are study-output columns, not raw
  parquet columns.

### 7.2 `two_photon_mass_mev(energy1, direction1, energy2, direction2)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/pi0_study.py:75–91`.

**Inputs:** two photon energies in MeV and two direction vectors supplied
by callers inside the study. No parquet columns are read directly by this
helper. In the larger ladder, energies and directions may come from Class
B truth daughters, reconstructed photon rows, or mixed truth/reco rungs;
those caller-specific column reads are documented with
`evaluate_pi0_mass_ladder` in later §7 units.

**Decision rule:** if either energy is non-finite or negative, return
`NaN` (`pi0_study.py:83–84`). Directions are normalized with
`_unit_vector`; zero or non-finite vectors return `NaN` (`pi0_study.py:85–88`).
The invariant mass assumes two massless photons:
`mass² = 2 * energy1 * energy2 * (1 - dot(u1, u2))`, with the dot product
clipped to [-1, 1] and negative roundoff protected by `max(mass2, 0)`
(`pi0_study.py:89–91`).

**Outputs:** one float mass in MeV, or `NaN` when inputs are unusable.

**Truth reads:** none directly.

### 7.3 Pending public entries

`evaluate_pi0_mass_ladder(...)` (`pi0_study.py:1876–1969`) and
`event_rows(report)` (`pi0_study.py:1971–1974`) remain to be expanded with
line-level input/output/truth-read detail. The intervening private helpers
implement energy-scale, photon-response, containment, candidate-taxonomy,
truth-gamma-coverage, detector-deposit lookup, and per-event row-building
stages consumed by `evaluate_pi0_mass_ladder`.
