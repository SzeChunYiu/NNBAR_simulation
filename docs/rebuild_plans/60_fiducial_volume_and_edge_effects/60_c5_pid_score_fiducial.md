---
id: 60_c5_pid_score_fiducial
title: Fiducial volume - C.5 PID-score acceptance derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# C.5 PID-score fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf C.5 from
plans 24 and 29. It defines when charged-PID scores are allowed to enter
efficiency budgets given the fiducial state of their input observables.

## 1. C.5 Physics derivation

- **What is physically measured:** the C.5 fiducial state measures whether a
  charged candidate has enough contained dE/dx, range, scintillator, and quality
  information for its pion/proton score to be interpreted as a detector response
  rather than an edge artifact. Truth PID labels are validation-only.
- **Estimator rationale:** a PID score is only meaningful inside the support of
  its calibrated input observables. Therefore the fiducial estimator is the
  conjunction of upstream C.1-C.4 fiducial states, score-validity state, and
  explicit uncertainty/profile metadata. Charged-particle PID reviews motivate
  reporting the accepted feature support separately from the classifier decision
  \cite{alice2014performance,ParticleDataGroup:2024RPP}.
- **Statistical character:** false rejection reduces charged-PID efficiency;
  false acceptance lets edge-truncated features create overconfident pion/proton
  scores. Dominant uncertainty comes from upstream containment losses, feature
  covariance, calibration drift, and threshold tuning near score boundaries.

## 2. C.5 Logic gaps

1. **Upstream-state conjunction:** OPEN: decide whether C.5 requires all of
   C.1-C.4 to pass, or whether warning states propagate with larger score
   uncertainty under the `loose` profile; target resolution date 2026-06-07.
2. **Score-validity region:** OPEN: define the observable feature support where
   the score was calibrated, including dE/dx path length and range coverage
   bins; target resolution date 2026-05-31.
3. **Invalid-feature policy:** OPEN: freeze whether missing C.2, C.3, or C.4
   inputs produce `not_applicable`, `warn`, or `fail` for PID-score acceptance;
   target resolution date 2026-05-24.
4. **Threshold/profile coupling:** OPEN: require plan-57 or plan-38 evidence
   before changing PID thresholds in response to fiducial-profile losses; target
   resolution date 2026-06-07.

## 3. C.5 Closure test for the derivation

1. Build frozen C.1-C.5 tables for the charged calibration samples and
   `sig_foil_500MeV_v3` with upstream fiducial fields attached but without
   truth labels in production inputs.
2. Persist upstream-fiducial summary, score-validity state, selected profile,
   feature-support bin, consumed C.1-C.4 hashes, and PID-threshold version before
   any validation-label join.
3. In validation-only scoring, compare ROC curves, confusion matrices,
   calibration residuals, and charged efficiency in bins of upstream fiducial
   state and feature-support bin.
4. The derivation passes when fiducial states explain score degradation without
   truth leakage, production rows are unchanged after Class-B columns are
   dropped, and plan 43/47 receive profile-specific PID losses.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes C.5 score-validity state, feature-support bins, selected
  profile, PID-threshold version, and charged-PID loss fractions.
- Plan 47 must downgrade charged-PID or charged-efficiency rows that lack the
  C.5 fiducial hash, upstream C.1-C.4 hashes, or calibration/systematics handoff.
