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

#### V.1 Physics derivation

- **What is physically measured:** V.1 estimates whether a set of TPC
  ionisation deposits is a single charged-particle trajectory segment in
  detector coordinates, before any truth-side `Track_ID` or species label is
  considered.
- **Estimator rationale:** in an Ar/CO2 TPC, a charged particle leaves local
  ionisation clusters whose drifted coordinates sample a continuous path;
  density/geometric clustering in `(x, y, z, t)` is therefore the first
  Class-A estimator for candidate membership, with straight-line seeding
  justified by the no-curvature baseline. This follows the TPC concept in
  Rubbia's drift-volume description and modern TPC tracking practice
  \cite{rubbia1977liquid,alice2014performance}; DBSCAN-style density
  clustering is the candidate non-parametric baseline \cite{Ester:1996DBSCAN}.
- **Statistical character:** the dominant uncertainty is fake splitting or
  merging from sparse hits and overlapping tracks; bias enters when the seed
  uses only first/last coordinates, while variance is controlled by hit count,
  coordinate resolution, and local hit density.
- **Citation:** `rubbia1977liquid`, `alice2014performance`, and
  `Ester:1996DBSCAN` are resolved in the thesis bibliography.

#### V.1 Logic gaps

1. **Minimum hit count = 2:** two finite coordinates are the mathematical
   minimum for a line seed; keep this as a derived lower bound, but require
   plan-25 quality flags to mark two-hit candidates as degraded.
2. **DBSCAN `eps` / time scale:** OPEN: optimise on
   `cal_singlepion_50to600MeV_v2` and `sig_foil_v3` with efficiency, fake
   rate, and split/merge fraction as the figure of merit; target resolution
   date 2026-05-17.
3. **DBSCAN `min_samples`:** OPEN: scan 2-6 hits with Wilson intervals on the
   same closure samples and choose the smallest value that keeps fake rate
   below the plan-25 acceptance band; target resolution date 2026-05-17.
4. **Hough/Kalman seed bins:** OPEN: defer bin widths and process-noise
   constants to the plan-49 improvement packet after V.1 baseline closure;
   target resolution date 2026-05-24.

#### V.1 Closure test for the derivation

1. Run the V.1 candidate builder on `cal_singlepion_50to600MeV_v2` after
   dropping `Track_ID`, `Parent_ID`, `Name`, and `origin_vol_name` from the
   production input.
2. Match frozen candidate hit memberships back to truth only inside a
   `validation_only` scorer, and compute efficiency, fake rate, and
   split/merge fractions with plan-04 Wilson intervals.
3. Pass when the truth-blind candidate table is invariant to dropping Class-B
   columns and the derived two-hit lower-bound rows are explicitly labelled
   degraded rather than silently accepted as high-quality tracks.

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

#### V.2 Physics derivation

- **What is physically measured:** V.2 estimates the charged-particle
  direction vector in detector coordinates from the Class-A hit positions
  assigned by V.1; truth momentum is only the validation target for pulls.
- **Estimator rationale:** with no magnetic-field curvature in the baseline,
  the optimal straight-track direction under independent Gaussian hit errors is
  the total-least-squares/PCA principal axis of the hit cloud. PDG tracking and
  multiple-scattering reviews set the uncertainty budget, ALICE documents TPC
  straight/curved track fitting practice, and Kalman filtering is the
  covariance-propagating upgrade path \cite{ParticleDataGroup:2024RPP,alice2014performance,Kalman:1960new}.
- **Statistical character:** bias is dominated by first/last-hit seeds,
  multiple scattering, and merged V.1 candidates; variance is driven by hit
  count, coordinate resolution, lever arm, and drift-time calibration. Robust
  production rows must expose covariance validity instead of letting V.4 infer
  trust from missing fields.
- **Citation:** `ParticleDataGroup:2024RPP`, `alice2014performance`, and
  `Kalman:1960new` are resolved in the thesis bibliography.

#### V.2 Logic gaps

1. **Two-coordinate direction lower bound:** two finite hit positions define a
   direction but not residual degrees of freedom; keep as a degraded fallback.
2. **Covariance minimum hit count = 3:** three points are the lower bound for a
   residual covariance estimate; rows below this threshold must set
   `covariance_valid=false` once that field lands.
3. **Per-hit coordinate σ:** OPEN: derive from plan-17 drift/gain calibration
   and single-pion residuals; figure of merit is pull width versus hit count;
   target resolution date 2026-05-24.
4. **Multiple-scattering material budget:** OPEN: propagate gas, foil, and
   scintillator material from plan 16 into the V.2 covariance model; target
   resolution date 2026-05-24.
5. **Pull acceptance `|mu| < 0.05`, width `[0.9, 1.1]`:** inherited from plan
   40 until the V.2 closure study has enough statistics to retune it; if
   changed, the plan-05 decision log must record the replacement tolerance.

#### V.2 Closure test for the derivation

1. Build V.2 fit rows from frozen V.1 candidates on
   `cal_singlepion_50to600MeV_v2` using only Class-A coordinates.
2. Compute PCA/least-squares direction, covariance, chi2/ndf, and residual
   sidecar rows before joining any truth direction.
3. In a `validation_only` scorer, compare fit direction to truth momentum and
   assert pull means and widths satisfy the plan-40 V.2 tolerance, with
   two-hit rows counted separately as degraded.
4. Pass when V.4 receives only finite directions with explicit covariance
   validity/degraded flags and the production output is unchanged by dropping
   Class-B truth direction columns.

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
