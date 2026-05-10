---
id: 64_bayesian_limit_cross_check
title: Bayesian limit cross-check for low-count NNBAR results
version: 0.1
status: draft
owner: Methodology Council
depends_on: [00_README, 04_statistical_uncertainty, 43_signal_efficiency, 44_background_taxonomy, 45_systematics_taxonomy, 46_significance_protocol, 47_reproduction_ledger]
outputs:
  - {path: docs/rebuild_plans/64_bayesian_limit_cross_check.md, schema: this file}
  - {path: output/statistics/<result_id>/bayesian_limit.json, schema: §5 result bundle}
  - {path: output/statistics/<result_id>/prior_sensitivity.parquet, schema: §7 prior-sensitivity table}
acceptance:
  - {test: Jeffreys and flat-prior limits are both specified, method: §§2-3 review, pass_when: posterior and integration rules are explicit}
  - {test: comparison to Feldman-Cousins and CLs is defined, method: §6 review, pass_when: dispatch and difference fields are present}
  - {test: prior sensitivity is not hidden, method: §7 review, pass_when: sensitivity table and promotion guard are explicit}
  - {test: plan 46 remains the primary convention, method: §8 review, pass_when: Bayesian output is labelled cross-check unless DEC approves otherwise}
risks:
  - {risk: Bayesian credible intervals are presented as the primary frequentist limit, mitigation: §8 labels them cross-check and requires plan-46 dispatch rows}
  - {risk: prior choice dominates a sparse-count result, mitigation: §7 requires prior-sensitivity bands and a reviewer caveat}
  - {risk: nuisance marginalisation silently drops unbounded plan-45 caveats, mitigation: §4 carries nuisance ids and unbounded limitations into every result}
estimated_effort: M
last_updated: 2026-05-10
---

# Bayesian limit cross-check

*Charter.* Provide an independent Bayesian cross-check for NNBAR limits
in the low-count regime. Plan 46 keeps Feldman-Cousins as the primary
small-count convention and CLs as the high-count cross-check when a
binned model exists. Plan 64 adds a transparent Bayesian calculation
with Jeffreys and flat priors so reviewers can see how much the final
limit depends on prior choice.

## 1. Scope and input contract

Plan 64 consumes the same input bundle as plan 46:

| Input | Source | Required field |
|---|---|---|
| signal expectation | plan 43 | `s_expected` or exposure-to-signal conversion |
| background expectation | plan 44 | `b_expected` plus channel decomposition |
| nuisance model | plan 45 | nuisance ids, priors/constraints, correlation flags |
| observed count | plan 47 / result ledger | `n_obs` and analysis region |
| primary method dispatch | plan 46 | `method_selected`, confidence level, DEC id |

The Bayesian result is not valid without the plan-46 dispatch row. The
cross-check asks whether a Bayesian credible upper limit is consistent
with, tighter than, or looser than the primary plan-46 interval; it does
not silently replace the primary result.

### 1.1 Counting model

For the first implementation, the observed count is modelled as:

`n_obs ~ Poisson(s + b)`

where `s >= 0` is the signal mean and `b >= 0` is the background mean.
When plan 46 has a binned pyhf/CLs model, plan 64 may either marginalise
the same bins or collapse to the total-count validation model. The
chosen mode is recorded in `bayes_model_id`.

## 2. Jeffreys-prior construction

The Jeffreys prior is applied to the total Poisson mean `mu = s + b`.
For known fixed background `b`, the induced prior on signal strength is:

`pi_J(s | b) proportional to (s + b)^(-1/2), for s >= 0`.

The posterior density is:

`p_J(s | n, b) proportional to Poisson(n | s + b) * (s + b)^(-1/2)`.

The 90% upper credible limit `s90_J` satisfies:

`integral_0^s90_J p_J(s | n, b) ds = 0.90 * integral_0^infinity p_J(s | n, b) ds`.

Rules:

1. Use numerical quadrature or an analytically equivalent incomplete
   gamma expression; record which implementation is used.
2. Enforce `s >= 0`; do not allow a negative signal estimate to cancel
   background.
3. If `b = 0` and `n = 0`, the posterior remains integrable under the
   Jeffreys prior; report the finite upper limit with the method id.
4. When background uncertainty is present, marginalise over `b` before
   integrating over `s` as specified in §4.

## 3. Flat-prior construction

The flat prior is the common sensitivity cross-check:

`pi_F(s) proportional to 1, for s >= 0`.

The posterior density is:

`p_F(s | n, b) proportional to Poisson(n | s + b)`.

The 90% upper credible limit `s90_F` is the 90% posterior quantile under
this posterior. The same integration, nonnegative-signal, and nuisance
marginalisation rules apply.

The flat-prior row is not labelled more objective than Jeffreys. It is a
reviewer-facing sensitivity bracket. If the flat and Jeffreys limits
differ by more than the threshold in §7, plan 50 must quote a prior
sensitivity caveat.

### 3.1 Physics derivation for Bayesian cross-checks

#### Physics derivation

Plan 64 physically estimates how much the low-count signal upper limit
depends on the statistical prior. The truth-side quantity is the
ensemble constraint on the nonnegative signal mean; the production
cross-check observes `n_obs`, expected background, nuisance constraints,
and the primary plan-46 dispatch. For a Poisson counting model, the
posterior is likelihood times prior, and the upper credible limit is the
posterior quantile over `s >= 0`. Jeffreys-on-total-mean and flat-on-
signal priors bracket common objective/sensitivity choices, while plan
46 keeps the frequentist interval as primary \cite{ParticleDataGroup:2024RPP}.

The estimator is therefore a replayable posterior integration plus a
comparison row, not a replacement convention: compute Jeffreys and flat
limits from the same input bundle, marginalise bounded nuisances, carry
unbounded caveats outside the numeric prior, and compare both priors to
the F-C or CLs primary result. Dominant uncertainty is prior choice in
sparse counts, then background-rate uncertainty, nuisance covariance,
model collapse from binned to total-count form, and unbounded plan-45
limitations.

The Wave-6 prior derivation ledger is:

| Prior/mode leaf | Truth-side quantity | Estimator rationale | Dominant uncertainty | Closure assertion |
|---|---|---|---|---|
| `bayes.jeffreys_total_mean` | 90% upper credible endpoint for nonnegative signal mean after conditioning on `n_obs` and `b` | Jeffreys prior on the Poisson total mean is invariant under reparameterisation of the count mean and stays finite for the zero-count validation row | sparse-count prior choice and background-rate uncertainty | independent quadrature/incomplete-gamma checks agree for zero and low-count fixtures |
| `bayes.flat_signal_mean` | sensitivity-bracketing 90% endpoint under a flat signal prior | flat-on-signal prior is a transparent reviewer cross-check and exposes how strongly the result depends on the prior family | prior choice dominates when `n_obs` and `b` are small | flat and Jeffreys ratios populate §7 before any defence quote |
| `bayes.nuisance_marginalised` | posterior endpoint after bounded calibration/rate nuisance integration | nuisance rows are part of the same plan-46 input bundle, so the Bayesian replay must integrate or sample them rather than dropping them | nuisance covariance and physical support truncation | output lists every nuisance id and replay seed/covariance id |
| `bayes.binned_model` | Bayesian cross-check on the same bins as a high-count CLs model | binned likelihood preserves shape information; total-count collapse is only a coarse fallback | model-collapse error relative to CLs/pyhf | collapsed rows carry `model_mismatch` unless a binned Bayesian model is attached |

These leaves are cross-check leaves: they may create caveats or
consistency evidence, but they do not supersede the plan-46 primary
F-C/CLs dispatch unless a future DEC changes the reporting convention.

#### Logic gaps

| Parameter | Status before production | Closure study / target date |
|---|---|---|
| Jeffreys prior on total mean versus flat prior on signal mean | Draft cross-check convention, not primary method | Recompute validation examples and freeze `DEC-64-PRIORS`; target 2026-06-30 |
| integration method: quadrature versus incomplete-gamma expression | `OPEN:` numerical implementation not frozen | Cross-check analytic/numerical results on zero and low-count examples; target 2026-06-30 |
| nuisance marginalisation kernels | `OPEN:` treatment depends on plan-45 nuisance type | Validate Gaussian/lognormal/beta or toy marginalisation with replay seeds; target 2026-07-05 |
| prior-sensitivity thresholds 20%/50% | `OPEN:` review defaults that affect caveat severity | Run validation panel and Methodology Council review before DEC; target 2026-07-10 |
| binned versus total-count model collapse | `OPEN:` high-count CLs comparison can be coarse | Require `model_mismatch` status unless a binned Bayesian model is used; target 2026-07-05 |

#### Closure test for the derivation

1. Build Bayesian input bundles that exactly match plan-46 dispatch rows
   for zero-survivor, low-background, nuisance, and high-count examples.
2. Compute Jeffreys and flat posterior upper limits with independent
   integration implementations or cross-checks.
3. Marginalise bounded nuisance rows and copy unbounded limitations into
   the result without converting them to numeric priors.
4. Compare Bayesian limits to the primary F-C or CLs result and assign
   pass/warn/fail/blocked prior-sensitivity status.
5. Verify plan-47/50 handoffs label Bayesian rows as cross-checks unless
   a future DEC explicitly changes the primary convention.

## 4. Nuisance marginalisation

Plan 45 nuisance rows are carried into the Bayesian calculation using
explicit nuisance ids. For v0.1:

| Nuisance type | Bayesian treatment | Guard |
|---|---|---|
| Gaussian calibration nuisance | integrate over truncated Gaussian or use toys | truncation at physical rates |
| lognormal rate nuisance | integrate over lognormal multiplier | median and sigma recorded |
| bounded efficiency nuisance | beta or truncated Gaussian constraint | support restricted to [0,1] |
| unbounded limitation caveat | not marginalised into a numeric prior | copied to `unbounded_limitations` and blocks unconditional quote |
| correlation group | sample jointly using plan-45 correlation flags | covariance id required |

A result that drops a nuisance id present in the plan-46 input bundle is
invalid. A result that numerically marginalises an unbounded limitation
instead of carrying a caveat is invalid.

## 5. Bayesian result bundle

Every Bayesian cross-check writes one JSON-like result bundle and one
prior-sensitivity table.

| Field | Required content | Review rule |
|---|---|---|
| `result_id` | plan-47 result key | matches plan-46 primary result |
| `bayes_model_id` | total-count or binned model id | replayable |
| `n_obs`, `s_expected`, `b_expected` | copied inputs | must match plan-46 input bundle |
| `confidence_level` | 0.90 primary, optional 0.95 | explicit |
| `primary_method_selected` | Feldman-Cousins or CLs/pyhf from plan 46 | Bayesian row cannot stand alone |
| `jeffreys_upper` | 90% Jeffreys-prior upper credible limit on signal mean | finite or blocked with reason |
| `flat_upper` | 90% flat-prior upper credible limit on signal mean | finite or blocked with reason |
| `nuisance_ids` | plan-45 nuisance ids included | no silent drops |
| `unbounded_limitations` | inherited caveats | non-empty blocks unconditional defence quote |
| `prior_sensitivity_status` | pass, warn, fail, or blocked | derived in §7 |
| `decision_dec_id` | `DEC-64-BAYES-CROSSCHECK` or successor | draft until approved |

## 6. Comparison with Feldman-Cousins and CLs

Plan 64 reports differences against the primary plan-46 result rather
than re-litigating the primary convention.

| Primary plan-46 method | Bayesian comparison | Required output |
|---|---|---|
| Feldman-Cousins low-count limit | compare `s90_J` and `s90_F` to F-C upper limit | ratios and absolute differences |
| CLs/pyhf high-count limit | compare total-count Bayesian result to CLs expected/observed limit | mark as coarse if binned model is collapsed |
| Asimov discovery Z | no direct Bayesian replacement | optional posterior predictive p-value row |

Comparison fields:

| Field | Meaning |
|---|---|
| `primary_upper` | upper limit from F-C or CLs when applicable |
| `jeffreys_to_primary_ratio` | `jeffreys_upper / primary_upper` |
| `flat_to_primary_ratio` | `flat_upper / primary_upper` |
| `jeffreys_minus_primary` | absolute signal-mean difference |
| `flat_minus_primary` | absolute signal-mean difference |
| `comparison_status` | `consistent`, `prior_sensitive`, `model_mismatch`, or `blocked` |

A Bayesian cross-check cannot turn a blocked plan-46 result into an
accepted result. It can only add evidence or a caveat.

## 7. Prior-sensitivity table

The prior-sensitivity table has one row per result and prior family.

| Column | Meaning |
|---|---|
| `result_id` | linked plan-47 result |
| `prior_id` | `jeffreys_poisson_mean`, `flat_signal_mean`, or approved successor |
| `upper_limit_signal_mean` | credible upper limit |
| `upper_limit_rate` | signal mean converted to rate/exposure when available |
| `ratio_to_primary` | ratio to plan-46 primary upper limit |
| `ratio_to_other_prior` | Jeffreys/flat ratio or inverse |
| `nuisance_throw_id` | null for analytic, id for toy marginalisation |
| `sensitivity_status` | `pass`, `warn`, `fail`, or `blocked` |
| `review_caveat` | required when status is warn/fail/blocked |

Initial thresholds:

| Status | Rule |
|---|---|
| `pass` | both Bayesian priors within 20% of the primary upper limit and of each other |
| `warn` | difference is 20-50%; quote prior sensitivity in plan 50 |
| `fail` | difference exceeds 50%; Methodology Council must review before thesis quote |
| `blocked` | missing nuisance ids, unbounded caveat, or non-replayable model |

Thresholds are review defaults. Any change requires a DEC update because
it changes how prior sensitivity is judged.

## 8. Governance and promotion rules

Decision-log stubs:

| DEC id | Decision to freeze | Required evidence |
|---|---|---|
| `DEC-64-BAYES-CROSSCHECK` | add Bayesian limits as required cross-checks, not primary convention | replayed result bundle for plan-46 examples |
| `DEC-64-PRIORS` | Jeffreys-on-total-mean and flat-on-signal priors | analytic/numerical validation and reviewer approval |
| `DEC-64-NUISANCE-MARGINALISATION` | nuisance integration / toy scheme | plan-45 covariance and toy reproducibility rows |
| `DEC-64-SENSITIVITY-THRESHOLDS` | 20%/50% prior-sensitivity warning thresholds | validation examples and plan-50 caveat policy |

Promotion rules:

1. Plan 46 remains authoritative for primary significance and limits.
2. Plan 64 must be run for every thesis-facing low-count limit.
3. A pass status supports the primary result; a warn/fail status creates
   a plan-50 caveat and may require method review.
4. A blocked Bayesian row blocks the claim only if plan 46 or plan 50
   explicitly requires the cross-check for that result class.

## 9. Validation examples

| Example | Inputs | Required behavior |
|---|---|---|
| zero survivor | `n_obs=0`, `b=0`, no nuisance | compute finite Jeffreys and flat upper limits; compare to F-C 2.44 primary mean |
| low background | `n_obs=1`, `b=0.2` | F-C remains primary; Bayesian rows report prior sensitivity |
| nuisance background | `n_obs=3`, `b=1.2` with rate nuisance | marginalise the rate nuisance and record throw or quadrature id |
| high-count CLs | `n_obs=18`, `b=12` with binned model | Bayesian total-count result marked coarse unless binned model is used |
| unbounded caveat | any row with plan-45 unbounded limitation | Bayesian numeric row may exist, but unconditional quote is blocked |

## 10. Acceptance checklist

| Check | Evidence artifact | Failure state |
|---|---|---|
| primary dispatch linked | plan-46 dispatch id in result bundle | Bayesian row rejected |
| both priors computed | §5 `jeffreys_upper` and `flat_upper` | incomplete cross-check |
| nuisances carried | nuisance id list matches plan-46 bundle | blocked |
| unbounded caveats copied | `unbounded_limitations` field | reviewer caveat missing |
| sensitivity table saved | §7 table | no prior-sensitivity claim |
| comparison ratios saved | §6 fields | cannot judge consistency |
| DEC stubs named | §8 table | no governance path |

## 11. A+ verifier transcript

Before this plan was committed, the local statistical-convention plans
were checked for existence and relevant sections. This plan contains no
runtime nnbar module command and no source-code line citation.

| Claim | Verifier |
|---|---|
| plan 04 F-C convention exists | `grep -n "Feldman-Cousins" docs/rebuild_plans/04_statistical_uncertainty.md` |
| plan 46 primary dispatch exists | `grep -n "method-dispatch" docs/rebuild_plans/46_significance_protocol.md` |
| plan 45 nuisance handoff exists | `grep -n "nuisance\|correlation" docs/rebuild_plans/45_systematics_taxonomy.md` |
| no stale code citation | no `*.py:<line>` citation appears in this plan |
