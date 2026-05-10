---
id: 60_c1_charged_candidate_fiducial
title: Fiducial volume - C.1 charged-candidate containment derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# C.1 charged-candidate containment fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf C.1 from
plans 24 and 29. It defines how TPC containment and upstream track quality
control which charged candidates can enter PID and efficiency budgets.

## 1. C.1 Physics derivation

- **What is physically measured:** the C.1 fiducial state measures whether a
  reconstructed charged-track candidate is sufficiently contained and
  observable in the TPC to be treated as an analysis object. Truth particle
  identity and ancestry are validation labels only after the C.1 row is frozen.
- **Estimator rationale:** in a no-magnetic-field TPC, the production
  charged-candidate definition must be a geometry and quality gate on Class-A
  track rows: contained hit support, V.1/V.2 quality states, nearest-edge
  distance, and explicit failure reasons. Tracking and PID performance reviews
  motivate separating containment from particle identity so edge losses do not
  become hidden pion/proton priors \cite{alice2014performance,ParticleDataGroup:2024RPP}.
- **Statistical character:** false rejection lowers charged multiplicity and
  signal acceptance; false acceptance passes edge-truncated or fake tracks into
  C.2-C.6. Dominant uncertainty comes from TPC active-volume modelling, sparse
  hit support, and upstream V.1/V.2 covariance quality.

## 2. C.1 Logic gaps

1. **Minimum candidate support:** OPEN: derive the candidate-level hit/support
   requirement from V.1 and V.2 closure scans rather than a truth-name filter;
   target resolution date 2026-05-31.
2. **Containment composition:** OPEN: decide whether C.1 passes only when both
   V.1 and V.2 fiducial states pass, or whether a V.2 warning can remain
   diagnostic under the `loose` profile; target resolution date 2026-06-07.
3. **Edge-distance aggregation:** OPEN: define the candidate edge distance as
   minimum hit distance, contained lever arm, or a covariance-weighted summary;
   optimise charged multiplicity stability and C.2 sample count; target
   resolution date 2026-05-31.
4. **Failure taxonomy:** OPEN: freeze observable-only C.1 fiducial reasons
   (`outside_tpc_active_volume`, `short_contained_track`,
   `upstream_fit_degraded`, `not_applicable`) before plan 47 consumes rows;
   target resolution date 2026-05-24.

## 3. C.1 Closure test for the derivation

1. Build frozen V.1, V.2, and C.1 tables for `sig_foil_500MeV_v3` and the
   charged calibration samples using only Class-A TPC coordinates and geometry
   sidecars.
2. Persist C.1 fiducial state, failure reason, edge-distance summary, consumed
   V.1/V.2 hashes, and selected profile before any truth-label join.
3. In validation-only scoring, compare charged-candidate efficiency, fake rate,
   charged multiplicity, C.2 selected-sample count, and S.2 pion-multiplicity
   stability in edge-distance and support-count bins.
4. The derivation passes when C.1 containment removes edge-driven fake/quality
   tails without using truth names, production rows are unchanged after Class-B
   columns are dropped, and plan 43/47 receive the selected profile loss.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes C.1 charged-candidate containment state, selected profile,
  edge-distance bins, and charged-object loss fractions.
- Plan 47 must downgrade charged-multiplicity or charged-PID rows that lack the
  C.1 fiducial hash, consumed V.1/V.2 hashes, or geometry/calibration nuisance
  handoff.
