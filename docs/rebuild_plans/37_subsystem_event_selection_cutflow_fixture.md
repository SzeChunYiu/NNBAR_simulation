---
id: 37_subsystem_event_selection_cutflow_fixture
title: Subsystem — event selection cut-flow fixture
version: 0.1
status: draft
owner: Analysis WG
depends_on: [37_subsystem_event_selection, 36_subsystem_event_variables, 47_reproduction_ledger]
outputs:
  - {path: docs/rebuild_plans/37_subsystem_event_selection_cutflow_fixture.md, schema: split cut-flow fixture}
acceptance:
  - {test: cut-flow rows preserve canonical pass columns and Ch 10 thresholds, method: review, pass_when: all rows pass}
last_updated: 2026-05-10
---

# Event-selection cut-flow fixture

This companion file keeps plan 37 below the line cap while preserving the
machine-readable Ch 10 cut-flow fixture and result-row examples.

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
