---
id: 30_subsystem_vertex
title: Subsystem — event vertex (leaves V.3, V.4, V.5)
version: 0.1
status: draft
owner: Tracking POG
depends_on: [00_README, 16_geometry_and_alignment, 24_reconstruction_question_tree, 25_subsystem_tpc_hits_to_tracks, 26_subsystem_track_fit_and_pulls, 38_truth_substitution_ladder, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/30_subsystem_vertex.md, schema: this file}
acceptance:
  - {test: vertex z and r residuals within plan 40 §2 tolerance, method: closure plot, pass_when: pass}
  - {test: Billoir χ² fit benchmarked vs mean-of-projections on ladder leaf V.4, method: plan 38, pass_when: matrix entry recorded}
  - {test: foil-acceptance gate uses geometry from plan 16 (no truth), method: plan 01 audit, pass_when: zero violations}
risks:
  - {risk: only modules 0/1 are field-managed (plan 17 §1) → unfielded modules contribute biased projections, mitigation: §4 per-module weighting + alignment scenario as systematic}
estimated_effort: M
last_updated: 2026-05-09
---

# Subsystem — event vertex

*Charter.* Owns leaves V.3 (foil projection), V.4 (aggregation),
V.5 (acceptance) of plan 24 §2.

## 1. Leaf input/output schemas

Per plan 24 V.3 / V.4 / V.5 schemas:

| Leaf | Class A inputs | Forbidden Class B | Output schema |
|---|---|---|---|
| V.3 foil projection | V.2 direction table and plan 16 foil-plane geometry | `Track_ID`, `Parent_ID`, `Name`, `origin_vol_name`, `particle_x/y/z`, truth `Vx/Vy/Vz` | `{event_id, candidate_id, projection_xyz, projection_covariance, projection_valid, skipped_reason, source_chi2_ndf}` |
| V.4 vertex aggregation | V.3 projection table and covariance / quality fields | truth primary or interaction vertices; `Track_ID`, `Parent_ID`, `Name` | `{event_id, vertex_xyz, vertex_covariance, n_tracks_used, n_tracks_skipped, radial_rms_mm, aggregation_method, vertex_valid}` |
| V.5 foil acceptance | V.4 vertex table and plan 16 foil radius / half-thickness | truth primary or interaction vertices; `Track_ID`, `Parent_ID`, `Name` | `{event_id, foil_compatible, vertex_valid, vertex_r_mm, vertex_z_mm, foil_geometry_version, acceptance_reason}` |

Current implementation citation: the vertex path is documented in plan
08 §3.3 as `reconstruction.py:200-430` (section heading near 200 to
about 430). It projects valid tracks to `z=0`, averages projections,
reports radial RMS / skipped counts, and currently excludes some seeds
with truth `Name`.

## 2. Current implementation

`reconstruction.py` (plan 08 §3.3):

- For each charged candidate (TPC track from plan 25 V.1) with
  valid TPC entry/exit: project to `z=0` plane.
- Reported event vertex = mean of valid projections.
- Reports radial RMS spread; counts skipped (parallel / endpoints
  missing) tracks.
- Truth-labelled EM / neutral / neutrino / nuclear-fragment tracks
  are excluded from seeding (Class B exclusion — see §2 migration).
- Sparse legacy tables fall back to all geometrically-valid tracks.

## 3. Migration: drop the truth-labelled exclusion

The current implementation reads `Name` to drop EM and neutral
seeds. Migration:

- Class A replacement: drop tracks whose lead-glass cluster (matched
  geometrically) tags them as charged-EM (plan 29 §3 EM rejection).
- Drop tracks with low χ²/ndf or short hit count.
- Sparse-table fallback remains allowed (plan 24 §7).

## 4. Improvement candidates (for plan 49)

| Candidate | Method | Pros |
|---|---|---|
| **Mean of projections** (current) | average | simple |
| **Billoir χ² fit** | covariance-weighted χ² minimisation | proper uncertainty per axis; downweights bad tracks |
| **Adaptive vertex fit (Kalman)** | iterative outlier-aware | robust to mismeasured tracks |

Plan 38 ladder leaf V.4 scores each on signal sample (plan 20).

## 5. Foil-acceptance gate (V.5)

Class A: a vertex is foil-compatible iff
`sqrt(Vx² + Vy²) ≤ foil_outer_radius` AND `|Vz| ≤ foil_half_thickness`
with the geometry constants from plan 16.

## 6. Closure (plan 40 §2)

Pull distributions on `sig_foil_v3`:

- pull_z = `(z_reco - z_true) / σ_z_reco` — `\|μ\| < 0.1`,
  width ∈ [0.9, 1.1].
- pull_r — same.

## 7. Acceptance criteria

- §3 migration complete.
- §4 ladder benchmark recorded.
- §6 closure passes.

## 8. Dependencies

- **16, 17, 24, 25, 26, 38, 40** — inputs.
- *Consumed by:* plans 33 (photon direction needs vertex), 36
  (event variables), 38 (ladder), 47.
