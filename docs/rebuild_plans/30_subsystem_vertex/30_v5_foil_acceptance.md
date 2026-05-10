---
id: 30_v5_foil_acceptance
title: Subsystem event vertex - V.5 foil-acceptance derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 30_subsystem_vertex
last_updated: 2026-05-10
---

# V.5 foil-acceptance derivation

This split file holds the Wave 6 V.5 scientific derivation for plan 30.
It is separate from `30_subsystem_vertex.md` only to keep the parent plan
under the 500-line cap; the parent remains the integration surface for V.3-V.5.

## 1. V.5 physics derivation

- **What is physically measured:** V.5 measures whether a reconstructed V.4
  event vertex is geometrically compatible with the physical foil volume. Truth
  primary/interactions vertices are validation targets only after the V.5 row is
  frozen.
- **Estimator rationale:** for a known foil radius, thickness, and alignment
  tag, the maximum-information production decision is a geometry gate on
  reconstructed radius and z. The live hook `apply_foil_acceptance`
  (`nnbar_reconstruction/vertex_reco.py:157-194`) implements this truth-blind
  gate from `FoilGeometry` (`nnbar_reconstruction/vertex_reco.py:13-18`), while
  `_acceptance_reason` (`nnbar_reconstruction/vertex_reco.py:197-204`) records
  the observable reason. HIBEAM/NNBAR design references define the target
  context, and plan 60 supplies the edge-efficiency surface
  \cite{HIBEAM_NNBAR_at_ESS,Santoro2024NNBARCDR,ParticleDataGroup:2024RPP}.
- **Statistical character:** V.5 is a binary geometry classifier. False
  rejection is dominated by V.4 resolution and edge buffers; false acceptance is
  dominated by off-foil backgrounds, alignment uncertainty, and tails of the V.4
  covariance model.

## 2. V.5 logic gaps

1. **Foil geometry constants:** OPEN: bind `outer_radius_mm` and
   `half_thickness_mm` to a plan-16 geometry version and side-car hash; target
   resolution date 2026-05-24.
2. **Edge / fiducial margin:** OPEN: derive a radius and z margin from plan-60
   efficiency-vs-edge scans before any hard selection consumes V.5; target
   resolution date 2026-05-31.
3. **Covariance-aware gate:** OPEN: compare hard inside/outside cuts with a
   probability-of-inside-foil gate using V.4 covariance; optimise signal
   efficiency, fake acceptance, and plan-43 uncertainty; target resolution date
   2026-06-07.
4. **Reason taxonomy:** OPEN: freeze `inside_foil`, `invalid_vertex`,
   `outside_foil_radius`, and `outside_foil_thickness` in the V.5 fixture schema;
   target resolution date 2026-05-24.
5. **Acceptance-surface binning:** OPEN: align V.5 radius/z bins with plan 60
   and plan 43 before publishing efficiency tables; target resolution date
   2026-05-31.

## 3. V.5 closure test for the derivation

1. Run `apply_foil_acceptance` on frozen V.4 vertex rows and a plan-16/60
   `FoilGeometry` payload for `sig_foil_v3`, with truth vertices and truth
   origin labels absent from the production input.
2. Persist `foil_compatible`, `vertex_r_mm`, `vertex_z_mm`,
   `foil_geometry_version`, `acceptance_reason`, and consumed V.4/geometry hashes
   before any validation-label join.
3. In a `validation_only` scorer, compare V.5 efficiency and off-foil fake
   acceptance in bins of radius, z, V.4 covariance, aggregation method, and
   plan-60 edge state.
4. The derivation passes when V.5 rows are unchanged by dropping every Class-B
   truth column and the resulting efficiency surface can be consumed directly by
   plan 43 signal-efficiency accounting.

## 4. A+ verification anchors

- `apply_foil_acceptance` is the live V.5 hook
  (`nnbar_reconstruction/vertex_reco.py:157-194`).
- `FoilGeometry` supplies the geometry constants
  (`nnbar_reconstruction/vertex_reco.py:13-18`).
- `_acceptance_reason` is the live reason helper
  (`nnbar_reconstruction/vertex_reco.py:197-204`).
