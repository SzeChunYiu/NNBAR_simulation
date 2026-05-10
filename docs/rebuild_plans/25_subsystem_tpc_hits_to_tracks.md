---
id: 25_subsystem_tpc_hits_to_tracks
title: Subsystem — TPC hits to track candidates (leaf V.1)
version: 0.1
status: draft
owner: Tracking POG
depends_on: [00_README, 01_realism_contract, 08_reconstruction_atomic_walkthrough, 09_io_schema_data_dictionary, 24_reconstruction_question_tree]
inputs:
  - {path: docs/rebuild_plans/20_sample_signal.md, schema: signal sample definition for `sig_foil_v3`}
  - {path: docs/rebuild_plans/03_dataset_registry.md, schema: charged calibration dataset id `cal_singlepion_50to600MeV_v2`}
outputs:
  - {path: docs/rebuild_plans/25_subsystem_tpc_hits_to_tracks.md, schema: this file}
acceptance:
  - {test: leaf V.1 has Class A inputs only, method: realism audit, pass_when: zero Class B reads in the V.1 production path}
  - {test: track-finding efficiency on cal_singlepion_50to600MeV_v2 ≥ 90% within fiducial, method: per-sample efficiency, pass_when: efficiency plus Wilson interval recorded, or signed limitation links the failing bin to plan 38 V.1 delta}
  - {test: alternative track-finder benchmarked on the ladder (Hough vs Kalman vs current), method: plan 38 IV(V.1), pass_when: matrix entry recorded}
risks:
  - {risk: current "first/last step" sparse representation loses tracking information, mitigation: §3 alternative finders restore intermediate steps when needed}
estimated_effort: M
last_updated: 2026-05-10
---

# Subsystem — TPC hits to track candidates

*Charter.* Owns leaf V.1 (plan 24 §2). The transformation from raw
TPC hits to track candidates is the foundation of vertex and charged-
PID. Improvements at this leaf propagate to V.2, V.3, V.4, C.1, …

## 1. Inputs and outputs

Per plan 24 §2.1 V.1 schema:

### 1.1 Leaf schema block

Leaf V.1 — TPC hits to track candidates

- **inputs (Class A):** `Event_ID`, `x`, `y`, `z`, `t`, `eDep`,
  `photons`, `px`, `py`, `pz`, `xHitID`, `module_ID`, `step_info`,
  `vol_name`.
- **forbidden (Class B):** `Track_ID`, `Parent_ID`, `Name`,
  `origin_vol_name`.
- **decision rule:** build track candidates from spatially and
  temporally compatible Class A TPC hits only. The current
  `Track_ID` grouping is a reproduction baseline and validation
  oracle, not an allowed production grouping rule.
- **output schema:** `candidate_id: int`, `event_id: int`,
  `hit_indices: list[int]`, `anchor_xyz: float[3]`,
  `direction_xyz: float[3]`, `n_hits: int`, `chi2_seed: float`.
- **allowed truth use:** `validation_only` for closure matching and
  ladder scoring; no Class B column may enter the production V.1
  candidate builder.
- **downstream consumers:** plans 26, 30, 38, and the charged-object
  reconstruction inputs consumed by plans 27–29.

### 1.2 Column contract

| Class A inputs (TPC parquet) | Forbidden Class B |
|---|---|
| `Event_ID`, `x`, `y`, `z`, `t`, `eDep`, `photons` (= electrons), `px`, `py`, `pz`, `xHitID`, `module_ID`, `step_info`, `vol_name` | `Track_ID`, `Parent_ID`, `Name`, `origin_vol_name` |

Output schema (`charged.csv` upstream, vertex.csv downstream):

```
candidate_id          # local id within event
event_id
hit_indices           # indices into TPC table for this event
anchor_xyz            # first hit position
direction_xyz         # unit vector
n_hits
chi2_seed             # quality estimator from fitter
```

### 1.3 Machine-readable V.1 candidate fixture

The L3 charged-side redesign needs a stable V.1 fixture before V.2,
vertexing, PID, or ladder scorers consume track candidates. The target
artifact stores one row per candidate plus a sidecar for hit membership:

| Fixture field | Meaning / invariant |
|---|---|
| `event_id`, `candidate_id` | stable join key; `candidate_id` is unique within each event |
| `hit_membership_key` | deterministic hash of sorted Class A TPC hit indices |
| `anchor_x`, `anchor_y`, `anchor_z` | first fitted/seeded point in detector coordinates |
| `direction_x`, `direction_y`, `direction_z` | finite unit direction vector used by V.2 |
| `n_hits` | number of Class A TPC hits in the candidate |
| `cluster_method` | `geometric_cluster`, `hough_seed`, `legacy_track_id_diagnostic`, or later DEC-approved method |
| `candidate_quality_state`, `candidate_failure_reason` | §5 quality contract in machine-readable form |
| `truth_grouping_used` | false for production rows; true only for legacy diagnostic fixtures |

The sidecar keyed by `(event_id, candidate_id, hit_membership_key)`
contains the ordered hit indices and optional per-hit residual seed
quantities. Dropping `Track_ID`, `Parent_ID`, `Name`, and
`origin_vol_name` from the input must not change any production fixture
row except rows explicitly labelled `legacy_track_id_diagnostic`.

## 2. Current implementation and live redesign hook

Legacy reconstruction still calls `_track_anchor_and_direction(group)`
(`nnbar_reconstruction/charged.py:62-81`). It sorts hits by time then input order; takes
anchor = first coord and direction = (last - first); and exposes no fit,
covariance, or quality cut beyond ≥ 2 valid coordinates. The legacy
grouping into "tracks" is driven by `Track_ID` (Class B violation), so
it remains a reproduction baseline and migration item, not the target
production V.1 path.

The live L3 charged-side hook for this plan is
`reconstruct_track_candidates` (`nnbar_reconstruction/charged.py:245-311`). It builds the
§1.3 typed V.1 candidate columns from Class A TPC hit coordinates,
records `cluster_method=geometric_cluster`, writes
`truth_grouping_used=False`, and uses `_hit_membership_key`
(`nnbar_reconstruction/charged.py:231-233`) plus `_track_seed_chi2` (`nnbar_reconstruction/charged.py:236-242`)
for stable membership and seed-quality fields. This is an initial
schema-producing hook: it unblocks V.2/plan-26 and DQM wiring, while
§3 alternatives still own the physics-performance upgrade from the
event-scoped seed to DBSCAN/Hough/Kalman candidates.

## 3. Alternative track finders (candidates for plan 49)

Each candidate is benchmarked on the truth-substitution ladder
(plan 38) at leaf V.1.

| Candidate | Source | Pros | Cons |
|---|---|---|---|
| **Geometric clustering** (DBSCAN-like in `(x, y, z, t)`) | new | Class A only | needs hit-density tuning |
| **Hough transform** (helix in cylindrical TPC) | ALICE | well-studied for TPC | no B-field; need straight-line variant |
| **Kalman seeded by Hough** | ACTS | covariance "for free" | implementation cost |
| **Riemann fit** | various | analytic for circles | not directly applicable without B-field |

### 3.1 Alternative comparison rows

| Alternative | Source paper / codebase | NNBAR-specific adaptation | Expected ladder leaf delta |
|---|---|---|---|
| Geometric clustering | DBSCAN (Ester et al.) / sklearn-style density clustering | Run in `(x, y, z, t)` after per-module normalisation; tune `eps` and `min_samples` on `cal_singlepion_50to600MeV_v2`. | Reduces V.1 truth substitution by removing the `Track_ID` grouping gate; possible efficiency loss in overlapping tracks. |
| Hough transform | ALICE TPC tracking notes / straight-line Hough variant | Use straight-line parameterisation because plan 17 has no B-field curvature; seed from TPC layer/module IDs. | Improves V.1 robustness for sparse first/last-step records; may add fake tracks in shower-rich events. |
| Kalman seeded by Hough | ACTS track-fitting codebase | Treat Hough seeds as straight-track states and defer curvature terms until a magnetic-field scenario exists. | Should reduce V.1 damage in the plan 38 matrix by stabilising V.2 direction covariance and V.4 vertex weighting; score against visible mass, vertex residuals, and charged multiplicity. |
| Riemann fit | Riemann-circle fit literature | Keep as a documented non-baseline option; without curvature it degenerates to a line-fit cross-check. | Low expected V.1 gain in the current no-B-field setup; useful mainly as a systematic comparison. |

The current "no B-field" configuration (plan 17) makes tracks
straight; this simplifies finders but eliminates momentum measurement
from curvature — momentum currently comes from kinematics (KE on
hits) plus stopping-range information.

## 4. Closure-test specification

1. **Dataset id:** `cal_singlepion_50to600MeV_v2` from plan 03,
   restricted to fiducial events with at least two Class A TPC hits.
2. **Observable:** V.1 track-finding efficiency and fake-candidate
   rate, reported with plan 04 Wilson intervals.
3. **Fitter / matcher:** run the candidate V.1 finder under test;
   match reconstructed candidates to truth tracks only inside a
   `@validation_only` scoring function using hit overlap / `Track_ID`.
4. **Pass criterion:** efficiency ≥ 90% in the fiducial slice, or a
   signed limitation documenting the loss mechanism and the ladder
   delta in plan 38.

## 5. Candidate-quality and DQM handoff

V.1 must expose candidate-building health before V.2, vertexing, or
charged PID consumes its rows. The production table extends §1 with
these diagnostic fields:

| Field | Meaning | Consumer |
|---|---|---|
| `candidate_quality_state` | `pass`, `warn`, `fail`, or `not_applicable` for the candidate | plans 26, 66 |
| `candidate_failure_reason` | first blocking reason, if any | plan 47 caveats |
| `cluster_method` | `legacy_track_id_diagnostic`, `geometric_cluster`, `hough_seed`, or future label | plan 38 ladder rows |
| `class_a_hit_count` | number of Class A TPC hits used by the candidate | plans 26, 40 |
| `truth_grouping_used` | true only in validation/reproduction mode | plan 01 realism audit |

Quality semantics:

- `pass` means the candidate uses Class A hit grouping, has at least two
  finite coordinates, and exposes a stable hit-index list for V.2.
- `warn` means the candidate is finite but sparse, near a plan 60 TPC
  edge, or produced by a degraded geometric seed.
- `fail` means the candidate is non-finite, empty, or would require
  production use of `Track_ID` to exist.
- `not_applicable` is reserved for event categories that contain no TPC
  hit rows after plan 09 schema loading.

Plan 66 aggregates candidate-quality fractions per run. A jump in
`warn` or `fail` rows is a DQM issue and must not silently retune V.2
or PID thresholds.

## 6. Stage E.1 implementation handoff

For L3's charged-side redesign, V.1 is the first typed charged-side
module and the plan-side contract is now explicit:

1. Input is the event-scoped TPC Class A hit table with no required
   truth/provenance columns.
2. The live baseline emits one candidate seed per event with
   `cluster_method=geometric_cluster`; future DBSCAN/Hough/Kalman
   implementations may change candidate multiplicity but not the §1.3
   schema without a plan 05 decision.
3. The legacy `Track_ID` grouping remains available only as
   `legacy_track_id_diagnostic` for reproduction and validation.
4. Output one V.1 row per candidate with hit indices, anchor, seed
   direction, hit count, quality fields, and no Class B columns.
5. Freeze the V.1 table before V.2 pull scoring or plan 38 truth
   substitution reads validation labels.
6. Plan 66 consumes `candidate_quality_state`, `cluster_method`, and
   `class_a_hit_count` as DQM fields once the V.1 table is present.

### 6.1 L3 target module, functions, and tests

- **Target module:** extend `nnbar_reconstruction/charged.py` without
  reopening Class B truth columns.
- **Public function:** `reconstruct_track_candidates(tpc)`
  (`nnbar_reconstruction/charged.py:245-311`).
- **Current unit coverage:** `tests/test_charged_reco.py` already
  asserts truth-column invariance in
  `test_track_candidates_ignore_forbidden_truth_columns`
  (`tests/test_charged_reco.py:61-70`) and V.1 schema/quality fields in
  `test_track_candidates_emit_plan_25_schema_and_quality`
  (`tests/test_charged_reco.py:73-103`).
- **Current integration coverage:** the real-output schema path is
  `test_track_candidates_real_sample_reads_particle_and_tpc_schema`
  (`tests/test_charged_reco.py:106-117`), which reads paired
  `Particle_output_*.parquet` / `TPC_output_*.parquet` fixtures before
  calling the public function.
- **Remaining test obligation:** any new candidate finder must extend
  those same tests so `truth_grouping_used=False`,
  `hit_membership_key`, and no-`Track_ID` production behavior stay
  invariant across the replacement.

### 6.2 Stage E.1 promotion invariants

The current live hook is schema-complete enough to unblock V.2, but
any physics-performance replacement for the event-scoped seed must keep
these plan-side invariants:

| Invariant | Current live behavior | Replacement requirement |
|---|---|---|
| truth blindness | `reconstruct_track_candidates` (`nnbar_reconstruction/charged.py:245-311`) reads Class A hit coordinates and emits `truth_grouping_used=False` | replacement finder must remain unchanged when `Track_ID`, `Parent_ID`, `Name`, and `origin_vol_name` are dropped |
| stable membership | `_hit_membership_key` (`nnbar_reconstruction/charged.py:231-233`) hashes sorted hit indices | candidate splitting/merging must keep a deterministic `hit_membership_key` for each row and sidecar |
| seed quality | `_track_seed_chi2` (`nnbar_reconstruction/charged.py:236-242`) provides the current seed-quality scalar | replacement finder must either keep `chi2_seed` semantics or version the quality field through plan 05 |
| candidate id stability | current hook emits one `candidate_id=0` row per event | multi-candidate replacements must number candidates deterministically within each event |
| downstream quality gate | `candidate_quality_state` and `candidate_failure_reason` already exist | replacements must preserve `pass`/`warn`/`fail`/`not_applicable` semantics so plans 26 and 66 do not infer quality from missing rows |

Acceptance of this checklist is a plan-side gate, not a request for L0
to edit L3 code. The matching L3 replacement patch must update
`test_track_candidates_ignore_forbidden_truth_columns`
(`tests/test_charged_reco.py:61-70`),
`test_track_candidates_emit_plan_25_schema_and_quality`
(`tests/test_charged_reco.py:73-103`), and
`test_track_candidates_real_sample_reads_particle_and_tpc_schema`
(`tests/test_charged_reco.py:106-117`) so both synthetic and
real-output chains prove the invariants.

## 7. Acceptance criteria

- §1 inputs match plan 09 (no Class B in production path).
- §2 current implementation noted; migration item logged.
- §3 alternatives each list source, NNBAR adaptation, and plan 38
  V.1 expected-delta observables for plan 49 to consume.
- §6 Stage E.1 handoff is actionable for L3: the target public
  function, current unit/integration tests, remaining test obligation,
  and mandatory V.1 fields (`candidate_id`, hit indices, anchor,
  direction, hit count, `cluster_method`, `candidate_quality_state`,
  `candidate_failure_reason`, `truth_grouping_used=False`, and
  `hit_membership_key`) are all named before replacement promotion.

## 8. Dependencies

- **08** — current implementation.
- **24** — leaf identity.
- **38** — ladder benchmark.
- *Consumed by:* plans 26 (fit), 30 (vertex), 38 (ladder).
