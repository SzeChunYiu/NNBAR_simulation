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

### 3.1 Required decision record

Every significance or limit calculation writes a method-dispatch row
before returning a number:

| Field | Meaning |
|---|---|
| `dataset_or_channel` | plan-43 signal row or plan-44 background node |
| `s_expected`, `b_expected`, `n_obs` | post-selection counts after nuisance weighting |
| `handover_rule` | literal rule string, initially `n_obs <= 5 or b <= 5` |
| `method_selected` | one of `Feldman-Cousins`, `Asimov Z0`, or `CLs/pyhf` |
| `confidence_level` | 0.90 primary, 0.95 cross-check when requested |
| `nuisance_ids` | plan-45 IDs included in the calculation |
| `decision_dec_id` | one of the DEC stubs below once signed |

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

Any record with missing `decision_dec_id`, hidden `unbounded_limitations`,
or a method mismatch between dispatch and result is rejected before the
number reaches the reproduction ledger.

## 4. Acceptance criteria

- §1 Z_0 target implementation lands in the L3-owned
  `nnbar_reconstruction/statistics/` package; until then, plan 46
  specifies the formula and validation examples only.
- §2 limit convention chosen and signed.
- §3 handover implemented and tested.

## 5. Dependencies

- **04, 43, 44, 45** — inputs.
- *Consumed by:* plan 47 (ledger), plan 50 (defence package).

## 6. References

- Cowan et al., *Eur. Phys. J. C* 71 (2011) 1554 (asymptotic
  formulas).
- Feldman & Cousins (cited in plan 04).
- pyhf documentation.
