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

### 1.1 Leaf schema block

Leaf V.2 — track fit, residuals, and pulls

- **inputs (Class A):** V.1 candidate hit indices plus TPC
  `Event_ID`, `x`, `y`, `z`, `t`, `eDep`, `photons`, `px`, `py`,
  `pz`, `xHitID`, `module_ID`, `step_info`, `vol_name`.
- **forbidden (Class B):** `Track_ID`, `Parent_ID`, `Name`,
  `origin_vol_name`, `particle_x`, `particle_y`, `particle_z`.
- **decision rule:** estimate the track direction and covariance from
  Class A hit coordinates only; truth direction may be used only after
  reconstruction output is frozen for pull scoring.
- **output schema:** `event_id: int`, `candidate_id: int`,
  `anchor_xyz: float[3]`, `direction_xyz: float[3]`,
  `direction_covariance: float[3,3]`, `chi2_ndf: float`,
  `n_direction_hits: int`, `direction_method: str`,
  `residuals_xyz: list[float[3]]`, `pulls_theta_phi: float[2]`.
- **allowed truth use:** `validation_only` for closure pulls and plan
  38 ladder rows; forbidden in the V.2 production fitter.
- **downstream consumers:** plans 27, 30, 38, 40, and any V.4 vertex
  aggregation that weights tracks by direction covariance.

### 1.2 Column contract

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

- *Current.* `_track_anchor_and_direction` (plan 08 §3.2; `charged.py:61-82`): direction
  is `(last_hit - first_hit) / |…|`; no covariance.
- *Kalman fit.* Seeded by V.1; produces direction + covariance +
  residuals. Standard ACTS implementation. Provides χ²/ndf.
- *Linear least-squares (PCA).* Cheaper than Kalman; gives
  covariance from the eigen-decomposition. Acceptable for straight
  tracks.


### 2.1 Alternative comparison rows

| Alternative | Source paper / codebase | NNBAR-specific adaptation | Expected ladder leaf delta |
|---|---|---|---|
| Current first-last direction | Existing `_track_anchor_and_direction` (`charged.py:61-82`) | Preserve as reproducibility baseline and degraded fallback when too few hits exist for a covariance fit. | No V.2 improvement; documents current truth-free but covariance-free baseline. |
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

## 4. Covariance and quality handoff

The V.2 output must make degraded fits explicit so downstream plans can
choose whether to consume a direction. The production table adds these
quality fields beside the physics fields in §1:

| Field | Meaning | Consumer |
|---|---|---|
| `fit_quality_state` | `pass`, `warn`, `fail`, or `not_applicable` for the candidate | plans 30, 66 |
| `fit_failure_reason` | first blocking reason, if any | plan 47 caveats |
| `covariance_valid` | covariance matrix finite, symmetric, and positive semidefinite | plans 30, 40 |
| `fit_degraded` | true when first-last direction is used because the fitter lacks enough hits | plan 38 ladder rows |
| `n_residual_degrees_of_freedom` | residual degrees of freedom used for χ²/ndf | plan 40 pulls |

Quality semantics:

- `pass` means the direction is finite, covariance is valid, and the
  residual degrees of freedom are sufficient for the configured fitter.
- `warn` means the direction is finite but covariance is missing,
  degraded, or close to singular; plan 30 may consume it with reduced
  weight.
- `fail` means the direction is non-finite or based on fewer than two
  usable Class A coordinates.
- `not_applicable` is reserved for candidates rejected by V.1 before a
  V.2 fit is attempted.

The DQM hook in plan 66 aggregates the fraction of `warn` and `fail`
rows per run. A sudden increase is a run-quality problem, not a reason
to silently retune vertex or PID thresholds.

## 5. Stage E.1 implementation handoff

For L3's reconstruction redesign, V.2 should become a standalone module
with a stable input/output seam:

1. Accept V.1 candidate hit indices and fetch only Class A TPC columns.
2. Run the configured fitter in priority order: PCA/linear LS first,
   then Kalman once the covariance model is source-backed.
3. Emit the §1 direction and covariance schema plus the §4 quality
   fields in one row per V.1 candidate.
4. Retain `_track_anchor_and_direction` only as a named degraded
   baseline, never as an unlabeled production-equivalent result.
5. Freeze the V.2 table before any truth direction, pull, or ladder
   scorer reads it.

## 6. Acceptance criteria

- §3 closure passes on calibration sample.
- Direction covariance is reported into output schema.

## 7. Dependencies

- **04, 25, 38, 40** — closure machinery, ladder scoring, and inputs.
- *Consumed by:* plans 27 (dE/dx normalised by track length), 30
  (vertex aggregation weighted by Σ), 38 (ladder).
