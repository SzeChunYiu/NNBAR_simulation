---
id: 37_subsystem_event_selection
title: Subsystem — event selection / cut-flow (leaves S.1–S.6)
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 24_reconstruction_question_tree, 36_subsystem_event_variables, 38_truth_substitution_ladder, 41_n_minus_1_and_roc_studies, 47_reproduction_ledger, 57_mva_method_protocol]
outputs:
  - {path: docs/rebuild_plans/37_subsystem_event_selection.md, schema: this file}
acceptance:
  - {test: every cut in the cut-flow has its threshold cited, the thesis chapter, and a §-row, method: §2 table, pass_when: complete}
  - {test: licentiate Ch 10 cut-flow reproduces "≈ 70% signal acceptance, 0 surviving cosmics", method: plan 47 ledger row, pass_when: reproduces}
  - {test: BDT/NN replacement scored on the ladder leaf S.6, method: plan 38, pass_when: matrix entry}
risks:
  - {risk: licentiate threshold values are sample-specific and don't generalise, mitigation: §3 plan 41 N-1 and ROC re-derives optimal cuts on the new sample}
estimated_effort: L
last_updated: 2026-05-09
---

# Subsystem — event selection / cut-flow

*Charter.* Owns leaves S.1–S.6. The thesis Ch 10 cut-based selection
plus its multivariate replacement.

## 1. Cuts (thesis Ch 9 defaults from `reconstruction.py`)

| Leaf | Cut | Threshold | Source |
|---|---|---|---|
| S.1 | `pass_scintillator_energy` | `selection_scintillator_energy_min ≤ Σ scint ≤ max` (20–2000 MeV) | thesis Ch 9 |
| S.1 | `pass_tpc_foil_track` | ≥ 1 TPC track foil-projecting | thesis Ch 9 |
| S.2 | `pass_pion_count` | π multiplicity ≥ 1 | thesis Ch 9 |
| S.3 | `pass_invariant_mass` | visible mass ≥ 500 MeV | thesis Ch 9 |
| S.4 | `pass_sphericity` | sphericity ≥ 0.2 | thesis Ch 9 |
| S.5 | `pass_scintillator_balance` | upper ≤ 320 MeV AND lower ≤ 930 MeV | thesis Ch 9 |
| S.6 | `passes_preliminary_selection` | AND of S.1–S.5 | thesis Ch 9 |

Cumulative cut-flow is reported by `cli.summarize`'s `_cutflow`
helper (plan 08 §4.1).

## 2. Reproduction

Plan 47 ledger row: licentiate Ch 10 final result = "≈ 70% signal
acceptance, 0 cosmic survivors in finite sample". Reproducing this
on `sig_foil_v3` + `cosmic_cry_essLund_overburdenA_v1` is a green
gate.

## 3. N-1 and ROC

Per plan 41:

- N-1 plot for every variable in §1.
- ROC curve over each continuous variable (visible mass, sphericity,
  upper/lower scint).
- Significance scan to identify a possibly better operating point.

## 4. MVA replacement (target improvement)

Per plan 57: train a BDT or NN on event variables (plan 36 §2) to
classify signal vs cosmic + beam-neutron backgrounds.

Scored against the cut-based baseline on the ladder. The MVA
replacement is reported alongside, never overriding, the cut-based
result for thesis-quoted numbers (per plan 06 §6 conservatism).

## 5. Acceptance criteria

- §1 cuts implemented exactly.
- §2 reproduction green.
- §3 N-1 / ROC produced.
- §4 MVA scored.

## 6. Dependencies

- **04, 24, 36, 38, 41, 47, 57** — inputs.
- *Consumed by:* plans 41–46 (analysis level), 47, 50.
