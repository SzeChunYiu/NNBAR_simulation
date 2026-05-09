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

Column schema follows the universal NNbarHit pattern (§8 below)
with the volume identification anchored to the Carbon LV.
Codex-supervisor populates the full per-column table.

## 6. Silicon table

Per-step records from SiliconSD. Same NNbarHit-derived schema (§8).

## 7. Beampipe table

Per-step records from TubeSD inside any Beampipe LV. Same NNbarHit
schema (§8). Used to study beampipe-origin secondaries (plan 14
validation suite).

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

Same NNbarHit-derived schema. The `eDep` column carries the
calorimeter energy deposit. The `vol_name` column resolves to the
specific lead-glass block.

When `WITH_SCINTILLATION=ON`, additional optical observables are
emitted by the LeadGlass SD; in fast mode these columns are zero-
populated. Plan 18 specifies the on/off audit.

The `module_ID` column for lead glass refers to per-block index. The
17972-block count cited in `docs/detector_fundamental_question_tree.md`
§2 is the maximum module index range.

Decision-path consumers: photon-object reconstruction (plan 08 §3.5).

## 11. PMT table

Optical-photon hits at the PMT face. Populated only when
`WITH_SCINTILLATION=ON` (or Opticks active).

| Column | Dtype | Units | Class | Rule |
|---|---|---|---|---|
| `Event_ID` | int64 | — | A | §3.7 |
| `Module_ID` | int32 | — | A | §3.7 |
| `photons` | int32 | photons | A+C | §3.3+§3.8 (QE Class C) |
| `t` | float64 | ns | A | §3.2 |
| `x`, `y`, `z` | float64 | mm | A | §3.1 |

Consumed by: `_pmt_photons_for_event` (`reconstruction.py:70–86`)
which sums per-`Module_ID` *max* photon counts.

## 12. GPUEnergy table

Output from `CeleritasCalorimeter` (plan 07 §11.4). Populated only
when `WITH_CELERITAS=ON` and Celeritas is active at runtime.

Records GPU-tracked e-, e+, gamma energy deposits in LeadGlass and
Scintillator volumes that bypassed the CPU SDs (`opts.sd.enabled =
false` per `main.cc:287`). Class A in column intent; the GPU/CPU
parity is itself a calibration constant (§3.8 Class C) until proven
identical at the percent level by plan 14.

Codex-supervisor populates the column list against the Celeritas
calorimeter source.

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
