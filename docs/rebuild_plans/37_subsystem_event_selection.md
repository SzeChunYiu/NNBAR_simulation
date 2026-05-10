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

## 1. Leaf S.1–S.6 cut-flow schema

Inputs are the plan-36 `events.csv` variables. Outputs are the
`pass_*` booleans below plus `passes_preliminary_selection`. Plan 08
identifies `_selection_flags` as the producer
(`reconstruction.py:1573–1600`) and `summarize_events` as the writer
(`reconstruction.py:1730–1733`). The CLI cumulative order is fixed by
`cli._cutflow` (`cli.py:37–44`, plan 08 §4.1):
`pass_scintillator_energy → pass_tpc_foil_track → pass_pion_count →
pass_invariant_mass → pass_sphericity → pass_scintillator_balance`.

| Leaf | CLI order | Input variable(s) | Produced column | Threshold / rule | Thesis source | Code citation |
|---|---:|---|---|---|---|---|
| S.1 | 1 | `scintillator_edep` | `pass_scintillator_energy` | `20 ≤ Σ scintillator eDep ≤ 2000 MeV` | licentiate Ch 10 cut-flow, defaults documented as Ch 9 in plan v0.1 | config `selection_scintillator_energy_min/max` (`reconstruction.py:42–43`); flag at `1573–1582` |
| S.1 | 2 | `has_foil_tpc_track` | `pass_tpc_foil_track` | at least one reconstructed TPC track projected to the foil | licentiate Ch 10 cut-flow | flag at `reconstruction.py:1583`; upstream `has_foil_tpc_track` row at `1723–1724` |
| S.2 | 3 | `pion_multiplicity` | `pass_pion_count` | `pion_multiplicity ≥ 1` | licentiate Ch 10 cut-flow | flag at `reconstruction.py:1584`; multiplicity at `1721–1722` |
| S.3 | 4 | `visible_invariant_mass` | `pass_invariant_mass` | finite visible mass `≥ 500 MeV` | licentiate Ch 10 cut-flow | config `selection_invariant_mass_min` (`reconstruction.py:44`); flag at `1585–1586` |
| S.4 | 5 | `sphericity` | `pass_sphericity` | finite sphericity `≥ 0.2` | licentiate Ch 10 cut-flow | config `selection_sphericity_min` (`reconstruction.py:45`); flag at `1587–1588` |
| S.5 | 6 | `upper_scintillator_edep`, `lower_scintillator_edep` | `pass_scintillator_balance` | upper `≤ 320 MeV` and lower `≤ 930 MeV` | licentiate Ch 10 cut-flow | config `selection_upper/lower_scintillator_max` (`reconstruction.py:46–47`); flag at `1589–1592` |
| S.6 | — | all S.1–S.5 booleans | `passes_preliminary_selection` | logical AND of the six cut booleans | licentiate Ch 10 final preselection | AND at `reconstruction.py:1593–1600`; cumulative report in `cli._cutflow` |

Truth-use boundary: S.1–S.6 consume only event-variable columns. Any
truth/provenance dependence must be resolved upstream before the row is
eligible for the reproduction ledger.

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

## 4. Selection alternative comparison matrix

| Candidate | S.6 decision rule | Current/source citation | Class-A status | Comparison metric | Reporting rule |
|---|---|---|---|---|---|
| **Thesis cut-flow baseline** | Apply §1 cuts in `cli._cutflow` order and require `passes_preliminary_selection`. | `_selection_flags` (`reconstruction.py:1573–1600`) and `cli._cutflow` (`cli.py:37–44`). | Production-eligible once upstream truth leaks are removed. | Reproduce Ch 10 signal acceptance and cosmic survivors. | Primary thesis reproduction number. |
| **Retuned rectangular cuts** | Re-derive thresholds from plan-41 N-1 / ROC scans while keeping the same variables. | Reuses §1 produced columns. | Eligible only with DEC entries for threshold changes. | Expected limit sensitivity vs baseline. | Report alongside baseline; do not overwrite Ch 10. |
| **BDT selection** | Train a bounded tree model on plan-36 variables and threshold the score. | Plan 57-governed replacement for S.6. | Eligible after frozen features, training provenance, and audit. | ROC AUC, background rejection at fixed signal efficiency, calibration. | Ladder comparison row; baseline remains quoted. |
| **Neural selection** | Train a small NN on the same feature contract. | Plan 57 alternative. | Eligible only if deterministic export and interpretability artifacts land. | Same as BDT plus seed/export reproducibility. | Use only if it materially beats BDT. |
| **Truth-informed oracle** | Use true signal/background labels or truth ancestry directly. | Validation labels from sample registry / truth tables. | Not production-eligible. | Upper-bound only. | Never part of cut-flow or final acceptance. |

The MVA replacement is reported alongside, never overriding, the
cut-based result for thesis-quoted numbers (plan 06 §6 conservatism).

## 5. Acceptance criteria

- §1 cuts implemented exactly.
- §2 reproduction green.
- §3 N-1 / ROC produced.
- §4 MVA scored.

## 6. Dependencies

- **04, 24, 36, 38, 41, 47, 57** — inputs.
- *Consumed by:* plans 41–46 (analysis level), 47, 50.
