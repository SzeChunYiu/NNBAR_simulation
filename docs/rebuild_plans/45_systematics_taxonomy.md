---
id: 45_systematics_taxonomy
title: Systematics taxonomy — named uncertainties + correlation tree
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 12_physics_list_audit, 13_signal_model, 14_background_models, 17_field_calibration, 18_intercalibration, 38_truth_substitution_ladder]
outputs:
  - {path: docs/rebuild_plans/45_systematics_taxonomy.md, schema: this file}
  - {path: data/systematics/registry.yml, schema: machine-readable nuisance list}
acceptance:
  - {test: every nuisance parameter has name, source, ±1σ definition, affected observables, method: registry review, pass_when: full coverage}
  - {test: correlation matrix between nuisances declared, method: §2 review, pass_when: matrix populated}
  - {test: every quoted result cites the nuisances applied, method: ledger cross-reference, pass_when: zero unflagged numbers}
risks:
  - {risk: double-counting if a calibration uncertainty enters both as a Class C constant and a nuisance parameter, mitigation: §3 single-source rule}
estimated_effort: M
last_updated: 2026-05-09
---

# Systematics taxonomy

*Charter.* The single registry of every systematic uncertainty. Each
nuisance is named, defined, sourced, scoped, and assigned a
correlation with every other nuisance. Plan 47 ledger and plan 50
defence package refer to nuisance names verbatim.

## 1. Nuisance registry (initial set)

| ID | Name | Source | ±1σ definition | Affects |
|---|---|---|---|---|
| N1 | TPC W-value | plan 17 §3 | reference 26.0 ± 1.5 eV vs current 23.6 eV | dE/dx, charged PID |
| N2 | Scintillator yield | plan 18 §3 | 11136 ± Δ photons/MeV (Δ to be set in plan 18) | scint energy, EL/ET |
| N3 | LG calibration | plan 18 §4 | per-energy slope ± fit uncertainty | LG energy, π⁰ mass |
| N4 | Physics list | plan 12 §3 | nominal vs qgsp_bert vs qgsp_bic | hadronic processes |
| N5 | Signal branching | plan 13 §4 | nominal vs amsler1991 vs friedman2007 | per-channel ε_signal |
| N6 | Cosmic flux | plan 14 §1.4 | ±15% on CRY normalisation | cosmic rate |
| N7 | Beam-neutron flux | plan 22 | ±10% (from ESS quoted) | beam-neutron rate |
| N8 | Geometry alignment | plan 16 §3 | perfect vs nominal_survey vs worst_case_construction | vertex resolution, π⁰ mass |
| N9 | Optical-photon yield | plan 18 §4 | optical-on vs optical-off paired | LG energy in optical builds |
| N10 | Material budget | plan 15 §6 | ±5% on per-region X₀ | photon conversion rate |

## 2. Correlation matrix

A nuisance is fully correlated with itself, fully anti-correlated
with its inverse, and otherwise nominally uncorrelated. Special
cases:

- N1 (W-value) and N4 (physics list) are slightly correlated through
  shared ionisation modelling — fix coefficient empirically from
  paired runs.
- N5 (signal branching) and N6/N7 (background flux) are uncorrelated.

## 3. Single-source rule

A calibration uncertainty enters the analysis exactly once. If it
appears as a Class C constant uncertainty (plan 04 §6) it does not
also appear as a nuisance parameter; if it appears as a nuisance, the
Class C value is the nominal.

## 4. Acceptance criteria

- §1 registry complete; ≥ 10 nuisances.
- §2 correlation matrix populated.
- §3 single-source rule audited (no double-counting).
- Plan 47 ledger and plan 50 defence package cite nuisance IDs by
  name.

## 5. Risks

- *Risk:* nuisances missing for unmodelled effects (plan 01 §6
  limitations).
  *Mitigation:* §1 N* assignments include "limitation" rows for L1,
  L2, L3, L4 explicitly; plan 50 surfaces them as "unbounded by
  current rebuild".

## 6. Dependencies

- **04, 12, 13, 14, 17, 18, 38** — inputs.
- *Consumed by:* plan 46 (significance), plan 47, plan 50.

## 7. References

- ATLAS / CMS standard nuisance-parameter conventions.
