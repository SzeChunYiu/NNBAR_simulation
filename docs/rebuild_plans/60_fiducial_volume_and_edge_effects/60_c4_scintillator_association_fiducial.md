---
id: 60_c4_scintillator_association_fiducial
title: Fiducial volume - C.4 scintillator-association coverage derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# C.4 scintillator-association fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf C.4 from
plans 24 and 28. It defines when charged-track to scintillator-hit matching is
inside the instrumented and time-compatible acceptance.

## 1. C.4 Physics derivation

- **What is physically measured:** the C.4 fiducial state measures whether a
  reconstructed charged track has an observable scintillator-hit association in
  an instrumented region with meaningful geometric and timing compatibility.
  Truth track ids are validation-only and must not drive production matching.
- **Estimator rationale:** hit association is a geometric-and-timing matching
  problem under finite segmentation. The fiducial observables are projected
  module coverage, distance to scintillator edges or cracks, timing residual
  state, and association ambiguity count. Detector-acceptance and
  passage-of-particles references motivate exposing missing coverage separately
  from a true physical non-stop \cite{ParticleDataGroup:2024RPP,HIBEAM_NNBAR_at_ESS}.
- **Statistical character:** false rejection removes valid range evidence;
  false acceptance attaches accidental or edge-leaked hits that bias C.3 and
  C.5. Dominant uncertainty comes from scintillator segmentation, timing
  calibration, projected-track covariance, and local inactive regions.

## 2. C.4 Logic gaps

1. **Association coverage buffer:** OPEN: derive the scintillator edge/crack
   buffer from module geometry, projected-track covariance, and accidental-match
   rate; target resolution date 2026-05-31.
2. **Timing compatibility window:** OPEN: bind timing residual gates to plan-18
   calibration and scan them against edge-distance bins; target resolution date
   2026-05-31.
3. **Ambiguity policy:** OPEN: decide whether multiple compatible hits produce a
   warning, the nearest-hit association, or a fail state before C.3 consumes the
   match; target resolution date 2026-06-07.
4. **Coverage-vs-nonstop reason:** OPEN: freeze reason labels that separate
   `outside_scintillator_coverage`, `no_compatible_hit`, `timing_mismatch`, and
   `ambiguous_match`; target resolution date 2026-05-24.

## 3. C.4 Closure test for the derivation

1. Build frozen C.1, V.2, and scintillator-hit inputs for
   `cal_singleproton_50to500MeV_v2`, `cal_singlepion_50to600MeV_v2`, and
   `sig_foil_500MeV_v3` using only Class-A coordinates, timing, and geometry.
2. Persist projected module id, edge distance, timing-residual state, ambiguity
   count, selected association, consumed input hashes, and fiducial profile
   before any truth-track join.
3. In validation-only scoring, compare match efficiency, accidental rate, C.3
   range residual, and C.5 PID shifts in bins of edge distance and timing state.
4. The derivation passes when coverage states distinguish true missing matches
   from detector-edge losses, production rows are unchanged after truth columns
   are dropped, and plan 43/47 receive the selected profile loss.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes C.4 coverage state, timing state, ambiguity bins, selected
  profile, and association-loss fractions.
- Plan 47 must downgrade range or charged-PID rows that lack the C.4 fiducial
  hash, timing-calibration tag, or scintillator geometry nuisance handoff.
