---
id: 60_v5_foil_acceptance_fiducial
title: Fiducial volume - V.5 foil-acceptance edge derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# V.5 foil-acceptance fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf V.5 from
plans 24 and 30. It defines the acceptance surface that plan 43 consumes
once L3 writes detector-wide fiducial tables.

## 1. V.5 Physics derivation

- **What is physically measured:** the V.5 fiducial observable is the signed
  distance of a reconstructed V.4 vertex to the foil radial and z boundaries,
  plus the binary statement that the vertex is compatible with the active foil
  volume. Truth interaction coordinates are validation denominators only.
- **Estimator rationale:** for a known foil geometry, the sufficient
  reconstructed quantities are `vertex_r_mm`, `vertex_z_mm`, their covariance,
  and the geometry version. The live V.5 gate `apply_foil_acceptance`
  (`nnbar_reconstruction/vertex_reco.py:157-194`) implements the unbuffered
  geometry decision from `FoilGeometry` (`nnbar_reconstruction/vertex_reco.py:13-18`);
  plan 60 extends it with edge-distance and profile-dependent buffers for plan
  43 efficiency accounting \cite{HIBEAM_NNBAR_at_ESS,Santoro2024NNBARCDR,ParticleDataGroup:2024RPP}.
- **Statistical character:** edge efficiency is a binomial acceptance surface
  with correlated uncertainty from V.4 resolution, foil alignment, and geometry
  version. False rejection appears as lost signal in near-edge bins; false
  acceptance appears as off-foil background leakage into V.5 and S.1.

## 2. V.5 Logic gaps

1. **Radial/z binning:** OPEN: fix radial bins in 25 mm steps to the foil edge
   and z bins in 1 mm steps across the half-thickness, then verify no bin has
   unresolved low-statistics Wilson intervals; target resolution date
   2026-05-31.
2. **Static edge buffer:** OPEN: derive `foil_radial_buffer_mm` and
   `foil_z_buffer_mm` from plan-16 geometry uncertainty plus V.4 closure tails;
   target resolution date 2026-05-31.
3. **Covariance-aware buffer:** OPEN: compare `max(static, 2 sigma)` against a
   probability-of-inside-foil profile on `sig_foil_500MeV_v3`; optimise signal
   efficiency and off-foil fake acceptance; target resolution date 2026-06-07.
4. **Profile semantics:** OPEN: freeze whether `loose` requires only V.5 pass or
   also buffered `foil_radial_state`/`foil_z_state` pass before plan 43 consumes
   it; target resolution date 2026-05-24.
5. **Reason mapping:** OPEN: map `_acceptance_reason`
   (`nnbar_reconstruction/vertex_reco.py:197-204`) to plan-60 `fiducial_reason`
   values without hiding invalid vertices; target resolution date 2026-05-24.

## 3. V.5 Closure test for the derivation

1. Run `apply_foil_acceptance` on frozen V.4 vertex tables and the plan-16
   geometry payload, then build plan-60 event fiducial rows for profiles `none`,
   `loose`, and `tight`.
2. Persist the V.5 gate, edge distances, buffers, profile, geometry version, and
   consumed V.4/geometry hashes before any truth-coordinate join.
3. In validation-only scoring, compute efficiency versus radius and z for
   `sig_foil_500MeV_v3`, including Wilson intervals and `tight-loose` shifts.
4. The derivation passes when V.5/profile rows are invariant to dropping truth
   vertices and plan 43 can consume the resulting efficiency-vs-edge tables with
   explicit N8/N10 nuisance handoff.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes `efficiency_vs_radius`, `efficiency_vs_z`,
  `fiducial_profile`, `geometry_version`, and the V.5 fixture hash.
- Plan 47 must downgrade any vertex or signal-efficiency row that lacks the V.5
  edge-surface hash, selected profile, Wilson interval settings, or dominant
  geometry nuisance ids.
