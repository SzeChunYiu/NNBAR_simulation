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
  - {path: docs/rebuild_plans/09_io_schema_data_dictionary/*.md, schema: per-parquet split docs}
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

## 3–12. Simulation parquet schema files

Detailed per-file column dictionaries moved to split files to keep the main plan under the 500-line cap. Section-number stubs are retained below for existing cross-references.

| Schema § | File pattern | Split file |
|---|---|---|
| §3 | `Particle_output_<run>.parquet` | [`09_particle.md`](09_io_schema_data_dictionary/09_particle.md) |
| §4 | `Interaction_output_<run>.parquet` | [`09_interaction.md`](09_io_schema_data_dictionary/09_interaction.md) |
| §5 | `Carbon_output_<run>.parquet` | [`09_carbon.md`](09_io_schema_data_dictionary/09_carbon.md) |
| §6 | `Silicon_output_<run>.parquet` | [`09_silicon.md`](09_io_schema_data_dictionary/09_silicon.md) |
| §7 | `Beampipe_output_<run>.parquet` | [`09_beampipe.md`](09_io_schema_data_dictionary/09_beampipe.md) |
| §8 | `TPC_output_<run>.parquet` | [`09_tpc.md`](09_io_schema_data_dictionary/09_tpc.md) |
| §9 | `Scintillator_output_<run>.parquet` | [`09_scintillator.md`](09_io_schema_data_dictionary/09_scintillator.md) |
| §10 | `LeadGlass_output_<run>.parquet` | [`09_leadglass.md`](09_io_schema_data_dictionary/09_leadglass.md) |
| §11 | `PMT_output_<run>.parquet` | [`09_pmt.md`](09_io_schema_data_dictionary/09_pmt.md) |
| §12 | `GPUEnergy_output_<run>.parquet` | [`09_gpuenergy.md`](09_io_schema_data_dictionary/09_gpuenergy.md) |

## 3. Particle table (truth primaries)

Detailed schema: [`09_particle.md`](09_io_schema_data_dictionary/09_particle.md).

## 4. Interaction table (decay/process tree)

Detailed schema: [`09_interaction.md`](09_io_schema_data_dictionary/09_interaction.md).

## 5. Carbon table

Detailed schema: [`09_carbon.md`](09_io_schema_data_dictionary/09_carbon.md).

## 6. Silicon table

Detailed schema: [`09_silicon.md`](09_io_schema_data_dictionary/09_silicon.md).

## 7. Beampipe table

Detailed schema: [`09_beampipe.md`](09_io_schema_data_dictionary/09_beampipe.md).

## 8. TPC table — full column listing (canonical example)

Detailed schema: [`09_tpc.md`](09_io_schema_data_dictionary/09_tpc.md).

## 9. Scintillator table

Detailed schema: [`09_scintillator.md`](09_io_schema_data_dictionary/09_scintillator.md).

## 10. LeadGlass table

Detailed schema: [`09_leadglass.md`](09_io_schema_data_dictionary/09_leadglass.md).

## 11. PMT table

Detailed schema: [`09_pmt.md`](09_io_schema_data_dictionary/09_pmt.md).

## 12. GPUEnergy table

Detailed schema: [`09_gpuenergy.md`](09_io_schema_data_dictionary/09_gpuenergy.md).

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
