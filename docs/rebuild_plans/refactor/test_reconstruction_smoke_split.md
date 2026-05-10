# `tests/test_reconstruction_smoke.py` split plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` and
> `test-driven-development` before implementing this plan after human
> approval. This file is a plan only; do not move tests in this lane
> iteration.

**Goal:** Split the remaining over-limit reconstruction smoke test into
reviewable, topic-owned test files without changing reconstruction
behavior.

**Current state:** In
`/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3`,
`tests/test_reconstruction_smoke.py` is 533 lines by `wc -l`, which
violates `CODING_STANDARDS.md` section 1. The production
`nnbar_reconstruction/reconstruction.py` facade is already below the
500-line cap in the L3 branch, so this plan only covers the actual
remaining Python test-file violation.

**Non-goal:** Do not change reconstruction algorithms, thresholds,
fixture values, assertions, imports, or public APIs. The implementation
is mechanical extraction plus shared helper placement.

---

## Constraints

- Preserve every current assertion exactly unless a moved import needs
  a local path adjustment.
- Keep each target test file below 250 lines; hard cap remains 500
  lines by `CODING_STANDARDS.md` section 1.
- Run `pytest tests/test_reco_*.py tests/test_reconstruction_io.py -x
  --tb=short` after the split, then full `pytest tests/ -x --tb=short`.
- Commit only the split and any helper module needed by these tests.
- If any behavior changes, stop and add a real decision-log entry before
  continuing.

---

## Current test inventory

| Current citation | Responsibility | Target file |
|---|---|---|
| `_write` (`tests/test_reconstruction_smoke.py:19-21`) | Parquet fixture writer | `tests/reconstruction_fixtures.py` |
| `test_discover_runs_ignores_macos_sidecars` (`tests/test_reconstruction_smoke.py:24-31`) | I/O discovery and sidecar filtering | `tests/test_reconstruction_io.py` |
| `test_charged_pid_uses_dedx_and_range` (`tests/test_reconstruction_smoke.py:34-55`) | charged PID smoke behavior | `tests/test_reco_charged_pid.py` |
| `test_charged_direction_uses_tpc_hit_geometry_before_momentum_columns` (`tests/test_reconstruction_smoke.py:58-97`) | charged direction geometry precedence | `tests/test_reco_charged_pid.py` |
| `test_charged_scintillator_energy_uses_geometry_not_truth_track_id` (`tests/test_reconstruction_smoke.py:100-143`) | truth-blind scintillator matching | `tests/test_reco_charged_pid.py` |
| `test_pi0_candidate_uses_thesis_selection_cuts` (`tests/test_reconstruction_smoke.py:146-160`) | pi0 mass and selection smoke | `tests/test_reco_photon_pi0.py` |
| `test_electron_pair_candidates_use_tpc_entry_point_separation` (`tests/test_reconstruction_smoke.py:163-180`) | e+/e- entry separation | `tests/test_reco_vertex_timing.py` |
| `test_event_vertex_projects_tpc_tracks_back_to_source_foil` (`tests/test_reconstruction_smoke.py:183-205`) | vertex projection smoke | `tests/test_reco_vertex_timing.py` |
| `test_timing_windows_filter_scintillator_and_leadglass_hits_from_vertex` (`tests/test_reconstruction_smoke.py:208-276`) | timing-window annotation and summary fields | `tests/test_reco_vertex_timing.py` |
| `test_photon_directions_use_reconstructed_vertex_for_pi0_mass` (`tests/test_reconstruction_smoke.py:279-360`) | photon directions and pi0 mass from vertex | `tests/test_reco_photon_pi0.py` |
| `test_photon_charged_match_uses_geometry_not_truth_track_id` (`tests/test_reconstruction_smoke.py:363-395`) | truth-blind charged/neutral match | `tests/test_reco_photon_pi0.py` |
| `test_reconstruct_run_writes_expected_tables` (`tests/test_reconstruction_smoke.py:398-441`) | top-level output table contract | `tests/test_reco_pipeline_events.py` |
| `test_preliminary_selection_uses_thesis_cutflow` (`tests/test_reconstruction_smoke.py:444-498`) | preliminary selection flags | `tests/test_reco_pipeline_events.py` |
| `test_event_summary_includes_thesis_calorimeter_directional_variables` (`tests/test_reconstruction_smoke.py:501-533`) | event-level calorimeter variables | `tests/test_reco_pipeline_events.py` |

---

## Target module budgets

| Target file | Planned contents | Budget |
|---|---|---:|
| `tests/reconstruction_fixtures.py` | `_write` plus any future shared dataframe helpers | 80 |
| `tests/test_reconstruction_io.py` | I/O discovery and load smoke tests | 90 |
| `tests/test_reco_charged_pid.py` | charged-object PID, direction, and scintillator-match tests | 190 |
| `tests/test_reco_vertex_timing.py` | electron-pair, vertex, and timing-window tests | 220 |
| `tests/test_reco_photon_pi0.py` | photon object, charged-match, and pi0 tests | 230 |
| `tests/test_reco_pipeline_events.py` | reconstruct-run table, selection, and event-variable tests | 230 |

---

## Decision-log entry stub

`DEC-2026-05-10-L3-test-smoke-split`

- **Title:** Behavior-preserving split of reconstruction smoke tests.
- **Status:** proposed only if reviewers decide test-file extraction
  needs a decision record.
- **Context:** `tests/test_reconstruction_smoke.py` is 533 lines and
  mixes I/O, charged, photon/pi0, vertex/timing, and event-summary
  responsibilities.
- **Decision:** Extract topic-owned test files while preserving all
  assertions and fixture data exactly.
- **Non-decisions:** No production behavior, threshold, selection,
  schema, or algorithm changes.
- **Validation:** Targeted split tests pass, then full `pytest tests/ -x
  --tb=short` passes.

---

## Execution tasks

### Task 1: Extract shared fixture helper

1. Create `tests/reconstruction_fixtures.py` containing `_write`.
2. Import `_write` from the new helper in the moved test files.
3. Do not add broad fixture factories until a moved test demonstrates
   duplication after extraction.

### Task 2: Move I/O and charged-object smoke tests

1. Create `tests/test_reconstruction_io.py` with the sidecar discovery
   test.
2. Create `tests/test_reco_charged_pid.py` with the three charged
   tests.
3. Run `pytest tests/test_reconstruction_io.py
   tests/test_reco_charged_pid.py -x --tb=short`.

### Task 3: Move vertex and timing smoke tests

1. Create `tests/test_reco_vertex_timing.py` with the electron-pair,
   vertex-projection, and timing-window tests.
2. Run `pytest tests/test_reco_vertex_timing.py -x --tb=short`.

### Task 4: Move photon and pi0 smoke tests

1. Create `tests/test_reco_photon_pi0.py` with the pi0 candidate,
   vertex-direction photon, and truth-blind charged-match tests.
2. Run `pytest tests/test_reco_photon_pi0.py -x --tb=short`.

### Task 5: Move pipeline and event-summary smoke tests

1. Create `tests/test_reco_pipeline_events.py` with the reconstruct-run,
   preliminary-selection, and event-variable tests.
2. Remove `tests/test_reconstruction_smoke.py` once all tests are moved.
3. Run `pytest tests/test_reco_*.py tests/test_reconstruction_io.py -x
   --tb=short`.
4. Run full `pytest tests/ -x --tb=short`.
5. Confirm every touched test file is below 500 lines by `wc -l`.
