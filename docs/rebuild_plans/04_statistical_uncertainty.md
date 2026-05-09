---
id: 04_statistical_uncertainty
title: Statistical uncertainty conventions
version: 0.1
status: draft
owner: Methodology Council
depends_on: [00_README, 03_dataset_registry]
inputs:
  - {path: any sample registered in plan 03, schema: dataset registry}
outputs:
  - {path: nnbar_reconstruction/statistics/, schema: shared uncertainty utilities}
  - {path: docs/rebuild_plans/04_statistical_uncertainty.md, schema: this file}
acceptance:
  - {test: every numeric claim in any plan or ledger cites a §-reference from this plan, method: cross-reference scan, pass_when: zero uncited numeric claims}
  - {test: zero-survivor cosmic upper limits use Feldman-Cousins, method: code path inspection, pass_when: no use of "0/N = 0" in cosmic significance}
  - {test: bootstrap implementations are deterministic given a seed, method: round-trip test, pass_when: identical resamples for identical seeds}
risks:
  - {risk: ad-hoc uncertainty quoting drifts from convention, mitigation: every uncertainty must come from a function in nnbar_reconstruction/statistics/}
  - {risk: correlation between systematics is ignored, mitigation: plan 45 systematics taxonomy maintains the correlation matrix}
estimated_effort: M
last_updated: 2026-05-09
---

# Statistical uncertainty conventions

*Charter.* This plan locks the conventions used by every numeric claim
in the rebuild. It names the estimator, the resampling protocol, the
seed binding, the propagation rules, and the upper-limit handling.
Every ledger row, every plot label, every reviewer-defence bracket
cites a section here. Without a single source of truth, "± 0.03" means
different things in different places and reviewers quickly stop trusting
the numbers.

## 1. Scope

Covered:
- Statistical uncertainties from finite Monte Carlo statistics.
- Calibration-uncertainty propagation through reconstruction.
- Selection-efficiency confidence intervals.
- Upper limits when the survivor count is zero.
- Significance estimation for signal-vs-background.

Not covered:
- Theoretical/model uncertainties. Those are handled in plan 13
  (signal model) and plan 14 (background models) as systematic
  variations using the *same* statistical machinery defined here.
- Detector-systematic uncertainties from limitations L1–L12 (plan 01).
  Those become alternative configurations whose differences are quoted
  using the conventions here.

## 2. Bootstrap convention

For finite-sample uncertainty on any scalar function `f` of a sample
(efficiency, mean, RMS, peak position, peak width, ROC AUC, …):

- Resample at the *event* level with replacement, preserving the run
  partitioning of plan 03 (do not mix events across run boundaries
  unless the run-mixing is itself part of `f`).
- `n_boot = 200` for plan-internal numbers; `n_boot = 1000` for
  thesis-quoted numbers.
- Seed is derived from the dataset ID hash and the plan ID hash:
  `seed = sha256(dataset_id || plan_id || "bootstrap")[:8]` interpreted
  as an unsigned 32-bit integer. This makes bootstraps deterministic
  and *different* between plans even on the same sample.
- Reported summary: mean of bootstraps as the central value (or the
  estimator on the original sample as the central value, with the
  bootstrap distribution providing only the uncertainty — both are
  acceptable, must be stated). Uncertainty is the central 68%
  inter-quantile range, *not* the standard deviation, unless the
  bootstrap distribution is verified Gaussian.

The shared implementation lives in `nnbar_reconstruction.statistics.bootstrap`.
Numbers reported via any other path are flagged as ad-hoc by the audit
(plan 53).

## 3. Jackknife convention

For uncertainties on selection efficiency where bootstrap is unstable
(small denominators, rare survivors):

- Block jackknife with block size = max(1, ⌈N_events / 50⌉).
- 50 jackknife blocks by default.
- Reported uncertainty:
  `σ²_ε = ((n_blocks - 1) / n_blocks) · Σ (ε_i - ε̄)²`
  where `ε_i` is the efficiency excluding block `i`.
- Seed binding identical to §2.

Implementation: `nnbar_reconstruction.statistics.jackknife_efficiency`.

## 4. Wilson interval for binomial efficiencies

When the bootstrap or jackknife is overkill (a single binomial
efficiency `k/N` with no resampling needed):

- Use the Wilson score interval at 68.27% (1σ-equivalent) and at 95%
  (2σ-equivalent).
- Quote both lower and upper bounds, not a symmetric ± figure, when
  asymmetry is non-trivial (typically when `k < 5` or `k > N-5`).
- Implementation: `nnbar_reconstruction.statistics.wilson_interval`.

## 5. Feldman-Cousins for upper limits with zero survivors

The licentiate abstract reports "no surviving cosmic-ray background
events" — a zero-survivor result on a finite sample. The PhD thesis
must report this as an upper limit, not as a point estimate of zero.

Convention:

- Use the Feldman-Cousins unified construction at 90% C.L. for the
  upper limit on the survival rate.
- Inputs: observed count `n_obs = 0`, expected background `μ_b = 0`
  (no other background source for the cosmic veto check), live-time
  weight from plan 21 sample-size derivation.
- For zero counts and zero expected background, the F-C 90% upper
  limit on signal mean is `μ_s ≤ 2.44`; survival rate is then
  `ε_upper = 2.44 / N_generated`.
- Quote the limit as `ε ≤ X · 10^-Y at 90% C.L. (Feldman-Cousins)`.
- Implementation: `nnbar_reconstruction.statistics.feldman_cousins_upper`.

For nonzero observed counts and nonzero expected background, plan 46
significance protocol takes over with the more general F-C construction.

## 6. Calibration-uncertainty propagation

A Class C calibration constant (plan 01 §2) carries a systematic
uncertainty. It propagates to any observable derived from it via:

- *Linear propagation* if the observable is a smooth function of the
  constant and the relative uncertainty is small (`< 10%`). The shared
  utility `propagate_calibration_linear` differentiates symbolically
  using `sympy` against the registered calibration value or
  numerically via `±1σ` evaluations.
- *Toy MC* if the observable is non-smooth (selection efficiencies
  with cuts on calibration-dependent quantities). Run the
  reconstruction `n_toys = 50` times with calibration values drawn
  from a Gaussian centred on the nominal with σ from §3 of plan 18.
  The systematic is the standard deviation of the resulting
  observable.

Calibration uncertainties combine with statistical uncertainties in
quadrature unless they are correlated; correlation is recorded in
plan 45 systematics taxonomy.

## 7. Significance and limits for analysis-level results

Plan 46 owns the significance protocol; this plan provides the
underlying statistical machinery only.

Definitions used downstream:

- Asymptotic discovery significance (`Z_0`): `Z_0 = sqrt(2 · (s+b) ·
  ln(1 + s/b) - 2s)` for `s > 0, b > 0`, falling back to F-C in the
  small-count regime.
- Expected limit at 90% C.L. via the F-C construction averaging over
  Asimov pseudo-experiments.
- Observed limit reported with the convention chosen at thesis-freeze
  in plan 46.

## 8. Reporting rules

Every quoted number ships with:

- *Central value.*
- *Statistical uncertainty* via §2, §3, or §4 as appropriate.
- *Systematic uncertainty* — sum of:
  - calibration uncertainties (§6),
  - signal-model alternatives (plan 13),
  - background-model alternatives (plan 14),
  - detector-realism limitation effects (plan 01 §6),
  combined per plan 45.
- *Convention citation* — `[stat: bootstrap n=1000, sys: §6]` or
  similar inline note.
- *Sample citation* — dataset ID from plan 03.

A claim that omits any of these in a thesis-quoted context fails plan
50 reviewer-defence-package sign-off.

## 9. Pull and bias diagnostics

Every fit (vertex fit, kinematic fit, calibration fit) reports:

- Pull mean: `mean((x_fit - x_true) / σ_fit)` — should be 0 within
  uncertainties.
- Pull width: `RMS((x_fit - x_true) / σ_fit)` — should be 1.
- Bias: `mean(x_fit - x_true)` — should be consistent with 0 within
  the systematic budget.

Plan 40 closure-and-pulls owns the closure-test schedule; this plan
defines the metric only.

## 10. Acceptance criteria

- Implementations of bootstrap, jackknife, Wilson, F-C, and
  calibration propagation live under
  `nnbar_reconstruction/statistics/` with deterministic-seed contracts.
- Every numeric claim in plans 47 (ledger), 50 (defence package), and
  any subsystem plan cites a §-reference here.
- A test suite validates: bootstrap reproduces published Gaussian
  examples, F-C reproduces the 2.44 reference value, Wilson reproduces
  Wikipedia worked examples.
- Plan 53 CI runs the convention-citation scan on every PR.

## 11. Risks and mitigations

- *Risk:* ad-hoc `np.std(...) / np.sqrt(n)` appears in subsystem code
  for "quick" uncertainties.
  *Mitigation:* the realism audit (plan 01) is extended to flag any
  uncertainty calculation outside `nnbar_reconstruction.statistics.*`.
- *Risk:* correlation between calibration systematics is ignored,
  giving anti-conservative combined uncertainties.
  *Mitigation:* plan 45 maintains the correlation matrix; plan 50
  requires every defence package to use it.
- *Risk:* `n_boot` insufficient for the precision needed.
  *Mitigation:* plan 50 reports the bootstrap MC noise on the
  uncertainty itself; if it dominates the quoted significant figure,
  `n_boot` is increased and the change is logged.

## 12. Dependencies

- **00_README** — plan ID space.
- **03_dataset_registry** — dataset IDs are an input to seed derivation.
- *Consumed by:* every numeric claim in every plan downstream;
  highest-traffic consumers are 47, 50, all subsystem plans 25–37,
  and all analysis-level plans 41–46.

## 13. Out of scope

- Theory uncertainties on signal cross-section (plan 13).
- Detector-physics modelling alternatives beyond what plan 01 limitations
  capture; those flow through this plan as systematic variations.

## 14. Open questions

- Should we adopt CMS-style impact plots or ATLAS-style nuisance-pull
  plots for systematic visualisation? *Default: ATLAS-style for
  consistency with the licenciate's plot style. Revisit if the analysis
  grows enough nuisance parameters to warrant impact plots.*
- Use `pyhf` for the limit calculation, or roll our own F-C? *Default:
  `pyhf` for limits; F-C for the cosmic-zero special case where pyhf
  is overkill.*

## 15. References

- Feldman & Cousins, *Phys. Rev. D 57, 3873 (1998)*.
- ATLAS Statistics Forum recommendations for asymptotic significance.
- pyhf documentation for the asymptotic-formula path.
- Wilson, *J. Am. Stat. Assoc.* 22 (1927) 209.
