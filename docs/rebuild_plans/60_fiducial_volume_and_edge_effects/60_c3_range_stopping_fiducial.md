---
id: 60_c3_range_stopping_fiducial
title: Fiducial volume - C.3 range/stopping coverage derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# C.3 range/stopping fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf C.3 from
plans 24 and 28. It defines when scintillator coverage and edge proximity
make a charged-particle range or stopping observable usable.

## 1. C.3 Physics derivation

- **What is physically measured:** the C.3 fiducial state measures whether the
  reconstructed charged candidate has enough instrumented scintillator coverage
  along its projected path to estimate range, stopping behaviour, or a Bragg-like
  profile. Truth kinetic energy and species labels are validation-only.
- **Estimator rationale:** range and stopping observables require a contained or
  at least instrumented path through the scintillator stack. The fiducial
  observable is the projected distance to module boundaries, associated-hit
  coverage, edge buffer, and valid range-quality state. Passage-of-particles and
  detector-acceptance references motivate treating uninstrumented path loss as a
  coverage uncertainty rather than as PID evidence \cite{ParticleDataGroup:2024RPP,HIBEAM_NNBAR_at_ESS}.
- **Statistical character:** false rejection removes stopping-particle
  information; false acceptance lets edge-truncated hit profiles bias range and
  C.5 PID scores. Dominant uncertainty comes from scintillator segmentation,
  projected-track uncertainty, and module-edge response.

## 2. C.3 Logic gaps

1. **Scintillator edge buffer:** OPEN: derive `scintillator_edge_buffer_mm` from
   module geometry, projected-track covariance, and range residuals in
   calibration samples; target resolution date 2026-05-31.
2. **Minimum instrumented path / hit count:** OPEN: scan required associated-hit
   count and path length against range residual and Bragg-profile stability;
   target resolution date 2026-05-31.
3. **Range-valid warning policy:** OPEN: decide whether edge-truncated rows with
   valid partial ranges feed C.5 as warnings or fail the `loose` profile; target
   resolution date 2026-06-07.
4. **Profile handoff to C.4:** OPEN: ensure C.3 range coverage and C.4 hit
   association use the same geometry sidecar and do not double-count the same
   edge loss; target resolution date 2026-05-24.

## 3. C.3 Closure test for the derivation

1. Build frozen C.1, C.3, and C.4 tables for
   `cal_singleproton_50to500MeV_v2`, `cal_singlepion_50to600MeV_v2`, and
   `sig_foil_500MeV_v3` using Class-A charged and scintillator rows.
2. Persist projected scintillator edge distance, associated-hit coverage,
   range-quality state, consumed C.1/C.4 hashes, and selected fiducial profile
   before any truth-label join.
3. In validation-only scoring, compare range residuals, Bragg-position
   stability, and C.5 PID-score shifts in bins of edge distance and hit count.
4. The derivation passes when coverage states remove unexplained edge-driven
   range bias, production rows are unchanged after Class-B truth columns are
   dropped, and plan 43/47 receive the selected profile loss.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes C.3 scintillator-coverage bins, associated-hit counts,
  range-quality state, selected profile, and C.3 object-loss fractions.
- Plan 47 must downgrade range, charged-PID, or charged-efficiency rows that
  lack the C.3 fiducial hash, consumed C.4 hash, or scintillator geometry
  nuisance handoff.
