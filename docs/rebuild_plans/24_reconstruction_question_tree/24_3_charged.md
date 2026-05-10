---
id: 24_3_charged_branch
title: Reconstruction question tree - charged-object branch
version: 0.1
status: draft
owner: Methodology Council
parent: 24_reconstruction_question_tree
last_updated: 2026-05-09
---

# Reconstruction question tree - charged-object branch

This file is a split-out branch of `docs/rebuild_plans/24_reconstruction_question_tree.md`
created to keep each plan file under the 500-line cap. It inherits the
truth-leakage gate, acceptance criteria, dependencies, and references from
plan 24.

## 3. Charged-object branch

**What is the irreducible TPC + scintillator evidence that a track is a
charged primary pion or proton?**

Answer now: a TPC-reconstructed track with scintillator-energy
matching consistent with a charged-track ray, characterised by dE/dx
and stopping range that distinguish π from p.

### 3.1 Leaves under charged

| Leaf ID | Decision |
|---|---|
| `C.1` | What constitutes a charged track candidate (post-V.1)? |
| `C.2` | How is dE/dx estimated from TPC step records? |
| `C.3` | How is stopping range estimated from scintillator hits? |
| `C.4` | How are scintillator hits associated to a TPC track? |
| `C.5` | How is the π/p decision made from {dE/dx, range, scintillator E}? |
| `C.6` | When is a candidate rejected (e.g. EM lineage)? |

**Owning subsystem plans:** 25 (V.1 reuse), 27 (dE/dx), 28 (range/
stopping), 29 (charged PID).

Plan 08 §3.4 documents the current code path. Plan 01 §4 audit
flags the current `Name`-gated PID as a Class B violation; the leaf
C.1 exit criterion is the migration of that gate.

Leaf C.1: V.1/V.2 tracks → charged-track candidates
  inputs (Class A): V.1 candidate-track table, V.2 direction table,
                    and referenced TPC columns
                    (Event_ID, x, y, z, t, eDep, photons, px, py,
                    pz, xHitID, module_ID, step_info, vol_name)
  forbidden (Class B): Name, Track_ID, Parent_ID, origin_vol_name,
                       particle_x, particle_y, particle_z
  decision rule: admit reconstructed track candidates by Class A
                 quality cuts (hit count, fitted direction, χ²/ndf,
                 and detector geometry) rather than by truth particle
                 name; plan 08 §3.4/§3.7 documents the current
                 `Name` gate that must move to validation only.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  candidate_id: int64, anchor_xyz: float64[3],
                  direction_xyz: float64[3], n_tpc_hits: int32,
                  track_quality: float64,
                  charged_candidate_valid: bool}
  allowed truth use: validation_only
  downstream consumers: C.2, C.3, C.4, C.5, C.6; plans 27, 28, 29

Leaf C.2: charged-track candidates → dE/dx estimator
  inputs (Class A): C.1 charged-candidate table plus referenced TPC
                    step columns (Event_ID, eDep, TrackLength, x, y,
                    z, t, photons, step_info)
  forbidden (Class B): Name, Track_ID, Parent_ID, origin_vol_name,
                       particle_x, particle_y, particle_z
  decision rule: compute per-step `eDep / TrackLength` in a
                 detector-only track slice, then form the plan 27
                 truncated mean (drop top 30%, bottom 10% until
                 calibration retunes it); the current plan 08 §3.4
                 `dedx` output remains valid only after the C.1
                 truth-name gate is removed.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  dedx_mev_per_cm: float64, estimator: string,
                  n_steps_used: int32, path_length_cm: float64,
                  low_truncation_fraction: float64,
                  high_truncation_fraction: float64,
                  calibration_source: string}
  allowed truth use: validation_only
  downstream consumers: C.5, C.6; plans 27, 29

Leaf C.3: charged-track candidates + scintillator hits → stopping range
  inputs (Class A): C.1 charged-candidate table, V.2 direction table,
                    matched-scintillator columns (Event_ID, x, y, z,
                    t, eDep, photons, module_ID, vol_name, step_info),
                    and `Scintillator_Module_Position.txt`
                    geometry side-car
  forbidden (Class B): Name, Track_ID, Parent_ID, origin_vol_name,
                       particle_x, particle_y, particle_z
  decision rule: after C.4 supplies geometrically associated
                 scintillator hits, project each hit onto the track
                 direction and report the maximum positive projected
                 distance from the TPC entry/anchor; plan 28 keeps the
                 current plan 08 §3.4 range estimator and adds a
                 Bragg-peak closure before using it as a PID input.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  range_cm: float64, range_edep_mev: float64,
                  n_scintillator_hits: int32,
                  last_hit_module_id: int32,
                  bragg_peak_position_cm: float64,
                  range_valid: bool}
  allowed truth use: validation_only
  downstream consumers: C.5, C.6; plans 28, 29

Leaf C.4: charged-track candidates + scintillator hits → hit association
  inputs (Class A): C.1 charged-candidate table, V.2 direction table,
                    scintillator hit columns (Event_ID, x, y, z, t,
                    eDep, photons, module_ID, vol_name, step_info),
                    and scintillator geometry side-car
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name,
                       particle_x, particle_y, particle_z
  decision rule: associate scintillator hits to a TPC track by
                 ray-to-hit angle, closest-approach distance, and
                 optional timing consistency using the
                 ReconstructionConfig thresholds cited in plan 08
                 §3.4; exact `Track_ID` matching is not a production
                 association rule and is retained only for validation
                 of sparse legacy tables.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  scintillator_hit_indices: int64[],
                  match_angle_deg: float64,
                  closest_approach_cm: float64,
                  time_residual_ns: float64,
                  matched_edep_mev: float64, match_method: string,
                  association_valid: bool}
  allowed truth use: validation_only
  downstream consumers: C.3, C.5, C.6; plans 28, 29

Leaf C.5: dE/dx + range + scintillator energy → π/p PID decision
  inputs (Class A): C.1 charged-candidate table, C.2 dE/dx table,
                    C.3 range table, C.4 scintillator association
                    table, and ReconstructionConfig PID thresholds
  forbidden (Class B): Name, Track_ID, Parent_ID, origin_vol_name,
                       particle_x, particle_y, particle_z, truth PID
                       labels from calibration tables
  decision rule: apply the cut-based plan 29 §1 baseline
                 (`dedx >= proton_dedx_min` or short-range +
                 lower-dE/dx proton rule) to every valid charged
                 candidate; likelihood-ratio or MVA replacements
                 must be scored on the plan 38 C.5 ladder before
                 replacing the baseline.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  pid: string, proton_score: float64,
                  pion_score: float64,
                  dedx_threshold_mev_per_cm: float64,
                  range_threshold_cm: float64,
                  decision_rule_version: string,
                  pid_valid: bool, decision_reason: string}
  allowed truth use: validation_only
  downstream consumers: C.6, E.9, S.2; plans 29, 36, 37

### Next measurement (charged branch)

Per-species reconstructed efficiency on `cal_singlepion*` and
`cal_singleproton` samples (plan 23), broken down by C.1–C.6.
