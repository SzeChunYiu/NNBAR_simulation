---
id: 08_3_event_variables
title: Reconstruction atomic walkthrough — event variables
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/reconstruction.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_3_event_variables.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# Event variables — split from plan 08 §3.6

This split file preserves and deepens plan 08 §3.6 so the main walkthrough
stays below the 500-line cap.

## 3.6 Event variables (`reconstruction.py:283-358`, `1602-1733`)

Per `reconstruction.md` §"event variables" lines 35–80, the event summary
surface covers calorimeter sums, multiplicities, visible invariant mass,
sphericity, longitudinal/transverse energy, hemispheric energy, timing-window
energy, and PMT counts.  Plan 31 owns per-variable deep dives; plan 41 owns N-1
and ROC studies.

### 3.6.1 `annotate_timing_windows(hits, vertices, detector, config=DEFAULT_CONFIG)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/reconstruction.py:283-358`.

**Inputs:** calorimeter `hits`, reconstructed `vertices`, detector name, and
`ReconstructionConfig`.  Required hit columns are `Event_ID`, `x`, `y`, `z`,
and `t`; required vertex columns are `event_id`, `vertex_x`, `vertex_y`, and
`vertex_z`, with optional `vertex_time_ns` (`reconstruction.py:291-324`).
The hit columns are Class A event, position, and timing fields under the
NNbarHit schema (`09_io_schema_data_dictionary.md:149-169`); vertices are the
Class A geometric output described in plan 09 §14.1
(`09_io_schema_data_dictionary.md:263-272`).

**Decision rule:** missing inputs, missing required columns, or empty tables
return a copy annotated with `distance_to_vertex = NaN`,
`timing_window_start_ns = NaN`, `timing_window_end_ns = NaN`, and
`in_timing_window = False` (`reconstruction.py:274-301`).  Detector names are
restricted to `scintillator` and `leadglass` (`reconstruction.py:303-305`).
The function left-joins one vertex per event, computes hit-to-vertex distance
and event time, and marks finite rows only (`reconstruction.py:307-331`).

For lead-glass hits, the timing window is centered at
`vertex_time + distance / c` with a ±2σ half-width using
`config.leadglass_time_resolution_ns`; defaults are 1 ns and
`c = 29.9792458 cm/ns` (`reconstruction.py:49-54`, `332-336`).  For
scintillator hits, the start uses a fast 1000 MeV charged pion β and the end
uses a slow 100 MeV charged pion β, each expanded by ±2σ using
`config.scintillator_time_resolution_ns`; defaults are 1000 MeV, 100 MeV,
139.57039 MeV pion mass, and 1 ns resolution (`reconstruction.py:49-53`,
`337-350`).  `in_timing_window` is true exactly when the hit time is within the
computed inclusive start/end window (`reconstruction.py:352-358`).

**Outputs:** the original hit rows plus `distance_to_vertex`,
`timing_window_start_ns`, `timing_window_end_ns`, and `in_timing_window`
(`reconstruction.py:353-358`).

**Truth reads:** none directly.  The function consumes reconstructed vertices
and Class A hit coordinates/times; any truth-equivalence of current perfect
detector coordinates is the known plan 01/09 limitation, not an explicit Class
B read.

### 3.6.2 `summarize_events(data, charged, photons, pi0, electron_pairs=None, vertices=None, config=DEFAULT_CONFIG)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/reconstruction.py:1602-1733`.

**Inputs:** raw run tables, reconstructed charged objects, photons, selected
π⁰ candidates, optional electron pairs and vertices, and `ReconstructionConfig`.
Event ids are unioned from every raw table `Event_ID`, charged/photon/pi0/event
object `event_id`, optional electron-pair `event_id`, and optional vertex
`event_id` (`reconstruction.py:1613-1623`).  Raw `Scintillator`, `LeadGlass`,
`TPC`, and `PMT` tables provide Class A `eDep`, positions, timing, and PMT
photon/module counts; the event output schema is plan 09 §14.6
(`09_io_schema_data_dictionary.md:305-312`).

**Decision rule:** for each event, the function slices scintillator,
lead-glass, TPC, and PMT rows, then computes total and upper/lower
scintillator and lead-glass energy with `y > 0` / `y < 0` hemispheres
(`reconstruction.py:1624-1638`).  It calls `annotate_timing_windows` for
scintillator and lead-glass, sums in-time energy, and derives out-of-time
energy by subtraction (`reconstruction.py:1639-1652`, `1697-1709`).
Longitudinal/transverse energy uses
`EL = Σ E_i z_i / r_i` and `ET = Σ E_i sqrt(x_i^2 + y_i^2) / r_i` in
`_directional_energy` (`reconstruction.py:244-264`, `1653-1654`,
`1710-1715`).  PMT observables are per-event hit count plus per-module maximum
photon sum when `Module_ID` and `photons` exist (`reconstruction.py:70-86`,
`1656-1657`).

Reconstructed objects are filtered by event: charged objects, all photons,
neutral photons (`has_tpc_track == False`), selected π⁰ candidates
(`passes_selection == True`), optional electron pairs, and optional vertex row
(`reconstruction.py:1658-1677`).  The row then records TPC energy, vertex
coordinates/time/spread/track count, charged/pion/proton/photon/π⁰/electron
multiplicities, foil-track flags, visible invariant mass, and sphericity
(`reconstruction.py:1688-1729`).  Visible mass treats charged-pion/proton rows
with fixed masses 139.57039 and 938.272088 MeV and photon rows as massless
four-vectors (`reconstruction.py:1547-1570`).  Sphericity is the standard
normalized momentum tensor eigenvalue metric
`1.5 * (lambda_1 + lambda_2)` (`reconstruction.py:1533-1544`).

Finally `_selection_flags` applies the preliminary cut flow: scintillator
energy 20-2000 MeV, at least one foil-origin TPC track, at least one charged or
π⁰ pion, visible mass ≥ 500 MeV, sphericity ≥ 0.2, upper scintillator ≤ 320
MeV, and lower scintillator ≤ 930 MeV (`reconstruction.py:42-47`,
`1573-1600`, `1730-1733`).

**Outputs:** one event-summary DataFrame.  Columns include `event_id`,
`tpc_edep`, vertex coordinates/time/spread/track count, scintillator,
lead-glass, and total calorimeter energies split into total, in-time,
out-of-time, upper/lower, longitudinal, and transverse forms, PMT photons and
hit count, reconstructed-object multiplicities, pion multiplicity,
TPC/foil-track flags, visible invariant mass, sphericity, six per-cut booleans,
and `passes_preliminary_selection` (`reconstruction.py:1688-1733`).

**Truth reads:** none directly in the event-summary arithmetic.  Some upstream
inputs, especially charged/photon provenance and `has_foil_origin`, may carry
Class B diagnostics from earlier reconstruction stages; this function consumes
their already emitted columns and should remain downstream of the plan 08 §3.7
truth-use audit.
