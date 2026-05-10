---
id: 08_3_reconstruction_objects
title: Reconstruction atomic walkthrough — vertex, charged objects, photons, and pi0
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough, 01_realism_contract, 09_io_schema_data_dictionary]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/reconstruction.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_3_reconstruction_objects.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# Reconstruction core objects — split from plan 08

This split file preserves and deepens plan 08 §§3.3–3.5 so the main
walkthrough stays below the 500-line cap.

### 3.3 Vertex reconstruction

#### 3.3.1 Helper: `_is_pion_proton_candidate_track(group)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/reconstruction.py:691–698`.

**Inputs:** one TPC track group. It reads `Name` when present; plan 09
classifies TPC `Name` as Class B truth (`docs/rebuild_plans/09_io_schema_data_dictionary.md:151–155`).
If `Name` is absent or all labels are missing, the helper returns true
and lets the geometric projection path run (`reconstruction.py:691–696`).

**Decision rule:** keep a labelled group only when any label is one of
`pi+`, `pi-`, `charged_pion`, `proton`, or `antiproton`
(`reconstruction.py:697–698`). This is a Class B exclusion of EM,
neutral, neutrino, and fragment tracks in the current baseline.

**Outputs:** boolean keep/drop flag.

**Truth reads:** `Name` (Class B). This is one of the current
truth-labelled reconstruction exclusions tracked by plan 08 §3.7.

#### 3.3.2 `reconstruct_event_vertices(tpc)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/reconstruction.py:1221–1313`.

**Inputs:** the TPC hit table. Required columns are `Event_ID`,
`Track_ID`, `x`, `y`, and `z` (`reconstruction.py:1234–1236`). Plan 09
classifies `Event_ID` as Class A, `Track_ID` as Class B Geant4 track
identity, and hit `x/y/z` as Class A position with limitation L1
(`docs/rebuild_plans/09_io_schema_data_dictionary.md:151–159`). Optional
`t` is Class A timing with limitation L2 and enables vertex-time
projection (`plan 09:159`; `reconstruction.py:1240–1244`, `1252–1257`).
Optional `Name` is read only through `_is_pion_proton_candidate_track` as
Class B truth filtering (§3.3.1).

**Decision rule:** empty/missing required columns return an empty vertex
table with the output schema (`reconstruction.py:1224–1236`). Otherwise
hits are sorted by event, track, optional time, and original row order
(`reconstruction.py:1238–1244`). For each `(Event_ID, Track_ID)` group,
non-pion/proton truth-labelled tracks are skipped without entering the
projection counters (`reconstruction.py:1246–1250`). Numeric finite
positions are required; groups with fewer than two valid points increment
`n_skipped_tracks` for that event (`reconstruction.py:1251–1260`). The
track line is `start = first valid hit`, `stop = last valid hit`,
`direction = stop - start`; a non-finite direction or `abs(direction[2]) <
1.0e-12` is skipped because it cannot project to the foil plane
(`reconstruction.py:1262–1267`). The projection scale is
`-start[2] / direction[2]`, giving `vertex = start + scale * direction`
with `projected_z = 0.0` (`reconstruction.py:1269–1287`). If two finite
hit times exist, projected time is linearly interpolated with the same
scale (`reconstruction.py:1271–1273`). Non-finite projected vertices are
skipped (`reconstruction.py:1274–1276`).

Per event, the reconstructed vertex is the mean of projected `x/y`, with
`vertex_z = 0.0`; `vertex_time_ns` is the mean finite projected time;
`vertex_radial_spread` is the RMS transverse spread around the mean;
`n_projected_tracks` counts accepted projections; `n_skipped_tracks`
comes from failed projection attempts (`reconstruction.py:1292–1313`).

**Outputs:** DataFrame columns exactly as declared in code:
`event_id`, `vertex_x`, `vertex_y`, `vertex_z`, `vertex_time_ns`,
`vertex_radial_spread`, `n_projected_tracks`, and `n_skipped_tracks`
(`reconstruction.py:1224–1233`). Plan 09 §14.1 documents the same vertex
surface concept but still names older aliases (`vertex_radial_rms`,
`n_tracks_used`, `n_tracks_skipped`); the source code is authoritative
for the current output names.

**Truth reads:** `Name` through `_is_pion_proton_candidate_track` and
`Track_ID` for grouping are Class B in plan 09. The geometric projection
itself uses Class A `x/y/z` and optional `t`.

### 3.4 Charged-object reconstruction (lines ≈ 430–700)

`reconstruct_charged_objects(tpc, scintillator, config)` is called by
`reconstruct_run` and by `calibration.py`'s
`scan_charged_pid_thresholds`.

Behaviour per `reconstruction.md`:

- Builds candidates only from TPC tracks whose simulation truth name
  is `pi+`, `pi-`, `proton`, or `antiproton`. Other truth labels are
  not assigned PID. **This is a Class B read in the current code path
  — flagged by the realism audit (plan 01 §4) and tracked as a
  required cleanup; see §3.7 for the migration plan.**
- Direction is reconstructed from the ordered TPC hit positions
  (`_track_anchor_and_direction`) when ≥ 2 valid coords are present;
  falls back to mean momentum direction otherwise.
- Scintillator hits are matched to a track by either
  (i) angular-and-distance match (track-ray vs hit position) when
  detector coordinates are available, or (ii) exact `Track_ID`
  matching for sparse legacy tables. Constants from
  `ReconstructionConfig`.
- PID rules:
  - `dedx >= proton_dedx_min` ⇒ proton, *or*
  - `0 < scintillator_range <= short_range_cm AND dedx >=
    short_range_proton_dedx_min` ⇒ proton.
  - Else: charged pion.
- Output columns include `pid` ∈ {proton, charged_pion}, `dedx`,
  `scintillator_range`, `track_anchor`, `track_direction`,
  `truth_name` (Class B, retained for validation).

### 3.5 Photon / π⁰ reconstruction (lines ≈ 700–1300)

The photon-object pipeline is documented at length in
`reconstruction.md` lines 88–155. Atomic steps:

1. *Lead-glass cluster grouping by truth ancestry.* Currently uses
   `Parent_ID` chains and the optional `Interaction` truth table to
   resolve descendant shower particles back to their gamma ancestor
   (`reconstruction.md` line 142–144). This is a heavy Class B read
   path that plan 26 (calorimeter clustering) must replace with a
   geometric/topological clustering algorithm.
2. *Charged/neutral discriminant.* TPC tracks are grouped into
   reconstructed candidates whose direction is taken from the event
   vertex toward the farthest TPC hit. A lead-glass cluster is
   tagged charged when its vertex-to-centroid direction falls inside
   `charged_cluster_match_angle_deg` (default 10.5°). Charged
   matches must also satisfy `charged_cluster_match_time_tolerance_ns`
   when timing is available. Class A path; the truth `Track_ID` is
   only stored as `source_track_id` for provenance.
3. *Photon merging.* Truth-labelled neutral gamma fragments with
   nearly identical reconstructed directions are merged before π⁰
   pairing (`photon_fragment_merge_angle_deg`, default 2°). The
   truth labels here are Class B; plan 26 audits whether merging
   can be moved to a geometric-only criterion.
4. *Photon four-vector.* Direction = vertex → shower centroid (when
   a vertex exists; else origin → centroid as legacy fallback).
   Energy = lead-glass eDep + scintillator eDep from gamma-shower
   descendants (resolved through ancestry). Plan 28 owns the per-leaf
   improvements.
5. *π⁰ pairing.* All photon pairs are formed; per pair the invariant
   mass, opening angle, and total energy are computed. The
   `passes_*` columns capture the thesis Ch 8 selection windows
   individually plus the strict `passes_selection`.
6. *π⁰ provenance columns.* Each π⁰ candidate carries
   `source_track_ids` (alias list), `truth_charge_match_class`,
   `selection_failure_reasons`, and pi0 timing diagnostics. These are
   *diagnostic / validation* columns marked with the
   `@diagnostic_only` decorator under plan 01.
