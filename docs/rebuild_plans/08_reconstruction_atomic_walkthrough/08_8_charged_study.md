---
id: 08_8
title: Reconstruction atomic walkthrough — charged study
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/charged_study.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_8_charged_study.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# Charged study — split from plan 08

This split file preserves and deepens plan 08 §8 so the main walkthrough
stays below the 500-line cap.

## 8. Charged study (`charged_study.py`, 2241 lines)

The largest module. Public surface:

- `evaluate_charged_stress(output_dir, *, run=0, runs=None)`
- `event_rows(report)`

Per `reconstruction.md` lines 270–319, the study enumerates every
`pi+`, `pi-`, and `proton` primary in `Particle`, checks whether a
same-event/same-truth-name charged object was reconstructed from TPC
hits, and reports per-species tracking efficiency, PID accuracy, and
detector hit coverage.  Plan 24 records the per-species charged-object
leaf identity; plan 29 consumes the per-primary breakdown.

### 8.1 Module constants and helper strata

- The truth population is hardcoded to `{"pi+", "pi-", "proton"}` at
  `charged_study.py:16`.  This is intentionally a stress-test label
  filter, not a reconstruction rule.
- The PID scan evaluates proton dE/dx thresholds from 0.02 to 8.0,
  short-range cuts from 5 to 40 cm, and short-range proton dE/dx
  thresholds from 0.02 to 4.0 (`charged_study.py:17-60`).  Its default
  row is scored with `DEFAULT_CONFIG.proton_dedx_min`,
  `short_range_cm`, and `short_range_proton_dedx_min`
  (`charged_study.py:2076-2083`).
- Calorimeter recovery scans use scintillator and lead-glass energy
  threshold grids of 0.001, 5, 10, 20, 50, 100, and 200 MeV, cluster
  timing residual maxima from 5 ns through infinity, direction-oracle
  angle cuts of 5 to 90 degrees, and high-purity thresholds of
  0.80/0.90/0.95 (`charged_study.py:61-91`).
- Acceptance diagnostics bin truth kinetic energy and direction:
  `TRUTH_KE_BINS_MEV`, `ABS_W_BINS`, and `SIGNED_W_BINS`
  (`charged_study.py:92-111`).  The active TPC geometry model is a
  twelve-box hardcoded cm map plus a 1 cm projection reach tolerance
  (`charged_study.py:112-126`).
- Helper groups:
  - event and same-truth hit summaries read `Event_ID`, `Name`, and
    `eDep` (`charged_study.py:169-210`);
  - same-truth position maps read `particle_x/y/z` or `x/y/z`, `KE`,
    `Proc`, and volume fields (`charged_study.py:213-259`);
  - `Interaction` parent-lineage summaries keep only `Parent_ID == 1`
    rows and preserve process, volume, KE, and coordinates
    (`charged_study.py:269-305`);
  - `_truth_primaries` filters `Particle` rows to the charged stress
    labels and emits `run`, `event_id`, `primary_index`, truth identity,
    truth charge/KE, and truth position/direction columns
    (`charged_study.py:308-345`);
  - `_row_for_primary` performs the per-primary join and emits the
    complete event-row schema (`charged_study.py:524-644`);
  - summary helpers compute efficiency/PID accuracy, detector coverage,
    loss taxonomy, topology, calorimeter recovery, acceptance,
    geometry, range, and PID-threshold scans (`charged_study.py:647-780`,
    `783-1168`, `1554-1715`, `1765-2145`).

### 8.2 `evaluate_charged_stress(output_dir, *, run=0, runs=None)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/charged_study.py:2148-2234`

**Inputs:** `output_dir` and either a single `run` or explicit `runs`.
When `runs` is supplied, it is copied verbatim; otherwise the selected
run list is `[run]` (`charged_study.py:2156`).

**Raw tables read:** `load_run(output_dir, selected_run)` supplies
`Particle`, `TPC`, `Scintillator`, `LeadGlass`, `Interaction`, `Carbon`,
`Silicon`, and `Beampipe` (`charged_study.py:2160-2190`).  `Particle`
uses plan 09 §3: `Event_ID` is Class A while `Track_ID`, `Parent_ID`,
`Name`, `KE`/`KineticEnergy`, charge/PDG/kinematics, vertex, and time
are Class B truth-like labels (`09_io_schema_data_dictionary.md:83-99`).
Detector hit tables follow the NNbarHit pattern: `Event_ID`, hit
position/time/energy/track-length/module/step fields are Class A, while
`Track_ID`, `Parent_ID`, `Name`, `Process`, `origin_vol_name`, and
`particle_x/y/z` are Class B provenance (`09_io_schema_data_dictionary.md:143-180`).
`Scintillator` and `LeadGlass` share that schema with detector-specific
energy/module semantics (`09_io_schema_data_dictionary.md:182-203`).
The reconstructed charged input is `reconstruct_run(...)[\"charged\"]`
(`charged_study.py:2162`), whose columns are the plan 09 §14.2
charged-object output, including reconstructed direction, dE/dx,
scintillator range, PID class, and diagnostic `truth_name`
(`09_io_schema_data_dictionary.md:274-281`).

**Decision rule:**

1. For each selected run, load raw tables, reduce `Particle` to charged
   stress primaries, and run the full reconstruction to obtain the
   `charged` table (`charged_study.py:2160-2162`).
2. Build module-level calorimeter clusters from `Scintillator` and
   `LeadGlass`; grouping prefers `Module_ID`, falls back to `Track_ID`,
   then to event-only grouping, computes energy-weighted centroid/time,
   time residual, hit count, and dominant truth name
   (`charged_study.py:1439-1551`, `2163-2176`).
3. Build event-level and same-truth hit summaries for TPC,
   scintillator, and lead-glass (`charged_study.py:2177-2182`).
4. Build primary-parent interaction provenance from `Interaction`, and
   merge same-truth position traces from Carbon, Silicon, Beampipe, TPC,
   Scintillator, and LeadGlass (`charged_study.py:2183-2191`).
5. For every truth primary, `_row_for_primary` matches reconstructed
   charged candidates in the same event by `truth_name`; if multiple
   candidates remain, it sorts by `n_tpc_hits` then `tpc_edep`
   (`charged_study.py:512-521`, `536-545`).  The row records truth
   kinematics, expected TPC box intersection, same-truth detector
   progress, parent-interaction summaries, detector hit coverage,
   matched reco fields, `pid_guess`, and `pid_correct`
   (`charged_study.py:575-644`).
6. The returned summary starts with total truth primaries,
   matched-reco primaries, charged-track efficiency, PID-labeled count,
   PID-correct count, and PID accuracy (`charged_study.py:647-663`).
   It then adds `runs`, `matching_scope`, `primary_topology`,
   `detector_coverage`, `geometry_acceptance`, `range_diagnostics`,
   `loss_taxonomy`, `calorimeter_recovery_ceiling`,
   `calorimeter_recovery_policy_scan`,
   `calorimeter_cluster_recovery_scan`,
   `calorimeter_cluster_direction_oracle_scan`, `by_particle`,
   `acceptance_diagnostics`, `threshold_scan`, and the raw
   `event_rows` list (`charged_study.py:2208-2233`).

**Outputs:** a dict whose scalar/top-level metrics quantify charged
tracking efficiency and PID accuracy, with nested studies for topology,
coverage, geometry, range, losses, calorimeter recovery, per-particle
breakdown, acceptance, PID scan, and per-primary rows.  The event-row
columns include truth identity/kinematics, expected TPC intersection,
same-truth detector progress, parent process/volume/KE summaries,
event-level and same-truth TPC/scintillator/lead-glass counts and
energies, matched reco track/PID features, and PID correctness
(`charged_study.py:575-644`, `2208-2233`).

**Truth reads:** extensive and intentional for a validation/study
module.  The study reads Class B `Particle` labels/kinematics, detector
`Name`/`Track_ID`/`Parent_ID`-style provenance, same-truth positions,
and `Interaction` ancestry.  These reads are allowed only as
diagnostics/validation under plan 01's Class B rule
(`01_realism_contract.md:76-89`) and must not be mistaken for the live
charged reconstruction decision path audited in plan 08 §3.7
(`08_reconstruction_atomic_walkthrough.md:211-226`).

### 8.3 `event_rows(report)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/charged_study.py:2237-2241`

**Inputs:** the report dict returned by `evaluate_charged_stress`.

**Decision rule:** read `report.get("event_rows", [])` and wrap it in a
`pandas.DataFrame`; missing rows produce an empty frame
(`charged_study.py:2237-2241`).

**Outputs:** one row per charged-stress truth primary, with the schema
described in §8.2.

**Truth reads:** none directly; the function materializes already
computed study rows.
