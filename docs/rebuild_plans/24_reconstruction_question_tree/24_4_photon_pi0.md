---
id: 24_4_photon_pi0_branch
title: Reconstruction question tree - photon / pi0 branch
version: 0.1
status: draft
owner: Methodology Council
parent: 24_reconstruction_question_tree
last_updated: 2026-05-09
---

# Reconstruction question tree - photon / pi0 branch

This file is a split-out branch of `docs/rebuild_plans/24_reconstruction_question_tree.md`
created to keep each plan file under the 500-line cap. It inherits the
truth-leakage gate, acceptance criteria, dependencies, and references from
plan 24.

## 4. Photon / π⁰ branch

**What is the irreducible lead-glass + scintillator evidence that two
clusters are a π⁰ decay?**

Answer now: two photon-like neutral objects whose summed four-momentum
satisfies the π⁰ mass and opening-angle window, with each cluster
charged-vetoed.

### 4.1 Leaves under photon / π⁰

| Leaf ID | Decision |
|---|---|
| `P.1` | What constitutes a calorimeter cluster (lead-glass and/or scintillator)? |
| `P.2` | What charged/neutral discriminant tags a cluster as photon-like? |
| `P.3` | What direction is associated with a photon (vertex → centroid)? |
| `P.4` | What energy is associated with a photon (deposited; possibly scintillator+lead-glass combined)? |
| `P.5` | How are two photons paired to a π⁰ candidate? |
| `P.6` | When are two photons accidentally compatible (rejection)? |
| `P.7` | What kinematic-fit corrections are applied to π⁰ candidates? |

**Owning subsystem plans:** 26 (clustering), 27 (shower shape), 28
(photon object), 29 (π⁰ pairing in plan numbering note: plan 29 is
charged PID; π⁰ pairing is plan 34), 30 (pairing — sic, plan 34),
35 (kinematic fit).

*Numbering correction:* per 00_README §4.7, plan 34 is π⁰ pairing
and plan 35 is kinematic fit.

Leaf P.1: calorimeter hits → neutral/EM cluster candidates
  inputs (Class A): LeadGlass and Scintillator hit columns
                    (Event_ID, x, y, z, t, eDep, photons,
                    module_ID, vol_name, step_info) plus calorimeter
                    geometry side-cars
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name,
                       Interaction ancestry, particle_x/y/z truth
                       origins
  decision rule: group spatially and temporally adjacent calorimeter
                 deposits into clusters using detector geometry and
                 timing only; the plan 08 §3.5 truth-ancestry grouping
                 is a baseline violation to replace, not an allowed
                 production rule.
  output schema: {event_id: int64, cluster_id: int64,
                  detector_region: string, centroid_xyz: float64[3],
                  centroid_covariance: float64[3,3], energy_mev:
                  float64, time_ns: float64, n_hits: int32,
                  cluster_valid: bool}
  allowed truth use: validation_only
  downstream consumers: P.2, P.3, P.4, P.5; plans 31, 32, 33, 34

Leaf P.2: clusters + charged tracks → photon-like discriminant
  inputs (Class A): P.1 cluster table, C.1/C.4 charged-candidate
                    and scintillator-association tables, cluster
                    timing, shower-shape observables, and geometry
                    side-cars
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name,
                       truth charge-match labels, Interaction ancestry
  decision rule: tag a cluster as charged when a reconstructed charged
                 track points to it within the plan 08 §3.5 angular and
                 timing windows; a photon-like cluster is a neutral
                 cluster passing shower-shape and charged-veto cuts.
  output schema: {event_id: int64, cluster_id: int64,
                  photon_like: bool, charged_veto: bool,
                  neutral_score: float64, charged_match_candidate_id:
                  int64, match_angle_deg: float64,
                  match_time_residual_ns: float64,
                  discriminant_version: string}
  allowed truth use: validation_only
  downstream consumers: P.3, P.4, P.5, P.6; plans 32, 33, 34

Leaf P.3: photon-like clusters + vertex → photon direction
  inputs (Class A): P.1/P.2 photon-like cluster centroid and timing,
                    V.4 event vertex estimate and covariance
  forbidden (Class B): truth gamma momentum, source_track_ids,
                       Track_ID, Parent_ID, Name, Interaction ancestry
  decision rule: define the photon direction as the unit vector from
                 the reconstructed event vertex to the cluster
                 centroid; if no valid vertex exists, use the declared
                 legacy origin fallback only as an auditable degraded
                 mode, never by reading truth.
  output schema: {event_id: int64, photon_id: int64,
                  cluster_id: int64, direction_xyz: float64[3],
                  direction_covariance: float64[3,3],
                  vertex_source: string, direction_valid: bool}
  allowed truth use: validation_only
  downstream consumers: P.5, P.7, E.7; plans 33, 34, 35, 36

### Next measurement (photon / π⁰ branch)

Truth-free clustering closure study on `cal_singlegamma_v1` (plan 23)
+ signal sample (plan 20). Charged-veto closure on signal +
`cal_singlepion*`.
