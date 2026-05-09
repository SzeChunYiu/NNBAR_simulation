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
  - {risk: only modules 0/1 are field-managed (plan 17 §1) → unfielded modules contribute biased projections, mitigation: §3 per-module weighting + alignment scenario as systematic}
estimated_effort: M
last_updated: 2026-05-09
---

# Subsystem — event vertex

*Charter.* Owns leaves V.3 (foil projection), V.4 (aggregation),
V.5 (acceptance) of plan 24 §2.

## 1. Current implementation

`reconstruction.py` (plan 08 §3.3):

- For each charged candidate (TPC track from plan 25 V.1) with
  valid TPC entry/exit: project to `z=0` plane.
- Reported event vertex = mean of valid projections.
- Reports radial RMS spread; counts skipped (parallel / endpoints
  missing) tracks.
- Truth-labelled EM / neutral / neutrino / nuclear-fragment tracks
  are excluded from seeding (Class B exclusion — see §2 migration).
- Sparse legacy tables fall back to all geometrically-valid tracks.

## 2. Migration: drop the truth-labelled exclusion

The current implementation reads `Name` to drop EM and neutral
seeds. Migration:

- Class A replacement: drop tracks whose lead-glass cluster (matched
  geometrically) tags them as charged-EM (plan 29 §3 EM rejection).
- Drop tracks with low χ²/ndf or short hit count.
- Sparse-table fallback remains allowed (plan 24 §7).

## 3. Improvement candidates (for plan 49)

| Candidate | Method | Pros |
|---|---|---|
| **Mean of projections** (current) | average | simple |
| **Billoir χ² fit** | covariance-weighted χ² minimisation | proper uncertainty per axis; downweights bad tracks |
| **Adaptive vertex fit (Kalman)** | iterative outlier-aware | robust to mismeasured tracks |

Plan 38 ladder leaf V.4 scores each on signal sample (plan 20).

## 4. Foil-acceptance gate (V.5)

Class A: a vertex is foil-compatible iff
`sqrt(Vx² + Vy²) ≤ foil_outer_radius` AND `|Vz| ≤ foil_half_thickness`
with the geometry constants from plan 16.

## 5. Closure (plan 40 §2)

Pull distributions on `sig_foil_v3`:

- pull_z = `(z_reco - z_true) / σ_z_reco` — `\|μ\| < 0.1`,
  width ∈ [0.9, 1.1].
- pull_r — same.

## 6. Acceptance criteria

- §2 migration complete.
- §3 ladder benchmark recorded.
- §5 closure passes.

## 7. Dependencies

- **16, 17, 24, 25, 26, 38, 40** — inputs.
- *Consumed by:* plans 33 (photon direction needs vertex), 36
  (event variables), 38 (ladder), 47.
