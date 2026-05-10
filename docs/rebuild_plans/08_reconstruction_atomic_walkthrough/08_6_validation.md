---
id: 08_6_validation
title: Reconstruction atomic walkthrough — validation public surface
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough, 01_realism_contract, 09_io_schema_data_dictionary]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/validation.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_6_validation.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# Validation public surface — split from plan 08

This split file preserves and deepens plan 08 §6 so the main walkthrough
stays below the 500-line cap while validation receives function-level detail.

## 6. Validation (validation.py, 509 lines)

### 6.1 Public entry points (inferred from `cli.py` imports)

- `evaluate_reconstruction_truth(result_dict) → dict`
  — runs one report against a single reconstructed result dict
  augmented with the `Particle` truth table.
- `aggregate_reconstruction_truth(list_of_results) → dict`
  — combines per-run reports.
- `assess_validation_readiness(report, **floors) → dict`
  — applies user-supplied floors and returns a `passed` flag plus
  per-metric pass/fail.

### 6.2 What is reported (per `reconstruction.md` §"validate-reco" doc)

- Charged π/proton PID metrics with floors.
- Lead-glass charged/neutral matching metrics.
- Electron-pair candidate purity (recomputed from carried truth
  names on the candidate table).
- Pi0 selection metrics under multiple selectors:
  - `pi0_selection` (strict thesis selection)
  - `pi0_mass_window_selection` (looser mass-window-only)
  - `pi0_mass_window_neutral_event_selection` (mass-window + no
    charged π/p in event)
  - `pi0_mass_window_track_isolated_selection` (mass-window +
    `near_charged_track_photons == 0`)
  - `pi0_mass_window_isolated_neutral_event_selection` (both)
  - `pi0_mass_window_high_energy_selection` (mass-window +
    `total_energy ≥ 400 MeV`)
  - `pi0_mass_window_prompt_timing_selection` (mass-window +
    photon timing within 2 ns of the vertex flight time)
- `non_truth_events`, `false_positive_event_rate` per pi0 selector.

Each metric carries a `usable` flag — single-class samples or
unlabelled samples never satisfy the gate.

### 6.3 Truth use

`validation.py` is the canonical home for `@validation_only`-decorated
code. Its read accesses to `Track_ID`, `Parent_ID`, `Name`, and primary
truth columns are *expected* and not flagged by the realism audit.
