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
last_updated: 2026-05-10
---

# Subsystem — event selection / cut-flow

*Charter.* Owns leaves S.1–S.6. The thesis Ch 10 cut-based selection
plus its multivariate replacement.

## 1. Leaf S.1–S.6 cut-flow schema

Inputs are the plan-36 `events.csv` variables. Outputs are the
`pass_*` booleans below plus `passes_preliminary_selection`. The
current L3 source defines numeric cut defaults in
`ReconstructionConfig` (`reconstruction.py:14-41`), computes the
production event-row booleans in `_selection_flags`
(`vertex.py:293-319`), writes the event row in `summarize_events`
(`vertex.py:322-447`), fixes the cumulative order in `CUT_ORDER`
(`selection.py:13-20`), computes cumulative counts in `cutflow_counts`
(`selection.py:95-111`), and exposes them through the CLI `_cutflow`
wrapper (`cli.py:31-32`):
`pass_scintillator_energy → pass_tpc_foil_track → pass_pion_count →
pass_invariant_mass → pass_sphericity → pass_scintillator_balance`.

| Leaf | CLI order | Input variable(s) | Produced column | Threshold / rule | Thesis source | Code citation |
|---|---:|---|---|---|---|---|
| S.1 | 1 | `scintillator_edep` | `pass_scintillator_energy` | `20 ≤ Σ scintillator eDep ≤ 2000 MeV` | licentiate Ch 10 cut-flow; defaults documented as Ch 9 in plan v0.1 | thresholds in `ReconstructionConfig` (`reconstruction.py:14-41`); input row in `summarize_events` (`vertex.py:322-447`); flag in `_selection_flags` (`vertex.py:293-319`) |
| S.1 | 2 | `has_foil_tpc_track` | `pass_tpc_foil_track` | at least one reconstructed TPC track projected to the foil | licentiate Ch 10 cut-flow | input row in `summarize_events` (`vertex.py:322-447`); flag in `_selection_flags` (`vertex.py:293-319`) |
| S.2 | 3 | `pion_multiplicity` | `pass_pion_count` | `pion_multiplicity ≥ 1` | licentiate Ch 10 cut-flow | input row in `summarize_events` (`vertex.py:322-447`); flag in `_selection_flags` (`vertex.py:293-319`) |
| S.3 | 4 | `visible_invariant_mass` | `pass_invariant_mass` | finite visible mass `≥ 500 MeV` | licentiate Ch 10 cut-flow | threshold in `ReconstructionConfig` (`reconstruction.py:14-41`); input row in `summarize_events` (`vertex.py:322-447`); flag in `_selection_flags` (`vertex.py:293-319`) |
| S.4 | 5 | `sphericity` | `pass_sphericity` | finite sphericity `≥ 0.2` | licentiate Ch 10 cut-flow | threshold in `ReconstructionConfig` (`reconstruction.py:14-41`); input row in `summarize_events` (`vertex.py:322-447`); flag in `_selection_flags` (`vertex.py:293-319`) |
| S.5 | 6 | `upper_scintillator_edep`, `lower_scintillator_edep` | `pass_scintillator_balance` | upper `≤ 320 MeV` and lower `≤ 930 MeV` | licentiate Ch 10 cut-flow | thresholds in `ReconstructionConfig` (`reconstruction.py:14-41`); input row in `summarize_events` (`vertex.py:322-447`); flag in `_selection_flags` (`vertex.py:293-319`) |
| S.6 | — | all S.1–S.5 booleans | `passes_preliminary_selection` | logical AND of the six cut booleans | licentiate Ch 10 final preselection | AND in `_selection_flags` (`vertex.py:293-319`); order/counts in `CUT_ORDER` and `cutflow_counts` (`selection.py:13-20`, `selection.py:95-111`); CLI wrapper in `_cutflow` (`cli.py:31-32`) |

### 1.1 Per-cut and cumulative accounting

The event table stores the six `pass_*` columns as independent cut
flags plus `passes_preliminary_selection` as their logical AND. The
`cutflow_counts` report, reached by the CLI `_cutflow` wrapper, is
cumulative in the `CUT_ORDER` order above. Plan 47 rows must therefore
store both:

- `n_pass_individual_<cut>` — count passing that cut alone; and
- `n_after_<cut>` — count passing all cuts up to that CLI step.

The Ch 10 reproduction claim uses the cumulative counts. N-1 / ROC
studies in plan 41 use the independent flags and may propose
retuned thresholds, but those retuned thresholds require a plan-05
DEC entry and must not overwrite the Ch 10 baseline columns.

Truth-use boundary: S.1–S.6 consume only event-variable columns. Any
truth/provenance dependence must be resolved upstream before the row is
eligible for the reproduction ledger.

### 1.2 Cut-column naming contract

The current source uses singular `pass_*` names for the six individual
cut booleans and `passes_preliminary_selection` for the final AND. Plan
37 treats those names as the canonical Ch 10 reproduction columns. If a
future table adds plural aliases for external consumers, those aliases
must be generated from the canonical `pass_*` columns and must not
replace them in the plan-47 ledger.

### 1.3 A+ citation and CLI-surface audit

This plan's source citations were re-checked against the current L3
source on 2026-05-10 before the cut-flow table above was frozen:

| Cited contract | Verifier evidence | Status |
|---|---|---|
| Numeric cut defaults | `class ReconstructionConfig` resolves at `reconstruction.py:14`, inside the cited `reconstruction.py:14-41` range. | keep citation |
| Individual cut booleans and final AND | `def _selection_flags` resolves at `vertex.py:293`, inside the cited `vertex.py:293-319` range. | keep citation |
| Event-row columns consumed by the cuts | `def summarize_events` resolves at `vertex.py:322`, inside the cited `vertex.py:322-447` range. | keep citation |
| Cumulative order tuple | `CUT_ORDER` resolves at `selection.py:13`, inside the cited `selection.py:13-20` range. | keep citation |
| Independent table evaluator | `def evaluate_event_selection` resolves at `selection.py:37`, inside the cited `selection.py:37-72` range. | keep citation |
| Cumulative count implementation | `def cutflow_counts` resolves at `selection.py:95`, inside the cited `selection.py:95-111` range. | keep citation |
| CLI wrapper | `def _cutflow` resolves at `cli.py:31`, inside the cited `cli.py:31-32` range. | keep citation |

Plan 37 does not specify a runtime CLI command; it cites `CUT_ORDER`
and `cutflow_counts` for ordering/counts plus the internal `_cutflow`
wrapper for CLI delegation. The L3 module help was smoke-tested and
returned non-error help, so no unimplemented CLI surface is introduced
here. No legacy split-study files are cited by this plan.

### 1.4 Machine-readable cut-flow fixture

The Ch 10 reproduction output serialises each cut into one row so plan
47 can compare independent and cumulative counts without parsing prose:

| Field | Required content | Review rule |
|---|---|---|
| `cut_id` | `S1_scintillator_energy` through `S6_preliminary_selection` | stable key matching §1 order |
| `cli_order` | integer 1-6 or null for the final AND row | must match `CUT_ORDER` for the six individual cuts |
| `input_columns` | list of event-table variables from §1 | every name must exist in plan-36 output schema |
| `produced_column` | canonical singular `pass_*` column or `passes_preliminary_selection` | no plural alias may replace the canonical name |
| `threshold_expression` | literal threshold/rule from §1 | preserves Ch 10 baseline before retuning |
| `n_pass_individual` | count passing this cut alone | computed before cumulative masking |
| `n_after_cut` | count after applying all cuts through `cli_order` | null only for the final AND row if it duplicates S.6 |
| `decision_dec_id` | `DEC-37-CH10-CUTFLOW-BASELINE` until retuned | retuned cuts need a separate DEC and new columns |

Review fixtures must include one signal row set and one cosmic row set.
The signal fixture checks the approximately 70% final acceptance target;
the cosmic fixture checks that zero survivors are reported with the
plan-04 interval convention rather than as exact zero background.

## 2. Closure-test specification / Ch 10 reproduction

1. **Dataset ids:** `sig_foil_v3` for signal acceptance and
   `cosmic_cry_essLund_overburdenA_v1` for cosmic rejection; beam
   neutron samples join later through plan 41.
2. **Observable:** cumulative `cutflow_counts` / CLI `_cutflow` counts
   in the §1 order, final `passes_preliminary_selection` acceptance,
   per-cut efficiencies, and surviving-event row ids for audit.
3. **Fitter / estimator:** no fit is applied to the baseline cut-flow;
   quote binomial/Wilson intervals for acceptance and Poisson or exact
   upper limits for zero-survivor backgrounds per plan 04.
4. **Pass criterion:** reproduce the licentiate Ch 10 target recorded
   in plan 47: approximately `70%` signal acceptance and `0` surviving
   cosmics in the finite reproduction sample, with every cut threshold
   matching §1.
5. **Audit hook:** rerun after dropping upstream truth/provenance
   columns. Cut booleans, cumulative counts, and final pass/fail must
   be unchanged.

## 3. N-1 and ROC

Per plan 41:

- N-1 plot for every variable in §1.
- ROC curve over each continuous variable (visible mass, sphericity,
  upper/lower scint).
- Significance scan to identify a possibly better operating point.

## 4. Selection alternative comparison matrix

| Candidate | S.6 decision rule | Current/source citation | Class-A status | Comparison metric | Reporting rule |
|---|---|---|---|---|---|
| **Thesis cut-flow baseline** | Apply §1 cuts in `CUT_ORDER` order and require `passes_preliminary_selection`. | `_selection_flags` (`vertex.py:293-319`), `CUT_ORDER` (`selection.py:13-20`), and `cutflow_counts` (`selection.py:95-111`). | Production-eligible once upstream truth leaks are removed. | Reproduce Ch 10 signal acceptance and cosmic survivors. | Primary thesis reproduction number. |
| **Retuned rectangular cuts** | Re-derive thresholds from plan-41 N-1 / ROC scans while keeping the same variables. | Reuses §1 produced columns. | Eligible only with DEC entries for threshold changes. | Expected limit sensitivity vs baseline. | Report alongside baseline; do not overwrite Ch 10. |
| **BDT selection** | Train a bounded tree model on plan-36 variables and threshold the score. | Plan 57-governed replacement for S.6. | Eligible after frozen features, training provenance, and audit. | ROC AUC, background rejection at fixed signal efficiency, calibration. | Ladder comparison row; baseline remains quoted. |
| **Neural selection** | Train a small NN on the same feature contract. | Plan 57 alternative. | Eligible only if deterministic export and interpretability artifacts land. | Same as BDT plus seed/export reproducibility. | Use only if it materially beats BDT. |
| **Truth-informed oracle** | Use true signal/background labels or truth ancestry directly. | Validation labels from sample registry / truth tables. | Not production-eligible. | Upper-bound only. | Never part of cut-flow or final acceptance. |

The MVA replacement is reported alongside, never overriding, the
cut-based result for thesis-quoted numbers (plan 06 §6 conservatism).

### 4.1 Decision-log stubs for selection changes

Any change to a cut threshold, cut order, or S.6 replacement is a
load-bearing analysis decision and needs plan-05 approval before plan
47 can quote it:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-37-CH10-CUTFLOW-BASELINE` | Freeze the six Ch 10 cuts, thresholds, and `CUT_ORDER` cumulative order as the reproduction baseline | plan-47 row reproducing signal acceptance and cosmic survivors with §1 thresholds |
| `DEC-37-RETUNED-CUTS` | Approve any retuned rectangular threshold set from plan 41 | N-1/ROC scan, expected-limit comparison, and explicit statement that Ch 10 columns remain unchanged |
| `DEC-37-MVA-SELECTION` | Permit BDT or NN S.6 replacement to be reported beside the cut-flow baseline | plan-57 feature freeze, plan-38 ladder row, calibration curve, and background-rejection evidence |
| `DEC-37-TRUTH-BLIND-GATE` | Declare the selection eligible for final quotes after upstream truth leaks are removed | plan-01 audit plus rerun showing all `pass_*` booleans unchanged when truth/provenance columns are dropped |

Until the relevant DEC is approved, alternative S.6 outputs are
diagnostic/ladder artifacts only and cannot supersede the baseline
cut-flow.

## 5. Acceptance criteria

- §1 cuts implemented exactly.
- §2 reproduction green.
- §3 N-1 / ROC produced.
- §4 MVA scored.

## 6. Dependencies

- **04, 24, 36, 38, 41, 47, 57** — inputs.
- *Consumed by:* plans 41–46 (analysis level), 47, 50.
