# `nnbar_reconstruction/reconstruction.py` split plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task in a reviewed feature branch after user approval.

**Goal:** Split `nnbar_reconstruction/reconstruction.py` into reviewable modules under the 500-line rule without changing reconstruction behavior.

**Current state:** In `/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3`, `nnbar_reconstruction/reconstruction.py` is 1062 lines. The large sibling files named in the L3 note (`pi0_study.py`, `charged_study.py`) are not present in this worktree, so this plan covers the actual over-limit file found here. Existing `tests/test_reconstruction_smoke.py` is also 533 lines and should be split during the same refactor series.

**Architecture:** Keep the public API import-compatible through `nnbar_reconstruction/reconstruction.py` as a thin facade. Move behavior into one-responsibility modules under a new `nnbar_reconstruction/reco/` package. Each move is extraction-only: copy tests first, move functions, update imports, and verify identical existing tests before the next extraction.

**Tech stack:** Python, pandas, numpy, pytest. No new dependencies.

---

## Constraints

- Preserve public imports from `nnbar_reconstruction.reconstruction` until downstream callers migrate.
- Do not change numerical thresholds, algorithms, feature definitions, or selection rules in the split commits.
- Any unavoidable behavior change stops the split and requires a decision-log entry before implementation.
- Keep every new source and test file below 500 lines, targeting 200-300 lines.
- Run `pytest tests/test_reconstruction_*.py -x --tb=short` after every extraction and full `pytest tests/ -x --tb=short` before final commit.

## Current function inventory

| Lines | Symbol | Proposed module |
|---:|---|---|
| 17-51 | `ReconstructionConfig` | `nnbar_reconstruction/reco/config.py` |
| 57-64 | `_empty`, `_safe_sum` | `nnbar_reconstruction/reco/table_utils.py` |
| 67-83 | `_pmt_photons_for_event` | `nnbar_reconstruction/reco/event_variables.py` |
| 86-178 | `_unit_vector`, `_weighted_centroid`, `_angle_between_deg`, `_span`, `_track_direction_from_hits`, `_track_anchor_and_direction`, `_position_coordinates` | `nnbar_reconstruction/reco/geometry.py` |
| 181-223 | `_select_scintillator_hits_for_track` | `nnbar_reconstruction/reco/charged.py` |
| 226-246 | `_directional_energy` | `nnbar_reconstruction/reco/event_variables.py` |
| 249-340 | `_beta_from_kinetic_energy`, `_false_timing_annotation`, `annotate_timing_windows` | `nnbar_reconstruction/reco/timing.py` |
| 343-429 | `_has_foil_origin`, `reconstruct_charged_objects` | `nnbar_reconstruction/reco/charged.py` |
| 432-573 | `reconstruct_photon_objects` | `nnbar_reconstruction/reco/photons.py` |
| 576-681 | `_electron_charge_sign`, `reconstruct_electron_pair_objects` | `nnbar_reconstruction/reco/electron_pairs.py` |
| 684-774 | `reconstruct_event_vertices` | `nnbar_reconstruction/reco/vertices.py` |
| 777-836 | `find_pi0_candidates` | `nnbar_reconstruction/reco/pi0.py` |
| 839-874 | `_sphericity`, `_visible_invariant_mass` | `nnbar_reconstruction/reco/event_variables.py` |
| 877-903 | `_selection_flags` | `nnbar_reconstruction/reco/selection.py` |
| 906-1032 | `summarize_events` | `nnbar_reconstruction/reco/event_variables.py` |
| 1035-1062 | `reconstruct_run` | `nnbar_reconstruction/reco/pipeline.py` |

## Target module budgets

| Target file | Responsibility | Planned public/private symbols | Budget |
|---|---|---|---:|
| `nnbar_reconstruction/reco/__init__.py` | Package exports | none or explicit convenience exports | 40 |
| `nnbar_reconstruction/reco/config.py` | Reconstruction constants/config | `ReconstructionConfig`, `DEFAULT_CONFIG` | 90 |
| `nnbar_reconstruction/reco/table_utils.py` | DataFrame scalar/table helpers | `_empty`, `_safe_sum` | 80 |
| `nnbar_reconstruction/reco/geometry.py` | Vector and geometric primitives | `_unit_vector`, `_weighted_centroid`, `_angle_between_deg`, `_span`, `_track_direction_from_hits`, `_track_anchor_and_direction`, `_position_coordinates` | 180 |
| `nnbar_reconstruction/reco/timing.py` | Chapter 7 timing windows | `_beta_from_kinetic_energy`, `_false_timing_annotation`, `annotate_timing_windows` | 160 |
| `nnbar_reconstruction/reco/charged.py` | TPC/scintillator charged objects | `_select_scintillator_hits_for_track`, `_has_foil_origin`, `reconstruct_charged_objects` | 190 |
| `nnbar_reconstruction/reco/photons.py` | Lead-glass photon-like objects | `reconstruct_photon_objects` plus local matching helpers if needed | 220 |
| `nnbar_reconstruction/reco/electron_pairs.py` | e+/e- TPC-entry candidates | `_electron_charge_sign`, `reconstruct_electron_pair_objects` | 160 |
| `nnbar_reconstruction/reco/vertices.py` | Foil-plane vertex projection | `reconstruct_event_vertices` | 170 |
| `nnbar_reconstruction/reco/pi0.py` | π0 pairing and selection cuts | `find_pi0_candidates` | 140 |
| `nnbar_reconstruction/reco/selection.py` | Preliminary event selection flags | `_selection_flags` | 100 |
| `nnbar_reconstruction/reco/event_variables.py` | Event-level summaries and observables | `_pmt_photons_for_event`, `_directional_energy`, `_sphericity`, `_visible_invariant_mass`, `summarize_events` | 260 |
| `nnbar_reconstruction/reco/pipeline.py` | Top-level run orchestration | `reconstruct_run` | 100 |
| `nnbar_reconstruction/reconstruction.py` | Backwards-compatible facade | re-export existing public API | 120 |

## Test split budget

| Current test file | New files | Target |
|---|---|---|
| `tests/test_reconstruction_smoke.py` (533 lines) | `tests/test_reco_charged.py`, `tests/test_reco_photons_pi0.py`, `tests/test_reco_vertices_timing.py`, `tests/test_reco_pipeline_events.py` | each < 250 lines |
| `tests/test_reconstruction_validation.py` (262 lines) | unchanged unless imports become unclear | < 500 lines |

## Decision-log entry stub

`DEC-2026-05-10-L3-reco-split`

- **Title:** Behavior-preserving split of `nnbar_reconstruction/reconstruction.py`.
- **Status:** proposed.
- **Context:** `reconstruction.py` violates the 500-line rule and mixes config, geometry, timing, object reconstruction, event variables, selection, and pipeline orchestration.
- **Decision:** Extract one-responsibility modules under `nnbar_reconstruction/reco/` while retaining `nnbar_reconstruction.reconstruction` as the compatibility facade.
- **Non-decisions:** No numerical threshold changes, no algorithm replacements, no MVA feature changes, no dependency changes.
- **Validation:** Existing reconstruction tests pass before and after every extraction; full test suite passes before merge.

## Execution tasks

### Task 1: Add the package shell and config extraction

**Files:**
- Create: `nnbar_reconstruction/reco/__init__.py`
- Create: `nnbar_reconstruction/reco/config.py`
- Modify: `nnbar_reconstruction/reconstruction.py`
- Test: existing reconstruction tests

**Steps:**
1. Move `ReconstructionConfig` and `DEFAULT_CONFIG` into `reco/config.py`.
2. Import and re-export them from `reconstruction.py`.
3. Run `pytest tests/test_reconstruction_*.py -x --tb=short`.
4. Commit only config/package/facade changes.

### Task 2: Extract table and geometry helpers

**Files:**
- Create: `nnbar_reconstruction/reco/table_utils.py`
- Create: `nnbar_reconstruction/reco/geometry.py`
- Modify: `nnbar_reconstruction/reconstruction.py`

**Steps:**
1. Move `_empty`, `_safe_sum`, and vector/geometry helpers.
2. Update imports in `reconstruction.py`.
3. Run `pytest tests/test_reconstruction_*.py -x --tb=short`.
4. Commit helper extraction.

### Task 3: Extract timing and vertex modules

**Files:**
- Create: `nnbar_reconstruction/reco/timing.py`
- Create: `nnbar_reconstruction/reco/vertices.py`
- Modify: `nnbar_reconstruction/reconstruction.py`
- Optional test split: `tests/test_reco_vertices_timing.py`

**Steps:**
1. Move timing-window helpers and `annotate_timing_windows`.
2. Move `reconstruct_event_vertices`.
3. Split timing/vertex tests out of `test_reconstruction_smoke.py` if the test file remains over 500 lines.
4. Run targeted and full reconstruction tests.
5. Commit timing/vertex extraction.

### Task 4: Extract charged and electron-pair modules

**Files:**
- Create: `nnbar_reconstruction/reco/charged.py`
- Create: `nnbar_reconstruction/reco/electron_pairs.py`
- Modify: `nnbar_reconstruction/reconstruction.py`
- Optional test split: `tests/test_reco_charged.py`

**Steps:**
1. Move charged-object functions and imports.
2. Move electron-pair functions and imports.
3. Preserve existing truth-diagnostic columns exactly.
4. Run reconstruction tests.
5. Commit charged/electron extraction.

### Task 5: Extract photon and π0 modules

**Files:**
- Create: `nnbar_reconstruction/reco/photons.py`
- Create: `nnbar_reconstruction/reco/pi0.py`
- Modify: `nnbar_reconstruction/reconstruction.py`
- Optional test split: `tests/test_reco_photons_pi0.py`

**Steps:**
1. Move `reconstruct_photon_objects` and its dependencies.
2. Move `find_pi0_candidates`.
3. Keep selection failure reason strings byte-for-byte stable.
4. Run reconstruction tests.
5. Commit photon/π0 extraction.

### Task 6: Extract event variables, selection, and pipeline facade

**Files:**
- Create: `nnbar_reconstruction/reco/event_variables.py`
- Create: `nnbar_reconstruction/reco/selection.py`
- Create: `nnbar_reconstruction/reco/pipeline.py`
- Modify: `nnbar_reconstruction/reconstruction.py`
- Optional test split: `tests/test_reco_pipeline_events.py`

**Steps:**
1. Move event-variable helpers and `summarize_events`.
2. Move `_selection_flags`.
3. Move `reconstruct_run` to `reco/pipeline.py`.
4. Reduce `reconstruction.py` to a compatibility facade with imports and `__all__`.
5. Run `wc -l nnbar_reconstruction/reconstruction.py nnbar_reconstruction/reco/*.py tests/test_reco_*.py tests/test_reconstruction_*.py`.
6. Run `pytest tests/ -x --tb=short`.
7. Commit final facade/pipeline extraction.

## Final acceptance checklist

- `nnbar_reconstruction/reconstruction.py` is below 500 lines and only re-exports public API.
- Every new `nnbar_reconstruction/reco/*.py` file is below 500 lines.
- Split test files are below 500 lines.
- `pytest tests/ -x --tb=short` passes.
- No numerical or algorithmic diff is introduced without a signed DEC update.
