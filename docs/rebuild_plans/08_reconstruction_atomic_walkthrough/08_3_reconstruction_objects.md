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

### 3.4 Charged-object reconstruction

#### 3.4.1 Helper map for charged objects

- `_track_anchor_and_direction(group)` (`reconstruction.py:165–184`)
  orders TPC hits by `t` when present, otherwise by input order, and
  returns the first valid `x/y/z` point plus the unit vector from first to
  last valid point. It uses Class A positions/timing from plan 09 §8
  lines 151–159.
- `_track_direction_from_hits(group)` (`reconstruction.py:153–162`) uses
  `_track_anchor_and_direction`; if that fails, it falls back to mean
  `px/py/pz` momentum direction (Class A direction in plan 09 §8 line
  162), else a zero vector.
- `_select_scintillator_hits_for_track(...)` (`reconstruction.py:199–241`)
  first restricts to matching `Event_ID` when available, then geometrically
  matches scintillator positions to the TPC track ray. The hardcoded
  default limits come from `ReconstructionConfig`: distance ≤ 15.0 cm and
  angle ≤ 10.0° (`reconstruction.py:40–41`, `225–234`). If geometry is not
  available, it falls back to exact `(Event_ID, Track_ID)` matching
  (`reconstruction.py:236–240`), a Class B fallback because `Track_ID` is a
  Geant4 truth identifier in plan 09.
- `_span(points)` (`reconstruction.py:143–150`) computes the maximum pairwise
  distance across `particle_x/y/z`. Plan 09 classifies TPC `particle_x/y/z`
  as Class B truth (line 168); scintillator uses the same NNbarHit-derived
  schema (plan 09 §9 lines 182–195). Because charged PID uses this span as
  `scintillator_range`, the short-range PID branch currently carries a Class
  B dependency.
- `_has_foil_origin(group)` (`reconstruction.py:361–367`) returns true when
  missing `Origin` (legacy permissive path) or when `Origin` contains
  `Carbon`, `Target`, or `Foil`. `Origin` is truth/provenance-like metadata;
  it is emitted only as `has_foil_origin` diagnostic output here.

#### 3.4.2 `reconstruct_charged_objects(tpc, scintillator=None, config=DEFAULT_CONFIG)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/reconstruction.py:701–780`.

**Inputs:** TPC and optional scintillator hit tables. TPC grouping requires
`Event_ID` (Class A event id) and `Track_ID` (Class B Geant4 identifier;
plan 09 §8 lines 151–153). The charged-object calculation reads TPC
`Name` (Class B truth label), `eDep` (Class A energy deposit), lowercase
`trackl` for path length as implemented, `x/y/z`, optional `t`, optional
`px/py/pz`, and optional `Origin` (`reconstruction.py:735–776`).
Scintillator matching reads `Event_ID`, `Track_ID` fallback, `eDep`, and
position columns (`particle_x/y/z` preferred, else `x/y/z`) through the
helpers above (`reconstruction.py:187–241`, `744–746`; plan 09 §9 lines
182–195).

**Decision rule:** empty or `None` TPC returns an empty charged table with
the declared columns (`reconstruction.py:712–730`). For each
`(Event_ID, Track_ID)` TPC group, `_is_pion_proton_candidate_track` first
drops truth-labelled non-π/p tracks (`reconstruction.py:735–738`; see
§3.3.1). TPC path is the sum of `trackl`, TPC energy is the sum of `eDep`,
and `dedx = edep / path` when path > 0 else `NaN` (`reconstruction.py:739–742`).
Direction is reconstructed from hit geometry or momentum fallback. Matching
scintillator hits are selected by geometry or exact truth-id fallback;
`scintillator_edep` sums their `eDep`, and `scintillator_range` is the
`_span` of matched scintillator positions (`reconstruction.py:744–746`).

PID is a two-branch threshold rule. A candidate is labelled proton when
`dedx >= config.proton_dedx_min` (default 8.0), or when
`0 < scintillator_range <= config.short_range_cm` (default 20.0 cm) and
`dedx >= config.short_range_proton_dedx_min` (default 4.5); otherwise it
is labelled `charged_pion` (`reconstruction.py:748–758`). These defaults
come from `ReconstructionConfig` (`reconstruction.py:25–27`).

**Outputs:** DataFrame columns `event_id`, `track_id`, `truth_name`,
`n_tpc_hits`, `tpc_edep`, `tpc_path`, `dedx`, `scintillator_edep`,
`n_scintillator_hits`, `scintillator_range`, `px`, `py`, `pz`,
`pid_guess`, and `has_foil_origin` (`reconstruction.py:712–728`,
`760–780`). Plan 09 §14.2 records the charged table concept and flags
`truth_name` as diagnostic truth (`docs/rebuild_plans/09_io_schema_data_dictionary.md:274–280`).

**Truth reads:** `Name` gates which TPC tracks get charged PID;
`Track_ID` is used for grouping and as the sparse scintillator fallback;
`particle_x/y/z` drives scintillator range when present; and `Origin`
feeds `has_foil_origin`. Under plan 09 these are Class B or
truth/provenance-like fields, so the current charged-object baseline still
has truth-dependent paths tracked by plan 08 §3.7.

### 3.5 Photon / π⁰ reconstruction

This subsection is being deepened in logical units. The current entry covers
lead-glass/scintillator shower source resolution, charged/neutral photon-object
classification, and photon-fragment merging. The π⁰-pairing public function
`find_pi0_candidates` remains the next §3.5 unit.

#### 3.5.1 Shower-source and charged-match helpers

- `_leadglass_shower_sources(leadglass, interactions=None)`
  (`reconstruction.py:407–499`) attaches `_shower_source_track_id` and
  `_shower_truth_name` to lead-glass or scintillator deposits. Empty inputs
  receive empty source columns; sparse inputs without `Event_ID`, `Track_ID`,
  `Parent_ID`, and `Name` fall back to raw `Track_ID`/`Name` or row index
  (`reconstruction.py:413–421`). With lineage columns, it builds maps from
  the calorimeter table plus optional `Interaction` table and walks EM
  ancestry so gamma/e±/pi0-related shower descendants are grouped under the
  appropriate source (`reconstruction.py:423–499`). `Event_ID` is Class A;
  `Track_ID`, `Parent_ID`, `Name`, `Process`/`Proc`, and interaction ancestry
  are Class B truth/provenance in plan 09 (§3–§4, §8–§10).
- `_tpc_tracks_to_skip_for_charged_matching(tpc, config)`
  (`reconstruction.py:632–688`) removes TPC tracks whose truth labels should
  not seed charged calorimeter matching: neutral names are always skipped;
  e± tracks from non-charged parents are skipped; close e+/e- sibling pairs
  within `config.electron_pair_max_entry_separation_cm` (default 5.0 cm) are
  skipped (`reconstruction.py:639–688`). Inputs `Name` and `Parent_ID` are
  Class B; positions are Class A.
- `_merge_photon_fragments(photons, config)` (`reconstruction.py:502–629`)
  merges neutral, truth-labelled gamma fragments when `has_tpc_track` is
  false and the angular separation to the seed direction is ≤
  `config.photon_fragment_merge_angle_deg` (default 2.0°;
  `reconstruction.py:502–535`). Merged rows sum lead-glass and scintillator
  energy, energy-weight centroids/times, union `source_track_ids`, force
  `truth_name = "gamma"`, recompute direction/path length, clear charged-match
  fields, and then reassign per-event `object_id` values (`reconstruction.py:543–629`).

#### 3.5.2 `reconstruct_photon_objects(leadglass, scintillator=None, tpc=None, config=DEFAULT_CONFIG, vertices=None, interactions=None)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/reconstruction.py:783–1101`.

**Inputs:** lead-glass and optional scintillator, TPC, vertices, and
Interaction tables. Lead-glass/scintillator deposits use the NNbarHit-derived
schema in plan 09 §9–§10: `Event_ID` (Class A), `Track_ID`/`Parent_ID`/`Name`
(Class B), `x/y/z` and `t` (Class A), and `eDep` (Class A calorimeter energy,
with detector calibration caveats). Vertices read `event_id`, `vertex_x/y/z`,
and optional `vertex_time_ns` from §3.3 output (`reconstruction.py:829–849`).
TPC inputs for charged matching require `Event_ID`, `Track_ID`, and `x/y/z`,
with optional `t` (`reconstruction.py:850–889`). Interactions provide Class B
ancestry for shower-source resolution and matchability (`reconstruction.py:891–911`).

**Decision rule:** if both lead-glass and scintillator are empty, return an
empty photon table with the declared schema (`reconstruction.py:793–827`).
Valid reconstructed vertices are cached per event; absent vertices fall back to
origin `(0,0,0)` and `used_reconstructed_vertex = false` in emitted objects
(`reconstruction.py:829–849`, `953–958`, `1030–1035`). TPC charged-match
candidate directions are built from the event vertex toward the farthest valid
TPC hit, after applying `_tpc_tracks_to_skip_for_charged_matching`; endpoint
time is retained when finite (`reconstruction.py:850–889`).

Lead-glass and scintillator deposits are first resolved to shower sources using
`_leadglass_shower_sources` (`reconstruction.py:890–896`). Parent maps across
Interaction, lead-glass, and scintillator sources support the nested
`has_matchable_tpc_origin`, `has_direct_matchable_tpc_track`, and
`has_lineage_evidence` predicates (`reconstruction.py:897–939`). For each
source group, `build_photon_row` energy-weights the cluster centroid and time,
computes direction and path length from the reconstructed vertex or origin,
then scans charged-match candidate tracks. A charged match is accepted only
when angle ≤ `config.charged_cluster_match_angle_deg` (default 10.5°) and, if
a finite time delta exists, `abs(delta) <= config.charged_cluster_match_time_tolerance_ns`
(default 50 ns; `reconstruction.py:941–989`).

Truth/provenance classification is diagnostic: `_shower_truth_name`, direct or
ancestor TPC matchability, and sparse geometric evidence feed
`_charge_match_truth_from_name` into `truth_charge_match_class`
(`reconstruction.py:990–1014`). Lead-glass groups emit first; groups with
`leadglass_edep < config.min_photon_energy` (default 5.0 MeV) are skipped
(`reconstruction.py:1046–1075`). Scintillator-only groups that were not already
emitted by a lead-glass source are emitted when `scintillator_edep >=
config.min_photon_energy` (`reconstruction.py:1077–1099`). The final table is
passed through `_merge_photon_fragments` before return (`reconstruction.py:1101`).

**Outputs:** DataFrame columns `event_id`, `object_id`, `source_track_id`,
`source_track_ids`, `truth_name`, `truth_charge_match_class`, `leadglass_edep`,
`scintillator_edep`, `total_energy`, `leadglass_fraction`, `cluster_x/y/z`,
`cluster_time_ns`, `vertex_x/y/z`, `vertex_time_ns`, `photon_path_length_cm`,
`used_reconstructed_vertex`, `ux/uy/uz`, `matched_tpc_track_id`,
`charged_match_angle_deg`, `matched_tpc_time_ns`,
`charged_match_time_delta_ns`, and `has_tpc_track` (`reconstruction.py:793–822`).
Plan 09 §14.4 describes the photon table as shower centroids, directions,
energy, charged/neutral outputs, and source-track truth provenance.

**Truth reads:** this path reads Class B `Track_ID`, `Parent_ID`, `Name`,
interaction ancestry, source-track aliases, and truth charge classes for shower
source grouping, diagnostic truth labels, charged-match-class diagnostics, and
fragment merging. The geometric charged/neutral decision itself is angle/timing
based, but the current source grouping and fragment merge still depend on truth
provenance, as tracked by plan 08 §3.7.

#### 3.5.3 Pending π⁰-pairing detail

`find_pi0_candidates(photons, config=DEFAULT_CONFIG)` (`reconstruction.py:1316–1531`)
forms photon pairs and applies the π⁰ mass/energy/opening-angle policy. It is the
next §3.5 unit to document with the same line-level input/output/truth-read detail.
