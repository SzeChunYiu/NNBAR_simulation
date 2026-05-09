---
id: 26_subsystem_track_fit_and_pulls
title: Subsystem — track fit, residuals, pulls (leaf V.2)
version: 0.1
status: draft
owner: Tracking POG
depends_on: [00_README, 04_statistical_uncertainty, 24_reconstruction_question_tree, 25_subsystem_tpc_hits_to_tracks, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/26_subsystem_track_fit_and_pulls.md, schema: this file}
acceptance:
  - {test: pull distribution mean / width within plan 40 §2 tolerance for V.2, method: closure plot, pass_when: pass}
  - {test: per-coordinate covariance reported by every fitter, method: code review, pass_when: covariance present}
risks:
  - {risk: current direction estimator has no covariance → vertex aggregation in V.4 cannot weight tracks, mitigation: §2 Kalman path provides Σ}
estimated_effort: M
last_updated: 2026-05-09
---

# Subsystem — track fit and pull distributions

*Charter.* Owns leaf V.2 (track direction estimation) plus its
covariance. The covariance feeds vertex aggregation (V.4) and
charged-PID dE/dx normalisation (C.2).

## 1. Inputs and outputs

Inputs: track-candidate hit list from V.1.
Outputs: `(direction, Σ_direction)` per candidate, plus `χ²/ndf` and
per-hit residuals for closure.

## 2. Current vs alternative

- *Current.* `_track_anchor_and_direction` (plan 08 §3.2): direction
  is `(last_hit - first_hit) / |…|`; no covariance.
- *Kalman fit.* Seeded by V.1; produces direction + covariance +
  residuals. Standard ACTS implementation. Provides χ²/ndf.
- *Linear least-squares (PCA).* Cheaper than Kalman; gives
  covariance from the eigen-decomposition. Acceptable for straight
  tracks.

The rebuild's recommended path: Linear LS → Kalman when momentum
measurement (curvature in B-field) becomes relevant. Currently no
B-field, so Linear LS suffices.

## 3. Closure (per plan 40 §2)

Per-coordinate pull distribution on `cal_singlepion_v1`:

```
pull_θ = (θ_fit - θ_true) / σ_θ_fit
pull_φ = (φ_fit - φ_true) / σ_φ_fit
```

Acceptance: \|μ\| < 0.05; width ∈ [0.9, 1.1].

## 4. Acceptance criteria

- §3 closure passes on calibration sample.
- Direction covariance is reported into output schema.

## 5. Dependencies

- **04, 25, 40** — closure machinery and inputs.
- *Consumed by:* plans 27 (dE/dx normalised by track length), 30
  (vertex aggregation weighted by Σ), 38 (ladder).
