---
id: 60_v1_tpc_containment_fiducial
title: Fiducial volume - V.1 TPC containment derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# V.1 TPC containment fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf V.1 from
plans 24 and 25. It defines how TPC active-volume edges enter the plan
43 acceptance budget without letting truth labels enter reconstruction.

## 1. V.1 Physics derivation

- **What is physically measured:** the V.1 fiducial state measures whether a
  reconstructed TPC hit cluster and its fitted support lie far enough inside the
  active drift volume that candidate formation is not dominated by missing charge
  at a module boundary. Truth ionisation location is a validation denominator
  only.
- **Estimator rationale:** for a module-composed TPC, the sufficient Class-A
  observable is the signed minimum distance from reconstructed hit support to
  the nearest active face, compared with a geometry-versioned buffer. TPC
  tracking references and the PDG detector review motivate treating boundary
  charge loss as containment/resolution uncertainty rather than PID information
  \cite{rubbia1977liquid,alice2014performance,ParticleDataGroup:2024RPP}.
- **Statistical character:** the V.1 fiducial decision is a binary containment
  classifier. Bias appears as an efficiency cliff in edge-distance bins;
  variance is measured with Wilson intervals and is dominated by coordinate
  resolution, diffusion/gain calibration, and active-face geometry.

## 2. V.1 Logic gaps

1. **`tpc_edge_buffer_mm`:** OPEN: derive from plan-17 coordinate residuals and
   plan-25 V.1 efficiency/fake closure by scanning 0-50 mm on
   `sig_foil_500MeV_v3` and charged calibration samples; target resolution date
   2026-05-31.
2. **`min_contained_track_length_cm`:** OPEN: scan contained support length
   against V.2 direction pull width and C.2 selected-step count; target
   resolution date 2026-05-31.
3. **Active-volume convention:** OPEN: bind each TPC module face, dead margin,
   and coordinate transform to a plan-16 geometry hash before a fiducial producer
   writes thesis-facing states; target resolution date 2026-05-24.
4. **Profile semantics:** OPEN: decide whether `loose` requires one contained
   charged object or only a non-failing V.1 state when photons dominate the
   event; optimise plan-43 signal efficiency and plan-47 non-regression; target
   resolution date 2026-06-07.

## 3. V.1 Closure test for the derivation

1. Build frozen V.1/V.2 reconstruction tables for `sig_foil_500MeV_v3`,
   `cal_singlepion_50to600MeV_v2`, and `cal_singleproton_50to500MeV_v2` using
   the help-verified reconstruction-table CLI in the parent plan.
2. Compute signed minimum distance to the active TPC boundary and contained
   support length from Class-A hit coordinates plus the plan-16 geometry sidecar;
   persist the V.1 fiducial state before any validation-label join.
3. In validation-only scoring, join generated ionisation positions and compare
   V.1 efficiency, fake rate, V.2 direction pull width, and C.2 selected-sample
   count in edge-distance bins.
4. The derivation passes when the selected buffer removes unexplained edge
   cliffs, production fiducial rows are unchanged after Class-B truth columns are
   dropped, and the profile loss is propagated to plan-43 and plan-47 budgets.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes V.1 `tpc_fiducial_state`, `contained_track_length_cm`,
  edge-distance bins, geometry version, and Wilson interval settings.
- Plan 47 must downgrade charged-track acceptance rows that lack the V.1
  containment hash, selected profile, or dominant geometry/calibration nuisance
  ids.
