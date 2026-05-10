---
id: 33_subsystem_photon_object_promotion_examples
title: Subsystem — photon object promotion examples
version: 0.1
status: draft
owner: EM-Object POG
depends_on: [33_subsystem_photon_object, 31_subsystem_calorimeter_clustering, 32_subsystem_shower_shape, 34_subsystem_pi0_pairing, 37_subsystem_event_selection]
outputs:
  - {path: docs/rebuild_plans/33_subsystem_photon_object_promotion_examples.md, schema: split photon-promotion fixture}
acceptance:
  - {test: promotion examples preserve direction, energy, merge, and scintillator-only guards, method: review, pass_when: all rows pass}
last_updated: 2026-05-10
---

# Photon-object promotion examples

This companion file keeps plan 33 below the line cap while preserving the
decision stubs, downstream-impact rows, handoff examples, promotion
checklist, evidence bundles, and reviewer audits for P.3/P.4.

### 6.2 Decision-log stubs for photon-object choices

P.3/P.4 choices feed π⁰ mass, visible mass, and event selection, so
they need explicit methodology approval before replacing the
reproduction baseline:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-33-DIRECTION-METHOD` | Choose vertex→centroid, origin fallback policy, or cluster-axis fit for production photon direction | §6 angular pull closure plus fallback-rate audit by sample |
| `DEC-33-ENERGY-METHOD` | Choose calibrated cluster sum, lead-glass-only, or regression calibration for production photon energy | §6 energy-response closure and plan-18 calibration provenance |
| `DEC-33-FRAGMENT-MERGE` | Freeze truth-blind fragment-merge thresholds and duplicate policy | duplicate/over-merge rate scan and plan-01 audit proving no truth-label dependence |
| `DEC-33-SCINT-ONLY-PHOTONS` | Freeze `leadglass_fraction = 0` semantics and downstream handling for scintillator-only photon rows | plan-34/37 impact table showing they do not enter Ch 8 π⁰ selection accidentally |

Initial scintillator-only downstream-impact examples:

| `impact_case_id` | Photon row pattern | Required downstream handling | Review guard |
|---|---|---|---|
| `scint_only_no_lg` | `leadglass_edep = 0`, `scintillator_edep > 0`, `leadglass_fraction = 0` | row may contribute to photon-efficiency diagnostics but cannot seed the Ch 8 π⁰ selection | plan-34/37 impact table shows zero accepted Ch 8 candidates from this case |
| `low_lg_fraction_edge` | both components positive but `leadglass_fraction < 0.55` | row remains a valid photon-object row while failing the Ch 8 lead-glass fraction guard | cut-flow audit separates object creation from selection rejection |
| `merged_with_lg_cluster` | scintillator-heavy fragment merges with a lead-glass fragment under an approved threshold | recompute `leadglass_fraction` from merged calibrated components rather than forcing zero | `DEC-33-FRAGMENT-MERGE` and `DEC-33-SCINT-ONLY-PHOTONS` evidence agree on the merged row |
| `legacy_truth_descendant_scint` | current reproduction alias supplies same-key scintillator energy without a target P.1 cluster sum | diagnostic only; cannot approve production P.4 energy or Ch 8 selection behavior | plan-38 ladder labels it non-production until plan-31/32 inputs exist |

Until approval, alternative direction/energy/merge outputs remain
plan-38 ladder rows; the Ch 10 reproduction keeps the current
baseline semantics.

Initial downstream-handoff examples:

| `handoff_case_id` | Photon output pattern | Consumer expectation | Review guard |
|---|---|---|---|
| `photon_fourvector_pass_to_p34` | frozen P.3/P.4 four-vector with stable `source_cluster_ids` | plan 34 may build π⁰ pairs | requires §6 closure pass and Class-B drop hash equality |
| `origin_fallback_diag_to_p36` | rows using origin fallback are explicitly flagged | plan 36 may report separate event-variable diagnostics | cannot be mixed into primary direction closure without category split |
| `fragment_merge_shadow` | merged-photon rows written beside no-merge baseline | plan 34/38 may compare pair multiplicity and over-merge rates | baseline photon ids and source clusters remain reviewable |
| `scint_only_selection_guard` | scintillator-only photons carry `leadglass_fraction = 0` | plan 34/37 must reject them from Ch 8 π⁰ selection | impact table must show zero accidental accepted candidates |

Initial production-promotion checklist:

| `promotion_check_id` | Evidence required | Blocks promotion when missing |
|---|---|---|
| `p33_fourvector_contract_present` | stable photon id, source clusters, direction method, and energy method | plan 34 cannot recompute pair kinematics reproducibly |
| `p33_all_energy_bins_pass` | closure rows for every required energy bin and direction-source category | photon response is not bounded across the calibration range |
| `p33_fragment_policy_stable` | duplicate/over-merge metrics and Class-B drop hash for fragment handling | π⁰ daughter separation can change under hidden provenance |
| `p33_scint_only_guard_audited` | impact rows for scintillator-only and low lead-glass-fraction photons | Ch 8 selection may accept unsupported photon rows |

Production P.3/P.4 promotion requires all four checks plus signed DEC
ids for direction, energy, and merge policy. Missing checks keep the
method as a plan-38 diagnostic rather than a plan-34 input.

Initial evidence-bundle examples:

| `evidence_bundle_id` | Included rows | Reviewer action |
|---|---|---|
| `p33_vertex_centroid_candidate_v0` | method bundle, all energy-bin closure rows, fallback audit, Class-B hash | candidate for plan-34 handoff if closure and DEC checks pass |
| `p33_origin_fallback_diag_v0` | origin-fallback category rows and angular-pull summary | keep separate from primary direction closure; diagnose sparse vertices |
| `p33_fragment_merge_shadow_v0` | duplicate/over-merge scans plus no-merge baseline ids | allow plan-38 comparison but block production without merge DEC |
| `p33_scint_only_blocker_v0` | scint-only impact table and Ch 8 guard audit | block plan-34 acceptance if any unsupported row seeds π⁰ selection |

Evidence bundles preserve the source-cluster, direction, and energy
method context that plan 34 needs to reproduce pair kinematics.

Initial reviewer audit cases:

| `audit_case_id` | Reviewer question | Required evidence before accept | Reject condition |
|---|---|---|---|
| `p33_fourvector_audit` | Can every photon four-vector be traced to source clusters and methods? | photon fixture row, direction method, energy method, and source-cluster ids | row has energy/direction but no stable photon id or source list |
| `p33_fallback_audit` | Are origin-fallback photons separated from vertex-based rows? | fallback flag, category closure row, and angular-pull summary | fallback rows are mixed into primary closure without a category |
| `p33_fragment_audit` | Does merging improve duplicates without hiding daughter loss? | no-merge baseline, merge scan, duplicate rate, and over-merge metric | only post-merge efficiency is shown |
| `p33_scint_guard_audit` | Are scintillator-only rows blocked from unsupported π⁰ use? | lead-glass-fraction guard and Ch 8 impact table | any unsupported row can seed a production π⁰ candidate |
