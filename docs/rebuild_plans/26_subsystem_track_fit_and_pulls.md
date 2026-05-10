---
id: 26_subsystem_track_fit_and_pulls
title: Subsystem — track fit, residuals, pulls (leaf V.2)
version: 0.1
status: draft
owner: Tracking POG
depends_on: [00_README, 04_statistical_uncertainty, 24_reconstruction_question_tree, 25_subsystem_tpc_hits_to_tracks, 38_truth_substitution_ladder, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/26_subsystem_track_fit_and_pulls.md, schema: this file}
acceptance:
  - {test: pull distribution mean / width within plan 40 §2 tolerance for V.2, method: closure plot, pass_when: pass}
  - {test: per-coordinate covariance reported by every fitter, method: code review, pass_when: covariance present}
  - {test: V.2 alternatives scored in the plan 38 ladder matrix, method: ladder IV(V.2) row, pass_when: visible-mass and vertex-residual deltas recorded}
risks:
  - {risk: current direction estimator has no covariance → vertex aggregation in V.4 cannot weight tracks, mitigation: §2 Kalman path provides Σ}
estimated_effort: M
last_updated: 2026-05-10
---

# Subsystem — track fit and pull distributions

*Charter.* Owns leaf V.2 (track direction estimation) plus its
covariance. The covariance feeds vertex aggregation (V.4) and
charged-PID dE/dx normalisation (C.2).

## 1. Inputs and outputs

Inputs: track-candidate hit list from V.1.
Outputs: `(direction, Σ_direction)` per candidate, plus `χ²/ndf` and
per-hit residuals for closure.

Per plan 24 V.2 schema:

| Class A inputs | Forbidden Class B |
|---|---|
| V.1 candidate table; referenced TPC columns `Event_ID`, `x`, `y`, `z`, `t`, `eDep`, `photons`, `px`, `py`, `pz`, `xHitID`, `module_ID`, `step_info`, `vol_name` | `Track_ID`, `Parent_ID`, `Name`, `origin_vol_name`, `particle_x`, `particle_y`, `particle_z` |

Output schema:

```
event_id
candidate_id
anchor_xyz
direction_xyz
direction_covariance
chi2_ndf
n_direction_hits
direction_method
residuals_xyz
pulls_theta_phi
```

## 2. Current vs alternative

- *Current.* `_track_anchor_and_direction` (plan 08 §3.2; `reconstruction.py:147-168`): direction
  is `(last_hit - first_hit) / |…|`; no covariance.
- *Kalman fit.* Seeded by V.1; produces direction + covariance +
  residuals. Standard ACTS implementation. Provides χ²/ndf.
- *Linear least-squares (PCA).* Cheaper than Kalman; gives
  covariance from the eigen-decomposition. Acceptable for straight
  tracks.


### 2.1 Alternative comparison rows

| Alternative | Source paper / codebase | NNBAR-specific adaptation | Expected ladder leaf delta |
|---|---|---|---|
| Current first-last direction | Existing `_track_anchor_and_direction` (`reconstruction.py:147-168`) | Preserve as reproducibility baseline and degraded fallback when too few hits exist for a covariance fit. | No V.2 improvement; documents current truth-free but covariance-free baseline. |
| Linear least-squares / PCA | Standard straight-line total least squares | Fit straight tracks in `(x, y, z)` because plan 17 has no B-field curvature; derive covariance from residuals. | Expected to improve plan 38 IV(V.2) pull width and enable V.4 weighted vertexing with low implementation cost. |
| Kalman fit | ACTS Kalman track-fitting codebase | Seed from V.1/PCA state and run straight-track process model until magnetic-field scenarios exist. | Best covariance model for plan 38 IV(V.2); likely similar central value to PCA in no-B-field data, but cleaner covariance propagation to V.4. |

The rebuild's recommended path: Linear LS → Kalman when momentum
measurement (curvature in B-field) becomes relevant. Currently no
B-field, so Linear LS suffices.

## 3. Closure-test specification (per plan 40 §2)

1. **Dataset id:** `cal_singlepion_50to600MeV_v2` from plan 03,
   using fiducial tracks with a V.1 candidate and validation truth
   direction available.
2. **Observable:** per-coordinate pull distributions,
   `pull_theta = (theta_fit - theta_true) / sigma_theta_fit` and
   `pull_phi = (phi_fit - phi_true) / sigma_phi_fit`.
3. **Fitter / matcher:** run the V.2 fitter under test (current,
   PCA, or Kalman); match to truth only inside a `@validation_only`
   closure function after the reconstruction output is frozen.
4. **Pass criterion:** `|mu| < 0.05` and width in `[0.9, 1.1]` for
   both pull coordinates, with covariance fields present for every
   non-degraded fitted candidate and a plan 38 IV(V.2) row recorded
   for the fitted direction choice.

## 4. Acceptance criteria

- §3 closure passes on calibration sample.
- Direction covariance is reported into output schema.

## 5. Dependencies

- **04, 25, 38, 40** — closure machinery, ladder scoring, and inputs.
- *Consumed by:* plans 27 (dE/dx normalised by track length), 30
  (vertex aggregation weighted by Σ), 38 (ladder).
