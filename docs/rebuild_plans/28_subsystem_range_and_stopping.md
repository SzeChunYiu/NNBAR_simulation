---
id: 28_subsystem_range_and_stopping
title: Subsystem — range and stopping (leaf C.3)
version: 0.1
status: draft
owner: Charged-PID POG
depends_on: [00_README, 18_intercalibration, 23_sample_calibration_aux, 24_reconstruction_question_tree, 25_subsystem_tpc_hits_to_tracks]
outputs:
  - {path: docs/rebuild_plans/28_subsystem_range_and_stopping.md, schema: this file}
acceptance:
  - {test: scintillator range estimate on cal_singleproton_50to500MeV_v2 vs validation path-length residual < 1 cm, method: per-sample closure, pass_when: pass}
  - {test: Bragg-peak position resolved within scintillator bar pitch on stopping protons, method: §3 closure, pass_when: pass}
risks:
  - {risk: scintillator hit pitch limits range resolution, mitigation: §3 documented hardware floor}
estimated_effort: S
last_updated: 2026-05-10
---

# Subsystem — range and stopping

*Charter.* Owns leaf C.3 (plan 24 §3). The scintillator stopping
range distinguishes short-range protons from long-range pions.

## 1. Range estimator

Match scintillator hits to TPC track via configurable angle and
distance (plan 08 §3.4: `charged_scintillator_match_angle_deg = 10°`,
`charged_scintillator_match_distance_cm = 15 cm`).

Range = max distance from track entry to last associated scintillator
hit, projected along the track direction.

Outputs: `range_cm`, `range_eDep` (energy in matched hits).

Per plan 24 C.3 schema:

### 1.1 Leaf schema block

Leaf C.3 — range and stopping observables

- **inputs (Class A):** C.1 charged-candidate rows, V.2 direction
  rows, C.4 matched scintillator hit `Event_ID`, `x`, `y`, `z`, `t`,
  `eDep`, `photons`, `module_ID`, `vol_name`, `step_info`, and the
  scintillator geometry side-car.
- **forbidden (Class B):** `Name`, `Track_ID`, `Parent_ID`,
  `origin_vol_name`, `particle_x`, `particle_y`, `particle_z`.
- **decision rule:** estimate range by projecting Class A
  scintillator hits along the reconstructed track direction; exact
  `Track_ID` matching is allowed only as a reproduction diagnostic, not
  as the production C.3 association rule.
- **output schema:** `event_id: int`, `charged_candidate_id: int`,
  `range_cm: float`, `range_edep_mev: float`,
  `n_scintillator_hits: int`, `last_hit_module_id: int | null`,
  `bragg_peak_position_cm: float | null`, `range_valid: bool`.
- **allowed truth use:** `validation_only` for PSTAR/range closure and
  stopping-proton slices after C.3 output is frozen.
- **downstream consumers:** plans 29, 38, 40, and range/stopping
  systematics in plan 45.

### 1.2 Column contract

| Class A inputs | Forbidden Class B |
|---|---|
| C.1 charged-candidate table; V.2 direction table; C.4 matched scintillator hit columns `Event_ID`, `x`, `y`, `z`, `t`, `eDep`, `photons`, `module_ID`, `vol_name`, `step_info`; scintillator geometry side-car | `Name`, `Track_ID`, `Parent_ID`, `origin_vol_name`, `particle_x`, `particle_y`, `particle_z` |

Legacy implementation citation: `reconstruct_charged_objects`
(`nnbar_reconstruction/charged.py:151-228`, plan 08 §3.4) reports
`scintillator_range` after matching hits by angular/distance cuts or,
for sparse legacy tables, exact `Track_ID` fallback. The fallback is
not a production C.3 rule. The live Stage E.1 hook is
`reconstruct_range_table` (`nnbar_reconstruction/range_reco.py:78-107`), which consumes V.1
candidates, V.2 fit rows, and Class A scintillator hits, then delegates
projection and Bragg-position extraction to `_range_row`
(`nnbar_reconstruction/range_reco.py:41-75`) or `_invalid_row` (`nnbar_reconstruction/range_reco.py:28-38`) when
inputs cannot support a range.

Output schema: `{event_id, charged_candidate_id, range_cm,
range_edep_mev, n_scintillator_hits, last_hit_module_id,
bragg_peak_position_cm, range_valid}`. The current live hook emits this
physics schema; §4 quality, edge, and association-method columns remain
explicit L3 follow-up gates before closure sign-off.

### 1.3 Machine-readable C.3 range fixture

The C.3 fixture freezes the scintillator association and range
observable before charged-PID scoring or stopping-proton closure reads
validation labels. It stores one row per charged candidate plus an
associated-hit sidecar:

| Fixture field | Meaning / invariant |
|---|---|
| `event_id`, `charged_candidate_id` | join key inherited from C.1/V.1 |
| `range_id` | stable method/version label for the configured range estimator |
| `association_method` | `angular_distance`, `projected_path`, or `legacy_track_id_diagnostic` |
| `range_cm`, `range_edep_mev` | projected range and associated energy, or null with a failure reason |
| `n_scintillator_hits`, `last_hit_module_id` | association multiplicity and terminal module |
| `bragg_peak_position_cm`, `range_valid` | optional stopping diagnostic and production validity flag |
| `range_quality_state`, `range_failure_reason` | §4 quality contract in machine-readable form |
| `scintillator_edge_distance_mm`, `scintillator_profile_bin` | plan 60 and closure binning hooks |

The sidecar keyed by `(event_id, charged_candidate_id, range_id)`
records the ordered scintillator hit ids, projected distance, and
whether each hit contributes to the Bragg-profile fit. Dropping
`Track_ID`, `Name`, `Parent_ID`, validation path length, and truth
species from the production input must not change rows whose
`association_method` is not explicitly diagnostic.

## 2. Bragg-peak

For stopping protons, the energy-vs-position profile peaks near the
end of the range. The Bragg-peak position is the inflection in
cumulative eDep as a function of distance along the track.

The Wave 2 baseline keeps Bragg information as a diagnostic feature:
`bragg_peak_position_cm` is written when at least three matched
scintillator hits define an ordered profile, and is null otherwise.
Promotion into PID requires a plan 29 / plan 57 comparison showing
incremental C.5 discrimination beyond `{range_cm, dedx_mev_per_cm}`
without consuming truth labels in the production decision path.

### 2.1 Alternative comparison rows

| Alternative | Source paper / codebase | NNBAR-specific adaptation | Expected ladder leaf delta |
|---|---|---|---|
| Farthest matched scintillator hit | Existing `reconstruct_charged_objects` (`nnbar_reconstruction/charged.py:151-228`) | Preserve the angular/distance match as the reproduction baseline; disable the exact `Track_ID` fallback for production C.3. | Baseline C.3 range with known granularity floor from scintillator pitch. |
| Projected path-length integration | Range-stack / sampling-calorimeter reconstruction practice | Project V.2 track direction through ordered scintillator modules and accumulate Class A hit distances until the last in-time module. | Expected to reduce range bias when hits skip modules or the farthest-hit point is noisy. |
| Bragg-profile endpoint fit | Stopping-proton Bragg-curve reconstruction | Fit cumulative eDep versus projected distance and report `bragg_peak_position_cm` plus fit quality. | Improves stopping-proton discrimination for C.5 when enough scintillator hits exist. |
| PSTAR-constrained range check | NIST PSTAR proton ranges used only in validation | Compare reconstructed range to kinetic-energy bins inside closure; do not use truth KE or species in production. | Adds calibration/systematics leverage for C.3 without loosening Class A production rules. |

## 3. Closure-test specification

1. **Dataset id:** `cal_singleproton_50to500MeV_v2` from plan 03,
   with stopping-proton slices identified only inside validation.
2. **Observable:** reconstructed `range_cm`, `range_edep_mev`, and
   `bragg_peak_position_cm` versus validation path length and initial
   kinetic-energy bins.
3. **Fitter / model:** compare mean range to PSTAR proton ranges and
   fit the cumulative eDep profile to locate the Bragg inflection;
   truth path length is a validation target, not an estimator input.
4. **Pass criterion:** mean range agrees within 1 cm or one
   scintillator bar pitch, whichever is larger; Bragg peak is resolved
   within one bar pitch for stopping protons.

## 4. Range-quality and edge diagnostics

The range estimator must publish diagnostic state separately from the
PID decision so that plan 66 can flag run-quality drift without changing
plan 29 scoring. The minimum diagnostic fields are:

| Field | Meaning | Consumer |
|---|---|---|
| `range_quality_state` | `pass`, `warn`, `fail`, or `not_applicable` for the C.3 object | plan 66 DQM |
| `range_failure_reason` | first blocking reason, if any | plan 47 caveat text |
| `scintillator_edge_distance_mm` | signed distance of the terminal associated hit to the nearest active-module edge | plan 60 edge studies |
| `scintillator_profile_bin` | coarse longitudinal bin used for Bragg-profile closure | plan 28 closure and plan 45 systematics |
| `association_method` | `angular_distance`, `legacy_track_id_diagnostic`, or future method label | plan 38 ladder rows |

Quality semantics:

- `pass` means at least one Class A scintillator association exists, the
  projected range is finite, and the object is not in the configured
  scintillator edge buffer.
- `warn` means the object is usable for diagnostic plots but has sparse
  scintillator coverage, missing Bragg fit, or an edge-distance warning.
- `fail` means the range is non-finite, negative, or based only on a
  production-forbidden exact `Track_ID` association.
- `not_applicable` is reserved for charged candidates that do not enter
  the scintillator acceptance volume under plan 60.

These flags do not change the PID label by themselves. Promotion of any
quality state into a hard PID veto is a methodology change that requires
plan 05 approval and a plan 38 C.3/C.5 ladder delta.

## 5. Stage E.1 implementation handoff

For L3's charged-side redesign, C.3 is now a typed range seam with
explicit remaining gates:

1. Inputs are C.1 charged candidates, V.2 direction/covariance rows,
   Class A scintillator hits, and the plan 60 geometry side-car. The
   live hook currently uses V.2 direction rows and all event-scoped
   scintillator hits; it must add geometry edge distances once plan 60's
   side-car is implemented.
2. The production association path is projected path-length matching;
   exact `Track_ID` is retained only under an explicitly named diagnostic
   mode.
3. The module writes §1 physics observables in one row per charged
   candidate. L3 still must add `range_id`, `association_method`,
   `range_quality_state`, `range_failure_reason`,
   `scintillator_edge_distance_mm`, `scintillator_profile_bin`, and the
   associated-hit sidecar before plan 40/45 closure can treat C.3 as
   complete.
4. The closure runner compares range and Bragg position only after the
   output table is frozen, with truth path length held in a validation
   namespace.
5. Plan 29 consumes only `range_cm`, `range_edep_mev`,
   `bragg_peak_position_cm`, and `range_valid` unless a later DEC
   promotes a quality field into PID.
6. Plan 66 consumes range quality, edge-distance, and association-method
   fractions once the §4 fields are present.

### 5.1 L3 target module, functions, and tests

- **Target module:** extend `nnbar_reconstruction/range_reco.py`.
- **Public function:** `reconstruct_range_table(candidates, fits,
  scintillator)` (`nnbar_reconstruction/range_reco.py:78-107`).
- **Current unit coverage:** `tests/test_charged_reco.py` already
  builds synthetic candidates, V.2 fit rows, and scintillator hits in
  `test_reconstruct_range_table_projects_scintillator_hits`
  (`tests/test_charged_reco.py:224-259`) and asserts projected
  `range_cm`, `range_edep_mev`, `bragg_peak_position_cm`, hit count,
  module id, and `range_valid`.
- **Current integration coverage:** the real-output chain is
  `test_reconstruct_range_table_real_sample_has_plan_28_schema`
  (`tests/test_charged_reco.py:262-279`), which feeds plan-25
  candidates and plan-26 fits into `reconstruct_range_table` on a
  scintillator fixture when available.
- **Remaining test obligation:** extend those tests for invalid-row
  behavior, no-`Track_ID` production dependency, geometry
  edge-distance fields, and the future associated-hit sidecar.

### 5.2 Stage E.1 code-gap checklist

The live L3 hook already projects Class A scintillator hits along V.2
directions, but the promoted C.3 fixture still needs explicit method,
quality, and edge provenance. L3 can promote C.3 only after these gaps
close in `reconstruct_range_table` (`nnbar_reconstruction/range_reco.py:78-107`):

| Gap | Current live behavior | Required promotion behavior |
|---|---|---|
| range identity | physics rows carry no stable range-estimator id | add `range_id` so plan 38/40/45 artifacts can key the configured C.3 method |
| association method | projected forward-hit association is implicit in `_range_row` (`nnbar_reconstruction/range_reco.py:41-75`) | add `association_method=projected_path` for production rows and reserve `legacy_track_id_diagnostic` for validation-only reproduction |
| invalid-row reason | `_invalid_row` (`nnbar_reconstruction/range_reco.py:28-38`) sets `range_valid=false` but does not explain the failure | add `range_quality_state` and `range_failure_reason` with the §4 semantics |
| edge provenance | no scintillator edge distance or profile bin is emitted | add `scintillator_edge_distance_mm` and `scintillator_profile_bin` once plan 60's geometry side-car is available |
| hit sidecar | associated scintillator hit ids and projected distances are not persisted | add the sidecar keyed by `(event_id, charged_candidate_id, range_id)` for Bragg closure and plan 45 systematics |

Acceptance of this checklist is a plan-side gate, not a request for L0
to edit L3 code. The matching L3 patch must update
`test_reconstruct_range_table_projects_scintillator_hits`
(`tests/test_charged_reco.py:224-259`) and
`test_reconstruct_range_table_real_sample_has_plan_28_schema`
(`tests/test_charged_reco.py:262-279`) so the synthetic and real-output
chains assert every required C.3 promotion column and invalid-row
reason.

### 5.3 Stage E.1 promotion invariants

The current live hook is a truth-blind projected-range bridge. L3 may
replace the association or geometry side-car only if these invariants
remain stable for C.3 consumers:

| Invariant | Current live behavior | Replacement requirement |
|---|---|---|
| truth blindness | `reconstruct_range_table` (`nnbar_reconstruction/range_reco.py:78-107`) consumes C.1 candidates, V.2 fits, and Class A scintillator rows | production output must be unchanged when legacy `Track_ID`, truth path length, or species labels are absent |
| range identity | current rows have no stable estimator id beyond the table columns | promoted rows must add `range_id` so plan 38/40/45 artifacts can key the configured association method |
| association transparency | `_range_row` (`nnbar_reconstruction/range_reco.py:41-75`) projects scintillator hits forward along the fitted direction | promoted rows must set `association_method=projected_path` and reserve any exact-id reproduction as `legacy_track_id_diagnostic` |
| invalid-row semantics | `_invalid_row` (`nnbar_reconstruction/range_reco.py:28-38`) emits `range_valid=false` with null physics fields | replacements must add `range_quality_state` and `range_failure_reason` before plan 29 can distinguish no-hit, bad-fit, and edge-loss cases |
| edge-profile provenance | current rows do not know the scintillator edge distance or profile bin | the plan 60 side-car must populate `scintillator_edge_distance_mm` and `scintillator_profile_bin` before fiducial systematics consume C.3 |
| sidecar reproducibility | associated hit ids and projected distances are not persisted | promoted rows must write an associated-hit sidecar keyed by `(event_id, charged_candidate_id, range_id)` for Bragg closure and nuisance propagation |

These invariants make C.3 promotion explicit without asking L0 to edit
L3 code. They also keep plan 29 charged PID from interpreting missing
range rows as physics until the failure reason and edge-distance fields
are present.

### 5.4 Stage E.1 producer/consumer contract

The L3 C.3 patch must make range association reproducible across PID,
closure, fiducial, and systematics consumers:

| Contract item | Required behavior | Downstream check |
|---|---|---|
| input key | consume C.1 candidates and V.2 fit rows by `(event_id, charged_candidate_id)` plus `fit_id` when available | range rows can be traced to the exact direction/covariance row used for projection |
| output key | emit one C.3 row keyed by `(event_id, charged_candidate_id, range_id)` for each attempted charged candidate | plan 29 PID can join range features without treating missing rows as physics |
| associated-hit sidecar | write matched scintillator hit ids, projected distances, and Bragg-rank fields keyed by the output key | plan 40/45 closure can audit range and Bragg observables without re-running association |
| geometry provenance | record plan 60 geometry/profile hash, edge distance, and scintillator profile bin | fiducial and edge-effect systematics can separate detector coverage from PID behavior |
| source hashes | record C.1 candidate hash, V.2 fit hash, and scintillator input hash in the manifest | plan 47 can prove C.3, C.5, and nuisance artifacts used the same upstream rows |
| failure taxonomy | emit `range_quality_state` and `range_failure_reason` for no-hit, bad-fit, backward-only, or edge-loss rows | plan 66 DQM and plan 29 PID consume explicit reasons, not null `range_cm` inference |

This contract keeps `reconstruct_range_table`
(`nnbar_reconstruction/range_reco.py:78-107`) as the Stage E.1 C.3
producer until L3 replaces the projection implementation behind the
same keys.

### 5.5 Stage E.1 verification command

L3's C.3 patch is promotable only when the range slice exercises the
projected-hit unit path and the real-output C.1/V.2→C.3 chain:

```bash
pytest tests/test_charged_reco.py::test_reconstruct_range_table_projects_scintillator_hits \
       tests/test_charged_reco.py::test_reconstruct_range_table_real_sample_has_plan_28_schema
```

The review note for that patch must quote the command output and the
C.3 artifact manifest fields `range_id`, `association_method`,
`range_quality_state`, `range_failure_reason`,
`scintillator_edge_distance_mm`, and `scintillator_profile_bin`. If the
real-output selector skips because scintillator fixtures are missing,
C.3 cannot feed plan 29 PID promotion or plan 60 fiducial profiles.

### 5.6 Stage E.1 artifact manifest schema

The C.3 producer must write a manifest that freezes range-association
identity, geometry provenance, and associated-hit sidecars before PID or
fiducial artifacts consume range rows:

```yaml
schema_version: plan28_c3_range@stage-e1
dataset_id: <plan-03 dataset id>
producer: reconstruct_range_table
range_id: <stable range-estimator version>
association_method: projected_path | legacy_track_id_diagnostic
input_c1_hash: <sha256 of C.1/V.1 candidate table>
input_v2_hash: <sha256 of V.2 fit table>
input_scintillator_hash: <sha256 of scintillator input table>
geometry_profile_hash: <sha256 of plan-60 geometry/profile sidecar>
output_range_hash: <sha256 of C.3 range table>
associated_hit_sidecar_hash: <sha256 of matched-hit sidecar>
edge_fields_required: [scintillator_edge_distance_mm, scintillator_profile_bin]
quality_states_allowed: [pass, warn, fail, not_applicable]
failure_reasons_allowed: [none, no_scintillator_hits, bad_fit_state, backward_only_hits, outside_scintillator_acceptance]
```

The manifest is invalid if `association_method` is omitted, if the
geometry profile hash is missing for edge-dependent rows, or if matched
hits cannot be joined back to `(event_id, charged_candidate_id,
range_id)`. Plans 29, 45, 60, and 66 consume this manifest before
trusting range or Bragg-profile observables.

### 5.7 Stage E.1 fixture matrix

The C.3 replacement patch must prove that range association is
observable-only and edge-aware before PID, fiducial, or DQM consumers
read the range manifest:

| Fixture case | Required input condition | Required assertion |
|---|---|---|
| truth-column drop | C.1/V.1, V.2, and scintillator rows are run with and without legacy track or truth path labels | `range_cm`, `association_method`, associated-hit sidecar keys, and quality state are unchanged |
| no forward scintillator hit | candidate has a valid V.2 direction but no scintillator hit in the projected forward cone | a C.3 row is emitted with `range_quality_state=fail` and `range_failure_reason=no_scintillator_hits` |
| bad fit state | the V.2 row is marked failed, degraded, or covariance-invalid | range production records `range_failure_reason=bad_fit_state` instead of recomputing direction from raw hits |
| backward-only hits | scintillator hits exist only behind the fitted direction anchor | row records `backward_only_hits` or equivalent failure and no PID feature is inferred from null range |
| edge-profile case | projected hit lies near the plan-60 scintillator edge/profile boundary | `scintillator_edge_distance_mm`, `scintillator_profile_bin`, and `geometry_profile_hash` are present before fiducial consumers read C.3 |
| real C.1/V.2 to C.3 chain | real paired output flows through plan 25 candidates and plan 26 fits first | C.3 consumes frozen upstream hashes and does not use exact `Track_ID` association outside validation artifacts |

The review artifact for any range replacement must state which fixture
rows are covered by synthetic tests, which require the real-output
selector from §5.5, and which remain gated on the plan-60 geometry
sidecar. Gated edge rows must still keep a manifest-level failure reason
so plans 29 and 66 do not infer detector acceptance from missing rows.

## 6. Acceptance criteria

- §3 closure passes.
- §2 Bragg-peak diagnostic is either written with a valid fit-status
  flag or explicitly null with a reason; any PID promotion cites a
  plan 38 C.3/C.5 ladder delta.
- §5 Stage E.1 handoff is actionable for L3: the target public
  function, current unit/integration tests, remaining test obligation,
  promotion invariants, producer/consumer contract, verification
  command, artifact manifest schema, fixture matrix, and required C.3 fields (`range_id`, `association_method`, `range_cm`,
  `range_edep_mev`, `bragg_peak_position_cm`,
  `range_quality_state`, `range_failure_reason`,
  `scintillator_edge_distance_mm`, `scintillator_profile_bin`, and
  associated-hit sidecar rows) are all named before replacement
  promotion.

## 7. Dependencies

- **18, 23, 24, 25** — inputs.
- *Consumed by:* plan 29 (PID).
