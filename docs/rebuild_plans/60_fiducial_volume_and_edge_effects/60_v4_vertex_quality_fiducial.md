---
id: 60_v4_vertex_quality_fiducial
title: Fiducial volume - V.4 vertex-quality edge derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# V.4 vertex-quality fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf V.4 from
plans 24 and 30. It defines when an aggregated reconstructed vertex is
stable enough to feed foil-edge and signal-efficiency budgets.

## 1. V.4 Physics derivation

- **What is physically measured:** the V.4 fiducial state measures whether the
  event-level reconstructed vertex is supported by enough consistent V.3
  projections that its radius, z, covariance, and residual spread are usable for
  edge accounting. Truth interaction coordinates are validation references only.
- **Estimator rationale:** an event vertex formed from multiple projected track
  measurements should carry a support count, covariance, and outlier/spread
  diagnostic before any binary foil decision is applied. Weighted-mean and
  adaptive vertex-estimator theory motivates treating poor projection agreement
  as a vertex-quality state rather than folding it silently into V.5
  \cite{Fruehwirth:2007AdaptiveVertex,ParticleDataGroup:2024RPP}.
- **Statistical character:** false acceptance lets poorly constrained vertices
  produce sharp but artificial edge losses; false rejection removes valid
  low-multiplicity signal topologies. Dominant uncertainty comes from V.3
  covariance, track multiplicity, outlier projections, and foil-alignment
  uncertainty.

## 2. V.4 Logic gaps

1. **Minimum projection support:** OPEN: compare one-track reproduction mode
   with two-track and three-track quality profiles on `sig_foil_500MeV_v3`;
   optimise V.4 residual width, V.5 efficiency, and plan-47 non-regression;
   target resolution date 2026-05-31.
2. **Radial-RMS warning threshold:** OPEN: derive a `radial_rms_mm` warning band
   from validation residual tails and plan-60 edge bins; target resolution date
   2026-05-31.
3. **Vertex covariance floor:** OPEN: set a minimum covariance from V.3 closure
   residuals so single-track or nearly collinear events cannot report zero edge
   uncertainty; target resolution date 2026-05-31.
4. **Aggregation-method profile:** OPEN: decide whether covariance-weighted or
   adaptive fits require separate fiducial profiles and plan-05 decisions before
   replacing the equal-weight reproduction baseline; target resolution date
   2026-06-07.

## 3. V.4 Closure test for the derivation

1. Build frozen V.3 projection and V.4 vertex tables for `sig_foil_500MeV_v3`
   using Class-A projection rows and the plan-16/60 geometry sidecar.
2. Persist support count, skipped count, covariance state, radial spread,
   aggregation method, edge-distance bins, and selected profile before any
   validation-coordinate join.
3. In validation-only scoring, compare vertex residuals, pull widths, V.5 pass
   fractions, and plan-43 signal efficiency in bins of projection multiplicity,
   covariance state, and radial spread.
4. The derivation passes when the selected V.4 quality state removes
   edge-driven residual tails, production rows are unchanged after truth columns
   are dropped, and plan 43/47 receive the selected profile loss plus N8
   geometry nuisance handoff.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes V.4 support-count bins, radial-spread bins, covariance state,
  selected fiducial profile, and geometry version.
- Plan 47 must downgrade vertex-resolution, foil-acceptance, or
  signal-efficiency rows that lack the V.4 quality-fiducial hash or omit the
  selected aggregation method.
