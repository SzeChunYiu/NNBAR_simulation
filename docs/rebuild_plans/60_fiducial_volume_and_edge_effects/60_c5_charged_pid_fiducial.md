---
id: 60_c5_charged_pid_fiducial
title: Fiducial volume - C.5 charged-PID fiducial derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# C.5 charged-PID fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf C.5 from
plans 24 and 29. It defines when a charged PID score is accepted for
edge-aware efficiency and reproduction budgets.

## 1. C.5 Physics derivation

- **What is physically measured:** the C.5 fiducial state measures whether the
  combined dE/dx, range, and scintillator-energy inputs to a pion/proton score
  are sufficiently contained and instrumented to support a PID decision. Truth
  species labels are calibration or validation inputs only after the production
  score is frozen.
- **Estimator rationale:** C.5 is a classifier on already-measured observables,
  so fiducial validity must be inherited from C.1-C.4 containment, not inferred
  from the predicted particle species. Detector-PID practice and classical
  discriminant theory motivate exporting a quality/profile state alongside the
  PID score so selection does not confuse edge loss with particle identity
  \cite{ParticleDataGroup:2024RPP,alice2014performance,Fisher1936Discriminant}.
- **Statistical character:** false rejection lowers pion/proton efficiency,
  while false acceptance lets edge-degraded dE/dx/range rows bias PID and event
  multiplicities. Dominant uncertainty comes from correlated C.2/C.3
  measurement quality and profile-dependent handling of warning rows.

## 2. C.5 Logic gaps

1. **Input-quality composition:** OPEN: freeze whether C.5 passes only when C.2,
   C.3, and C.4 all pass, or whether warning rows can enter with inflated
   uncertainty under the `loose` profile; target resolution date 2026-06-07.
2. **Score-validity threshold:** OPEN: derive a minimum valid PID-confidence or
   score-separation requirement from calibration ROC curves and plan-38 ladder
   deltas; target resolution date 2026-05-31.
3. **Correlated edge loss:** OPEN: estimate covariance between TPC edge loss and
   scintillator coverage loss so plan 43 does not double-count the same rejected
   candidate; target resolution date 2026-06-07.
4. **Profile handoff:** OPEN: decide whether `unclassified` C.5 rows count as
   fiducial failures, PID failures, or separate efficiency-denominator rows;
   target resolution date 2026-05-24.

## 3. C.5 Closure test for the derivation

1. Build frozen C.1-C.5 tables for pion/proton calibration samples and
   `sig_foil_500MeV_v3`, keeping truth species out of the production C.5 score.
2. Persist C.5 fiducial state, input-quality vector, selected profile,
   score-validity fields, and consumed C.2/C.3/C.4 hashes before validation
   labels are joined.
3. In validation-only scoring, compare PID confusion matrices, ROC curves,
   charged multiplicities, and plan-43 efficiency shifts in bins of input
   fiducial state and edge-distance profile.
4. The derivation passes when C.5 fiducial states identify edge-driven PID
   losses without altering truth-blind score rows and plan 43/47 receive the
   selected profile loss plus dominant nuisance ids.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes C.5 PID-valid state, input-quality vector, selected profile,
  and pion/proton fiducial-loss fractions.
- Plan 47 must downgrade charged-PID, charged-multiplicity, or signal-efficiency
  rows that lack the C.5 fiducial hash or input-quality provenance.
