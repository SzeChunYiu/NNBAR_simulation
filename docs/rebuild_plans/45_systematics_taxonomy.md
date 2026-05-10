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
last_updated: 2026-05-10
---

# Systematics taxonomy

*Charter.* The single registry of every systematic uncertainty. Each
nuisance is named, defined, sourced, scoped, and assigned a
correlation with every other nuisance. Plan 47 ledger and plan 50
defence package refer to nuisance names verbatim.

## 1. Nuisance registry (initial set)

Correlation flags are group labels consumed by §2: nuisances sharing a
flag are tested for non-zero correlation before the final covariance is
frozen; otherwise they default to independent.

| ID | Name | Source | ±1σ definition | Affected observables | Correlation flags |
|---|---|---|---|---|---|
| N1 | TPC W-value | plan 17 §3 | nominal 23.6 eV varied by the reference spread 26.0–27.4 eV; implement as ±15% gain on TPC ionisation charge | dE/dx, charged PID, foil-track acceptance | `detector_calibration`, `charged_pid` |
| N2 | Scintillator yield | plan 18 §3 | nominal 11136 photons/MeV; ±1136 photons/MeV spans the optical-table value 10000 photons/MeV | scintillator energy, E.1/E.2, E.3/E.4, S.1, S.5 | `detector_calibration`, `calorimeter_energy` |
| N3 | Lead-glass calibration | plan 18 §4 | per-energy linear-fit slope/intercept varied by the fitted 1σ covariance; pre-fit envelope capped by the 5% closure criterion | lead-glass energy, photon energy, π⁰ mass, visible mass | `detector_calibration`, `calorimeter_energy` |
| N4 | Physics list | plan 12 §3 | discrete model envelope over `nominal_hp`, `qgsp_bert`, `qgsp_bic`, and `em_opt0`; quote half-spread as ±1σ-equivalent | hadronic multiplicity, secondary interactions, neutron transport | `hadronic_model`, `background_shape` |
| N5 | Signal branching | plan 13 §4 | discrete model envelope over `nominal_geant4`, `branching_amsler1991`, `branching_friedman2007`, and η/ω ±1σ brackets | per-channel signal efficiency, π⁰/photon multiplicity, event shapes | `signal_model` |
| N6 | Cosmic flux | plan 14 §1.4 | ±15% on CRY normalisation, covering solar-cycle/date/location uncertainty | cosmic background normalisation, cosmic cut-flow rates | `background_normalization`, `cosmic` |
| N7 | Beam-neutron flux | plan 22 §§1,4 | ±10% on beam-neutron per-pulse yield until the ESS MCPL/parameterised source is frozen; preserve the plan-22 14 Hz conversion separately | beam-neutron normalisation, capture-γ and secondary rates | `background_normalization`, `beam_neutron` |
| N8 | Geometry alignment | plan 16 §3 | scenario envelope over `perfect`, `nominal_survey`, and `worst_case_construction`; quote half-spread of affected observable | vertex resolution, track-cluster matching, π⁰ mass | `geometry`, `tracking`, `calorimeter_energy` |
| N9 | Optical-photon yield | plan 18 §4 | optical-on/off paired residual after Cerenkov/eDep conversion; absolute residual is the ±1σ range | lead-glass response in optical builds, photon energy | `detector_calibration`, `optical`, `calorimeter_energy` |
| N10 | Material budget | plan 15 §§2,6 | ±5% per-region radiation-length envelope until measured composition is cited; recompute conversion and scattering observables | photon conversion rate, multiple scattering, vertex and π⁰ resolutions | `geometry`, `material_budget`, `background_shape` |

### 1.1 Machine-readable nuisance fixture

The registry output serialises each §1 row into a throw-ready record.
A quoted result may consume only records with this minimum field set:

| Field | Required content | Review rule |
|---|---|---|
| `nuisance_id` | `N1`–`N10` | exactly matches the §1 table and §2 matrix labels |
| `name` | human-readable nuisance name | stable enough for plan-47 and plan-50 references |
| `source_plan` | plan id and section anchor | no free-form citation without a plan owner |
| `variation_kind` | `continuous`, `discrete_envelope`, or `scenario_envelope` | determines how up/down throws are generated |
| `minus_1sigma`, `plus_1sigma` | numeric scale, named scenario, or envelope endpoint | both directions required even for symmetric throws |
| `nominal_ref` | constant, model tag, or scenario id used by the baseline | must resolve before a result can be frozen |
| `affected_observables` | list copied from §1 | used to decide which result requires the nuisance |
| `correlation_flags` | list copied from §1 | must match at least one §2 row/column policy |
| `unbounded_limitations` | plan-01 limitation ids not covered by this nuisance | empty list only after §3.1 review |
| `status` | `draft`, `measured`, or `frozen` | `frozen` requires signed DEC plus paired variation evidence |

Example draft records:

| `nuisance_id` | `variation_kind` | `minus_1sigma` / `plus_1sigma` | `status` |
|---|---|---|---|
| `N2` | `continuous` | `-1136` / `+1136` photons per MeV around nominal scintillator yield | `draft` |
| `N4` | `discrete_envelope` | lowest/highest physics-list response within the listed model set | `draft` |
| `N8` | `scenario_envelope` | `perfect` / `worst_case_construction` geometry scenarios around `nominal_survey` | `draft` |

The fixture is deliberately stricter than the prose registry: a result
with missing `nominal_ref`, empty `affected_observables`, or an
unreviewed `unbounded_limitations` list is incomplete rather than a
zero-systematic result.

### 1.2 Machine-readable nuisance throw fixture

Each nuisance application emits one nominal-linked throw record. This is
the audit surface used to build the §2 covariance and to prove that a
quoted result really included the claimed nuisance set:

| Field | Required content | Review rule |
|---|---|---|
| `throw_id` | stable key, e.g. `N2.minus.sig_foil_v3` | unique within the dataset/result scope |
| `nuisance_id` | one of `N1`-`N10` | must resolve to a §1 registry row |
| `direction` | `minus`, `plus`, `nominal`, or named scenario endpoint | both non-nominal directions required unless the DEC defines a discrete envelope |
| `variation_payload` | numeric shift, model tag, or scenario id | matches `variation_kind` and the §1 ±1σ definition |
| `dataset_or_channel` | sample id, background node, or signal-efficiency row | joins to plan 44/47 result rows |
| `affected_observables` | list actually recomputed by the throw | non-empty subset of the registry row |
| `paired_nominal_result_id` | baseline result key | every throw is compared to a frozen nominal row |
| `paired_opposite_throw_id` | plus/minus mate or null for envelopes | required for continuous nuisances |
| `correlation_flags` | copied registry flags | used to select §2 matrix entries |
| `throw_status` | `draft`, `measured`, `frozen`, or `incomplete` | incomplete throws cannot enter final covariance |

A covariance row may consume only `measured` or `frozen` throw pairs.
Draft or incomplete throws are still listed in plan 47, but their
result rows carry the relevant missing-systematic flag.

Initial throw-row examples:

| `throw_id` | `nuisance_id` | `direction` | `variation_payload` | `dataset_or_channel` | `affected_observables` | `paired_nominal_result_id` | `paired_opposite_throw_id` | `throw_status` |
|---|---|---|---|---|---|---|---|---|
| `N2.minus.sig_foil_v3.ch10` | `N2` | `minus` | scintillator yield `nominal - 1136 photons/MeV` | `sig_foil_v3` | E.1/E.2, E.3/E.4, S.1, S.5, signal acceptance | `sig_foil_v3.ch10.nominal` | `N2.plus.sig_foil_v3.ch10` | `draft` |
| `N2.plus.sig_foil_v3.ch10` | `N2` | `plus` | scintillator yield `nominal + 1136 photons/MeV` | `sig_foil_v3` | same as the N2 minus row | `sig_foil_v3.ch10.nominal` | `N2.minus.sig_foil_v3.ch10` | `draft` |
| `N4.qgsp_bert.beam_direct.ch10` | `N4` | `qgsp_bert` | physics-list endpoint `qgsp_bert` | `beam_neutron_hibeam_direct_v1` | secondary multiplicity and background survival | `beam_direct.ch10.nominal_hp` | null for discrete envelope | `draft` |
| `N8.worst_geometry.cosmic_muon.ch10` | `N8` | `plus` | scenario endpoint `worst_case_construction` | `cosmic_cry_essLund_overburdenA_v1` | vertex, matching, π⁰ mass, selection survival | `cosmic_muon.ch10.nominal_survey` | `N8.perfect_geometry.cosmic_muon.ch10` | `draft` |

These examples are audit-row shapes. They cannot enter the covariance
until the paired nominal rows exist and the corresponding result hashes
show that only the declared nuisance payload changed.

Initial throw-row rejection examples:

| `throw_rejection_id` | Invalid throw pattern | Required status | Review guard |
|---|---|---|---|
| `continuous_missing_plus` | continuous minus throw has no paired plus throw | `incomplete` | covariance cannot consume one-sided continuous shifts |
| `nominal_hash_missing` | throw lacks a frozen paired nominal result id/hash | `incomplete` | result delta cannot be attributed to the nuisance |
| `payload_kind_mismatch` | scenario endpoint used for a `continuous` nuisance or numeric shift used for an envelope | `incomplete` | variation payload must match §1 `variation_kind` |
| `empty_observable_list` | throw recomputes no affected observables | `incomplete` | cannot clear a missing-systematic flag for any quoted result |

## 2. Correlation matrix

A nuisance is fully correlated with itself. The up/down throws of a
single nuisance are anti-correlated by construction, but that
anti-correlation is encoded inside the throw pair rather than in the
inter-nuisance matrix. Until paired variation runs exist, `M0` means
"correlation to be measured; use numeric 0.0 in interim covariance and
carry the missing-correlation flag in the ledger."

Explicit seed matrix (rows/columns are the §1 nuisance IDs):

| Row | N1 | N2 | N3 | N4 | N5 | N6 | N7 | N8 | N9 | N10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| N1 | 1.0 | M0 | M0 | M0 | 0.0 | 0.0 | 0.0 | 0.0 | M0 | 0.0 |
| N2 | M0 | 1.0 | M0 | 0.0 | 0.0 | 0.0 | 0.0 | M0 | M0 | 0.0 |
| N3 | M0 | M0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | M0 | M0 | 0.0 |
| N4 | M0 | 0.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | M0 |
| N5 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| N6 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| N7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| N8 | 0.0 | M0 | M0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | M0 | M0 |
| N9 | M0 | M0 | M0 | 0.0 | 0.0 | 0.0 | 0.0 | M0 | 1.0 | 0.0 |
| N10 | 0.0 | 0.0 | 0.0 | M0 | 0.0 | 0.0 | 0.0 | M0 | 0.0 | 1.0 |

Freeze rules:

| Pair / group | Initial correlation | How it is frozen |
|---|---:|---|
| same nuisance varied up/down | -1.0 | analytic by construction |
| N1/N2/N3/N9 detector-calibration group | M0 | paired calibration throws; default numeric 0.0 until measured |
| N2/N3/N8/N9 calorimeter-energy group | M0 | paired calorimeter and geometry runs; default numeric 0.0 until measured |
| N1/N4 ionisation-model overlap | M0 | paired W-value and physics-list variation |
| N4/N10 background-shape overlap | M0 | paired physics-list and material-budget variation |
| N6 cosmic flux vs N7 beam-neutron flux | 0.0 | independent source normalisations despite sharing a broad background-normalisation label |
| N8 geometry vs N10 material budget | M0 | geometry/material paired scenario envelope |
| no shared flag and no listed exception | 0.0 | default independence |

### 2.1 Correlation-matrix validation gate

Before plan 47 or plan 50 quotes a covariance result, the nuisance
matrix is checked mechanically:

1. The §1 registry must contain exactly one row for each ID `N1`–`N10`.
2. The §2 matrix must be square with the same row/column IDs and no
   missing cells.
3. Diagonal entries must be `1.0`; off-diagonal entries must be one of
   `0.0` or `M0` until paired variation runs replace them with a
   measured coefficient.
4. The matrix must be symmetric. A pair such as `N2/N8` may be marked
   `M0`, but both directions must carry the same marker.
5. Any `M0` pair used in a quoted result is listed in the plan-47
   ledger as a missing-correlation flag, even though the interim
   numeric covariance uses `0.0` for that pair.

### 2.2 Machine-readable correlation-pair fixture

The matrix is serialized as canonical unordered pair rows so plan 47 can
audit covariance inputs without re-parsing the prose table:

| Field | Required content | Review rule |
|---|---|---|
| `correlation_pair_id` | stable key such as `N2__N8` | one row per unordered nuisance pair, including diagonals |
| `nuisance_id_a`, `nuisance_id_b` | IDs from the §1 registry | both IDs must exist exactly once |
| `seed_value` | `1.0`, `0.0`, or `M0` from §2 | must match both matrix directions |
| `numeric_interim_value` | numeric value used before paired runs | `M0` maps to `0.0` and requires a flag |
| `measurement_required` | boolean | true for every `M0` off-diagonal pair |
| `measurement_result_id` | paired-run result key or null | required before an `M0` pair becomes frozen |
| `ledger_flag_required` | boolean | true whenever `measurement_required` is true and result is used |
| `correlation_dec_id` | DEC id authorising the grouping | draft DEC keeps covariance provisional |
| `pair_status` | `seeded`, `measured`, `frozen`, or `blocked` | only measured/frozen pairs can clear missing-correlation flags |

The pair fixture is rejected if a matrix cell has no matching pair row,
if a pair row is asymmetric with the table, or if an `M0` pair reaches a
quoted result without a ledger flag.

Initial pair-row examples:

| `correlation_pair_id` | `nuisance_id_a` | `nuisance_id_b` | `seed_value` | `numeric_interim_value` | `measurement_required` | `measurement_result_id` | `ledger_flag_required` | `correlation_dec_id` | `pair_status` |
|---|---|---|---:|---:|---:|---|---:|---|---|
| `N1__N1` | `N1` | `N1` | 1.0 | 1.0 | false | null | false | `DEC-45-CORRELATION-SEED` | `seeded` |
| `N2__N8` | `N2` | `N8` | `M0` | 0.0 | true | null | true | `DEC-45-CALIBRATION-GROUPING` | `seeded` |
| `N6__N7` | `N6` | `N7` | 0.0 | 0.0 | false | null | false | `DEC-45-CORRELATION-SEED` | `seeded` |
| `N8__N10` | `N8` | `N10` | `M0` | 0.0 | true | null | true | `DEC-45-GEOMETRY-MATERIAL-GROUPING` | `seeded` |

These examples cover the three seed classes: diagonal identity,
independent off-diagonal zero, and measured-later `M0` pairs.

DEC stubs:

| DEC id | Convention to sign | Default |
|---|---|---|
| `DEC-45-CORRELATION-SEED` | initial correlation policy before paired runs exist | self = +1, up/down = -1, unshared pairs = 0, M0 pairs numerically 0.0 but flagged |
| `DEC-45-CALIBRATION-GROUPING` | whether N1/N2/N3/N9 share detector-calibration correlations and whether N2/N3/N8/N9 share `calorimeter_energy` | group them and require paired runs before final covariance |
| `DEC-45-GEOMETRY-MATERIAL-GROUPING` | whether N8/N10 are correlated | treat as measured-only correlation, default 0 |

## 3. Single-source rule

A calibration uncertainty enters the analysis exactly once. If it
appears as a Class C constant uncertainty (plan 04 §6) it does not
also appear as a nuisance parameter; if it appears as a nuisance, the
Class C value is the nominal.

Initial single-source conflict examples:

| `conflict_case_id` | Duplicate source pattern | Required resolution | Review guard |
|---|---|---|---|
| `scint_yield_classc_vs_N2` | scintillator yield varied as both a Class C constant and nuisance `N2` | keep nominal in Class C and move uncertainty to `N2` throws | plan-47 result cites one uncertainty source only |
| `leadglass_calib_N3_vs_N9` | lead-glass calibration and optical-yield residual both change photon energy | separate response-slope covariance (`N3`) from optical residual (`N9`) | covariance row must not count the same residual twice |
| `geometry_alignment_N8_vs_material_N10` | geometry displacement changes material path length and alignment observables | keep alignment in `N8`; put radiation-length/material envelope in `N10` | paired-run metadata states which payload was changed |
| `beam_flux_N7_vs_rate_source` | beam-neutron per-pulse yield appears in both plan-44 rate source and nuisance `N7` | rate-source DEC defines nominal yield; `N7` varies only around it | plan-46 bundle includes nominal rate plus nuisance throw, not two normalisations |

### 3.1 Limitation coverage map

Plan 01 §6 limitations are not all numeric nuisances yet. The ledger
must therefore distinguish *bounded by a §1 nuisance* from
*unbounded caveat carried to plan 50*:

| Plan-01 limitation | Coverage in this registry | Reporting rule |
|---|---|---|
| L1 position exact / no sensor resolution | N8 geometry alignment plus plan-40 closure pulls | quote residual geometry/position envelope; cite digitisation seam as missing if no smearing run exists |
| L2 timing exact / no jitter | unbounded until timing-jitter scenario exists | carry as timing caveat on E.8, S.1/S.6 results |
| L3 no energy noise / threshold / non-linearity | N2, N3, N9 cover gain/response; thresholds remain unbounded | quote calibration envelope and separately flag threshold/noise absence |
| L4 no dead or hot channels | unbounded until channel-mask scenario exists | plan-50 caveat for acceptance and fake-rate claims |
| L5 no trigger/dead-time/buffer model | unbounded | no live-rate or DAQ-efficiency claim without explicit caveat |
| L6 no beam bunch structure | N7 covers flux only | beam-timing background claims carry bunch-structure caveat |
| L7 exact geometry / no alignment systematics | N8 | include N8 in vertex, matching, π⁰, and selection results |
| L8 no ageing / temperature drift | unbounded | long-run stability claims require caveat |
| L9 no B-field | out of current scope | no charge-sign or magnetic-momentum claim may be quoted |
| L10 MC-tuned calibration constants | N1, N2, N3, N9 | include detector-calibration group in all energy/PID results |
| L11 no cosmic+signal pile-up | unbounded | total-background and overlay claims require caveat |
| L12 optical-path on/off changes lead-glass observable | N9 | include optical nuisance in photon/π⁰/visible-mass results |

### 3.2 Unbounded limitation handling rule

An `unbounded` entry in §3.1 is not a hidden nuisance parameter. It is
a blocking caveat until a bounded scenario or calibration study creates
a named §1 nuisance with a ±1σ definition. Quoted results therefore
follow this rule:

1. Do not assign Gaussian, log-normal, or envelope weights to an
   `unbounded` limitation.
2. Any result whose observable touches an `unbounded` limitation carries
   an explicit plan-47 ledger field `unbounded_limitations: [...]` and
   a plan-50 caveat sentence.
3. If the limitation can change an acceptance, fake-rate, or live-rate
   conclusion, the result is labelled `conditional_on_current_rebuild_model`
   and cannot be used as an unconditional defence claim.
4. Closing the caveat requires either adding a bounded §1 nuisance row
   or a DEC entry that proves the limitation is irrelevant for the
   quoted observable.

### 3.3 Machine-readable unbounded-limitation fixture

Every unbounded or partially bounded plan-01 limitation emits a caveat
record so plan 46, plan 47, and plan 50 can reject unconditional quotes:

| Field | Required content | Review rule |
|---|---|---|
| `limitation_id` | `L1`-`L12` from §3.1 | must resolve to exactly one coverage row |
| `coverage_status` | `bounded`, `partially_bounded`, `unbounded`, or `out_of_scope` | no implicit numeric nuisance for unbounded rows |
| `nuisance_ids` | matching §1 nuisance ids or empty list | empty requires `coverage_status != bounded` |
| `affected_observables` | observables/results that must carry the caveat | non-empty unless out of current scope |
| `ledger_flag` | plan-47 field name, e.g. `unbounded_limitations` | required for all non-bounded rows |
| `defence_caveat_text` | plan-50 sentence stub | required before a quoted result can ship |
| `closure_path` | bounded scenario, calibration study, or DEC proof needed to close | prevents silent caveat disappearance |
| `conditional_quote_required` | boolean | true for acceptance, fake-rate, or live-rate impacts |

A result row with a touched non-bounded limitation is incomplete unless
it carries the matching `ledger_flag` and caveat text.

Initial unbounded-limitation examples:

| `limitation_id` | `coverage_status` | `nuisance_ids` | `affected_observables` | Required ledger behavior |
|---|---|---|---|---|
| `L2` | `unbounded` | [] | timing windows, E.8, S.1/S.6 timing-dependent rates | carry `unbounded_limitations: [L2]` until a timing-jitter nuisance exists |
| `L3` | `partially_bounded` | [`N2`, `N3`, `N9`] | energy response, photon/π⁰ mass, thresholds | include calibration nuisances and separately flag threshold/noise absence |
| `L5` | `unbounded` | [] | live-rate, exposure, DAQ-efficiency, total-background claims | mark quotes conditional on current rebuild model |
| `L9` | `out_of_scope` | [] | charge-sign or magnetic-momentum claims | reject such claims from the current defence package |
| `L11` | `unbounded` | [] | pile-up, overlay, total-background robustness | require caveat beside plan-44/46 background sums |

These rows prevent missing limitations from being converted into
zero-width Gaussian nuisances. A bounded replacement must add a new §1
nuisance or cite a DEC proof that the limitation is irrelevant.

### 3.4 Initial downstream-handoff examples

Systematics handoffs must expose whether a result is using frozen throws,
seed correlations, or caveat-only limitations:

| `handoff_case_id` | Downstream consumer | Required payload | Required guard |
|---|---|---|---|
| `frozen_throw_bundle_to_p46` | plan 46 significance protocol | nominal result id, paired throw ids, nuisance ids, and covariance pair ids | every throw is measured/frozen and every consumed `M0` pair has a ledger flag or measurement |
| `draft_throw_caveat_to_p47` | plan 47 reproduction ledger | draft or incomplete throw ids plus missing evidence reason | cannot clear a systematic-coverage checklist item |
| `unbounded_limitation_to_p50` | plan 50 defence package | limitation id, affected observables, caveat sentence, and closure path | not converted to a numeric nuisance or zero-width uncertainty |
| `single_source_conflict_to_review` | plan 05/47 review | duplicate source ids, proposed owning nuisance, and result rows affected | blocked until exactly one source owns the uncertainty |

Any significance bundle lacking these handoff ids is incomplete because
it cannot prove which nuisance set, correlations, and unbounded caveats
were applied to the quoted result.

Initial production-promotion checklist:

| `promotion_check_id` | Evidence required | Blocks promotion when missing |
|---|---|---|
| `p45_registry_complete` | nuisance rows N1-N10 with variation kind, ±1σ definition, and affected observables | quoted results cannot prove systematic coverage |
| `p45_throw_pairs_measured` | nominal-linked plus/minus or envelope throws with hashes | result deltas cannot be attributed to a nuisance |
| `p45_correlations_accounted` | correlation-pair rows for every consumed nuisance pair | covariance would silently assume missing correlations |
| `p45_unbounded_caveats_carried` | non-bounded limitations copied into ledger and defence caveats | caveat-only effects could become zero-width nuisances |

A plan-46 input bundle may mark systematics complete only when these
checks are traceable. Draft throws or M0 correlations without flags keep
the result provisional.

Initial evidence-bundle examples:

| `evidence_bundle_id` | Included rows | Reviewer action |
|---|---|---|
| `p45_frozen_covariance_bundle_v0` | N1-N10 registry rows, measured throw pairs, correlation-pair rows, and frozen covariance hash | approve as plan-46 covariance input only when every consumed nuisance is bounded |
| `p45_draft_throw_incomplete_bundle_v0` | nominal-linked plus/minus throws missing one hash or affected-observable row | keep provisional and exclude from quoted uncertainty until completed |
| `p45_m0_flagged_bundle_v0` | zero-correlation placeholders, rationale flags, and reviewer signoff rows | allow temporary diagonal covariance only with explicit M0 limitation text |
| `p45_unbounded_limitation_bundle_v0` | caveat-only limitations, no numeric ±1σ, defence-package prose, and affected observables | carry to plan 50 rather than assigning a zero-width nuisance |

Evidence bundles separate measured covariance inputs from draft throws,
temporary correlation assumptions, and unbounded limitations. Plan 46
should consume only frozen bundles for numeric propagation and should
quote caveat bundles separately.

## 4. Acceptance criteria

- §1 registry complete; ≥ 10 nuisances.
- §2 correlation matrix populated.
- §3 single-source rule and §3.1 limitation coverage audited (no
  double-counting; no unbounded limitation silently folded into a
  numeric nuisance).
- Plan 47 ledger and plan 50 defence package cite nuisance IDs by
  name.
- Promotion checks prove registry completeness, paired throw evidence,
  consumed correlations, and carried caveats before plan 46 treats the
  covariance as final.
- Evidence bundles keep frozen covariance, incomplete throws, M0
  placeholders, and unbounded limitations separate.

## 5. Risks

- *Risk:* nuisances missing for unmodelled effects (plan 01 §6
  limitations).
  *Mitigation:* §3.1 maps every limitation either to a named nuisance
  or to an explicit "unbounded by current rebuild" caveat surfaced by
  plan 50.

## 6. Dependencies

- **04, 12, 13, 14, 17, 18, 38** — inputs.
- *Consumed by:* plan 46 (significance), plan 47, plan 50.

## 7. References

- ATLAS / CMS standard nuisance-parameter conventions.
