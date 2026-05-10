---
id: 60_v3_projection_fiducial
title: Fiducial volume - V.3 foil-projection derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# V.3 foil-projection fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf V.3 from
plans 24 and 30. It defines when a reconstructed track-to-foil projection
is usable for edge-aware vertex and signal-efficiency accounting.

## 1. V.3 Physics derivation

- **What is physically measured:** the V.3 fiducial state measures whether a
  reconstructed track projection to the foil plane is geometrically stable and
  lands in a region where the downstream V.4/V.5 vertex chain can make a
  meaningful edge decision. Truth vertices are validation targets only after
  the V.3 production row is frozen.
- **Estimator rationale:** linear propagation from a fitted TPC direction to a
  known foil plane is the minimal Class-A estimator in the no-magnetic-field
  reconstruction. Its fiducial quality is controlled by projection length,
  direction-z degeneracy, propagated covariance, and signed distance to the
  foil radial boundary. Standard track-parameter uncertainty propagation and
  detector-edge treatments motivate recording the projection state separately
  from the final foil gate \cite{ParticleDataGroup:2024RPP,Fruehwirth:2007AdaptiveVertex,HIBEAM_NNBAR_at_ESS}.
- **Statistical character:** false acceptance propagates unstable or nearly
  parallel tracks into biased V.4 vertices; false rejection removes valid
  charged topology near the foil edge. Dominant uncertainty comes from V.2
  direction covariance, foil alignment, and finite TPC lever arm.

## 2. V.3 Logic gaps

1. **Parallel-track threshold:** OPEN: scan the minimum accepted absolute
   direction-z value jointly with V.3 residual bias and V.4 pull width on
   `sig_foil_500MeV_v3`; target resolution date 2026-05-31.
2. **Maximum projection length:** OPEN: set a geometry-aware extrapolation
   length cap so distant TPC fragments cannot dominate the foil edge budget;
   optimise V.3 residual tails and charged-candidate retention; target
   resolution date 2026-05-31.
3. **Projection covariance to edge state:** OPEN: propagate V.2 covariance to
   radial/z projection uncertainty and choose whether plan 60 uses `2 sigma`,
   a static buffer, or a probability-of-inside profile; target resolution date
   2026-06-07.
4. **Projection-envelope semantics:** OPEN: decide whether out-of-radius
   projections fail at V.3 or remain diagnostic until V.5; require plan-43
   signal-efficiency non-regression before changing the default; target
   resolution date 2026-06-07.

## 3. V.3 Closure test for the derivation

1. Build frozen V.2 and V.3 projection tables for `sig_foil_500MeV_v3` and the
   charged calibration samples using Class-A track-fit rows and the plan-16
   foil geometry sidecar.
2. Compute projection length, direction-z state, signed radial edge distance,
   and propagated projection uncertainty; persist those fiducial fields before
   any validation-label join.
3. In validation-only scoring, compare projection residuals and V.4 vertex
   pull width in bins of projection length, edge distance, and covariance.
4. The derivation passes when selected V.3 fiducial states suppress
   edge-driven residual tails, production rows are unchanged after Class-B truth
   columns are dropped, and plan 43/47 receive the selected profile loss and
   dominant geometry nuisance ids.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes V.3 projection-length bins, edge-distance bins, projection
  covariance state, selected profile, and geometry version.
- Plan 47 must downgrade vertex and signal-efficiency rows that lack the V.3
  projection-fiducial hash or omit the N8 geometry/alignment nuisance handoff.
