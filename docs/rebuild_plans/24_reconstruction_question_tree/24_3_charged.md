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

### Next measurement (charged branch)

Per-species reconstructed efficiency on `cal_singlepion*` and
`cal_singleproton` samples (plan 23), broken down by C.1–C.6.
