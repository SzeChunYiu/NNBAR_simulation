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

Baseline cut identity rows, before plan-47 counts are attached:

| `cut_id` | `cli_order` | `input_columns` | `produced_column` | `threshold_expression` | `n_pass_individual` | `n_after_cut` | `decision_dec_id` |
|---|---:|---|---|---|---:|---:|---|
| `S1_scintillator_energy` | 1 | [`scintillator_edep`] | `pass_scintillator_energy` | `20 <= scintillator_edep <= 2000 MeV` | null | null | `DEC-37-CH10-CUTFLOW-BASELINE` |
| `S1_tpc_foil_track` | 2 | [`has_foil_tpc_track`] | `pass_tpc_foil_track` | `has_foil_tpc_track == true` | null | null | `DEC-37-CH10-CUTFLOW-BASELINE` |
| `S2_pion_count` | 3 | [`pion_multiplicity`] | `pass_pion_count` | `pion_multiplicity >= 1` | null | null | `DEC-37-CH10-CUTFLOW-BASELINE` |
| `S3_invariant_mass` | 4 | [`visible_invariant_mass`] | `pass_invariant_mass` | `finite visible_invariant_mass >= 500 MeV` | null | null | `DEC-37-CH10-CUTFLOW-BASELINE` |
| `S4_sphericity` | 5 | [`sphericity`] | `pass_sphericity` | `finite sphericity >= 0.2` | null | null | `DEC-37-CH10-CUTFLOW-BASELINE` |
| `S5_scintillator_balance` | 6 | [`upper_scintillator_edep`, `lower_scintillator_edep`] | `pass_scintillator_balance` | `upper <= 320 MeV and lower <= 930 MeV` | null | null | `DEC-37-CH10-CUTFLOW-BASELINE` |
| `S6_preliminary_selection` | null | all six `pass_*` columns above | `passes_preliminary_selection` | logical AND of all six cut booleans | null | null | `DEC-37-CH10-CUTFLOW-BASELINE` |

The count columns are null in the contract row and are populated only by
dataset-specific plan-47 reproduction rows.

Initial cut-flow result-row examples:

| `cutflow_result_id` | `dataset_id` | `cut_id` | Count fields | Required interval/caveat |
|---|---|---|---|---|
| `sig_foil_v3.S1_scintillator_energy.ch10` | `sig_foil_v3` | `S1_scintillator_energy` | fill `n_pass_individual` and `n_after_cut` from the saved event table | Wilson interval on cumulative signal efficiency |
| `sig_foil_v3.S6_preliminary_selection.ch10` | `sig_foil_v3` | `S6_preliminary_selection` | final `passes_preliminary_selection` acceptance | compare to the plan-47 approximately 70% target |
| `cosmic_overburdenA.S5_scintillator_balance.ch10` | `cosmic_cry_essLund_overburdenA_v1` | `S5_scintillator_balance` | cumulative survivor count after all six individual cuts | if zero, hand off F-C upper limit rather than exact zero |
| `beam_direct.S6_preliminary_selection.diag` | `beam_neutron_hibeam_direct_v1` | `S6_preliminary_selection` | diagnostic final survivor count for beam-neutron extension | cannot feed plan-44 rate sum until sample/rate DEC is signed |

These examples define count-row shape only. They do not replace the
baseline identity rows, and they must be regenerated whenever the
selection config id or input event hash changes.

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

### 2.1 Machine-readable truth-blind selection audit fixture

Every Ch 10 reproduction run writes a paired audit row proving that
selection decisions do not depend on upstream truth/provenance fields:

| Field | Required content | Review rule |
|---|---|---|
| `selection_config_id` | Ch 10 baseline or approved retune id | must match the cut-flow fixture |
| `dataset_id` | signal, cosmic, or beam-neutron sample id | every quoted cut-flow sample gets an audit row |
| `input_event_hash` | hash of the original event table | establishes the audited input snapshot |
| `truth_blind_event_hash` | hash after dropping Class B/provenance columns | required even when no such columns are present |
| `cut_boolean_hash_before`, `cut_boolean_hash_after` | hashes of all §1 `pass_*` and final AND columns | must match exactly |
| `cutflow_counts_before`, `cutflow_counts_after` | cumulative counts from `CUT_ORDER` | must match exactly |
| `changed_event_ids` | list of event ids whose selection changed | must be empty for production eligibility |
| `audit_status` | `pass`, `fail`, or `diagnostic_only` | only `pass` rows can support final quotes |

A failed audit keeps the cut-flow row out of plan 47 and blocks
`DEC-37-TRUTH-BLIND-GATE` until the upstream truth dependency is fixed.

Required audit row-key inventory:

| `dataset_id` | Sample role | Required row purpose | Acceptance guard |
|---|---|---|---|
| `sig_foil_v3` | signal acceptance reproduction | Ch 10 final acceptance and truth-blind pass/fail stability | matching before/after hashes and empty `changed_event_ids` |
| `cosmic_cry_essLund_overburdenA_v1` | cosmic rejection reproduction | zero-survivor cut-flow and interval handoff to plan 44/46 | matching before/after hashes and no exact-zero background claim |
| `beam_neutron_hibeam_direct_v1` | beam-neutron extension sample | verify selection semantics before plan-41/44 beam rows quote rates | diagnostic-only until beam sample registry and rates are signed |
| `plan41_retune_panel` | optimisation scan panel | guard retuned thresholds against truth/provenance coupling | required before any §3.2 handoff can be promoted |

The inventory defines required audit keys only. It does not authorize a
selection row for final quotes until measured §2.1 hashes and status
fields are attached.

Initial selection-audit failure examples:

| `audit_case_id` | Failing pattern | Required status | Review guard |
|---|---|---|---|
| `truth_blind_hash_mismatch` | cut booleans differ after Class-B/provenance columns are removed | `fail` | blocks `DEC-37-TRUTH-BLIND-GATE` and final quotes |
| `changed_event_ids_nonempty` | before/after hashes differ and selected event ids are listed | `fail` | every changed row must be traced to an upstream leak before rerun |
| `cosmic_zero_no_interval` | cosmic sample has zero survivors but no interval handoff | `fail` | zero-survivor background cannot be quoted as exact zero |
| `beam_sample_unsigned` | beam-neutron audit row exists before sample/rate source is signed | `diagnostic_only` | cannot feed plan-44 rates or plan-46 background sums |

## 3. N-1 and ROC

Per plan 41:

- N-1 plot for every variable in §1.
- ROC curve over each continuous variable (visible mass, sphericity,
  upper/lower scint).
- Significance scan to identify a possibly better operating point.

### 3.1 Machine-readable N-1/ROC scan fixture

Plan 41 scan artifacts must expose enough structure for plan 37 to
decide whether a proposed threshold change is reviewable:

| Field | Required content | Review rule |
|---|---|---|
| `scan_artifact_id` | stable key for the N-1/ROC artifact | referenced by §3.2 handoff rows |
| `baseline_selection_config_id` | Ch 10 baseline tuple id | must match §1 thresholds before masking one cut |
| `variable_name` | one §1 input variable or S.6 score | no unregistered feature may enter a scan |
| `masked_cut_column` | canonical `pass_*` column removed for the N-1 study | null only for all-variable S.6 scans |
| `threshold_grid` | ordered thresholds or score bins | deterministic and saved with the artifact |
| `signal_efficiency_curve` | efficiency with plan-04 intervals | computed on held-out or declared validation split |
| `background_survival_curve` | survivor counts/intervals per threshold | zero-survivor points use F-C intervals |
| `objective_curve` | expected limit or Z0 proxy with uncertainty | must name the plan-46 method used |
| `best_candidate_threshold` | selected threshold or null | diagnostic until DEC approval |
| `scan_status` | `diagnostic`, `candidate`, or `blocked` | blocked rows cannot appear in promotion evidence |

The scan fixture is rejected if it uses a variable outside the §1
selection contract or if the objective cannot be recomputed from saved
signal/background curves.

Required scan row-key inventory:

| `scan_artifact_id` | `variable_name` | `masked_cut_column` | Required row purpose | Acceptance guard |
|---|---|---|---|---|
| `scan_s1_scintillator_edep` | `scintillator_edep` | `pass_scintillator_energy` | retune total scintillator-energy window | stores both low/high threshold grids |
| `scan_s3_visible_mass` | `visible_invariant_mass` | `pass_invariant_mass` | retune visible-mass lower bound | objective curve names the plan-46 method |
| `scan_s4_sphericity` | `sphericity` | `pass_sphericity` | retune event-shape threshold | signal/background curves include plan-04 intervals |
| `scan_s5_upper_scintillator` | `upper_scintillator_edep` | `pass_scintillator_balance` | retune upper scintillator-balance bound | paired with lower-bound scan before handoff |
| `scan_s5_lower_scintillator` | `lower_scintillator_edep` | `pass_scintillator_balance` | retune lower scintillator-balance bound | paired with upper-bound scan before handoff |
| `scan_s6_candidate_score` | `candidate_selection_score` | null | score-threshold scan for BDT/NN replacement | diagnostic until plan-57 feature freeze exists |

The inventory defines required scan artifacts only; promotion still
requires a §3.2 handoff row, held-out result, and DEC approval.

### 3.2 Machine-readable optimisation handoff fixture

Plan 41 may propose thresholds or an S.6 replacement, but plan 37 owns
the selection contract. Each proposed optimisation therefore enters this
plan as one handoff row before any DEC can promote it:

| Field | Required content | Review rule |
|---|---|---|
| `handoff_id` | stable key for the proposed retune or model | unique within the plan-37 selection family |
| `baseline_selection_config_id` | Ch 10 baseline tuple id | must preserve the §1 cut thresholds and `CUT_ORDER` |
| `candidate_selection_config_id` | proposed cut tuple or S.6 model id | cannot overwrite baseline columns |
| `plan41_artifact_ids` | N-1/ROC/cut-search JSON ids | every touched variable must have a plan-41 artifact |
| `touched_cut_columns` | subset of §1 `pass_*` columns or `passes_preliminary_selection` | no hidden variable promotion |
| `objective` | signed objective name from plan 41 §3 | required before comparing against baseline |
| `test_split_result_id` | held-out result row | validation-only gains cannot promote a candidate |
| `expected_limit_or_Z0_delta` | candidate minus baseline with uncertainty | must include plan-04 interval source |
| `promotion_dec_id` | `DEC-37-RETUNED-CUTS` or `DEC-37-MVA-SELECTION` | draft DEC keeps row diagnostic-only |
| `ledger_status` | `baseline`, `diagnostic`, `candidate`, or `promoted` | only `promoted` rows may feed non-Ch10 quotes |

A handoff row is rejected if it changes the Ch 10 baseline fields, lacks
plan-41 artifact coverage for a touched cut, or uses truth labels outside
sample-level signal/background identity.

Initial optimisation handoff examples:

| `handoff_id` | `candidate_selection_config_id` | `plan41_artifact_ids` | `touched_cut_columns` | Required held-out evidence | `promotion_dec_id` |
|---|---|---|---|---|---|
| `handoff_s3_visible_mass_lower_v0` | `retune_visible_mass_lower_v0` | [`scan_s3_visible_mass`] | [`pass_invariant_mass`] | expected-limit delta with plan-04 interval source and unchanged S.1/S.2/S.4/S.5 columns | `DEC-37-RETUNED-CUTS` |
| `handoff_s4_sphericity_lower_v0` | `retune_sphericity_lower_v0` | [`scan_s4_sphericity`] | [`pass_sphericity`] | held-out signal efficiency and background-survival curves with sparse-sentinel audit attached | `DEC-37-RETUNED-CUTS` |
| `handoff_s5_scintillator_balance_v0` | `retune_scintillator_balance_v0` | [`scan_s5_upper_scintillator`, `scan_s5_lower_scintillator`] | [`pass_scintillator_balance`] | paired upper/lower scan result proving neither bound alone creates an unreviewed operating point | `DEC-37-RETUNED-CUTS` |
| `handoff_s6_bdt_score_v0` | `bdt_s6_candidate_score_v0` | [`scan_s6_candidate_score`] | [`passes_preliminary_selection`] | plan-57 feature freeze, calibration curve, and truth-blind hash equality | `DEC-37-MVA-SELECTION` |

These examples are promotion-ledger row keys, not executable commands.
They preserve the Ch 10 baseline tuple and require new candidate columns
for any retuned or MVA selection.

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

Initial selection-change approval examples:

| `approval_case_id` | Selection output pattern | Allowed use before DEC approval | Promotion guard |
|---|---|---|---|
| `ch10_cutflow_freeze` | §1 six-cut baseline with current `CUT_ORDER` | plan-47 reproduction control and all cumulative count audits | requires signal and background count reproduction before final quote |
| `retuned_rectangular_diag` | one or more S.1-S.5 thresholds retuned in plan-41 scans | diagnostic N-1/expected-limit comparison only | must keep original Ch 10 columns unchanged and add separate retuned columns |
| `mva_s6_shadow` | BDT/NN S.6 score written beside `passes_preliminary_selection` | shadow ladder output only | needs feature freeze, calibration, and background rejection before `DEC-37-MVA-SELECTION` |
| `truth_blind_gate_blocked` | pass booleans change after truth/provenance columns are removed upstream | no final selection quote | blocks `DEC-37-TRUTH-BLIND-GATE` until upstream leak is removed |

Until the relevant DEC is approved, alternative S.6 outputs are
diagnostic/ladder artifacts only and cannot supersede the baseline
cut-flow.

### 4.2 Initial downstream-handoff examples

Selection outputs feed several analysis plans, so the handoff must name
whether it carries the Ch 10 baseline, a retune candidate, or a shadow
MVA score:

| `handoff_case_id` | Downstream consumer | Required payload | Required guard |
|---|---|---|---|
| `ch10_cutflow_to_p47` | plan 47 reproduction ledger | cut identity rows, independent counts, cumulative counts, and final acceptance | uses baseline config id and unchanged `CUT_ORDER` |
| `zero_survivor_to_p44_p46` | plans 44 and 46 background/significance rows | survivor counts plus interval-method handoff for cosmic and beam samples | zero survivors are upper-limit inputs, never exact-zero background claims |
| `retune_candidate_to_p41` | plan 41 optimisation review | candidate config id, touched columns, held-out result id, and objective delta | diagnostic until retune DEC approval and truth-blind audit pass |
| `mva_shadow_to_p57` | plan 57 MVA protocol and plan 38 ladder | baseline booleans, shadow score, feature-freeze id, and calibration summary | cannot overwrite `passes_preliminary_selection` before MVA DEC approval |

Any downstream quote that omits the handoff case id is rejected because
it becomes impossible to tell baseline reproduction from an optimisation
proposal. Plan 37 owns the canonical selection contract; downstream
plans may aggregate its rows but may not rename or silently retune them.

## 5. Acceptance criteria

- §1 cuts implemented exactly.
- §2 reproduction green.
- §3 N-1 / ROC produced.
- §4 MVA scored.

## 6. Dependencies

- **04, 24, 36, 38, 41, 47, 57** — inputs.
- *Consumed by:* plans 41–46 (analysis level), 47, 50.
