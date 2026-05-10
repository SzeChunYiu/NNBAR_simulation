---
id: 09_io_schema_data_dictionary
title: IO schema and data dictionary — every column, every parquet
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [00_README, 01_realism_contract, 07_simulation_atomic_walkthrough, 08_reconstruction_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/output/*.parquet, schema: simulation outputs}
  - {path: NNBAR_Detector/src/output/ParquetOutputManager.cc, schema: producer source}
  - {path: NNBAR_Detector/src/sensitive/*.cc, schema: hit producers}
  - {path: NNBAR_Detector/src/core/EventAction.cc, schema: row writer}
outputs:
  - {path: docs/rebuild_plans/09_io_schema_data_dictionary.md, schema: this file}
  - {path: nnbar_reconstruction/_schemas/*.yml, schema: machine-readable per-file schema}
acceptance:
  - {test: every column read by any reco function maps to a § entry, method: realism audit cross-reference, pass_when: zero unmapped reads}
  - {test: every column written by any SD or EventAction maps to a § entry, method: source ↔ doc cross-reference, pass_when: zero unmapped writes}
  - {test: every Class A / B / C tag matches plan 01 §3 rule, method: tag-vs-rule check, pass_when: zero rule violations}
risks:
  - {risk: schema drifts silently when SD code is edited, mitigation: plan 53 CI rule blocks PRs that change SD/EventAction without paired §-update here}
  - {risk: reconstruction-side derived columns proliferate without §-entries, mitigation: 09 owns derived columns too — reconstruction PRs add rows here}
estimated_effort: L
last_updated: 2026-05-09
---

# IO schema and data dictionary

*Charter.* The single authority on every column produced by the
simulation and the reconstruction. For every parquet file and every
column inside it: name, dtype, units, semantics, provenance class
(A/B/C from plan 01), upstream producer, downstream consumers. This
plan replaces ad-hoc knowledge of "what's in the TPC parquet."

This v0.1 establishes the schema *template* and instantiates it for
the most-cited tables. Codex-supervisor fills the remaining tables
against the acceptance criteria and re-runs the realism audit until
no column lacks an entry.

## 1. Schema entry template

For every column, the canonical record is:

```yaml
- name: <column name in parquet>
  dtype: int32 | int64 | float32 | float64 | string | bool
  units: <SI or local unit, e.g. mm, ns, MeV>
  semantics: <one-line description>
  realism_class: A | B | C
  rule: <which §3 rule of plan 01 governs the classification>
  produced_by: <SD class, EventAction line range, or reco function>
  consumed_by: [<list of downstream functions / plans>]
  notes: <optional, e.g. unit caveats, AppleDouble status, deprecated>
```

The Markdown form below is human-readable; codex-supervisor mirrors
the same content into `nnbar_reconstruction/_schemas/<file>.yml` for
machine consumption by the realism audit (plan 01 §4).

## 2. Output-file inventory (recap from plan 07 §9)

| File pattern | Producer SD/Action | Schema § |
|---|---|---|
| `Particle_output_<run>.parquet` | EventAction (truth primaries) | §3 |
| `Interaction_output_<run>.parquet` | EventAction (decay/process tree) | §4 |
| `Carbon_output_<run>.parquet` | CarbonSD | §5 |
| `Silicon_output_<run>.parquet` | SiliconSD | §6 |
| `Beampipe_output_<run>.parquet` | TubeSD | §7 |
| `TPC_output_<run>.parquet` | TPCSD | §8 |
| `Scintillator_output_<run>.parquet` | ScintillatorSD | §9 |
| `LeadGlass_output_<run>.parquet` | LeadGlassSD | §10 |
| `PMT_output_<run>.parquet` | PMTSD | §11 |
| `GPUEnergy_output_<run>.parquet` | CeleritasCalorimeter | §12 |
| `Scintillator_Module_Position.txt` | Scintillator builder | §13 (geometry side-car) |
| Reconstruction tables (CSV) | `nnbar_reconstruction.cli` | §14 |

## 3. Particle table (truth primaries)

Inferred from plan 07 §8.2 (EventAction primary recording) and
`reconstruction.py` cross-references (`Particle` is loaded by
`cli._add_truth_tables`):

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int64 | — | per-run event index | A | §3.7 (sensor-equivalent identifier) | offsetable across runs by `EVENT_ID_OFFSET` (cli.py:27) |
| `Track_ID` | int64 | — | Geant4 internal track identifier | B | §3.4 | every primary has a Track_ID; secondaries inherit |
| `Parent_ID` | int64 | — | parent track identifier (0 = primary) | B | §3.4 | |
| `Name` | string | — | PDG particle name | B | §3.5 | e.g. "anti_neutron", "pi+", "pi-", "proton" |
| `pdg_code` | int32 | — | PDG identifier | B | §3.5 | |
| `KineticEnergy` | float64 | MeV | primary kinetic energy at production | B | §3.5 | |
| `Px`, `Py`, `Pz` | float64 | MeV/c | primary momentum components | B | §3.5 | |
| `Vx`, `Vy`, `Vz` | float64 | mm | primary production vertex | B | §3.5 | currently equal to truth (limitation L1) |
| `Time` | float64 | ns | primary production time | B | §3.5 | |
| `Process` | string | — | creator process name | B | §3.5 | "primary" for primaries |

This table is loaded by `validation.py` and the studies; it is
**never** loaded by `reconstruction.py` (the realism audit confirms
this). Plan 47 reproduction ledger uses it only inside
`@validation_only` functions.

## 4. Interaction table (decay/process tree)

Sparse table; populated when a primary interacts (decay, hadronic
interaction, conversion). Used by `reconstruction.py` to resolve
shower-source ancestry (plan 08 §3.5 step 1) — flagged for migration.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int64 | — | event index | A | §3.7 | |
| `Track_ID` | int64 | — | child track id | B | §3.4 | |
| `Parent_ID` | int64 | — | parent track id | B | §3.4 | |
| `Process` | string | — | interaction process name | B | §3.5 | e.g. "Decay", "conv", "compt" |
| `Vx`, `Vy`, `Vz` | float64 | mm | interaction vertex | B | §3.5 | |
| `Time` | float64 | ns | interaction time | B | §3.5 | |
| Optional: `secondary_pdg` | int32 | — | first secondary PDG | B | §3.5 | |
| Optional: `name` | string | — | parent particle name | B | §3.5 | |

The exact column list will be verified by codex-supervisor against
`EventAction.cc` writer; this is a v0.1 stub.

## 5. Carbon table

Per-step records from CarbonSD inside the foil. Used by
`reconstruction.py` only for diagnostics
(`@diagnostic_only` once plan 01 audit lands). Plan 13 (signal model)
consumes this to study annihilation-product distributions inside the
foil.

The active Parquet writer persists this table from `CarbonSD` hits via
`NNbarRun::RecordEvent`. Positions are stored in **cm** because the
writer divides hit coordinates by `CLHEP::cm` before filling Parquet.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:147`; consumed_by=`io.load_run`, plan 13 diagnostics |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier | B | §3.4 | produced_by=`CarbonSD.cc:58,91` → `NNbarRun.cc:130,147`; consumed_by=diagnostic joins only |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track id | B | §3.4 | produced_by=`CarbonSD.cc:59,92` → `NNbarRun.cc:131,147`; consumed_by=diagnostic ancestry only |
| `Name` | string | dimensionless | particle PDG name | B | §3.5 | produced_by=`CarbonSD.cc:56-57,90` → `NNbarRun.cc:132,147`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name, or `primary` | B | §3.5 | produced_by=`CarbonSD.cc:60-61,93` → `NNbarRun.cc:133,148`; consumed_by=diagnostic process studies |
| `Step_info` | int32 | dimensionless | first/last-in-volume flag (`2` both, `0` first, `1` last) | A | §3.7 | produced_by=`CarbonSD.cc:106-120` → `NNbarRun.cc:134,148`; consumed_by=foil-hit diagnostics |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.5 | produced_by=`CarbonSD.cc:86,94` → `NNbarRun.cc:135,148`; consumed_by=truth-leak audit and diagnostics |
| `x`, `y`, `z` | float64 | cm | midpoint of pre/post step in the carbon foil | A | §3.1 | produced_by=`CarbonSD.cc:66-73,96-98` → `NNbarRun.cc:137-149`; consumed_by=plan 13 distributions |
| `px`, `py`, `pz` | float64 | dimensionless | pre-step momentum unit-vector components | A | §3.3 | produced_by=`CarbonSD.cc:85,101-103` → `NNbarRun.cc:140-150`; consumed_by=plan 13 angular diagnostics |
| `t` | float64 | ns | global track time at the carbon hit | A | §3.2 | produced_by=`CarbonSD.cc:75-76,99` → `NNbarRun.cc:143,151`; consumed_by=timing diagnostics |
| `KE` | float64 | MeV | mean of pre/post-step kinetic energy | A | §3.3 | produced_by=`CarbonSD.cc:78-83,100` → `NNbarRun.cc:144,151`; consumed_by=plan 13 spectra |
| `eDep` | float64 | MeV | step total energy deposit in carbon | A | §3.3 | produced_by=`CarbonSD.cc:63-64,104` → `NNbarRun.cc:145,151`; consumed_by=plan 13 energy-loss studies |

## 6. Silicon table

Per-step records from SiliconSD. The writer stores only silicon hits
with positive `eDep`, and positions are persisted in **cm** via
`NNbarRun::RecordEvent`.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:230`; consumed_by=`io.load_run`, silicon diagnostics |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier | B | §3.4 | produced_by=`SiliconSD.cc:71,145` → `NNbarRun.cc:208,230`; consumed_by=diagnostic joins only |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track id | B | §3.4 | produced_by=`SiliconSD.cc:109-116,140` → `NNbarRun.cc:209,230`; consumed_by=diagnostic ancestry only |
| `Name` | string | dimensionless | particle PDG name | B | §3.5 | produced_by=`SiliconSD.cc:102-103,143` → `NNbarRun.cc:210,230`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name, or `primary` | B | §3.5 | produced_by=`SiliconSD.cc:112-117,141` → `NNbarRun.cc:211,231`; consumed_by=diagnostic process studies |
| `Step_info` | int32 | dimensionless | first-step flag (`1` first in volume, `0` otherwise) | A | §3.7 | produced_by=`SiliconSD.cc:134-136` → `NNbarRun.cc:212,231`; consumed_by=silicon-hit diagnostics |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.5 | produced_by=`SiliconSD.cc:128,134` → `NNbarRun.cc:213,231`; consumed_by=truth-leak audit and diagnostics |
| `Layer_ID` | int32 | dimensionless | silicon replica/layer id from `replicaNumber(0)` | A | §3.7 | produced_by=`SiliconSD.cc:92-94,146` → `NNbarRun.cc:214,231`; consumed_by=geometry and material diagnostics |
| `x`, `y`, `z` | float64 | cm | midpoint of pre/post step in silicon | A | §3.1 | produced_by=`SiliconSD.cc:81-86,153-155` → `NNbarRun.cc:216-232`; consumed_by=plan 14/16 diagnostics |
| `px`, `py`, `pz` | float64 | dimensionless | pre-step momentum unit-vector components | A | §3.3 | produced_by=`SiliconSD.cc:127,150-152` → `NNbarRun.cc:219-233`; consumed_by=angular diagnostics |
| `t` | float64 | ns | global track time at the silicon hit | A | §3.2 | produced_by=`SiliconSD.cc:96-97,142` → `NNbarRun.cc:222,234`; consumed_by=timing diagnostics |
| `KE` | float64 | MeV | post-step kinetic energy | A | §3.3 | produced_by=`SiliconSD.cc:121-123,149` → `NNbarRun.cc:223,234`; consumed_by=energy-spectrum diagnostics |
| `eDep` | float64 | MeV | step total energy deposit in silicon | A | §3.3 | produced_by=`SiliconSD.cc:73-74,148` → `NNbarRun.cc:224,234`; consumed_by=material/energy-loss diagnostics |

## 7. Beampipe table

Per-step records from TubeSD inside any Beampipe LV. Used to study
beampipe-origin secondaries (plan 14 validation suite). Positions are
stored in **cm** by `NNbarRun::RecordEvent`.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:188`; consumed_by=`io.load_run`, plan 14 diagnostics |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier | B | §3.4 | produced_by=`TubeSD.cc:51,85` → `NNbarRun.cc:170,188`; consumed_by=diagnostic joins only |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track id | B | §3.4 | produced_by=`TubeSD.cc:52,86` → `NNbarRun.cc:171,188`; consumed_by=diagnostic ancestry only |
| `Name` | string | dimensionless | particle PDG name | B | §3.5 | produced_by=`TubeSD.cc:49-50,84` → `NNbarRun.cc:172,188`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name, or `primary` | B | §3.5 | produced_by=`TubeSD.cc:53-54,87` → `NNbarRun.cc:173,189`; consumed_by=diagnostic process studies |
| `Step_info` | int32 | dimensionless | first/last-in-volume flag (`2` both, `0` first, `1` last) | A | §3.7 | produced_by=`TubeSD.cc:100-114` → `NNbarRun.cc:174,189`; consumed_by=beampipe-hit diagnostics |
| `Current_Vol` | string | dimensionless | current beampipe physical-volume name | A | §3.7 | produced_by=`TubeSD.cc:80,88` → `NNbarRun.cc:176,189`; consumed_by=geometry/material diagnostics |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.5 | produced_by=`TubeSD.cc:79,89` → `NNbarRun.cc:175,189`; consumed_by=truth-leak audit and diagnostics |
| `x`, `y`, `z` | float64 | cm | midpoint of pre/post step in the beampipe | A | §3.1 | produced_by=`TubeSD.cc:59-66,90-92` → `NNbarRun.cc:178-190`; consumed_by=plan 14/16 diagnostics |
| `px`, `py`, `pz` | float64 | dimensionless | pre-step momentum unit-vector components | A | §3.3 | produced_by=`TubeSD.cc:78,95-97` → `NNbarRun.cc:181-191`; consumed_by=angular diagnostics |
| `t` | float64 | ns | global track time at the beampipe hit | A | §3.2 | produced_by=`TubeSD.cc:68-69,93` → `NNbarRun.cc:184,192`; consumed_by=timing diagnostics |
| `KE` | float64 | MeV | mean of pre/post-step kinetic energy | A | §3.3 | produced_by=`TubeSD.cc:71-76,94` → `NNbarRun.cc:185,192`; consumed_by=energy-spectrum diagnostics |
| `eDep` | float64 | MeV | step total energy deposit in the beampipe | A | §3.3 | produced_by=`TubeSD.cc:56-57,98` → `NNbarRun.cc:186,192`; consumed_by=material/energy-loss diagnostics |

## 8. TPC table — full column listing (canonical example)

The TPCSD writer (plan 07 §6.1) produces one row per recorded step
(first/last in volume only). The columns reflect the `NNbarHit`
fields written by `EventAction.cc`.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int64 | — | event index | A | §3.7 | |
| `Track_ID` | int64 | — | Geant4 track identifier | B | §3.4 | |
| `Parent_ID` | int64 | — | parent track identifier | B | §3.4 | |
| `Name` | string | — | particle PDG name | B | §3.5 | |
| `Process` | string | — | creator process | B | §3.5 | "primary" if Parent_ID == 0 |
| `vol_name` | string | — | current volume name | A | §3.7 | sensor-equivalent (volume ID) |
| `origin_vol_name` | string | — | track origin volume | B | §3.5 | track ancestry — Class B |
| `x`, `y`, `z` | float64 | mm | hit position (midpoint of pre/post-step) | A | §3.1 | limitation L1 (no smearing yet) |
| `t` | float64 | ns | hit global time | A | §3.2 | limitation L2 (no jitter) |
| `eDep` | float64 | MeV | step energy deposit | A | §3.3 | limitation L3 (no noise/threshold) |
| `kinEnergy` | float64 | MeV | step-mean kinetic energy | A | §3.3 | derived from pre/post-step KE |
| `px`, `py`, `pz` | float64 | — | pre-step momentum unit vector | A | §3.3 | direction only; magnitude = 1 |
| `TrackLength` | float64 | mm | step length | A | §3.3 | |
| `photons` | int32 | electrons | Poisson-distributed electron count from `eDep / 23.6 eV` | A+C | §3.3 + §3.8 | **field name reused** (TPCSD.cc:149); the **23.6 eV W-value** is Class C with calibration source `TPCSD.cc:102`. Plan 17 audits the value. |
| `xHitID` | int32 | — | TPC layer index (`replicaNumber(0)`) | A | §3.7 | |
| `module_ID` | int32 | — | TPC module index 0–11 (`replicaNumber(1)`) | A | §3.7 | per `DetectorConstruction.cc:273–300` |
| `step_info` | int32 | — | step provenance flag | A | §3.7 | 1 = first step from outside; 0 = last step from outside; 999 = origin inside TPC layer |
| `particle_x/y/z` | float64 | mm | particle production vertex | B | §3.5 | propagated from primary |

`TPC_output_*.parquet` is loaded by:
- `nnbar_reconstruction.cli.summarize` → `reconstruct_run`
- `nnbar_reconstruction.cli.scan-pid` → `reconstruct_charged_objects`
- `nnbar_reconstruction.cli.validate-reco`
- `pi0_study.evaluate_pi0_mass_ladder`
- `charged_study.evaluate_charged_stress`
- `pi0_fake_study.evaluate_pi0_fake_background`

Truth columns currently consumed by the reconstruction decision path
(flagged for migration per plan 08 §3.7): `Name`, `Track_ID`
(sparse-table fallback only), `origin_vol_name` (diagnostic).

## 9. Scintillator table

Same NNbarHit-derived schema as TPC (§8) with the following
differences:

- `photons` column carries *photon-equivalent count* per
  `11136 photons/MeV` rule (per plan 07 §6.2; plan 18 audits against
  the optical-table 10000 photons/MeV value when
  `WITH_SCINTILLATION=ON`). Both factors are Class C.
- `module_ID` indexes the scintillator module per builder placement;
  the geometric mapping lives in `Scintillator_Module_Position.txt`
  (§13).

Decision-path consumers: `reconstruct_charged_objects` (matches
scintillator hits to TPC tracks); event-variable functions (per-
hemisphere energy sums).

## 10. LeadGlass table

Rows are produced by `LeadGlassSD` only for non-optical tracks that
create at least one Cerenkov optical photon in `LeadGlassPV`. The
writer stores lead-glass block translations in **cm** and filters out
zero-photon rows.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:391`; consumed_by=photon reconstruction and event summaries |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier | B | §3.4 | produced_by=`LeadGlassSD.cc:72,162` → `NNbarRun.cc:370,391`; consumed_by=diagnostic/ancestry paths |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track id | B | §3.4 | produced_by=`LeadGlassSD.cc:133-145,158` → `NNbarRun.cc:371,391`; consumed_by=truth grouping until plan 26 replaces ancestry |
| `Name` | string | dimensionless | particle PDG name | B | §3.5 | produced_by=`LeadGlassSD.cc:113-114,161` → `NNbarRun.cc:372,391`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name, or `primary` | B | §3.5 | produced_by=`LeadGlassSD.cc:132-145,159` → `NNbarRun.cc:373,392`; consumed_by=diagnostic process studies |
| `Step_info` | int32 | dimensionless | first-step flag (`1` first in volume, `0` otherwise) | A | §3.7 | produced_by=`LeadGlassSD.cc:173-174` → `NNbarRun.cc:374,393`; consumed_by=calorimeter-hit diagnostics |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.5 | produced_by=`LeadGlassSD.cc:171-172` → `NNbarRun.cc:375,394`; consumed_by=truth-leak audit and diagnostics |
| `Module_ID` | int32 | dimensionless | lead-glass block index from `replicaNumber(1)` | A | §3.7 | produced_by=`LeadGlassSD.cc:92-94,163` → `NNbarRun.cc:386,395`; consumed_by=photon clustering/block mapping |
| `x`, `y`, `z` | float64 | cm | lead-glass block translation coordinates | A | §3.1 | produced_by=`LeadGlassSD.cc:99-102,164-166` → `NNbarRun.cc:377-395`; consumed_by=photon-object geometry |
| `t` | float64 | ns | global track time at the lead-glass hit | A | §3.2 | produced_by=`LeadGlassSD.cc:107-108,160` → `NNbarRun.cc:380,396`; consumed_by=timing/event summaries |
| `KE` | float64 | MeV | post-step kinetic energy | A | §3.3 | produced_by=`LeadGlassSD.cc:148-151,169` → `NNbarRun.cc:381,396`; consumed_by=energy-spectrum diagnostics |
| `eDep` | float64 | MeV | step total energy deposit in lead glass | A | §3.3 | produced_by=`LeadGlassSD.cc:74-75,168` → `NNbarRun.cc:382,396`; consumed_by=photon energy reconstruction |
| `photons` | int32 | photons | Cerenkov photons produced in the step | A+C | §3.3 + §3.8 | produced_by=`LeadGlassSD.cc:120-130,170` → `NNbarRun.cc:387,396`; consumed_by=plan 18 intercalibration and photon-object studies |

Decision-path consumers: photon-object reconstruction (plan 08 §3.5).

## 11. PMT table

Optical-photon hits at the PMT face. Populated only when
`WITH_SCINTILLATION=ON` (or Opticks active). `NNbarRun::RecordEvent`
aggregates individual optical photons into one row per `(Event_ID,
Module_ID)`, with per-photon `KE` and `t` stored as list columns.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:465`; consumed_by=`_pmt_photons_for_event` lines 67-83 |
| `Module_ID` | int32 | dimensionless | PMT/lead-glass module id from `replicaNumber(1)` | A | §3.7 | produced_by=`PMTSD.cc:82-84,137` → `NNbarRun.cc:427,466`; consumed_by=PMT photon grouping |
| `x`, `y`, `z` | float64 | cm | PMT face translation coordinates for the module | A | §3.1 | produced_by=`PMTSD.cc:86-89,138-140` → `NNbarRun.cc:428-469`; consumed_by=geometry diagnostics |
| `photons` | int32 | photons | count of accepted optical photons in this PMT module/event | A+C | §3.3 + §3.8 | produced_by=`PMTSD.cc:126-145` → `NNbarRun.cc:445-470`; consumed_by=`_pmt_photons_for_event` lines 74-82; QE/acceptance is Class C |
| `KE` | list<float64> | MeV | per-photon post-step kinetic-energy list for the module/event | B | §3.5 | produced_by=`PMTSD.cc:118-123,144` → `NNbarRun.cc:433,458-471`; consumed_by=diagnostics only |
| `t` | list<float64> | ns | per-photon global-time list for the module/event | A | §3.2 | produced_by=`PMTSD.cc:93-94,134` → `NNbarRun.cc:426,457-472`; consumed_by=timing diagnostics |

Consumed by: `_pmt_photons_for_event` (`reconstruction.py:67–83`)
which sums per-`Module_ID` *max* photon counts.

## 12. GPUEnergy table

Planned output from `CeleritasCalorimeter` (plan 07 §11.4), populated
only when `WITH_CELERITAS=ON` and Celeritas is active at runtime. The
current `NNBAR_Detector-L3` source tree contains no `src/physics/`, no
`CeleritasCalorimeter`, and no `GPUEnergy_output` writer/layout; a
source scan found only reconstruction I/O accepting an optional
`GPUEnergy` kind. Therefore the active schema has zero produced columns
in the current build.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| _none currently produced_ | — | — | No active Celeritas/GPUEnergy writer exists in this source tree | — | — | produced_by=absent; consumed_by=`io.load_run` tolerates missing `GPUEnergy_output_<run>.parquet` as an empty table |

When `CeleritasCalorimeter` is restored, this section must be replaced
with the concrete Parquet layout before any `WITH_CELERITAS=ON` sample
is registry-eligible. GPU/CPU parity remains Class C (§3.8) until plan
14 proves percent-level equivalence.

## 13. Scintillator_Module_Position.txt (geometry side-car)

Text file written by the Scintillator builder during construction.
Lines list `(module_id, x, y, z, axis_orientation)` for each
scintillator module. Used by reconstruction-side hemispheric
partitioning (plan 31 event variables).

This is *configuration data*, not Class A/B/C. Plan 16 (geometry)
freezes the format.

## 14. Reconstruction-side tables (CSV)

The CLI commands write per-run CSVs that downstream plotting and
ledger code consume. Schema mirrors the dict returned by
`reconstruct_run` (plan 08 §3.8).

### 14.1 vertices.csv

| Column | Dtype | Units | Semantics |
|---|---|---|---|
| `event_id` | int64 | — | run-offset event id |
| `vertex_x`, `vertex_y`, `vertex_z` | float64 | mm | reconstructed event vertex |
| `vertex_radial_rms` | float64 | mm | RMS radial spread of valid track projections |
| `n_tracks_used` | int32 | — | number of TPC tracks contributing to projection |
| `n_tracks_skipped` | int32 | — | tracks whose projection failed |

All columns Class A (the truth-labelled track exclusions are *which
input tracks were used* — the *output* is geometric).

### 14.2 charged.csv

Per-charged-object table emitted by `reconstruct_charged_objects`.
Columns include reconstructed direction, dE/dx, scintillator range,
PID class, plus *truth* columns (`truth_name`) marked `@diagnostic`.

Codex-supervisor enumerates all columns against the function's actual
return DataFrame.

### 14.3 electron_pairs.csv

Pairs of TPC tracks compatible with e+ e- conversion under the Ch 8.2
5 cm rule (plan 08 §3.4). Carries truth-name pair for validation.

### 14.4 photons.csv

Per-photon-object table per plan 08 §3.5. Columns include
shower-centroid coordinates, vertex-relative direction, total energy,
charged/neutral discriminant outputs, source-track aliases (truth
provenance).

### 14.5 pi0.csv

Per-π⁰-candidate table. Columns include the strict
`passes_selection` and the per-cut booleans
(`passes_mass_window`, `passes_total_energy`,
`passes_scintillator_energy`, `passes_leadglass_energy`,
`passes_leadglass_fraction`, `passes_opening_angle`),
`selection_failure_reasons`, `truth_charge_match_class`, photon
source-track aliases, prompt-timing diagnostics.

### 14.6 events.csv

Per-event summary. Columns include all event variables in
`reconstruction.md` lines 35–80 (calorimeter sums, multiplicities,
visible mass, sphericity, EL/ET, hemispheric splits, in-time/out-of-
time energy, PMT counts), the strict
`passes_preliminary_selection` and per-cut booleans matching
`cli._cutflow` (cli.py:37–44), and the cumulative cut-flow flags.

## 15. Cross-tabulation rules

Standard joins used downstream (codified for codex-supervisor):

- Event-level: `Event_ID` is the canonical join key. Multi-run
  merging applies `EVENT_ID_OFFSET = 1_000_000_000` per
  `cli.py:27`.
- Track-level: `(Event_ID, Track_ID)` is unique within a run (truth
  bookkeeping). Multi-run uses both offsets.
- Hit-to-track: SDs do not record a `Hit_ID`; hits are joined to
  tracks by `(Event_ID, Track_ID)` plus geometry indices when needed.

## 16. Acceptance criteria

- §5, §6, §7, §10, §11, §12, §14.2, §14.3, §14.4, §14.5, §14.6 are
  populated to the per-column depth of §8 by codex-supervisor in
  the next plan revision (v0.2).
- The realism audit (plan 01) imports the YAML mirror of this file
  and reports any column it cannot resolve.
- Plan 53 CI rule blocks PRs that change `*_output_*.parquet`
  schemas (additions or removals) without paired changes here.
- Every Class C column carries a `would_change_with_real_data: true`
  flag and a calibration-source citation per plan 01 §2.3.

## 17. Risks and mitigations

- *Risk:* §5–§14 stubs become permanent.
  *Mitigation:* the §8 column list is the target depth; v0.2 review
  rejects this plan unless §5–§14 match.
- *Risk:* unit confusion (mm vs cm, MeV vs GeV) creeps in via the
  C++ side using Geant4 internal units (`G4SystemOfUnits`).
  *Mitigation:* every column entry explicitly states units; plan 17
  field-calibration audit verifies that the parquet writer applies
  conversions consistently.

## 18. Dependencies

- **00_README** — plan space.
- **01_realism_contract** — Class A/B/C scheme; this plan instantiates
  it column-by-column.
- **07_simulation_atomic_walkthrough** — upstream producer of every
  simulation column.
- **08_reconstruction_atomic_walkthrough** — downstream consumer
  list per column.
- *Consumed by:* every plan that reads or writes parquet; plan 01
  audit; plan 47 ledger; plan 50 defence package.

## 19. References

- `NNBAR_Detector/include/hits/NNbarHit.hh` — the C++ source of
  truth for hit fields.
- `NNBAR_Detector/src/output/ParquetOutputManager.cc` — the C++
  writer implementation.
- HEP-data column-naming conventions (loose precedent only).
