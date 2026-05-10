---
id: 60_c2_dedx_path_fiducial
title: Fiducial volume - C.2 dE/dx path-containment derivation
version: 0.1
status: draft
owner: Tracking POG
parent: 60_fiducial_volume_and_edge_effects
last_updated: 2026-05-10
---

# C.2 dE/dx path-containment fiducial derivation

This child file binds plan 60's fiducial-volume policy to leaf C.2 from
plans 24 and 27. It defines when the TPC path used for dE/dx is contained
enough that edge losses do not masquerade as particle-ID information.

## 1. C.2 Physics derivation

- **What is physically measured:** the C.2 fiducial state measures whether the
  reconstructed ionisation samples used for dE/dx cover a sufficiently
  contained path length with stable charge collection. Truth momentum or
  species labels are validation-only closure inputs.
- **Estimator rationale:** dE/dx is a path-normalised ionisation estimator, so
  edge truncation changes both numerator and denominator. The fiducial
  observable is therefore selected path length, sample count after truncation,
  nearest active-face distance, and saturation/degraded-charge state before PID
  scoring. TPC PID reviews and the PDG passage-of-particles review motivate
  treating containment as an uncertainty on the estimator, not as a species
  prior \cite{alice2014performance,ParticleDataGroup:2024RPP}.
- **Statistical character:** false rejection reduces PID statistics and signal
  efficiency; false acceptance admits short or edge-degraded samples whose
  Landau tail and calibration bias can shift C.5 scores. Dominant uncertainty
  comes from path-length modelling, gain calibration, and sample-count
  fluctuations near detector boundaries.

## 2. C.2 Logic gaps

1. **Minimum selected path length:** OPEN: scan path-length thresholds jointly
   with the plan-27 truncation fractions; optimise Bethe-Bloch residual width
   and charged-candidate retention; target resolution date 2026-05-31.
2. **Minimum selected sample count:** OPEN: derive after truncation from
   calibration samples so dE/dx rows cannot report precision from too few
   contained deposits; target resolution date 2026-05-31.
3. **Edge/degraded-charge state:** OPEN: decide whether near-edge deposits are
   excluded, down-weighted, or retained with `dedx_quality_state=warn`; target
   resolution date 2026-06-07.
4. **Profile semantics:** OPEN: decide whether the `loose` fiducial profile
   allows C.2 warning rows to feed C.5 with larger uncertainty, or blocks them
   from PID scoring; target resolution date 2026-06-07.

## 3. C.2 Closure test for the derivation

1. Build frozen C.1 and C.2 tables for `cal_singlepion_50to600MeV_v2`,
   `cal_singleproton_50to500MeV_v2`, and `sig_foil_500MeV_v3` using only
   Class-A TPC deposits, track rows, and geometry sidecars.
2. Persist selected path length, selected sample count, nearest-edge distance,
   degraded-charge state, consumed C.1/V.2 hashes, and selected fiducial profile
   before any truth-label join.
3. In validation-only scoring, compare dE/dx residuals, sample-count stability,
   and C.5 PID-score shifts in bins of path length and edge distance.
4. The derivation passes when edge bins do not show unexplained dE/dx residual
   bias, production rows are unchanged after Class-B truth columns are dropped,
   and the accepted profile loss is exported to plan 43 and plan 47.

## 4. Plan 43 / plan 47 handoff

- Plan 43 consumes C.2 path-containment bins, selected sample-count bins,
  quality state, selected profile, and C.2 loss fractions.
- Plan 47 must downgrade dE/dx, charged-PID, or charged-efficiency rows that
  lack the C.2 fiducial hash or omit calibration/geometry nuisance handoff.
