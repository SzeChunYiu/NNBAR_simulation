---
id: 60_c6_rejection_fiducial
title: Fiducial volume - C.6 rejection-state fiducial derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# C.6 rejection-state fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf C.6 from
plans 24 and 29. It defines when charged-candidate rejection is an
observable fiducial/quality decision rather than a hidden truth filter.

## 1. C.6 Physics derivation

- **What is physically measured:** the C.6 fiducial state measures whether a
  charged candidate is rejected because observable detector geometry, topology,
  timing, or upstream-quality states make it unusable for pion/proton counting.
  Truth ancestry and particle labels are validation-only.
- **Estimator rationale:** rejection after PID must preserve the pre-rejection
  PID state and expose an observable reason. Fiducial rejection is therefore a
  profile-aware composition of C.1-C.5 quality states plus geometry/timing
  states for EM-like, neutral-like, conversion-like, or edge-loss cases. PDG and
  TPC/PID practice motivate separating object quality/rejection from truth
  particle identity \cite{ParticleDataGroup:2024RPP,alice2014performance}.
- **Statistical character:** false rejection lowers charged signal efficiency;
  false acceptance contaminates charged multiplicity and downstream event-shape
  leaves. Dominant uncertainty comes from correlated upstream edge losses,
  conversion/EM topology ambiguity, and profile-specific warning policies.

## 2. C.6 Logic gaps

1. **Observable rejection taxonomy:** OPEN: align plan-29 reasons with plan-60
   fiducial reasons so `geometry_loss`, `em_like`, `conversion_like`, and
   `invalid_upstream` remain distinguishable; target resolution date
   2026-05-24.
2. **Profile composition:** OPEN: decide whether `loose` allows warning-only
   upstream states to remain non-rejected while `tight` rejects them; target
   resolution date 2026-05-31.
3. **Correlation accounting:** OPEN: prevent the same edge loss from being
   counted once as C.1/C.3 fiducial failure and again as C.6 rejection; target
   resolution date 2026-06-07.
4. **Efficiency denominator:** OPEN: define whether C.6 fiducial rejection is a
   charged-PID loss, object-quality loss, or final-selection loss in plan 43;
   target resolution date 2026-05-31.

## 3. C.6 Closure test for the derivation

1. Build frozen C.1-C.6 tables for charged calibration samples and
   `sig_foil_500MeV_v3`, carrying upstream fiducial states and C.5
   `pid_before_rejection` but no truth ancestry in production inputs.
2. Persist rejection fiducial state, primary observable reason, upstream-state
   vector, selected profile, and consumed C.1-C.5 hashes before validation labels
   are joined.
3. In validation-only scoring, compare rejection efficiency, fake rejection,
   charged multiplicity, and plan-43 efficiency shifts in bins of upstream
   fiducial state and rejection reason.
4. The derivation passes when C.6 rejection rows are invariant to Class-B column
   removal, every rejection has one observable primary reason, and plan 43/47
   receive non-double-counted profile-specific charged-object losses.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes C.6 rejection reason, upstream-state vector, selected profile,
  and non-double-counted charged-object loss fractions.
- Plan 47 must downgrade charged-multiplicity, charged-PID, or signal-efficiency
  rows that lack the C.6 rejection-fiducial hash or reason-taxonomy version.
