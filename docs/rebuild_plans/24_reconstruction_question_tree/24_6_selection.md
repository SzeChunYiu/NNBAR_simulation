---
id: 24_6_selection_branch
title: Reconstruction question tree - selection branch
version: 0.1
status: draft
owner: Methodology Council
parent: 24_reconstruction_question_tree
last_updated: 2026-05-09
---

# Reconstruction question tree - selection branch

This file is a split-out branch of `docs/rebuild_plans/24_reconstruction_question_tree.md`
created to keep each plan file under the 500-line cap. It inherits the
truth-leakage gate, acceptance criteria, dependencies, and references from
plan 24.

## 6. Selection branch

**Which combination of event variables maximises signal-to-background
under the realism contract?**

Answer now: the licentiate Ch 10 cut-flow achieves ~70% signal
acceptance with zero surviving cosmics in finite sample. Reproduction
gates the rebuild's legitimacy; improvement (cut optimisation,
multivariate replacement) is scored against this baseline.

### 6.1 Leaves under selection

| Leaf ID | Decision |
|---|---|
| `S.1` | Pre-selection (TPC-foil track presence, scint energy window) |
| `S.2` | Pion-multiplicity cut |
| `S.3` | Visible invariant mass cut |
| `S.4` | Sphericity cut |
| `S.5` | Hemisphere balance cut |
| `S.6` | Final-rate computation (with statistical and systematic uncertainty) |

**Owning subsystem plan:** plan 37 (event selection).

Leaf S.1: vertex + scintillator energy → pre-selection flags
  inputs (Class A): V.5 foil-compatible vertex flag, E.1 total and
                    scintillator energy, E.8 timing split, and plan 37
                    thresholds for scintillator energy and foil-track
                    presence
  forbidden (Class B): truth annihilation vertex, truth primary name,
                       Track_ID, Parent_ID, truth signal/background
                       labels inside the event decision
  decision rule: pass pre-selection only when at least one reconstructed
                 TPC track projects to a foil-compatible vertex and the
                 scintillator energy lies in the thesis Ch 9 window
                 (20-2000 MeV in plan 37 §1).
  output schema: {event_id: int64, pass_tpc_foil_track: bool,
                  pass_scintillator_energy: bool,
                  passes_preselection: bool,
                  scintillator_energy_mev: float64,
                  preselection_reason: string}
  allowed truth use: validation_only
  downstream consumers: S.6; plans 37, 41, 47

Leaf S.2: reconstructed pion counts → pion-multiplicity cut
  inputs (Class A): E.9 object multiplicities, C.5/C.6 charged PID
                    outputs, P.5-P.7 selected π0 candidates, and plan
                    37 pion-count threshold
  forbidden (Class B): truth pion multiplicity, truth particle Name,
                       Track_ID, Parent_ID, Interaction ancestry
  decision rule: count reconstructed charged-pion and π0 candidates
                 that survive their observable validity gates and pass
                 the licentiate baseline when pion multiplicity is at
                 least one; truth final-state multiplicity is only a
                 validation target.
  output schema: {event_id: int64, n_reconstructed_pions: int32,
                  n_charged_pions: int32, n_pi0: int32,
                  pion_count_threshold: int32,
                  pass_pion_count: bool}
  allowed truth use: validation_only
  downstream consumers: S.6; plans 37, 41, 47

Leaf S.3: visible invariant mass → mass cut
  inputs (Class A): E.7 visible invariant mass and uncertainty,
                    object-validity flags, and plan 37 visible-mass
                    threshold
  forbidden (Class B): truth invariant mass, truth particle
                       four-vectors, Track_ID, Parent_ID, Name
  decision rule: pass when reconstructed visible invariant mass is
                 valid and at least the thesis Ch 9 threshold
                 (500 MeV in plan 37 §1), with no substitution from
                 truth four-vectors when objects are missing.
  output schema: {event_id: int64, visible_invariant_mass_mev:
                  float64, mass_threshold_mev: float64,
                  mass_valid: bool, pass_invariant_mass: bool}
  allowed truth use: validation_only
  downstream consumers: S.6; plans 37, 41, 47

### Next measurement (selection branch)

Reproduce the licentiate's cut-flow on the registered signal sample
(plan 20) and cosmic sample (plan 21).
