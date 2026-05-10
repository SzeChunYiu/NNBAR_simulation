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

### Next measurement (selection branch)

Reproduce the licentiate's cut-flow on the registered signal sample
(plan 20) and cosmic sample (plan 21).
