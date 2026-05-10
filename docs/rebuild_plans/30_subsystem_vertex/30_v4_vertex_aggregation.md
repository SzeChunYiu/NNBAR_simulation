---
id: 30_v4_vertex_aggregation
title: Subsystem event vertex - V.4 aggregation derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 30_subsystem_vertex
last_updated: 2026-05-10
---

# V.4 vertex aggregation derivation

This split file holds the Wave 6 V.4 scientific derivation for plan 30.
It is separate from `30_subsystem_vertex.md` only to keep the parent plan
under the 500-line cap; the parent still owns V.3-V.5 fixture integration.

## 1. V.4 physics derivation

- **What is physically measured:** V.4 measures the event-level reconstructed
  annihilation vertex coordinate by combining valid V.3 foil-plane projection
  points from the same event. The target for closure is the generated
  interaction/primary vertex, but production aggregation must not read truth
  vertices or truth track labels.
- **Estimator rationale:** for independent projection measurements with known
  covariance, the maximum-likelihood estimator is the inverse-covariance
  weighted mean. The live equal-weight mean in `aggregate_event_vertices`
  (`nnbar_reconstruction/vertex_reco.py:90-132`) is the equal-covariance
  baseline; adaptive vertex fitting is the planned robust extension for
  non-primary or conversion outliers
  \cite{ParticleDataGroup:2024RPP,Fruehwirth:2007AdaptiveVertex}.
- **Statistical character:** V.4 variance is controlled by the V.3 projection
  covariance and number of valid projections. Bias is driven by residual foil
  alignment, direction-z degeneracy, merged V.1 candidates, and outlier tracks.
  The sidecar covariance from `_vertex_covariance`
  (`nnbar_reconstruction/vertex_reco.py:150-154`) is currently empirical and
  must be replaced or calibrated before precision pull claims.

## 2. V.4 logic gaps

1. **Projection multiplicity:** OPEN: compare `n_tracks_used >= 1` reproduction
   mode against a physics-motivated `n_tracks_used >= 2` gate and N>=3 robust
   fits on `sig_foil_v3`; optimise residual width, outlier tails, and V.5
   acceptance stability; target resolution date 2026-05-24.
2. **Equal versus covariance weights:** OPEN: promote inverse-covariance weights
   only after V.2/V.3 covariance closure; figure of merit is pull width in
   track-multiplicity bins; target resolution date 2026-05-31.
3. **Adaptive-fit scale / outlier cutoff:** OPEN: scan robust weight scales in
   plan 38 V.4 ladder rows and require no degradation to plan 47 reproduction;
   target resolution date 2026-06-07.
4. **Radial RMS warning threshold:** OPEN: derive a `radial_rms_mm` warning band
   from validation residual tails and plan-60 edge bins before S.1 or V.5 uses
   it as a hard gate; target resolution date 2026-05-31.
5. **Covariance floor:** OPEN: set the minimum vertex covariance from V.3 closure
   residuals so single-track or nearly collinear events cannot report zero
   uncertainty; target resolution date 2026-05-31.

## 3. V.4 closure test for the derivation

1. Run `aggregate_event_vertices` on frozen V.3 projection rows for
   `sig_foil_v3`, with truth vertices, `Track_ID`, particle names, and truth
   origins absent from the production input.
2. Persist `event_id`, `vertex_xyz`, `vertex_covariance`, `n_tracks_used`,
   `n_tracks_skipped`, `radial_rms_mm`, `aggregation_method`, and consumed V.3
   fixture hashes before any validation-label join.
3. In a `validation_only` scorer, compare vertex residuals and pulls against
   generated vertices in bins of projection multiplicity, V.3 covariance, radial
   RMS, aggregation method, and plan-60 fiducial state.
4. The derivation passes when residual means are consistent with zero, pull
   widths satisfy the plan-40 V.4 band, and the production V.4 table is
   unchanged when every Class-B truth column is removed.

## 4. A+ verification anchors

- `aggregate_event_vertices` is the live V.4 hook
  (`nnbar_reconstruction/vertex_reco.py:90-132`).
- `_vertex_covariance` is the live covariance sidecar
  (`nnbar_reconstruction/vertex_reco.py:150-154`).
- `reconstruct_event_vertices` remains the legacy reproduction hook
  (`nnbar_reconstruction/vertex.py:163-254`) for plan-47 comparisons.
