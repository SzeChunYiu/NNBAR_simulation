---
id: 60_v2_track_fit_containment_fiducial
title: Fiducial volume - V.2 track-fit containment derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# V.2 track-fit containment fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf V.2 from
plans 24 and 26. It defines how track-fit lever arm and edge proximity
enter the plan 43 acceptance budget.

## 1. V.2 Physics derivation

- **What is physically measured:** the V.2 fiducial state measures whether a
  fitted TPC track direction is supported by enough contained hit lever arm that
  the direction and covariance can be trusted for V.3 projection and downstream
  charged PID. Truth momentum is a validation target only.
- **Estimator rationale:** for a straight-line TPC fit, direction uncertainty is
  controlled by hit coordinate resolution, hit count, and contained lever arm.
  Edge losses shorten the lever arm and bias first/last-hit or PCA directions,
  so the fiducial observable is the contained segment length plus nearest-edge
  distance, keyed to a geometry version \cite{ParticleDataGroup:2024RPP,alice2014performance}.
- **Statistical character:** false rejection removes valid short tracks, while
  false acceptance propagates biased directions into V.3 and C.4. Dominant
  uncertainty comes from coordinate calibration, multiple scattering, and sparse
  hit support near the active-volume boundary.

## 2. V.2 Logic gaps

1. **Contained lever-arm threshold:** OPEN: scan `min_contained_track_length_cm`
   against V.2 direction pull width, V.3 projection residual, and C.4 matching
   fake rate; target resolution date 2026-05-31.
2. **Nearest-edge distance:** OPEN: derive `tpc_edge_buffer_mm` jointly with the
   V.1 containment study so V.1 and V.2 do not apply inconsistent active-volume
   definitions; target resolution date 2026-05-31.
3. **Covariance validity:** OPEN: require V.2 rows with insufficient lever arm
   or hit count to publish `covariance_valid=false` before plan 60 maps them to
   `warn` or `fail`; target resolution date 2026-05-24.
4. **Profile semantics:** OPEN: decide whether the `loose` profile treats short
   contained tracks as diagnostic-pass when another track gives a stable V.4
   vertex; target resolution date 2026-06-07.

## 3. V.2 Closure test for the derivation

1. Build frozen V.1/V.2 tables for `sig_foil_500MeV_v3` and
   `cal_singlepion_50to600MeV_v2` using only Class-A TPC coordinates and the
   help-verified reconstruction-table CLI in the parent plan.
2. Compute contained lever arm, nearest-edge distance, and covariance-validity
   state from reconstructed hits plus the plan-16 geometry sidecar; persist V.2
   fiducial rows before any truth-momentum join.
3. In validation-only scoring, compare direction pull width, V.3 projection
   residual, and C.4 matching fake rate in bins of lever arm and edge distance.
4. The derivation passes when the selected V.2 fiducial state removes edge-driven
   pull tails without changing production rows after Class-B truth columns are
   dropped, and the profile loss is exported to plan 43 and plan 47.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes V.2 contained lever-arm bins, covariance-validity state,
  geometry version, and selected fiducial profile.
- Plan 47 must downgrade vertex-projection or charged-PID rows that lack the V.2
  containment hash or dominant geometry/calibration nuisance ids.
