---
id: 34_subsystem_pi0_pairing_handoff_examples
title: Subsystem — pi0 pairing downstream handoff examples
version: 0.1
status: draft
owner: EM-Object POG
depends_on: [34_subsystem_pi0_pairing, 35_subsystem_kinematic_fit, 36_subsystem_event_variables, 37_subsystem_event_selection, 38_truth_substitution_ladder]
outputs:
  - {path: docs/rebuild_plans/34_subsystem_pi0_pairing_handoff_examples.md, schema: split downstream-handoff fixture}
acceptance:
  - {test: handoff examples preserve production, shadow, and validation boundaries, method: review, pass_when: all rows pass}
last_updated: 2026-05-10
---

# Pi0-pairing downstream handoff examples

This companion file keeps plan 34 below the line cap while preserving the
initial downstream handoff, promotion, evidence-bundle, and reviewer-audit
examples for P.5/P.6.

### 5.3 Initial downstream-handoff examples

The first rebuild handoffs from plan 34 must make the boundary between
production π⁰ candidates, diagnostics, and validation labels explicit:

| `handoff_case_id` | Downstream consumer | Required payload | Required guard |
|---|---|---|---|
| `pi0_candidate_pass_to_p35` | plan 35 kinematic fit | ordered photon ids, candidate id, four-vector inputs, six cut booleans, and Ch 8 `passes_selection` | row is produced without truth-parent labels and references an approved cut-config id |
| `baseline_cut_columns_to_p37` | plan 37 event selection | per-candidate `passes_mass_window`, energy/fraction cuts, opening-angle cut, and final strict AND | selection may aggregate these columns but may not recompute a different π⁰ baseline |
| `prompt_timing_shadow` | plan 36 timing/event variables and plan 38 ladder | timing-veto score or residual sidecar keyed by candidate id | diagnostic-only until timing calibration and retuned-cut DEC approval exist |
| `truth_label_sideband_only` | plan 44/47 accidental-rate studies | evaluator-only shared-parent or wrong-parent label keyed by production candidate id | label must be droppable with unchanged pair list, kinematics, and cut booleans |

Any downstream table that cannot distinguish these four handoff modes is
blocked from promoting a π⁰-pairing change. The default production handoff
is `pi0_candidate_pass_to_p35`; the other rows are shadow or validation
surfaces until their DEC and closure evidence are attached.

Initial production-promotion checklist:

| `promotion_check_id` | Evidence required | Blocks promotion when missing |
|---|---|---|
| `p34_candidate_key_stable` | deterministic candidate id from ordered photon ids, pairing method, and cut config | plan 35 cannot join raw, fitted, and failure rows safely |
| `p34_per_cut_columns_emitted` | six Ch 8 cut booleans plus strict final AND and failure reasons | plan 37 cannot audit the π⁰ selection contribution |
| `p34_accidental_rate_bounded` | no-π⁰ and wrong-parent accidental rows with finite intervals | P.6 fake rejection remains unquantified |
| `p34_truth_drop_stable` | pair list, kinematics, and cut hashes match after truth/provenance drop | evaluator labels may be affecting production pairing |

The Ch 8 all-pairs baseline may feed plan 35 only after these checks
resolve to measured rows. Retuned pair rankings or timing vetoes stay
shadow-only until their separate DEC and closure evidence pass.

Initial evidence-bundle examples:

| `evidence_bundle_id` | Included rows | Reviewer action |
|---|---|---|
| `p34_ch8_allpairs_candidate_v0` | pair fixture, cut-config row, closure rows, accidental-rate rows, truth-drop hash | candidate for plan-35 input once measured/pass and DEC evidence attach |
| `p34_no_pi0_accidental_bundle_v0` | no-π⁰ control row, selected-candidate count, and interval | required before approving P.6 fake rejection |
| `p34_prompt_timing_shadow_v0` | timing-veto sidecar and baseline six-cut rows | keep diagnostic until timing calibration and retuned-cut DEC pass |
| `p34_truth_parent_oracle_blocked_v0` | truth-parent sideband labels and production hash comparison | validation-only upper bound; never production pairing evidence |

Evidence bundles make it explicit which π⁰ rows are production candidates,
which are accidental-rate studies, and which are validation or shadow
surfaces.

Initial reviewer audit cases:

| `audit_case_id` | Reviewer question | Required evidence before accept | Reject condition |
|---|---|---|---|
| `p34_candidate_key_audit` | Is every π⁰ candidate reproducibly keyed from ordered photon ids? | candidate fixture, pairing method id, and cut-config id | key can change when rows are resorted or fit outputs are added |
| `p34_cut_columns_audit` | Are all Ch 8 cut booleans and failure reasons emitted? | six per-cut booleans, strict final AND, and failure-reason fixture | only a final pass/fail column is available |
| `p34_accidental_audit` | Is P.6 fake rejection bounded on no-π⁰ and wrong-parent samples? | accidental-rate rows with denominators and intervals | fake rate is inferred from signal rows only |
| `p34_truth_drop_audit` | Are evaluator labels droppable without changing production rows? | before/after pair-list, kinematic, and cut hashes | truth labels alter pair ordering, cuts, or selected candidates |
