---
id: 44_background_taxonomy
title: Background taxonomy — full channel tree per source
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 14_background_models, 21_sample_cosmic_CRY, 22_sample_neutron_beam]
outputs:
  - {path: docs/rebuild_plans/44_background_taxonomy.md, schema: this file}
  - {path: data/background_taxonomy/tree.yml, schema: machine-readable tree}
acceptance:
  - {test: every background channel has node = (source, sub-channel, sample, expected rate, survivor count), method: tree review, pass_when: complete tree}
  - {test: zero-survivor channels report Feldman-Cousins upper limits per plan 04 §5, method: review of upper-limit rows, pass_when: zero "0 / N = 0" entries}
risks:
  - {risk: an unmodelled background source slips through, mitigation: §3 explicit registry of unmodelled sources from plan 01 §6 limitations}
estimated_effort: M
last_updated: 2026-05-10
---

# Background taxonomy

*Charter.* The full enumeration of backgrounds the analysis claims
to control. Every claim of "no surviving background" or "1 in 10⁶
survival" is a specific rate on a specific node in this tree.

## 1. Tree structure

Each background node is a row in the canonical tree. `survivors` is
filled by the reconstruction output; if it is zero, §2 supplies the
reported upper limit rather than a literal zero rate.

| Source | Sub-channel | Source citation | Sample id / label | Expected-rate convention | Observable signature | Related plan-24 leaf |
|---|---|---|---|---|---|---|
| cosmic | `cosmic_muon` | CRY mixture and per-species split: plan 14 §§1.1–1.3; sample sizing: plan 21 §4 | `cosmic_cry_essLund_overburdenA_v1` primary species label `mu±`; `cosmic_cry_essLund_overburdenB_v1` systematic cross-check | CRY normalisation at ESS Lund; target survival upper limit `ε90 ≤ 1e-5` for 244k events if zero survivors | through-going charged track, high scintillator energy, timing outlier, hemisphere imbalance | C.1, C.4, E.8, E.9, S.1, S.5 |
| cosmic | `cosmic_electron` | CRY particle set includes e±: plan 14 §1.1; legacy per-species macros retained: plan 14 §1.3 | `cosmic_cry_essLund_overburdenA_v1` primary species label `e±`; `cosmic_cry_essLund_overburdenB_v1` systematic cross-check; per-species macro row in plan 47 | CRY e± flux component times measured survival; zero survivors reported with F-C `ε90` | EM shower with charged track, possible photon-like cluster contamination | P.1, P.2, P.3, P.4, E.5, S.4 |
| cosmic | `cosmic_gamma` | CRY particle set includes γ: plan 14 §1.1 | `cosmic_cry_essLund_overburdenA_v1` primary species label `γ`; `cosmic_cry_essLund_overburdenB_v1` systematic cross-check; per-species macro row in plan 47 | CRY γ flux component times measured survival; zero survivors reported with F-C `ε90` | isolated EM clusters, π⁰-like photon pairs, little TPC activity | P.1, P.2, P.5, P.6, E.7, S.3 |
| cosmic | `cosmic_neutron` | Cosmic hadron sub-channel: plan 14 §1.2; `_HP` dependency: plan 21 §9 | `cosmic_cry_essLund_overburdenA_v1` primary species label `n`; `cosmic_cry_essLund_overburdenB_v1` systematic cross-check | CRY neutron component times measured survival; zero survivors reported with F-C `ε90` | delayed hadronic activity, capture γ, secondary charged tracks | C.1, P.1, E.8, S.1, S.6 |
| cosmic | `cosmic_proton` | Cosmic hadron sub-channel: plan 14 §1.2 | `cosmic_cry_essLund_overburdenA_v1` primary species label `p`; `cosmic_cry_essLund_overburdenB_v1` systematic cross-check | CRY proton component times measured survival; zero survivors reported with F-C `ε90` | stopping charged track, high dE/dx, scintillator asymmetry | C.2, C.3, C.5, E.9, S.5 |
| beam_neutron | `direct_beam_neutron` | HIBEAM source choice: plan 22 §1; sub-channel table: plan 22 §3 | `beam_neutron_hibeam_direct_v1` | per-event survival folded with per-pulse yield; plan 22 target false-positive rate `≤1e-4` per pulse at 90% C.L. | neutron reaches detector volume; prompt hadronic secondaries near beam direction | C.1, E.8, E.9, S.6 |
| beam_neutron | `scattered_neutron` | sub-channel table: plan 22 §3; beam-line source: plan 14 §2.1 | `beam_neutron_hibeam_scattered_v1` | same per-pulse convention as direct beam neutrons, with beampipe/collimator interaction label | off-axis hadronic activity, displaced vertex/topology, timing compatible with beam | V.4, V.5, E.5, E.8, S.4 |
| beam_neutron | `capture_gamma` | capture-γ source details: plan 14 §3; sample id: plan 22 §3 | `beam_neutron_hibeam_captgamma_v1` | neutron-transport capture rate folded with survival; zero survivors reported with F-C `ε90` | low-to-moderate energy γ cascade in lead glass/scintillator, can fake π⁰ photons in pile-up | P.1, P.2, P.5, P.6, E.1, E.8 |
| beam_neutron | `secondary_hadronic` | neutron inelastic sub-channel: plan 14 §2.2; sample id: plan 22 §3 | `beam_neutron_hibeam_secondaries_v1` | secondary-fragment rate folded with per-pulse neutron yield; F-C for zero survivors | charged hadrons with pion/proton PID-like signatures and calorimeter deposits | C.2, C.3, C.5, P.5, E.9, S.2 |

Unmodelled nodes are listed separately in §3 because they have no
registered simulated sample in the first rebuild cycle.

Decision-log stubs for freezing the rate conventions:

| DEC id | Convention to sign | Default in this plan |
|---|---|---|
| `DEC-44-COSMIC-RATE-SOURCE` | Cosmic total-rate source and overburden baseline | CRY ESS Lund `cosmic_cry_essLund_overburdenA_v1` is the conservative baseline; `cosmic_cry_essLund_overburdenB_v1` is the systematic cross-check. |
| `DEC-44-BEAM-RATE-SOURCE` | Beam-neutron source and per-pulse conversion | Prefer ESS HIBEAM MCPL; fallback is plan-22 parameterised spectrum; per-event survivors are folded with per-pulse yield. |
| `DEC-44-ZERO-SURVIVOR-REPORTING` | Zero-survivor reporting convention for all background nodes | Report Feldman-Cousins 90% C.L. upper limits per plan 04 §5; never quote `0 / N = 0`. |

Each node carries:

| Field | Source |
|---|---|
| node_status | `registered_sample` for §1 rows; `unregistered_caveat` for §3 sentinels |
| sample_id | plan 03 for registered samples; `unregistered_*` sentinel for caveat rows |
| events_generated | plan 03 manifest for registered samples; null for caveat rows |
| survivors | counted on the reconstruction output; null for caveat rows |
| rate | survivors / events_generated for registered samples; not computed for caveat rows |
| upper_limit_FC | plan 04 §5 when survivors = 0 |
| systematic | plan 45 |
| limitation_flags | plan 01 §6 |
| rate_included_in_b | true only for registered samples with reviewed rate convention |

Sample-id provenance used by the §1 tree:

| Background family | Dataset ids | Registry source |
|---|---|---|
| cosmic CRY baseline | `cosmic_cry_essLund_overburdenA_v1`, `cosmic_cry_essLund_overburdenB_v1` | plan 21 §6 proposed sample registry; plan 03 sample-id naming contract |
| beam-neutron sub-channels | `beam_neutron_hibeam_direct_v1`, `beam_neutron_hibeam_scattered_v1`, `beam_neutron_hibeam_captgamma_v1`, `beam_neutron_hibeam_secondaries_v1` | plan 22 §3 sub-channel registry; plan 03 sample-id naming contract |

### 1.1 Rate and survivor accounting

For every §1 node, the machine-readable tree stores both the measured
survivor count and the convention used to convert it to an expected
background contribution:

| Source | Survivor field | Rate conversion | Required zero-survivor output |
|---|---|---|---|
| cosmic | `n_survivors_after_plan37` from the CRY sample, optionally split by primary species label | `survival_fraction * CRY_component_flux * exposure`, with overburden A as baseline and B as systematic | `epsilon90 = FC90(0, n_generated)`; for the 244k-event plan-21 sample this targets `≈ 1.0e-5` |
| beam_neutron | `n_survivors_after_plan37` from each plan-22 sub-channel sample | `survival_fraction * neutron_yield_per_pulse * pulse_count * subchannel_weight` | `epsilon90` plus false-positive-per-pulse upper limit; target `≤ 1e-4` per pulse |

Rows with nonzero survivors quote the measured fraction with the plan
04 interval. Rows with zero survivors quote the F-C upper limit from
§2; no report may collapse a zero-survivor node to exactly zero
expected background.

### 1.2 Machine-readable node fixture

The tree output must be checkable without prose parsing. Each §1 row
serialises to one record with this minimum field set:

| Field | Required value / example | Review rule |
|---|---|---|
| `node_id` | `cosmic.muon`, `beam_neutron.capture_gamma` | stable dotted key; never re-used for a different source |
| `source` | `cosmic` or `beam_neutron` | must match the §1 table source column |
| `sub_channel` | §1 sub-channel token | must be unique within `source` |
| `sample_id` | registry id from plan 21 or 22 | must not be free text or a file path |
| `expected_rate_expression` | cosmic or beam-neutron formula from §1.1 | formula is stored until survivor counts exist |
| `survivor_count_field` | `n_survivors_after_plan37` | every node uses the same post-selection count boundary |
| `zero_survivor_interval` | `feldman_cousins_90cl` | required when survivor count is zero |
| `observable_signature` | concise signature from §1 | copied to plan 50 defence tables |
| `related_leaves` | plan-24 leaf list | at least one reconstruction/selection leaf |
| `rate_included_in_b` | boolean | false unless the rate convention DEC is signed |

Example records:

| `node_id` | `sample_id` | `expected_rate_expression` | `rate_included_in_b` |
|---|---|---|---:|
| `cosmic.muon` | `cosmic_cry_essLund_overburdenA_v1` | `survival_fraction * CRY_muon_flux * exposure` | false |
| `beam_neutron.capture_gamma` | `beam_neutron_hibeam_captgamma_v1` | `survival_fraction * neutron_yield_per_pulse * pulse_count * capture_gamma_weight` | false |

`rate_included_in_b = false` is the draft default because the rate-source
DECs in §1 are still unsigned. The flag flips only when the relevant DEC
and plan-47 reproduction row both exist.

### 1.3 Machine-readable rate-result fixture

Each reconstruction campaign emits one result row per registered §1
node. This row is separate from the static node fixture so repeated
samples, systematic throws, and plan-37 retunes cannot overwrite the
background definition:

| Field | Required content | Review rule |
|---|---|---|
| `node_id` | dotted key from §1.2 | must resolve to exactly one background node |
| `sample_id` | sample used for this campaign | must match the node or an approved systematic cross-check |
| `selection_config_id` | plan-37 cut-flow or retune id | distinguishes Ch 10 baseline from retuned studies |
| `events_generated` | denominator after sample-quality gates | zero or null denominators are invalid for rate rows |
| `n_survivors_after_plan37` | post-selection survivor count | counted after the same plan-37 boundary for all nodes |
| `survival_fraction` | survivor count divided by denominator | quote with plan-04 interval, never as an exact zero |
| `interval_method` | `feldman_cousins_90cl` or plan-04 approved alternative | zero-survivor rows must use F-C |
| `epsilon90` | upper limit when survivors are zero | required before a zero-survivor claim reaches plan 46 |
| `expected_rate` | folded exposure or per-pulse rate, if authorised | null until the relevant rate-source DEC is signed |
| `rate_included_in_b` | boolean copied to plan 46 | true only for authorised, caveat-reviewed rows |

Plan 46 may sum `expected_rate` into `b` only from rows with
`rate_included_in_b = true`; all other rows remain caveats or validation
artifacts in plan 47 and plan 50.

Draft rate-result examples:

| `rate_result_id` | `node_id` | `sample_id` | `selection_config_id` | `events_generated` | `n_survivors_after_plan37` | `survival_fraction` | `interval_method` | `epsilon90` | `expected_rate` | `rate_included_in_b` |
|---|---|---|---|---:|---:|---|---|---|---|---:|
| `cosmic_muon_ch10_zero_survivor_v0` | `cosmic.muon` | `cosmic_cry_essLund_overburdenA_v1` | `ch10_baseline` | 244000 | 0 | `0/244000`, quoted only with interval | `feldman_cousins_90cl` | `FC90(0, 244000)` | null until `DEC-44-COSMIC-RATE-SOURCE` | false |
| `cosmic_gamma_overburdenB_crosscheck_v0` | `cosmic.gamma` | `cosmic_cry_essLund_overburdenB_v1` | `ch10_baseline` | 244000 | 0 | `0/244000`, systematic cross-check | `feldman_cousins_90cl` | `FC90(0, 244000)` | null until overburden convention is signed | false |
| `beam_direct_ch10_nonzero_validation_v0` | `beam_neutron.direct_beam_neutron` | `beam_neutron_hibeam_direct_v1` | `ch10_baseline` | 100000 | 2 | `2/100000` with interval | `feldman_cousins_90cl` | null | null until `DEC-44-BEAM-RATE-SOURCE` | false |

These rows are examples of result-shape and review gates, not measured
background claims. A row can become part of a plan-46 background sum only
after the denominator, survivor count, interval, and rate-source DEC are
attached to the corresponding plan-47 artifact.

### 1.4 Machine-readable background-sum handoff fixture

Plan 46 receives a background sum, not a prose table. Each handoff row
records exactly which rate results were folded into `b` and which
caveats stayed outside the numeric sum:

| Field | Required content | Review rule |
|---|---|---|
| `background_sum_id` | stable key for the summed background hypothesis | referenced by plan-46 input bundles |
| `rate_result_ids` | list of §1.3 rows included in the sum | every row must have `rate_included_in_b = true` |
| `excluded_caveat_node_ids` | §3 caveat nodes not folded into `b` | copied to plan-46 `unbounded_limitations` |
| `selection_config_id` | plan-37 cut-flow or retune id | must match every included rate result |
| `exposure_label` | exposure or pulse-count label for the quote | must match signal and limit rows |
| `b_expected` | numeric expected background after authorised folds | null when any required rate-source DEC is unsigned |
| `b_expected_formula` | reproducible expression from included rates | no hand-entered total without terms |
| `included_nuisance_ids` | plan-45 nuisance throws applied to rates | copied to plan-46 input bundles |
| `rate_source_dec_ids` | signed DEC ids authorising the folds | draft DEC keeps the handoff provisional |
| `handoff_status` | `draft`, `complete`, or `blocked` | only `complete` rows may feed final significance quotes |

The handoff row is rejected if it includes an unregistered caveat as a
numeric zero or omits a caveat from the limitation list.

Draft handoff examples:

| `background_sum_id` | `rate_result_ids` | `excluded_caveat_node_ids` | `selection_config_id` | `exposure_label` | `b_expected` | `b_expected_formula` | `included_nuisance_ids` | `rate_source_dec_ids` | `handoff_status` |
|---|---|---|---|---|---:|---|---|---|---|
| `background_sum_validation_high_b` | [`validation_background_rate_high_b`] | [] | `validation_ch10_baseline` | `validation_only` | 20 | `validation_background_rate_high_b.expected_rate` | [] | [`validation_only`] | `draft` |
| `background_sum_registered_blocked` | [`cosmic.muon.rate`, `beam_neutron.direct_beam_neutron.rate`] | [`unmodelled.environmental_gamma`, `unmodelled.detector_internal`, `unmodelled.beampipe_activation`] | `ch10_baseline` | `analysis_exposure_v1` | null | null until rate-source DECs are signed | [`N6`, `N7`] | [`DEC-44-COSMIC-RATE-SOURCE`, `DEC-44-BEAM-RATE-SOURCE`] | `blocked` |
| `background_sum_zero_survivor_validation` | [`cosmic_muon_zero_survivor`] | [`unmodelled.environmental_gamma`, `unmodelled.detector_internal`, `unmodelled.beampipe_activation`] | `validation_ch10_baseline` | `plan46_zero_survivor_case` | null | `epsilon90` is a limit, not a central expected-rate sum | [] | [`DEC-44-ZERO-SURVIVOR-REPORTING`] | `draft` |

The `validation_*` ids are calculation fixtures for plan 46; they are
not plan-03 sample registrations and cannot be promoted to analysis
background rates.

## 2. Zero-survivor handling

Per plan 04 §5: never quote `0 / N = 0`. Every zero-survivor channel
reports a Feldman-Cousins 90% C.L. upper limit on the survival rate.

Initial zero-survivor reporting examples:

| `zero_case_id` | Survivor pattern | Required reported quantity | Review guard |
|---|---|---|---|
| `zero_small_denominator` | `n_survivors_after_plan37 = 0` with low generated statistics | F-C 90% upper survival limit and low-statistics caveat | cannot enter plan-46 `b` as a central zero |
| `zero_large_denominator` | `n_survivors_after_plan37 = 0` with approved denominator | F-C 90% upper survival limit plus exposure fold only after rate-source DEC | plan-46 receives the limit separately from central `expected_rate` |
| `nonzero_validation` | at least one survivor after plan 37 | central survival fraction with interval, not `epsilon90` | reviewed with the same selection boundary as zero rows |
| `zero_unregistered_source` | no registered sample for the background node | caveat row only | cannot be converted to `0/N` or included as a numeric zero |

## 3. Unmodelled sources

These nodes are not simulated in the first rebuild cycle. They must
appear as explicit caveats beside every total-background quote in plan
50; they do not get folded into `b` until a registered sample exists.

| Unmodelled source | Source citation | Missing sample id | Expected-rate status | Observable signature | Limitation flags |
|---|---|---|---|---|---|
| `environmental_gamma` | plan 14 §4; plan 01 §6 | `unregistered_environmental_gamma` | unbounded by current rebuild | room γ activity in lead glass/scintillator, low-energy EM pile-up | L3, L5, L8, L11 |
| `detector_internal` | plan 14 §4; plan 01 §6 | `unregistered_detector_internal` | unbounded by current rebuild | scintillator self-radioactivity, lead-glass dark/photoelectron activity, dead/hot channel fakes | L4, L5, L8, L12 |
| `beampipe_activation` | plan 14 §4; plan 01 §6 | `unregistered_beampipe_activation` | unbounded by current rebuild | delayed activation γ/charged secondaries correlated with beam operation | L5, L6, L8, L11 |

The `unregistered_*` values are deliberate caveat sentinels, not
registry dataset ids. Their machine-readable rows must carry
`node_status = unregistered_caveat` and `rate_included_in_b = false`.
A total-background quote must fail review if it silently treats one of
these sentinels as zero expected background.

### 3.1 Machine-readable caveat fixture

Unmodelled sources serialise to explicit caveat rows rather than absent
background nodes:

| Field | Required content | Review rule |
|---|---|---|
| `node_id` | stable dotted key, e.g. `unmodelled.environmental_gamma` | never collides with registered §1 nodes |
| `node_status` | `unregistered_caveat` | distinguishes caveats from zero-survivor samples |
| `missing_sample_id` | `unregistered_*` sentinel from §3 | not accepted as a plan-03 dataset id |
| `expected_rate_status` | `unbounded_by_current_rebuild` | blocks numeric folding into `b` |
| `observable_signature` | §3 signature text | copied to plan-50 defence caveats |
| `limitation_flags` | plan-01 limitation ids | non-empty for every caveat row |
| `rate_included_in_b` | `false` | hard fail if true before sample registration |
| `replacement_sample_required` | boolean | true until plan 03 registers a real sample |
| `caveat_dec_id` | `DEC-44-UNMODELLED-CAVEATS` | required beside every total-background quote |

Plan 46 and plan 50 must preserve these rows as caveats. They may not
convert a missing sample into an expected rate of zero.

Initial caveat-row examples:

| `node_id` | `missing_sample_id` | `expected_rate_status` | Required plan-46 behavior | Required plan-50 text |
|---|---|---|---|---|
| `unmodelled.environmental_gamma` | `unregistered_environmental_gamma` | `unbounded_by_current_rebuild` | copy to `unbounded_limitations`; do not include in `b_expected` | state that environmental γ pile-up is not bounded by current samples |
| `unmodelled.detector_internal` | `unregistered_detector_internal` | `unbounded_by_current_rebuild` | block unconditional total-background quote if detector-internal fakes affect the observable | cite dead/hot channel and self-radioactivity caveat |
| `unmodelled.beampipe_activation` | `unregistered_beampipe_activation` | `unbounded_by_current_rebuild` | keep outside numeric beam-neutron rate sum | state delayed activation remains a registered missing-sample item |

These examples are mandatory caveat shapes, not background-rate rows.
They remain present until plan 03 registers replacement samples and a
new rate-result row supersedes the caveat through DEC review.

DEC stub: `DEC-44-UNMODELLED-CAVEATS` — keep these rows out of the
numeric background sum until simulated samples are registered, but
require them as plan-50 caveats for every quoted total-background
result.

## 4. Acceptance criteria

- §1 tree complete.
- §2 zero-survivor handling correct.
- §3 unmodelled list audited against plan 01 §6.

## 5. Dependencies

- **04, 14, 21, 22** — inputs.
- *Consumed by:* plan 45 (systematics), plan 46 (significance), plan
  47, plan 50.
