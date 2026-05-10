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

### 3.3 Vertex reconstruction (located by section heading near reconstruction.py:200–~430)

The current vertex function, per `reconstruction.md`:

- Builds candidate charged tracks from TPC hits (per plan 07 §6.1,
  TPCSD writes only first/last steps in volume).
- For each candidate track with valid TPC entry/exit points,
  computes the projection to the foil plane `z = 0`.
- The reported event vertex is the *mean of valid track projections*
  (cf. licentiate Ch 7 description).
- Reports the RMS radial spread and the count of "skipped" tracks
  that could not project (parallel to foil, missing endpoints).
- Truth-labelled EM, neutral, neutrino, and nuclear-fragment tracks
  are excluded from vertex seeding (this is a Class B *exclusion*
  — see §3.7 for the policy).
- Sparse legacy tables without truth labels fall back to using all
  geometrically valid tracks.

Plan 25 takes this as the baseline; alternatives (Billoir χ², iterative
weighted projection) are evaluated against it.

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
