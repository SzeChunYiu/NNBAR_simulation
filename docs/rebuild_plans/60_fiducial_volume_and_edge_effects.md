---
id: 60_fiducial_volume_and_edge_effects
title: Fiducial volume and edge effects
version: 0.1
status: draft
owner: Tracking POG
depends_on: [00_README, 03_dataset_registry, 04_statistical_uncertainty, 16_geometry_and_alignment, 30_subsystem_vertex, 43_signal_efficiency, 45_systematics_taxonomy]
outputs:
  - {path: docs/rebuild_plans/60_fiducial_volume_and_edge_effects.md, schema: this file}
acceptance:
  - {test: fiducial-volume table names every active detector subsystem, method: §3 review, pass_when: no unowned edge cut remains}
  - {test: efficiency-vs-radius and efficiency-vs-z slices are produced on signal and proton calibration samples, method: §5 closure, pass_when: tables and plots saved}
  - {test: edge-related uncertainty maps to plan 45 nuisance IDs, method: §7 review, pass_when: N8/N10 hooks present}
risks:
  - {risk: a tight fiducial cut can hide upstream vertex or geometry bugs, mitigation: §6 requires loose-vs-tight and no-fiducial comparisons}
  - {risk: current reconstruction uses a z=0 vertex plane before a full fiducial helper exists, mitigation: §2 makes that gap explicit and keeps production promotion blocked}
estimated_effort: M
last_updated: 2026-05-10
---

# Fiducial volume and edge effects

*Charter.* Define the fiducial-volume policy that protects thesis
numbers from detector-edge pathologies without hiding reconstruction
failures. The plan is intentionally analysis-facing: it specifies the
cuts, closure slices, tables, and systematics that L3 code must later
produce before plan 43 can quote signal efficiency near detector edges.

## 1. Scope and non-goals

This plan owns the geometry-to-analysis boundary for reconstructed
objects and generated acceptance. It covers:

- TPC drift-volume containment for V.1/V.2/C.1 charged tracks.
- Scintillator coverage for C.3/C.4 range and hit association.
- Lead-glass angular and radial acceptance for P.1-P.7 photons and pi0s.
- Foil-edge buffers for V.3/V.4/V.5 vertex compatibility.
- Efficiency-vs-radius and efficiency-vs-z reporting for plan 43.
- The mapping of residual edge sensitivity into plan 45 systematics.

Non-goals:

- Changing detector geometry. Plan 16 owns geometry and alignment
  scenarios.
- Retuning event-selection thresholds. Plan 37 and plan 41 own S.1-S.6
  threshold decisions.
- Using truth origin labels in production reconstruction. Truth enters
  only acceptance denominators or validation closures.

## 2. Current state and verified source hooks

The live reconstruction has no detector-wide fiducial-volume helper
yet. The current orchestration path is `reconstruct_run`
(`nnbar_reconstruction/reconstruction.py:60-87`), which loads one run, builds charged,
vertex, photon, pi0, and event tables, and returns those named tables.
The numeric reconstruction defaults live in `ReconstructionConfig`
(`nnbar_reconstruction/reconstruction.py:14-48`). Those defaults include selection and
matching thresholds but do not define a detector-wide fiducial-volume
contract.

The legacy vertex path is `reconstruct_event_vertices`
(`nnbar_reconstruction/vertex.py:163-254`). It groups TPC rows by event and track id,
projects each valid line to `z=0`, averages valid projections per
event, and reports radial spread plus skipped-track counts. The split
plan-30 foil gate is `apply_foil_acceptance` (`nnbar_reconstruction/vertex_reco.py:157-194`),
fed by `FoilGeometry` (`nnbar_reconstruction/vertex_reco.py:13-18`). It provides the
observable-only V.5 foil compatibility row, but plan 60 still owns the
detector-wide fiducial contract: TPC containment, scintillator and
lead-glass coverage, covariance-aware edge buffers, and common
geometry-version provenance.

Event-level fields are written by `summarize_events`
(`nnbar_reconstruction/vertex.py:322-447`). It records vertex coordinates, calorimeter
energies, object counts, `has_foil_tpc_track`, visible mass,
sphericity, and the selection booleans. The selection booleans are made
by `_selection_flags` (`nnbar_reconstruction/vertex.py:293-319`). A fiducial plan must
therefore add an explicit geometry/edge artifact rather than silently
reinterpreting existing selection columns.

## 3. Fiducial definitions by subsystem

All distances below are policy names until plan 16 publishes the exact
geometry constants in a machine-readable side car. The first L3
implementation must resolve each name to a geometry version and record
that version in every output manifest.

| Subsystem | Fiducial cut | Edge buffer | Output field | Failure label |
|---|---|---|---|---|
| TPC drift volume | track anchor and fitted direction remain within active TPC module envelope for the usable path length | `tpc_edge_buffer_mm` applied to nearest active face | `tpc_fiducial_state` | `outside_tpc_active_volume` |
| TPC track length | V.1/V.2 track has enough contained length for a stable direction and dE/dx path length | `min_contained_track_length_cm` | `contained_track_length_cm` | `short_contained_track` |
| Scintillator coverage | C.3/C.4 matched hit lies inside an instrumented scintillator module reached by the projected track | `scintillator_edge_buffer_mm` around module boundaries | `scintillator_coverage_state` | `outside_scintillator_coverage` |
| Lead-glass coverage | photon or pi0 shower axis intersects an active lead-glass block face inside the block grid | `leadglass_edge_buffer_mm` around block-face and module cracks | `leadglass_acceptance_state` | `outside_leadglass_acceptance` |
| Foil radial edge | reconstructed V.4 vertex radius is inside the foil radius after subtracting an uncertainty-aware buffer | `foil_radial_buffer_mm = max(static buffer, 2 sigma_r)` | `foil_radial_state` | `near_foil_radial_edge` |
| Foil z edge | reconstructed V.4 vertex z is inside half-thickness after subtracting an uncertainty-aware buffer | `foil_z_buffer_mm = max(static buffer, 2 sigma_z)` | `foil_z_state` | `near_foil_z_edge` |
| Global event | all required subsystem states are pass or diagnostic-pass for the requested study tier | versioned policy profile | `fiducial_profile` | `fiducial_profile_fail` |

Recommended v0.1 policy profiles:

| Profile | Purpose | Rule |
|---|---|---|
| `none` | diagnose raw edge sensitivity | write states but do not reject events |
| `loose` | default plan-43 acceptance stress test | require foil pass and at least one contained charged or photon object |
| `tight` | systematic envelope | require all used reconstructed objects to pass their subsystem edge states |

## 4. Output schema

The fiducial producer writes two tables. The event table is joined into
plan 43; the object table lets subsystem owners diagnose which leaves
cause losses.

### 4.1 Event fiducial table

| Column | Dtype | Meaning |
|---|---|---|
| `event_id` | int | event id after plan 09 offsetting |
| `dataset_id` | string | plan 03 dataset id |
| `geometry_version` | string | plan 16 geometry/alignment tag |
| `profile` | string | `none`, `loose`, or `tight` |
| `vertex_r_mm` | float | reconstructed V.4 radius |
| `vertex_z_mm` | float | reconstructed V.4 z |
| `sigma_r_mm` | float/null | V.4 radial uncertainty if available |
| `sigma_z_mm` | float/null | V.4 z uncertainty if available |
| `foil_radial_pass` | bool | radius inside buffered foil |
| `foil_z_pass` | bool | z inside buffered foil |
| `has_contained_charged` | bool | at least one TPC/charged object passes containment |
| `has_accepted_photon` | bool | at least one photon or pi0 object passes lead-glass coverage |
| `fiducial_pass` | bool | profile-specific event result |
| `fiducial_reason` | string | primary pass/fail reason |

### 4.2 Object fiducial table

| Column | Dtype | Meaning |
|---|---|---|
| `event_id` | int | event id |
| `object_kind` | string | `charged`, `photon`, `pi0`, `vertex`, or `scintillator_match` |
| `object_id` | int/string | object-local id |
| `leaf` | string | plan 24 leaf that owns the object |
| `distance_to_nearest_edge_mm` | float/null | signed distance to the relevant boundary |
| `edge_buffer_mm` | float | applied buffer |
| `edge_state` | string | pass/fail/diagnostic state |
| `failure_label` | string/null | one of the labels in §3 |

Truth columns are forbidden in both output tables except when the table
is explicitly under a validation-only closure path.

## 5. Closure procedure

The procedure uses verified existing CLI surface only for table
production and validation. Any future fiducial producer is an L3-owned
implementation gate until its `--help` output exists.

1. Build reconstruction tables for the frozen signal sample. Plan 20
   names the target `sig_foil_v3`; the current plan 03 frozen registry
   id is `sig_foil_500MeV_v3`, so the manifest must record both the
   plan-20 alias and the plan-03 id.

   ```bash
   python -m nnbar_reconstruction.cli summarize \
       NNBAR_Detector/output/sig_foil_500MeV_v3 --all-runs \
       --tables-dir output/reco/sig_foil_500MeV_v3/ \
       --table output/reco/sig_foil_500MeV_v3/runs.csv \
       --json output/reco/sig_foil_500MeV_v3/summary.json
   ```

2. Build the charged calibration tables for `cal_singleproton_50to500MeV_v2`
   with the same command shape and a dataset-specific output directory.
3. **Blocked L3 implementation gate:** expose a help-verified fiducial
   producer that reads `vertices.csv`, `charged.csv`, `photons.csv`,
   `pi0.csv`, plan 16 geometry, and the selected profile, then writes
   the §4 event and object tables under `output/fiducial/<dataset_id>/`.
4. Run `validate-reco` on the same event set to keep truth-label
   validation separate from fiducial production:

   ```bash
   python -m nnbar_reconstruction.cli validate-reco \
       NNBAR_Detector/output/sig_foil_500MeV_v3 --all-runs \
       --json output/fiducial/sig_foil_500MeV_v3/validation.json
   ```

5. Save `efficiency_vs_radius.parquet` and `efficiency_vs_z.parquet`
   with bins, generated counts, reconstructed counts, selected counts,
   Wilson intervals, and profile name.
6. Assert every saved table has a manifest with dataset id, geometry
   version, command hashes, source table hashes, and profile.
7. Assert `profile=none` never changes any plan-37 selection boolean;
   it only writes diagnostics.

## 6. Efficiency-vs-edge reporting tables

The first report must include the following rows. Values are filled by
closure jobs, not by hand.

| Table | Bin axis | Datasets | Numerator | Denominator | Pass criterion |
|---|---|---|---|---|---|
| `efficiency_vs_radius` | vertex radius in 25 mm bins to the foil edge | `sig_foil_500MeV_v3`, `cal_singleproton_50to500MeV_v2` | events passing profile and S.6 | generated or validation-matched events in bin | no unmodelled >2σ cliff in the last two inner bins |
| `efficiency_vs_z` | vertex z in 1 mm bins across foil half-thickness and buffers | `sig_foil_500MeV_v3` | events passing profile and S.6 | generated foil-origin events in bin | symmetric efficiency within statistical uncertainty unless geometry says otherwise |
| `object_loss_by_subsystem` | subsystem/leaf | both datasets | objects failing edge state | objects entering subsystem | top loss source has named mitigation or nuisance |
| `profile_comparison` | `none`, `loose`, `tight` | `sig_foil_500MeV_v3` | final selected events | generated foil-origin events | loose and tight differences become plan 45 N8/N10 inputs |

The plan 43 efficiency factorisation consumes the `loose` profile by
default and quotes `tight-loose` as an edge systematic. The `none`
profile remains a diagnostic baseline and cannot be thesis-facing unless
plan 45 records why edge effects are negligible.

## 7. Per-observable acceptance budget

Every plan 43 signal-efficiency artifact that consumes a fiducial
profile must carry the observable-level budget below. The central value
is filled by the closure job; this plan fixes the denominator, the
profile dependency, and the nuisance handoff so reviewers can see
whether an edge cut protects or distorts the quoted observable.

| Observable / result | Denominator | Numerator | Profile comparison | Required budget fields | Ledger hook |
|---|---|---|---|---|---|
| signal acceptance | generated `sig_foil_v3` alias / `sig_foil_500MeV_v3` registry events | events with `fiducial_pass` before reconstruction and selection losses | `none`, `loose`, `tight` | central efficiency, Wilson interval, `tight-loose` shift, geometry tag | LIC-CH06 signal-acceptance rows |
| vertex residual / foil compatibility | events with reconstructable V.4 vertices | events passing V.5 and buffered foil states | `loose` vs `tight` | radial/z residual mean, pull width, edge-bin occupancy, N8 shift | plan 30 / plan 47 vertex rows |
| charged PID efficiency | charged candidates entering C.1-C.6 | candidates passing TPC and scintillator fiducial states plus PID validity | `loose` vs `tight` | C.1/C.2/C.3 object-loss fractions, DQM warn/fail counts, N1/N2/N8 hooks | plan 29 charged-PID rows |
| photon and pi0 efficiency | photon/pi0 candidates entering P.1-P.7 | candidates passing lead-glass acceptance and pi0 selection states | `loose` vs `tight` | edge-loss fraction, pi0-mass shift, N3/N8/N10 hooks | plans 34-35 / plan 47 pi0 rows |
| final S.6 selection efficiency | generated signal events | events passing fiducial profile and plan 37 S.6 | `none`, `loose`, `tight` | direct selected/generated ratio, product closure against plan 43 factors, covariance with object losses | LIC-CH10 cut-flow rows |

A budget row is complete only if it records the plan-03 dataset id, the
plan-20 alias when applicable, the fiducial profile, the geometry tag,
and the dominant plan 45 nuisance IDs. Missing fields downgrade the
corresponding plan 47 row to `not-attempted` even if the raw event count
exists.

## 7.1 Wave 6 per-leaf fiducial derivations

Leaf-specific fiducial derivations are split into child files so this
parent plan stays below the 500-line cap. Current children:

- `docs/rebuild_plans/60_fiducial_volume_and_edge_effects/60_v1_tpc_containment_fiducial.md`
- `docs/rebuild_plans/60_fiducial_volume_and_edge_effects/60_v2_track_fit_containment_fiducial.md`
- `docs/rebuild_plans/60_fiducial_volume_and_edge_effects/60_v3_projection_fiducial.md`
- `docs/rebuild_plans/60_fiducial_volume_and_edge_effects/60_v4_vertex_quality_fiducial.md`
- `docs/rebuild_plans/60_fiducial_volume_and_edge_effects/60_v5_foil_acceptance_fiducial.md`
- `docs/rebuild_plans/60_fiducial_volume_and_edge_effects/60_c1_charged_candidate_fiducial.md`

## 8. Systematics and ledger integration

Edge effects map to existing plan 45 nuisances:

| Edge source | Plan 45 hook | Required artifact |
|---|---|---|
| alignment-driven vertex or projection drift | N8 Geometry alignment | profile comparison under `perfect`, `nominal_survey`, and `worst_case_construction` geometry tags |
| material-induced conversion or scattering near boundaries | N10 Material budget | object-loss comparison with conversion and multiple-scattering categories |
| scintillator / lead-glass module crack response | N2/N3 detector calibration if energy scale dominates, otherwise N8 geometry | edge-loss table split by subsystem |
| missing sensor noise / dead channels | plan 01 L3/L4 caveat until a channel-mask nuisance exists | explicit plan 47 caveat field |

Plan 47 rows that quote signal acceptance, vertex resolution,
pi0-mass width, or selection efficiency must store the fiducial profile
and geometry version. A row without those two fields is incomplete, even
if its numeric efficiency agrees with the thesis.

## 9. Alternatives and promotion policy

| Alternative | Pros | Cons | Promotion rule |
|---|---|---|---|
| No fiducial cut, diagnostics only | maximum statistics; exposes raw edge behaviour | edge-driven failures can contaminate quoted efficiency | allowed only for debugging and profile comparison |
| Loose fiducial profile | protects obvious foil/subsystem edges while retaining statistics | can leave small crack effects in photon/scintillator observables | default if §6 tables show smooth efficiency and plan 45 nuisance covers residuals |
| Tight fiducial profile | conservative; simpler reviewer defence | can hide reconstruction deficiencies and reduce signal acceptance | use for systematic envelope or if loose profile fails edge-smoothness checks |
| Covariance-aware adaptive buffer | principled per-event uncertainty treatment | requires V.2/V.3/V.4 covariance fields that are not fully live yet | promote after plans 26 and 30 produce covariance-complete tables |

Any change to the default profile, buffer size, or edge-smoothness pass
criterion is a methodology change and needs a plan 05 decision-log entry
before plan 43 or plan 47 can quote the result.

## 10. Software handoff and blocker contract

The verified live CLI can build reconstruction tables, validation
metrics, and run-quality artifacts with `summarize`, `validate-reco`,
and `dqm`. The DQM surface is relevant because §7 budget rows may carry
DQM warn/fail counts alongside edge-loss fractions. The live software
does not yet expose a detector-wide fiducial producer. Until that
producer has a help-verified surface, this plan's runnable work stops at
table production, validation, DQM support, and schema/manifest
assertions.

The current support surface covers only the plan-30 foil subset:
`apply_foil_acceptance` (`nnbar_reconstruction/vertex_reco.py:157-194`) and
`FoilGeometry` (`nnbar_reconstruction/vertex_reco.py:13-18`) are tested by
`test_aggregate_and_accept_vertices_use_plan_16_geometry_only`
(`tests/test_vertex_reco.py:77-100`). That coverage is necessary for
the V.5 foil row, but it is not sufficient for detector-wide fiducial
production across TPC containment, scintillator coverage, lead-glass
coverage, and profile/budget export.

L3/software handoff requirements:

1. The fiducial producer reads `vertices.csv`, `charged.csv`,
   `photons.csv`, `pi0.csv`, plan 16 geometry/alignment side-cars, and
   a named profile (`none`, `loose`, or `tight`). It writes both §4
   tables and fails if any active subsystem in §3 lacks an edge state.
2. The edge-report producer reads the fiducial event/object tables,
   truth denominators where validation is allowed, and plan 43
   selection outputs. It writes the §6 radius, z, subsystem-loss, and
   profile-comparison tables without mutating plan 37 selection flags.
3. The budget exporter writes the §7 per-observable rows with dataset
   id, plan-20 alias, geometry tag, fiducial profile, nuisance ids, and
   plan 47 ledger hook. Missing budget fields downgrade the consumer row
   rather than being filled by hand.
4. All fiducial artifacts record source hashes, geometry version,
   profile name, command hashes for the verified upstream steps,
   bootstrap/Wilson settings, and the plan 45 nuisance handoff.
5. New command lines may be added only after their CLI surfaces are
   verified under the A+ examiner gate. Until then, this section is a
   software contract, not a runnable command list.

### 10.1 Fiducial artifact manifest schema

The fiducial producer, edge-report producer, and budget exporter must
write manifest rows that freeze the geometry/profile state consumed by
plan 43:

```yaml
schema_version: plan60_fiducial_edges@stage-e1
dataset_id: sig_foil_500MeV_v3
plan20_alias: sig_foil_v3
producer_stage: fiducial_tables | edge_reports | budget_export
geometry_version: <plan-16 geometry/alignment tag>
fiducial_profile: none | loose | tight
input_table_hashes: {vertices: <sha256>, charged: <sha256>, photons: <sha256>, pi0: <sha256>, events: <sha256>}
event_fiducial_hash: <sha256 of §4.1 table>
object_fiducial_hash: <sha256 of §4.2 table>
edge_report_hashes: {radius: <sha256>, z: <sha256>, subsystem_loss: <sha256>, profile_comparison: <sha256>}
budget_export_hash: <sha256 of §7 budget table>
dominant_nuisance_ids: [N8, N10]
dqm_manifest_hash: <sha256|null>
producer_help_verified: true
```

The manifest is invalid if any active subsystem in §3 lacks an edge
state, if geometry version or profile is missing, or if a budget row is
written without the plan 45 nuisance handoff. Plan 43 must consume this
manifest hash before quoting any fiducial-profile efficiency.

## 11. Acceptance criteria

- §3 names a fiducial rule for every active subsystem and foil edge.
- §4 event and object schemas are implemented by an L3 help-verified
  producer before any efficiency quote consumes them.
- §5 closure runs on `sig_foil_500MeV_v3` and
  `cal_singleproton_50to500MeV_v2` with manifests and hashes.
- §6 radius/z/profile tables exist and show no unexplained edge cliff.
- §7 per-observable budget rows record denominator, numerator,
  profile comparison, ledger hook, and dominant nuisance IDs.
- §8 maps residual edge effects to plan 45 nuisance IDs or explicit
  plan 01 caveats.
- Plan 43 stores the selected fiducial profile and geometry version in
  every signal-efficiency artifact.
- §10 software handoff is complete: fiducial production, edge reports,
  and budget export have explicit inputs, outputs, failure assertions,
  provenance fields, a required manifest schema, the existing foil-only
  support surface is cited, the current DQM support surface is cited,
  and a no-invented-CLI rule is in force.

## 12. Dependencies

- **03** — dataset ids and frozen sample status.
- **04** — Wilson intervals and bootstrap/jackknife uncertainty rules.
- **16** — geometry constants, alignment tags, and material edge inputs.
- **30** — V.3/V.4/V.5 vertex and foil-compatibility semantics.
- **43** — signal-efficiency factorisation consuming fiducial profiles.
- **45** — N8/N10 and detector-calibration nuisance hooks.
