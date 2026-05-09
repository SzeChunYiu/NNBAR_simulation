---
id: 40_closure_and_pulls
title: Per-leaf closure tests and pull distributions
version: 0.1
status: draft
owner: Combined Performance
depends_on: [00_README, 04_statistical_uncertainty, 24_reconstruction_question_tree, 38_truth_substitution_ladder, 39_fast_mc_sanity_check]
inputs: []
outputs:
  - {path: docs/rebuild_plans/40_closure_and_pulls.md, schema: this file}
  - {path: output/closure/, schema: per-leaf closure plots}
acceptance:
  - {test: every fitted quantity reports pull mean ≈ 0, width ≈ 1, method: per-leaf closure plot, pass_when: per-leaf bands met}
  - {test: every leaf has a closure schedule (when re-run, what tolerance), method: §2 schedule, pass_when: full coverage}
risks:
  - {risk: pull width > 1 indicates underestimated uncertainties, mitigation: §3 escalation procedure}
estimated_effort: M
last_updated: 2026-05-09
---

# Per-leaf closure tests and pull distributions

*Charter.* Every fitted quantity in the rebuild reports a pull
distribution. Pull mean ≈ 0 (no bias) and width ≈ 1 (correct
uncertainty) are the universal closure criteria. Plan 40 owns the
schedule.

## 1. Pull definition (recap of plan 04 §9)

```
pull = (x_fit - x_true) / σ_fit
```

For an unbiased fitter with correct covariance, pull is `N(0, 1)`.

## 2. Per-leaf closure schedule

| Leaf | Quantity | Truth source | Tolerance (mean / width) | Frequency |
|---|---|---|---|---|
| V.4 | event vertex (x, y, z) | `Particle_output Vx,Vy,Vz` | (\|μ\| < 0.1) / ([0.9, 1.1]) | every signal-sample freeze |
| V.2 | track direction | momentum direction at production | (\|μ\| < 0.05) / ([0.9, 1.1]) | every signal-sample freeze |
| C.5 | proton/π PID | `Name` (`@validation_only`) | accuracy > 0.95 (no pull; classifier metric) | per calibration sample |
| P.3 | photon direction | gamma momentum at production | (\|μ\| < 0.05) / ([0.9, 1.2]) | per `cal_singlegamma` sample |
| P.4 | photon energy | gamma kinetic energy | (\|μ\| < 0.05) / ([0.9, 1.2]) | per `cal_singlegamma` sample |
| P.5 | π⁰ mass | known PDG π⁰ mass (134.977 MeV) | (\|μ\| < 1 MeV) / ([0.9, 1.2]) | per signal sample |
| E.7 | visible invariant mass | computed from truth four-vectors | (\|μ\| < 50 MeV) / ([0.8, 1.2]) | per signal sample |
| (others) | as listed in plan 24 | … | per leaf | per relevant sample |

## 3. Escalation when closure fails

When pull-width > tolerance:

1. *Stat-only diagnosis.* Bootstrap (plan 04 §2) the pull-width
   uncertainty. If the failure is statistical, increase sample size.
2. *Bias diagnosis.* Plot pull vs each calibration-constant
   (W-value, photon yield, lead-glass calibration). A trend exposes
   a Class C miscalibration.
3. *Systematic diagnosis.* Compare under physics-list alternatives
   (plan 12 §3). A list-dependent bias indicates a modelling effect.
4. *Code-bug diagnosis.* Check the realism audit (plan 01 §4); a
   recent Class B leak can produce odd pulls.

Each path produces an action plan recorded in plan 05 (decision log)
or plan 51 (reviewer-question registry).

## 4. Acceptance criteria

- §2 table is complete with tolerances and frequencies.
- Every closure plot is auto-produced and embedded in plan 47
  ledger.
- Plan 53 CI re-runs the closures on every PR to a closure-relevant
  module.

## 5. Risks

- *Risk:* tolerances in §2 are tighter than achievable.
  *Mitigation:* tolerances v0.1 are starting points; revised based
  on first-pass closure runs.

## 6. Dependencies

- **04** — pull definition and uncertainty propagation.
- **24, 38, 39** — leaves and validation instruments.
- *Consumed by:* plans 25–37 (each leaf's closure), plan 47.

## 7. References

- ATLAS / CMS standard pull-distribution practice.
