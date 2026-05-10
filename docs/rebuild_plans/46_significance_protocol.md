---
id: 46_significance_protocol
title: Significance protocol — Z₀, expected/observed limits
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 43_signal_efficiency, 44_background_taxonomy, 45_systematics_taxonomy]
outputs:
  - {path: docs/rebuild_plans/46_significance_protocol.md, schema: this file}
acceptance:
  - {test: Z₀ definition signed in DEC, method: §1 review, pass_when: signed}
  - {test: expected and observed limit conventions named (CLs vs F-C), method: §2 review, pass_when: signed}
  - {test: finite-sample regime (zero or near-zero observed) handled by F-C explicitly, method: §3, pass_when: implemented}
risks:
  - {risk: asymptotic significance overstates Z₀ in low-stats regime, mitigation: §3 F-C handover}
estimated_effort: S
last_updated: 2026-05-10
---

# Significance protocol

*Charter.* The single-source convention for every "discovery
significance" or "limit" the rebuild quotes.

## 1. Discovery significance

Definition: asymptotic Asimov discovery formula

```
Z_0 = sqrt( 2 ((s + b) ln(1 + s/b) - s) )
```

valid for `s, b > 0` and reasonably large counts. Inputs `s` and `b`
come from plan 43 (signal efficiency) and plan 44 (background tree),
weighted by their nuisances per plan 45.

`s` is the expected selected signal count for the exposure being
quoted; `b` is the summed expected selected background count after
applying plan-44 channel rates and plan-45 nuisance weights. The
function is not evaluated for `b = 0`; those rows use §3.

Worked examples for implementation tests:

| Case | s | b | Expected `Z_0` | Use |
|---|---:|---:|---:|---|
| high-background sanity | 50 | 20 | 8.68 | asymptotic path should run |
| modest-count boundary | 10 | 6 | 3.37 | asymptotic path still allowed |
| zero-background row | 10 | 0 | not evaluated | must dispatch to §3 F-C |

### 1.1 Numerical validation gate

The implementation test fixture must recompute the examples rather than
copy the table. The gate is:

1. the Asimov calculation for `s = 50`, `b = 20` rounds to `8.68` at two decimals.
2. the Asimov calculation for `s = 10`, `b = 6` rounds to `3.37` at two decimals.
3. Any request with `b = 0` returns no asymptotic value and records a
   §3 method-dispatch row selecting `Feldman-Cousins`.
4. The zero-survivor background example in §2 computes
   `2.44 / 244000 = 1.0e-5` within displayed precision.

#### 1.1.1 Machine-readable numerical validation fixture

The worked examples are serialized as validation cases so an
implementation cannot pass by copying prose values:

| Field | Required content | Review rule |
|---|---|---|
| `validation_case_id` | stable key such as `asimov_high_b` | unique within plan 46 |
| `quantity` | `discovery_Z0` or `background_survival_ul` | selects the formula under test |
| `s_input`, `b_input`, `n_obs_input` | numeric inputs or null where not applicable | copied into a §3.1 dispatch row |
| `expected_method` | `Asimov Z0` or `Feldman-Cousins` | must follow §3 handover |
| `expected_display_value` | rounded target such as `8.68` or `1.0e-5` | recomputed by the implementation, not hard-coded |
| `rounding_rule` | two-decimal Z or displayed-precision upper limit | prevents hidden precision drift |
| `dispatch_required` | boolean | true for every validation row |
| `validation_status` | `pass`, `fail`, or `not_run` | `not_run` blocks acceptance |

A validation row is accepted only when the result row, dispatch row, and
input bundle all agree on method, inputs, and displayed value.

Initial validation rows:

| `validation_case_id` | `quantity` | `s_input` | `b_input` | `n_obs_input` | `expected_method` | `expected_display_value` | `rounding_rule` | `dispatch_required` | `validation_status` |
|---|---|---:|---:|---:|---|---:|---|---:|---|
| `asimov_high_b` | `discovery_Z0` | 50 | 20 | 70 | `Asimov Z0` | 8.68 | two-decimal Z | true | `not_run` |
| `asimov_modest_boundary` | `discovery_Z0` | 10 | 6 | 16 | `Asimov Z0` | 3.37 | two-decimal Z | true | `not_run` |
| `zero_background_dispatch` | `discovery_Z0` | 10 | 0 | 10 | `Feldman-Cousins` | null | no asymptotic value when `b = 0` | true | `not_run` |
| `zero_survivor_background_ul` | `background_survival_ul` | 0 | 0 | 0 | `Feldman-Cousins` | 1.0e-5 | displayed-precision upper limit from `2.44 / 244000` | true | `not_run` |

The rows start as `not_run` because L3 owns the eventual statistics
implementation. Plan 47 may flip them only after recomputing the formula
and checking the linked dispatch/result/input-bundle rows.

DEC stub: `DEC-46-Z0-ASYMPTOTIC` — choose the Cowan Asimov discovery
formula above for `s > 5` and `b > 5`; require §3 F-C handover for
zero/near-zero rows. Status: draft, pending Methodology Council sign-off.

## 2. Limit conventions

Plan 46 chooses a convention; codex-supervisor implements the chosen
path. Candidates:

- **CLs** (LHC standard) via `pyhf`.
- **Feldman-Cousins** (PDG standard).

For NNBAR's near-zero-background regime, F-C is more honest in low
stats and is the recommended default. CLs is the alternative for
cross-check.

90% C.L. is the default reporting level; 95% C.L. is reported in
parallel for cross-comparison with literature.

Decision table:

| Quantity | Primary convention | Cross-check | Worked example / expected output |
|---|---|---|---|
| zero-survivor background upper limit | Feldman-Cousins 90% C.L. | none required | `n_obs=0`, `b=0`, `N=244000` gives `ε90 = 2.44 / 244000 = 1.0e-5` per plan 04 §5 |
| nonzero low-count observed limit | Feldman-Cousins unified interval | CLs only if a pyhf model exists | `n_obs=3`, `b=1.2` dispatches to F-C table/toy construction, not asymptotic Z |
| high-count expected/observed limit | CLs via `pyhf` | Feldman-Cousins spot-check | `b>5` and binned nuisance model present: report CLs 90% and 95% in the appendix |

DEC stub: `DEC-46-LIMIT-CONVENTION` — choose Feldman-Cousins as the
primary low-count and zero-survivor limit convention; use CLs as the
high-count cross-check when a pyhf model is available. Status: draft,
pending Methodology Council sign-off.

## 3. Finite-sample handover

When observed `n_obs ≤ 5` or expected `b ≤ 5`, the asymptotic Z_0
is replaced by F-C. The handover threshold is signed in DEC.

Handover rule for every significance/limit request:

1. Build `s`, `b`, and `n_obs` after applying plan-44 rates and
   plan-45 nuisances.
2. If `n_obs ≤ 5` **or** `b ≤ 5`, record
   `method selected = Feldman-Cousins` and do not evaluate asymptotic `Z_0`.
3. Otherwise use §1 for discovery significance and §2 CLs for
   high-count limits; still record the F-C spot-check when available.

Worked examples:

| n_obs | b | Decision | Reason |
|---:|---:|---|---|
| 0 | 0.0 | F-C | zero-survivor upper-limit row |
| 4 | 12.0 | F-C | observed count is in small-count regime |
| 8 | 4.5 | F-C | expected background is in small-count regime |
| 8 | 5.5 | asymptotic/CLs allowed | both thresholds are above the handover |

### 3.1 Machine-readable method-dispatch fixture

Every significance or limit calculation writes a method-dispatch row
before returning a number:

| Field | Required content | Review rule |
|---|---|---|
| `dispatch_id` | stable key for this method decision | referenced by the result and input-bundle rows |
| `dataset_or_channel` | plan-43 signal row or plan-44 background node | must match the input bundle |
| `s_expected`, `b_expected`, `n_obs` | post-selection counts after nuisance weighting | copied from a traceable §3.4 input bundle |
| `handover_rule` | literal rule string, initially `n_obs <= 5 or b <= 5` | cannot be changed without `DEC-46-FC-HANDOVER` |
| `method_selected` | one of `Feldman-Cousins`, `Asimov Z0`, or `CLs/pyhf` | must follow the handover rule |
| `confidence_level` | 0.90 primary, 0.95 cross-check when requested | must match the result row |
| `nuisance_ids` | plan-45 IDs included in the calculation | must match applied throw ids in the input bundle |
| `unbounded_limitations` | caveat ids inherited from plans 44-45 | non-empty blocks unconditional defence claims |
| `decision_dec_id` | one of the DEC stubs below once signed | draft DEC keeps result provisional |

The `method_selected` values are ledger labels, not claims that CLI
subcommands or Python functions with matching names currently exist.

This row is what plan 47 and plan 50 cite. A result without the
dispatch row is incomplete even if the numeric Z or limit can be
computed.

DEC stub: `DEC-46-FC-HANDOVER` — freeze the handover at
`n_obs ≤ 5 or b ≤ 5`, with no data-driven retuning after unblinding.
Status: draft, pending Methodology Council sign-off.

### 3.2 Dispatch-row validation examples

The method-dispatch row is itself a tested output. Fixtures should
check the following rows before any plan-47 or plan-50 number is
accepted:

| Example | `dataset_or_channel` | `s_expected` | `b_expected` | `n_obs` | `method_selected` | Required behavior |
|---|---|---:|---:|---:|---|---|
| high-background discovery | `sig_validation_high_b` | 50 | 20 | 70 | `Asimov Z0` | computes §1 `Z_0 = 8.68` and records no F-C substitution |
| zero-survivor background | `cosmic_muon_zero_survivor` | 0 | 0 | 0 | `Feldman-Cousins` | records no asymptotic Z and reports `epsilon90 = 1.0e-5` for `N=244000` |
| nonzero low-count limit | `beam_neutron_low_count` | 0 | 1.2 | 3 | `Feldman-Cousins` | dispatches to low-count interval construction, not CLs/asymptotic Z |
| high-count limit cross-check | `background_high_count_shape` | 0 | 12 | 18 | `CLs/pyhf` | allowed only when a binned nuisance model exists; otherwise result is incomplete |

For all examples, `handover_rule`, `confidence_level`,
`nuisance_ids`, and `decision_dec_id` must be populated even when the
calculator is a target implementation rather than current CLI surface.

### 3.3 Machine-readable result fixture

Each significance or limit calculation emits a result record as well as
the dispatch row. This prevents a review from accepting a naked number
whose method or caveats cannot be reconstructed. Minimum fields:

| Field | Required content | Review rule |
|---|---|---|
| `result_id` | stable ledger key | unique within plan 47 and plan 50 |
| `dataset_or_channel` | plan-43 signal row or plan-44 background node | must match the dispatch row |
| `quantity` | `discovery_Z0`, `expected_limit`, `observed_limit`, or `background_survival_ul` | drives the allowed method set |
| `method_selected` | copied from §3.1 | no mismatch between dispatch and result |
| `central_value` | numeric result or null when dispatch forbids it | asymptotic `Z_0` is null for F-C rows |
| `interval_low`, `interval_high` | confidence/credible interval endpoints when applicable | never collapse a zero-survivor upper limit to `[0, 0]` |
| `confidence_level` | `0.90` primary, optional `0.95` cross-check | must match §2 reporting level |
| `s_expected`, `b_expected`, `n_obs` | post-nuisance counts used by the calculation | copied from dispatch row after rounding policy is applied |
| `nuisance_ids` | plan-45 nuisance IDs included | empty only for an explicitly nuisance-free validation fixture |
| `unbounded_limitations` | plan-45 §3.1 caveats affecting the result | non-empty list blocks unconditional defence claims |
| `decision_dec_id` | signed or draft DEC id | must name the convention that authorised the method |

Review fixtures:

| Fixture | Required record property |
|---|---|
| `sig_validation_high_b` | `quantity = discovery_Z0`, `method_selected = Asimov Z0`, and `central_value = 8.68` after rounding |
| `cosmic_muon_zero_survivor` | `quantity = background_survival_ul`, `method_selected = Feldman-Cousins`, `central_value = null`, and `interval_high = 1.0e-5` within displayed precision |
| `beam_neutron_low_count` | `method_selected = Feldman-Cousins` and no asymptotic or CLs value is emitted |
| `background_high_count_shape` | `method_selected = CLs/pyhf` only if a binned model is attached; otherwise `result_status = incomplete` |

Initial result-record examples:

| `result_id` | `dataset_or_channel` | `quantity` | `method_selected` | `central_value` | `interval_low`, `interval_high` | `decision_dec_id` | `result_status` |
|---|---|---|---|---:|---|---|---|
| `result_asimov_high_b` | `sig_validation_high_b` | `discovery_Z0` | `Asimov Z0` | 8.68 | null, null | `DEC-46-Z0-ASYMPTOTIC` | `validation` |
| `result_zero_survivor_ul` | `cosmic_muon_zero_survivor` | `background_survival_ul` | `Feldman-Cousins` | null | 0, `1.0e-5` | `DEC-46-LIMIT-CONVENTION` | `validation` |
| `result_beam_low_count_fc` | `beam_neutron_low_count` | `observed_limit` | `Feldman-Cousins` | null | populated by F-C construction | `DEC-46-FC-HANDOVER` | `draft` |
| `result_high_count_shape_blocked` | `background_high_count_shape` | `expected_limit` | `CLs/pyhf` | null | null, null | `DEC-46-LIMIT-CONVENTION` | `incomplete_without_binned_model` |

These examples are ledger shapes. They are accepted only if the linked
dispatch row and input bundle carry the same method, counts, caveats,
and confidence level.

Any record with missing `decision_dec_id`, hidden `unbounded_limitations`,
or a method mismatch between dispatch and result is rejected before the
number reaches the reproduction ledger.

Initial result-record rejection examples:

| `result_rejection_id` | Invalid result pattern | Required status | Review guard |
|---|---|---|---|
| `method_dispatch_mismatch` | dispatch selects F-C but result records Asimov or CLs | `blocked` | method must be copied exactly from the dispatch row |
| `zero_ul_collapsed` | zero-survivor upper limit written as interval `[0, 0]` | `blocked` | F-C interval high must remain positive and explicit |
| `missing_decision_id` | result has a number but no convention DEC | `blocked` | unsigned methods cannot enter plan 47/50 |
| `hidden_limitations` | input bundle carries caveats but result row omits `unbounded_limitations` | `blocked` | unconditional defence quote is rejected |

### 3.4 Machine-readable input-bundle fixture

Every dispatch/result pair also records the input bundle that produced
`s_expected`, `b_expected`, and `n_obs`. This prevents a later review
from accepting counts that cannot be traced back to signal, background,
and nuisance records:

| Field | Required content | Review rule |
|---|---|---|
| `input_bundle_id` | stable key for this calculation input set | referenced by both dispatch and result rows |
| `signal_result_id` | plan-43 signal-efficiency or validation row | null only for background-only upper limits |
| `background_rate_result_ids` | plan-44 rate-result rows included in `b` | every row must have `rate_included_in_b = true` |
| `nuisance_throw_ids` | plan-45 measured/frozen throws applied | draft throws require a missing-systematic flag |
| `selection_config_id` | plan-37 Ch 10 baseline or retune id | must match the background and signal rows |
| `s_expected_source`, `b_expected_source`, `n_obs_source` | formulas or ledger keys used to build counts | no hand-entered count without provenance |
| `unbounded_limitations` | caveats inherited from plans 44-45 | non-empty list blocks unconditional defence claims |
| `bundle_status` | `validation`, `complete`, or `incomplete` | only complete bundles may feed final quotes |

Initial input-bundle examples linked to the validation cases:

| `input_bundle_id` | `validation_case_id` | `dispatch_id` | `result_id` | `signal_result_id` | `background_rate_result_ids` | Count sources | `bundle_status` |
|---|---|---|---|---|---|---|---|
| `bundle_asimov_high_b_validation` | `asimov_high_b` | `dispatch_asimov_high_b` | `result_asimov_high_b` | `validation_signal_s50` | [`validation_background_b20`] | `s=50`, `b=20`, `n_obs=70` from validation constants | `validation` |
| `bundle_asimov_modest_boundary_validation` | `asimov_modest_boundary` | `dispatch_asimov_modest_boundary` | `result_asimov_modest_boundary` | `validation_signal_s10` | [`validation_background_b6`] | `s=10`, `b=6`, `n_obs=16` from validation constants | `validation` |
| `bundle_zero_background_dispatch_validation` | `zero_background_dispatch` | `dispatch_zero_background` | `result_zero_background_fc` | `validation_signal_s10` | [`validation_background_b0`] | `s=10`, `b=0`, `n_obs=10`; asymptotic Z forbidden | `validation` |
| `bundle_zero_survivor_ul_validation` | `zero_survivor_background_ul` | `dispatch_zero_survivor_ul` | `result_zero_survivor_ul` | null | [`validation_zero_survivor_rate_244k`] | denominator `244000`, survivors `0`, F-C upper limit only | `validation` |

The `validation_*` ids are calculation fixtures, not plan-44 background
rates for final analysis. A production bundle must replace them with
complete plan-43, plan-44, and plan-45 ledger rows before any quote can
enter plan 47 or plan 50.

The dispatch row copies only the final numeric counts; the bundle row is
the provenance contract that makes those counts reviewable.

Initial input-bundle rejection examples:

| `bundle_rejection_id` | Invalid provenance pattern | Required status | Review guard |
|---|---|---|---|
| `missing_signal_source` | `s_expected` is hand-entered but `signal_result_id` is null for a signal quote | `incomplete` | no discovery or expected-limit result may be emitted |
| `draft_background_rate` | background row lacks `rate_included_in_b = true` or signed rate-source DEC | `incomplete` | plan-44 caveat remains outside central `b_expected` |
| `draft_nuisance_throw` | plan-45 nuisance throw is draft or missing paired nominal hash | `incomplete` | result carries missing-systematic flag and cannot be final |
| `unbounded_limitation_hidden` | inherited plan-45 caveat list is non-empty but absent from result row | `blocked` | plan-50 unconditional defence claim is rejected |

### 3.5 Initial downstream-handoff examples

Significance outputs are publishable only through explicit ledger and
defence handoffs:

| `handoff_case_id` | Downstream consumer | Required payload | Required guard |
|---|---|---|---|
| `validation_case_to_p47` | plan 47 reproduction ledger | validation case, input bundle, dispatch row, result row, and recomputed value | all linked rows agree on method, counts, confidence level, and rounding |
| `final_result_to_p50` | plan 50 defence package | complete result row, convention DEC ids, nuisance ids, and caveat list | rejected if any unbounded limitation blocks an unconditional quote |
| `fc_zero_survivor_to_p44` | plan 44 background summary | F-C upper-limit result id and interval endpoint | never converted into central expected background zero |
| `incomplete_bundle_to_review` | plan 05/47 review | missing signal/background/nuisance provenance reason and blocked result id | no result number may be quoted until provenance is complete |

These handoff ids keep validation fixtures, draft calculations, and final
analysis quotes separable. A naked `Z_0`, limit, or upper-limit number
without this linkage is rejected even if the arithmetic is correct.

Initial production-promotion checklist:

| `promotion_check_id` | Evidence required | Blocks promotion when missing |
|---|---|---|
| `p46_validation_cases_recomputed` | worked-example rows linked to dispatch/result/input bundles | formula implementation could be hard-coded or stale |
| `p46_method_dispatch_complete` | every result has a handover-rule row with method and confidence level | low-count rows may use the wrong convention |
| `p46_input_bundle_provenance` | signal, background, nuisance, and caveat inputs trace to plan rows | counts cannot be audited back to sources |
| `p46_limit_conventions_signed` | DEC ids for Z0, limit convention, and F-C handover | unsigned methods could enter plan 47/50 quotes |

A significance or limit row is promotion-ready only when all four checks
are present. Validation rows may exercise arithmetic, but final quotes
require complete provenance and signed convention decisions.

Initial evidence-bundle examples:

| `evidence_bundle_id` | Included rows | Reviewer action |
|---|---|---|
| `p46_asimov_validation_bundle_v0` | Cowan-style worked examples, input bundle ids, dispatch rows, recomputed `Z_0`, and rounding audit | approve arithmetic only; final quotes still need complete provenance |
| `p46_fc_zero_survivor_bundle_v0` | F-C zero-survivor interval, confidence level, background-limit linkage, and handover-rule row | pass endpoint to plan 44/47 without converting it to central `b = 0` |
| `p46_complete_final_quote_bundle_v0` | signal, background, nuisance covariance, caveats, DEC ids, and validation-case references | eligible for plan 47/50 only if no caveat blocks an unconditional quote |
| `p46_incomplete_provenance_bundle_v0` | missing input reason, blocked result id, and review owner for the absent source row | reject any quoted significance or limit number until the source row is supplied |

Evidence bundles force statistics outputs to carry their provenance and
method-dispatch context. A number that cannot name its signal,
background, nuisance, caveat, and convention rows remains a validation
fixture rather than a final result.

## 4. Acceptance criteria

- §1 Z_0 target implementation lands in the L3-owned
  `nnbar_reconstruction/statistics/` package; until then, plan 46
  specifies the formula and validation examples only.
- §2 limit convention chosen and signed.
- §3 handover implemented and tested.
- Promotion checks prove recomputed validation cases, complete method
  dispatch, source-bundle provenance, and signed convention DEC ids
  before plan 47/50 quote a result.
- Evidence bundles keep arithmetic validation, F-C zero-survivor
  endpoints, final quotes, and incomplete-provenance blockers separate.

## 5. Dependencies

- **04, 43, 44, 45** — inputs.
- *Consumed by:* plan 47 (ledger), plan 50 (defence package).

## 6. References

- Cowan et al., *Eur. Phys. J. C* 71 (2011) 1554 (asymptotic
  formulas).
- Feldman & Cousins (cited in plan 04).
- pyhf documentation.
