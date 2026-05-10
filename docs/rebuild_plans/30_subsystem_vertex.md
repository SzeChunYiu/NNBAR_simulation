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
  - {test: vertex z and r residuals on sig_foil_500MeV_v3 within plan 40 §2 tolerance, method: closure plot, pass_when: pass}
  - {test: Billoir χ² fit benchmarked vs mean-of-projections on ladder leaf V.4, method: plan 38, pass_when: matrix entry recorded}
  - {test: foil-acceptance gate uses geometry from plan 16 (no truth), method: plan 01 audit, pass_when: zero violations}
risks:
  - {risk: only modules 0/1 are field-managed (plan 17 §1) → unfielded modules contribute biased projections, mitigation: §4 per-module weighting + alignment scenario as systematic}
estimated_effort: M
last_updated: 2026-05-10
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

### 1.1 Leaf schema block — V.3 foil projection

- **inputs (Class A):** V.2 direction rows, anchor coordinates,
  direction covariance, track quality, and plan 16 foil-plane geometry.
- **forbidden (Class B):** `Track_ID`, `Parent_ID`, `Name`,
  `origin_vol_name`, `particle_x`, `particle_y`, `particle_z`, truth
  `Vx`, truth `Vy`, truth `Vz`.
- **decision rule:** project each reconstructed track to the signed
  foil plane using Class A track state and geometry only; mark tracks
  invalid when the projection is parallel, ill-conditioned, or outside
  the configured geometry envelope.
- **output schema:** `event_id: int`, `candidate_id: int`,
  `projection_xyz: float[3]`, `projection_covariance: float[3,3]`,
  `projection_valid: bool`, `skipped_reason: str | null`,
  `source_chi2_ndf: float`.
- **allowed truth use:** `validation_only` for projection residual
  plots and ladder scoring after projection output is frozen.
- **downstream consumers:** V.4, V.5, plans 33, 36, 38, 40, and 47.

### 1.2 Leaf schema block — V.4 vertex aggregation

- **inputs (Class A):** V.3 projection rows, projection covariance,
  track quality fields, and reconstructed candidate multiplicity.
- **forbidden (Class B):** truth primary vertices, truth interaction
  vertices, `Track_ID`, `Parent_ID`, `Name`, and truth origin labels.
- **decision rule:** aggregate valid Class A projections with the
  signed mean, covariance-weighted, or adaptive fitter; truth-labelled
  seed exclusions are forbidden in production.
- **output schema:** `event_id: int`, `vertex_xyz: float[3]`,
  `vertex_covariance: float[3,3]`, `n_tracks_used: int`,
  `n_tracks_skipped: int`, `radial_rms_mm: float`,
  `aggregation_method: str`, `vertex_valid: bool`.
- **allowed truth use:** `validation_only` for vertex residuals, pull
  widths, and plan 38 ladder rows.
- **downstream consumers:** V.5, plans 33, 36, 38, 40, 43, and 47.

### 1.3 Leaf schema block — V.5 foil acceptance

- **inputs (Class A):** V.4 vertex rows, vertex covariance, plan 16
  foil radius, foil half-thickness, and geometry/alignment version.
- **forbidden (Class B):** truth primary vertices, truth interaction
  vertices, `Track_ID`, `Parent_ID`, `Name`, and truth origin labels.
- **decision rule:** accept an event as foil-compatible only from the
  reconstructed vertex and plan 16 geometry constants; no truth-origin
  label may enter the acceptance gate.
- **output schema:** `event_id: int`, `foil_compatible: bool`,
  `vertex_valid: bool`, `vertex_r_mm: float`, `vertex_z_mm: float`,
  `foil_geometry_version: str`, `acceptance_reason: str`.
- **allowed truth use:** `validation_only` for acceptance efficiency
  and closure plots after the V.5 gate output is frozen.
- **downstream consumers:** plans 36, 38, 41, 43, 45, and 47.

Current implementation citation: the vertex path is implemented by
`reconstruct_event_vertices` (`vertex.py:163-254`; plan 08 §3.3).
It projects valid tracks to `z=0`, averages projections,
reports radial RMS / skipped counts, and currently excludes some seeds
with truth `Name`.

### 1.4 Machine-readable vertex fixtures

The vertex path is split into three fixtures so projection, aggregation,
and foil acceptance can be closure-tested without leaking truth
vertices into production decisions:

| Fixture | Required fields | Production invariant |
|---|---|---|
| V.3 projection | `event_id`, `candidate_id`, `projection_x`, `projection_y`, `projection_z`, covariance components, `projection_valid`, `skipped_reason`, `source_chi2_ndf` | depends only on V.2 state and plan 16 geometry |
| V.4 vertex | `event_id`, `vertex_x`, `vertex_y`, `vertex_z`, covariance components, `n_tracks_used`, `n_tracks_skipped`, `radial_rms_mm`, `aggregation_method`, `vertex_valid` | truth vertices and truth names are absent from aggregation input |
| V.5 foil acceptance | `event_id`, `foil_compatible`, `vertex_valid`, `vertex_r_mm`, `vertex_z_mm`, `foil_geometry_version`, `acceptance_reason` | uses plan 16 geometry and plan 60 fiducial profile, not truth origin |

Projection residuals, vertex pulls, and truth foil-origin labels are
written only to closure artifacts keyed by `(event_id,
aggregation_method, foil_geometry_version)`. The production V.5 fixture
is valid only when its consumed V.3/V.4 fixture hashes and geometry tag
match the manifest used by plan 43 signal efficiency.

## 2. Current implementation

`vertex.py` (plan 08 §3.3):

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


### 4.1 Alternative comparison rows

| Alternative | Source paper / codebase | NNBAR-specific adaptation | Expected ladder leaf delta |
|---|---|---|---|
| Mean of projections | Existing `reconstruct_event_vertices` (`vertex.py:163-254`) | Preserve as reproduction baseline; use V.3 projection validity and no truth-name seed exclusion after migration. | Baseline V.4 result; simple but no covariance weighting. |
| Billoir χ² fit | Billoir-style covariance-weighted vertex fit | Use V.2/V.3 covariance matrices and plan 16 foil geometry; downweight high-χ² tracks. | Expected to reduce vertex r/z pull width and improve V.5 foil compatibility stability. |
| Adaptive vertex fit | Kalman/adaptive robust vertex literature | Iterate weights to suppress outlier tracks from secondary interactions or EM conversions. | Potentially best V.4 robustness in shower-rich signal events; higher tuning burden before plan 38 scoring. |

Plan 38 ladder leaf V.4 scores each on signal sample (plan 20).

## 5. Foil-acceptance gate (V.5)

Class A: a vertex is foil-compatible iff
`sqrt(Vx² + Vy²) ≤ foil_outer_radius` AND `|Vz| ≤ foil_half_thickness`
with the geometry constants from plan 16.

## 6. Closure-test specification (plan 40 §2)

1. **Dataset id:** `sig_foil_500MeV_v3` from plan 03.
2. **Observable:** V.3 projection residuals, V.4 vertex `z` and `r`
   residuals, and V.5 foil-compatible acceptance efficiency.
3. **Fitter / matcher:** run the candidate vertex aggregator (mean,
   Billoir χ², or adaptive fit) and compute residuals against truth
   vertices only in a `@validation_only` closure function.
4. **Pass criterion:** `pull_z = (z_reco - z_true) / sigma_z_reco`
   and `pull_r` both have `|mu| < 0.1` and width in `[0.9, 1.1]`;
   the foil-acceptance gate must use plan 16 geometry constants, not
   truth origin labels.

## 7. Stage E.1 implementation handoff

The legacy reproduction hook is `reconstruct_event_vertices`
(`vertex.py:163-252`). It remains useful for comparing against older
event-level V.4 coordinates, but it groups by `Track_ID` and is no
longer the preferred plan-30 fixture surface.

The live Stage E.1 fixture hooks are now split in `vertex_reco.py`:
`project_tracks_to_foil` (`vertex_reco.py:45-87`) writes V.3
projection rows, `aggregate_event_vertices` (`vertex_reco.py:90-132`)
writes V.4 event vertices and covariance, and `apply_foil_acceptance`
(`vertex_reco.py:157-194`) writes the V.5 foil gate from
`FoilGeometry` (`vertex_reco.py:13-18`). The corresponding regression
coverage lives in `tests/test_vertex_reco.py`: V.3 schema/projection
rows at `test_project_tracks_to_foil_emits_plan_30_v3_rows`
(`tests/test_vertex_reco.py:39-74`), geometry-only V.4/V.5 acceptance
at `test_aggregate_and_accept_vertices_use_plan_16_geometry_only`
(`tests/test_vertex_reco.py:77-100`), and a real-sample smoke path at
`test_vertex_reco_real_sample_consumes_particle_and_tpc_rows`
(`tests/test_vertex_reco.py:103-118`).

Plan-side gates for the L3 implementation:

1. Consume V.2 fit rows and plan 16 geometry through the split
   Stage E.1 hooks instead of reopening raw `Track_ID` groupings.
2. Keep the separate V.3, V.4, and V.5 fixtures aligned with the §1.4
   fields and add hashes of the consumed V.2 fit table and geometry
   side-car before plan 47 consumes them.
3. Preserve the mean-of-projections result as a named reproduction
   mode; any Billoir or adaptive fitter promotion needs a plan 38 V.4
   ladder row and a plan 05 decision entry.
4. Keep truth vertices and truth origin labels out of production V.3,
   V.4, and V.5 rows. They may appear only in closure artifacts after
   the production fixtures are frozen.
5. Extend `tests/test_vertex_reco.py` so dropping `Name`, `Track_ID`,
   and truth vertex columns cannot change the production V.5
   foil-acceptance decision.
6. Plan 60 consumes `foil_geometry_version`, vertex edge distances,
   and fiducial-profile states once the V.5 fixture is present.

## 8. Acceptance criteria

- §3 migration complete.
- §4 ladder benchmark recorded.
- §6 closure passes.
- §7 Stage E.1 handoff is actionable for L3: the legacy reproduction
  hook, split V.3/V.4/V.5 fixture hooks, and vertex-reco regression
  tests are cited; the fixtures remain split from closure artifacts;
  and vertex-reco tests must prove the foil gate is invariant to
  dropping Class B truth columns.

## 9. Dependencies

- **16, 17, 24, 25, 26, 38, 40** — inputs.
- *Consumed by:* plans 33 (photon direction needs vertex), 36
  (event variables), 38 (ladder), 47.
