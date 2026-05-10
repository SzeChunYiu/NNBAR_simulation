---
id: 24_2_vertex_branch
title: Reconstruction question tree - vertex branch
version: 0.1
status: draft
owner: Methodology Council
parent: 24_reconstruction_question_tree
last_updated: 2026-05-10
---

# Reconstruction question tree - vertex branch

This file is a split-out branch of `docs/rebuild_plans/24_reconstruction_question_tree.md`
created to keep each plan file under the 500-line cap. It inherits the
truth-leakage gate, acceptance criteria, dependencies, and references from
plan 24.

## 2. Vertex branch

**What is the irreducible TPC evidence that an event vertex is real
and at the foil?**

Answer now: at least two independent reconstructed track directions
should project consistently to the foil plane (`z=0`) with quality-
dependent residuals.

### 2.1 Leaves under vertex

| Leaf ID | Decision |
|---|---|
| `V.1` | What constitutes a TPC track from hits? |
| `V.2` | What direction is associated with that track? |
| `V.3` | How do we project a track to the foil plane? |
| `V.4` | How do we aggregate multiple track projections into one event vertex? |
| `V.5` | When do we accept the event vertex as foil-compatible? |

**Owning subsystem plans:** plan 25 for V.1, plan 26 for V.2,
and plan 30 for V.3-V.5.

### Per-leaf input/output schemas

```
Leaf V.1: TPC hits → track candidates
  inputs (Class A): TPC parquet columns
                    (Event_ID, x, y, z, t, eDep, photons[=electrons],
                     px, py, pz, xHitID, module_ID, step_info,
                     vol_name)
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name
  decision rule: clustering algorithm produces track candidates
  output schema: {event_id: int64, candidate_id: int64,
                  hit_indices: int64[], anchor_xyz: float64[3],
                  direction_xyz: float64[3], n_hits: int32,
                  chi2_seed: float64}
  allowed truth use: validation_only
                    matching to truth Track_ID for efficiency scoring
  downstream consumers: V.2, V.3, V.4 (this plan); plan 25 (subsystem)
```

Leaf V.2: track candidates → fitted track directions
  inputs (Class A): V.1 candidate-track table plus the referenced TPC
                    hit columns (Event_ID, x, y, z, t, eDep, photons,
                    px, py, pz, xHitID, module_ID, step_info, vol_name)
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name,
                       particle_x, particle_y, particle_z
  decision rule: fit or estimate a direction from the ordered Class A
                 hit coordinates; the current baseline is the
                 first-to-last-hit unit vector from plan 08 §3.2
                 (`_track_anchor_and_direction`; `charged.py:62-81`),
                 with covariance and
                 residuals supplied by plan 26 before sign-off.
  output schema: {event_id: int64, candidate_id: int64,
                  anchor_xyz: float64[3], direction_xyz: float64[3],
                  direction_covariance: float64[3,3],
                  chi2_ndf: float64, n_direction_hits: int32,
                  direction_method: string}
  allowed truth use: validation_only
  downstream consumers: V.3, V.4, C.2, C.4; plans 26, 27, 29, 30

Leaf V.3: fitted track directions → foil-plane projections
  inputs (Class A): V.2 direction table
                    (event_id, candidate_id, anchor_xyz,
                     direction_xyz, direction_covariance, chi2_ndf)
                    plus the foil-plane definition from plan 16
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name,
                       particle_x, particle_y, particle_z, Vx, Vy, Vz
                       from truth-primary or interaction tables
  decision rule: intersect the track ray
                 `anchor_xyz + λ direction_xyz` with the nominal
                 foil plane (`z = 0` in the current baseline from
                 plan 08 §3.3); mark the projection invalid instead
                 of substituting truth when direction_z is zero,
                 non-finite, or the input candidate is below the
                 V.2 quality gate.
  output schema: {event_id: int64, candidate_id: int64,
                  projection_xyz: float64[3],
                  projection_covariance: float64[3,3],
                  projection_valid: bool, skipped_reason: string,
                  source_chi2_ndf: float64}
  allowed truth use: validation_only
  downstream consumers: V.4, V.5; plan 30

Leaf V.4: foil-plane projections → event vertex estimate
  inputs (Class A): V.3 projection table
                    (event_id, candidate_id, projection_xyz,
                     projection_covariance, projection_valid,
                     skipped_reason, source_chi2_ndf)
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name,
                       truth-primary vertices (Vx, Vy, Vz) and
                       interaction-table vertices
  decision rule: aggregate valid track projections into one event
                 vertex using a documented estimator; the current
                 baseline is the unweighted mean of valid projections
                 with radial RMS and skipped-track counts from plan
                 08 §3.3, while sign-off requires the plan 30
                 covariance-weighted alternative to be benchmarked.
  output schema: {event_id: int64, vertex_xyz: float64[3],
                  vertex_covariance: float64[3,3],
                  n_tracks_used: int32, n_tracks_skipped: int32,
                  radial_rms_mm: float64,
                  aggregation_method: string, vertex_valid: bool}
  allowed truth use: validation_only
  downstream consumers: V.5, P.3, P.7, E.7, S.1; plans 30, 33, 35, 36, 37

Leaf V.5: event vertex estimate → foil-compatible vertex flag
  inputs (Class A): V.4 vertex table
                    (event_id, vertex_xyz, vertex_covariance,
                     n_tracks_used, radial_rms_mm, vertex_valid)
                    plus foil geometry constants from plan 16
  forbidden (Class B): truth-primary vertices (Vx, Vy, Vz),
                       interaction-table vertices, Track_ID,
                       Parent_ID, Name, origin_vol_name
  decision rule: accept only a valid reconstructed vertex whose
                 transverse radius and z position fall inside the
                 plan 16 foil envelope; the current baseline uses the
                 `z = 0` projection path in plan 08 §3.3, but sign-off
                 requires explicit geometry-versioned radii and
                 thickness tolerances instead of truth-origin cuts.
  output schema: {event_id: int64, foil_compatible: bool,
                  vertex_valid: bool, vertex_r_mm: float64,
                  vertex_z_mm: float64,
                  foil_geometry_version: string,
                  acceptance_reason: string}
  allowed truth use: validation_only
  downstream consumers: S.1; plans 30, 37, 47

### Next measurement (vertex branch)

Truth-free clustering / vertex closure study on signal annihilation
events using only Class A columns; truth used only for validation
scoring.
