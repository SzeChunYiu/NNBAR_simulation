---
id: 08_reconstruction_atomic_walkthrough
title: Reconstruction atomic walkthrough — what nnbar_reconstruction/ does
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [00_README, 01_realism_contract, 07_simulation_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/, schema: source tree}
  - {path: NNBAR_Detector/output/*.parquet, schema: simulation outputs (plan 09)}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough.md, schema: this file}
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/, schema: split section files}
acceptance:
  - {test: every public function in nnbar_reconstruction/*.py has a § entry, method: source ↔ doc cross-reference, pass_when: zero unmatched public symbols}
  - {test: every CLI command in cli.py is documented in §11, method: subcommand audit, pass_when: full coverage}
  - {test: every Class B truth column read by any function is listed under that function's "uses truth" line, method: realism audit (plan 01) cross-reference, pass_when: zero unlisted Class B reads}
risks:
  - {risk: walkthrough rots as code changes, mitigation: plan 53 CI rule blocks PRs that touch nnbar_reconstruction/ without updating this file}
  - {risk: duplicates plan 24 (question tree) on decision rules, mitigation: 08 describes "what is"; 24 names leaves and rules for "what should be"}
estimated_effort: XL
last_updated: 2026-05-09
---

# Reconstruction atomic walkthrough — what nnbar_reconstruction/ does

*Charter.* Forensic, function-by-function accounting of the existing
offline reconstruction package. Records what the code does today, with
file paths and line numbers, decision rules, hardcoded constants,
truth-column reads, and sparse-table fallback paths. Every reconstruction
plan that follows (24, 25–37, 47, 50) cites this baseline rather than
re-deriving it from source.

The package lives at `NNBAR_Detector/nnbar_reconstruction/`. It consumes
the parquet outputs documented in plan 09 (data dictionary), produced
by the Geant4 simulation walked through in plan 07.

## 1. Module map

| Module | Lines | Purpose |
|---|---|---|
| `__init__.py` | 6 | Re-exports `load_run`, `read_output_table`, `reconstruct_run` |
| `io.py` | 68 | Parquet reader; output-kind enumeration |
| `reconstruction.py` | 1764 | Reconstruction core: vertex, charged objects, photons, π⁰, event variables, selection |
| `cli.py` | 519 | Command-line entry points |
| `validation.py` | 509 | Truth-aware metric evaluation; readiness assessment |
| `calibration.py` | 137 | PID-threshold grid scan against truth labels |
| `geometry_audit.py` | 419 | Geometry-vs-reference cross-check (called from CLI) |
| `pi0_study.py` | 1974 | Truth-to-reco π⁰ mass ladder |
| `charged_study.py` | 2241 | Charged stress sample evaluation |
| `pi0_fake_study.py` | 325 | π⁰ fake-rate study on no-π⁰ samples |

Total: ≈ 8 000 lines of Python.

## 2. I/O layer (io.py, 68 lines)

### 2.1 OUTPUT_KINDS

`io.py:12–23` — the canonical list of simulation output kinds:

```
Particle, Interaction, Carbon, Silicon, Beampipe, TPC,
Scintillator, LeadGlass, PMT, GPUEnergy
```

This is the ground truth for the IO schema in plan 09. Adding a new
output requires editing this list and plan 09 in lock-step.

### 2.2 Functions

- `output_path(output_dir, kind, run=0) → Path` (`io.py:26–31`):
  builds `<output_dir>/<kind>_output_<run>.parquet`. Raises
  `ValueError` for unknown `kind`.
- `read_output_table(output_dir, kind, run=0) → DataFrame`
  (`io.py:34–45`): reads the file via `pyarrow.parquet`. Missing
  files return an *empty DataFrame* — this is the sparse-table
  contract that lets reconstruction run on partial simulations.
  macOS AppleDouble (`._*.parquet`) sidecars are bypassed by addressing
  the expected filename directly.
- `load_run(output_dir, run=0) → dict[str, DataFrame]`
  (`io.py:48–51`): reads every kind for one run.
- `discover_runs(output_dir) → Mapping[str, list[int]]`
  (`io.py:54–68`): scans the directory for `<kind>_output_<int>.parquet`
  files, returning per-kind run-id lists. AppleDouble files are
  excluded (`io.py:59`).

### 2.3 Truth-column reads

The IO layer is *Class A / B / C agnostic*. It returns the parquet
columns as-is. Truth-leakage discipline is enforced one layer up by
the realism audit (plan 01 §4) against `reconstruction.py` and the
study modules.

## 3. Reconstruction core (reconstruction.py, 1764 lines)

### 3.1 `ReconstructionConfig` dataclass (lines 16–55)

A frozen dataclass holding 30+ numerical thresholds. Defaults encode
the thesis-prescribed values where available. Key entries (with
thesis citations from `reconstruction.md`):

| Field | Default | Thesis anchor |
|---|---|---|
| `proton_dedx_min` | 8.0 | preliminary, not yet measured |
| `short_range_cm` | 20.0 | preliminary |
| `short_range_proton_dedx_min` | 4.5 | preliminary |
| `min_photon_energy` | 5.0 (MeV) | from photon-cluster threshold |
| `pi0_mass_min`, `pi0_mass_max` | 100, 180 (MeV) | Ch 8 π⁰ window |
| `pi0_total_energy_max` | 720 (MeV) | Ch 8 |
| `pi0_scint_energy_max` | 250 (MeV) | Ch 8 |
| `pi0_leadglass_energy_max` | 980 (MeV) | Ch 8 |
| `pi0_leadglass_fraction_min` | 0.55 | Ch 8 |
| `pi0_opening_angle_min_deg` | 30.0 | Ch 8 |
| `pi0_prompt_time_max_abs_residual_ns` | 2.0 | timing diagnostic |
| `photon_fragment_merge_angle_deg` | 2.0 | gamma-fragment merge |
| `charged_cluster_match_angle_deg` | 10.5 | calibration scan |
| `charged_cluster_match_time_tolerance_ns` | 50.0 | charged-cluster timing |
| `charged_scintillator_match_angle_deg` | 10.0 | scint–TPC match |
| `charged_scintillator_match_distance_cm` | 15.0 | scint–TPC match |
| `selection_scintillator_energy_min/max` | 20 / 2000 (MeV) | Ch 9 |
| `selection_invariant_mass_min` | 500 (MeV) | Ch 9 |
| `selection_sphericity_min` | 0.2 | Ch 9 |
| `selection_upper_scintillator_max` | 320 (MeV) | Ch 9 |
| `selection_lower_scintillator_max` | 930 (MeV) | Ch 9 |
| `electron_pair_max_entry_separation_cm` | 5.0 | Ch 8.2 |
| `scintillator_time_resolution_ns`, `leadglass_time_resolution_ns` | 1.0, 1.0 | configurable |
| `fast_pion_kinetic_energy_mev`, `slow_pion_kinetic_energy_mev` | 1000, 100 | Ch 7 timing window |
| `charged_pion_mass_mev` | 139.57039 | PDG |
| `speed_of_light_cm_per_ns` | 29.9792458 | physical constant |

`DEFAULT_CONFIG = ReconstructionConfig()` is exported and used by
every consumer that does not override fields.

### 3.2 Geometry / vector helpers (lines 60–197)

- `_empty(columns)` — DataFrame with the right column schema and zero
  rows. Used pervasively by sparse-table fallback paths.
- `_safe_sum(df, column)` — robust numeric sum tolerant of missing
  columns and NaN.
- `_pmt_photons_for_event(pmt, event_id)` (lines 70–86) — sums
  per-module *max* photon counts (not naive sum) to avoid
  double-counting multi-step PMT hits.
- `_unit_vector(values)` — normalises a 3-vector with NaN handling.
- `_weighted_centroid(group, energy_col="eDep")` (lines 96–116) —
  energy-weighted centroid with multiple fall-backs: invalid points
  filtered, falls back to unweighted mean if all weights are
  non-positive, returns origin if no valid points.
- `_weighted_time(group, time_col="t", energy_col="eDep")` —
  energy-weighted mean time with similar fall-back ladder.
- `_angle_between_deg(a, b)` — clipped `arccos` to avoid floating-
  point overshoots.
- `_span(points)` — maximum pairwise distance over `(particle_x,
  particle_y, particle_z)` columns. Used to estimate effective track
  span for sparse tables.
- `_track_direction_from_hits(group)` — wraps
  `_track_anchor_and_direction`; falls back to mean-momentum
  direction if positional data is unavailable.
- `_track_anchor_and_direction(group)` (lines 165–184) — sorts hits by
  time-then-input-order, returns first-hit anchor + unit vector from
  first to last hit. This is the *current* direction-from-hits
  algorithm; plan 25 evaluates it against alternatives.
- `_position_coordinates(df)` — preferred-column resolver: uses
  `particle_*` if present, else `x/y/z`.

**Truth use in helpers:** none. All helpers operate on Class A
columns (`x, y, z, t, eDep, px, py, pz, photons`) and the
`particle_*` columns which are either Class A (origin coordinates
recorded by the SD as a sensor-derived quantity, currently equal to
truth — limitation L1) or Class B if interpreted strictly as
production point. Plan 09 freezes the classification.

### 3.3 Vertex reconstruction (split)

Detailed forensic entries for vertex reconstruction live in
[`08_3_reconstruction_objects.md`](08_reconstruction_atomic_walkthrough/08_3_reconstruction_objects.md#33-vertex-reconstruction-located-by-section-heading-near-reconstructionpy200430).

### 3.4 Charged-object reconstruction (split)

Detailed forensic entries for `reconstruct_charged_objects` and helpers live in
[`08_3_reconstruction_objects.md`](08_reconstruction_atomic_walkthrough/08_3_reconstruction_objects.md#34-charged-object-reconstruction-lines--430700).

### 3.5 Photon / π⁰ reconstruction (split)

Detailed forensic entries for photon objects, π⁰ pairing, and related helpers
live in [`08_3_reconstruction_objects.md`](08_reconstruction_atomic_walkthrough/08_3_reconstruction_objects.md#35-photon--π⁰-reconstruction-lines--7001300).
### 3.6 Event variables (lines ≈ 1300–1600)

Per `reconstruction.md` §"event variables" (lines 35–80):

- *Calorimeter sums*: `calorimeter_edep`, scintillator and lead-glass
  per-hemisphere splits, in-time / out-of-time splits.
- *Multiplicities*: charged-object count, photon count, π⁰ count.
- *Visible mass*: invariant mass from object directions and
  deposited / visible energies. Documented as an *analysis surface,
  not a calibrated final estimator*.
- *PMT counts*: `pmt_photons` (per-module max) and `n_pmt_hits`.
- *Sphericity*: standard sphericity tensor with eigenvalue
  decomposition.
- *EL / ET* (longitudinal / transverse calorimeter energy): per the
  Ch 9 definitions
  `EL = Σ E_i cos α_i`, `ET = Σ E_i sin α_i`.
- *Upper / lower scintillator and lead-glass energy*: hemispheric
  partitioning per Ch 9.
- *Signed longitudinal calorimeter energy*: signed by direction along
  beam.
- *Out-of-time energy*: the Chapter 7 timing window applied per hit.

Plan 31 owns the per-variable deep dive; plan 41 owns the N-1 and
ROC studies on these variables.

### 3.7 Truth use audit (current state of the code, will change)

The current reconstruction reads the following Class B columns inside
its decision path. Each is flagged by the plan-01 realism audit and
must move out of the decision path before reproduction-ledger sign-off:

| Column | Where used | Why used today | Migration target |
|---|---|---|---|
| `Name` (TPC) | charged-object PID gating | "only assign π/p PID to truth-labelled tracks" | plan 24: drop the gate; PID rule applies to all reconstructed tracks; truth `Name` only enters validation |
| `Parent_ID` (LeadGlass) | gamma-shower grouping | recover gamma ancestors | plan 26: topological clustering replaces ancestry |
| `Interaction` table | shower-source ancestry | resolve descendants to source | plan 26: replaced by geometric grouping |
| `Track_ID` (Scintillator) | sparse-table fallback for charged-cluster matching | when no detector coordinates | plan 02: digitisation seam removes the sparse-fallback need |

The code currently has fallback paths that activate on sparse tables
without truth labels — those paths are *Class A* and should become the
*default*, with truth-aware paths gated behind `@validation_only`.

### 3.8 `reconstruct_run(output_dir, run, config)` orchestrator

Top-level entry point. Returns a dict of DataFrames:

```python
{
  "vertices":       <vertex table>,
  "charged":        <charged-object table>,
  "electron_pairs": <electron-pair table>,
  "photons":        <photon-object table>,
  "pi0":            <π⁰ candidate table>,
  "events":         <per-event summary table>,
}
```

Consumed by `cli.summarize`, `cli.validate_reco`, `pi0_study`,
`pi0_fake_study`, and `charged_study`.

The orchestrator path is the canonical reconstruction sequence; any
new step inserted here requires a paired DEC entry (plan 05) and an
update to plan 09 (data dictionary) for the new output columns.

## 4. CLI (cli.py, 519 lines)

Seven subcommands defined in `build_parser` (lines 363–509). Common
patterns:

- `--run <int>` (single) and `--runs <a,b,c>` (multi) and
  `--all-runs` (autodiscover). Helper `_resolve_runs(args)`
  (lines 125–128) returns the list. Multi-run merging uses a constant
  `EVENT_ID_OFFSET = 1_000_000_000` (line 27) so per-run event/track
  IDs do not collide.
- `--json` writes the report; stdout always prints the JSON payload.
- `--table` writes per-row CSVs for downstream plotting.

### 4.1 `summarize` (lines 57–94)

Reconstructs one run, emits a small summary JSON: object counts,
calorimeter sums, PMT counts, selected-pi0 count, mean sphericity,
cumulative cut-flow under `_cutflow` (lines 36–54).

The cut-flow constants in `_cutflow` (lines 37–44) are:
`pass_scintillator_energy → pass_tpc_foil_track →
pass_pion_count → pass_invariant_mass → pass_sphericity →
pass_scintillator_balance`. Cumulative AND chain.

### 4.2 `scan-pid` (lines 172–201)

Loads merged TPC + scintillator across runs, calls
`scan_charged_pid_thresholds` (calibration.py §5), prints top-N
configurations and the `calibration_usable` flag (true iff sample
contains both protons and pions in truth).

### 4.3 `validate-reco` (lines 239–294)

Reconstructs one or more runs with optional candidate PID overrides
(`--pid-proton-dedx-min`, `--pid-short-range-cm`,
`--pid-short-range-proton-dedx-min`), evaluates against truth via
`evaluate_reconstruction_truth` (validation.py §6), aggregates over
runs via `aggregate_reconstruction_truth`, scores readiness via
`assess_validation_readiness`. `--fail-on-not-ready` exits non-zero
when readiness fails.

The readiness gate floors are user-supplied via
`--min-class-count`, `--min-accuracy`, `--min-balanced-f1`,
`--min-electron-pair-purity`, `--min-pi0-efficiency`. Defaults are
permissive (zero) so that quoting validity flows from explicit user
intent.

### 4.4 `pi0-study` (lines 297–313)

Reconstructs one run, calls `evaluate_pi0_mass_ladder` (pi0_study.py),
optionally writes per-event ladder rows. The "mass ladder" is the
truth-vs-reco progression mentioned in `reconstruction.md`:
truth-only → truth direction + reco energy → reco direction + truth
energy → fully reco. This is a precursor to plan 38 (truth-substitution
ladder) and will be subsumed by it.

### 4.5 `charged-study` (lines 316–328)

Multi-run charged stress-sample evaluation via
`evaluate_charged_stress` (charged_study.py). Reports per-species
recovery, hit coverage, PID accuracy, and per-primary CSV rows.

### 4.6 `pi0-fake-study` (lines 331–350)

Multi-run no-π⁰ background evaluation via
`evaluate_pi0_fake_background` (pi0_fake_study.py). Optional
`--include-near-charged` and `--prompt-timing` flags toggle the
mass-window definition.

### 4.7 `geometry-audit` (lines 353–360)

Calls `audit_detector_geometry` (geometry_audit.py). Cross-checks
the active CMake source tree against
`docs/Detector_Geometry_Reference.md`.

## 5. Calibration (calibration.py, 137 lines)

### 5.1 `scan_charged_pid_thresholds` (lines 26–137)

Inputs:
- `tpc` DataFrame (TPC parquet content)
- `scintillator` DataFrame
- `proton_dedx_values`, `short_range_values`,
  `short_range_proton_dedx_values` (iterables)
- `base_config: ReconstructionConfig`

Behaviour:

1. Reconstructs charged objects on the merged sample
   (`reconstruct_charged_objects`).
2. Filters to truth-labelled tracks (`Name` ∈ proton, π+, π-).
   `_truth_pid` (lines 13–19) maps to {`proton`, `charged_pion`}.
   *Class B read* — explicitly marked because this is *training*
   data for the threshold scan, not production selection.
3. For each grid point of (proton_dedx, short_range,
   short_range_dedx), computes TP/FP/TN/FN, accuracy, proton
   precision/recall, π recall, balanced F1.
4. Returns a sorted DataFrame by
   (has_both_classes, balanced_f1, accuracy, proton_recall,
   pion_recall) descending.

This function is a *training-time tool*. Its output is meant to
inform manual default-cut updates. Plan 57 (MVA protocol) will absorb
this kind of threshold scan into a proper likelihood-ratio training
pipeline.

## 6. Validation (validation.py, 509 lines)

Detailed forensic entries for the validation public surface live in
[`08_6_validation.md`](08_reconstruction_atomic_walkthrough/08_6_validation.md).
## 7. π⁰ study (pi0_study.py, 1974 lines)

Detailed forensic entries for the π⁰ mass-ladder study live in
[`08_7_pi0_study.md`](08_reconstruction_atomic_walkthrough/08_7_pi0_study.md).
## 8. Charged study (charged_study.py, 2241 lines)

Detailed forensic entries for the charged stress-sample study live in
[`08_8_charged_study.md`](08_reconstruction_atomic_walkthrough/08_8_charged_study.md).
## 9. π⁰ fake study (pi0_fake_study.py, 325 lines)

Detailed forensic entries for the fake-π⁰ background study live in
[`08_9_pi0_fake_study.md`](08_reconstruction_atomic_walkthrough/08_9_pi0_fake_study.md).
## 10. Geometry audit (geometry_audit.py, 419 lines)

Cross-checks the active `src/detector/*.cc` against
`docs/Detector_Geometry_Reference.md`. Returns a structured `report`
with per-component pass/fail. Plan 16 (geometry / alignment) consumes
this audit as one of its acceptance criteria.

## 11. CLI surface (recap)

```
python -m nnbar_reconstruction.cli summarize <output_dir> [--run] [--json] [--tables-dir]
python -m nnbar_reconstruction.cli scan-pid <output_dir> [--run|--runs|--all-runs]
                                              [--proton-dedx ...] [--short-range ...]
                                              [--short-range-dedx ...] [--top N]
                                              [--json] [--table]
python -m nnbar_reconstruction.cli validate-reco <output_dir>
                                              [--run|--runs|--all-runs]
                                              [--min-class-count ...] [--min-accuracy ...]
                                              [--min-balanced-f1 ...]
                                              [--min-electron-pair-purity ...]
                                              [--min-pi0-efficiency ...]
                                              [--pid-proton-dedx-min ...]
                                              [--pid-short-range-cm ...]
                                              [--pid-short-range-proton-dedx-min ...]
                                              [--fail-on-not-ready] [--json]
python -m nnbar_reconstruction.cli pi0-study <output_dir> [--run] [--json] [--table]
python -m nnbar_reconstruction.cli charged-study <output_dir>
                                              [--run|--runs|--all-runs] [--json] [--table]
python -m nnbar_reconstruction.cli pi0-fake-study <output_dir>
                                              [--run|--runs|--all-runs]
                                              [--include-near-charged] [--prompt-timing]
                                              [--pid-proton-dedx-min ...] [--pid-short-range-cm ...]
                                              [--pid-short-range-proton-dedx-min ...]
                                              [--json] [--table]
python -m nnbar_reconstruction.cli geometry-audit [<repo_root>] [--json] [--fail-on-mismatch]
```

Plan 10 (macro & sample inventory) records the canonical invocation
patterns used in current studies; plan 47 (reproduction ledger) cites
the exact command line per ledger row.

## 12. Acceptance criteria

- §3.3 (vertex) and §3.4 (charged) deepened to the same line-level
  detail as §2 (I/O) and §3.1 (config) — owned by plan 25 and
  plan 29 respectively when those plans are written.
- §3.5 (photon / π⁰) deepened by plan 26, plan 28, plan 29 (sic — the
  pi0 plans).
- §3.6 (event variables) deepened by plan 31.
- §6 (validation) deepened by plan 40 closure-and-pulls.
- §7, §8, §9 deepened to function-level depth by plan 14 (validation
  suite).
- The realism audit (plan 01) reads §3.7 and uses it as the
  whitelist of currently allowed Class B reads pending migration.
- A CI rule blocks any PR that adds a new public function to
  `nnbar_reconstruction/` without an entry here.

## 13. Risks and mitigations

- *Risk:* §3.3, §3.4, §3.5 stubs become permanent.
  *Mitigation:* the CI rule cited above; Methodology Council
  reviews quarterly that the plan depth matches the code depth.
- *Risk:* §3.7 truth-use list is incomplete; new Class B reads creep in.
  *Mitigation:* plan 01 §4 audit treats this list as authoritative;
  any new Class B access must either appear here as "documented
  legacy" or be flagged as a failure.

## 14. Dependencies

- **00_README** — plan space.
- **01_realism_contract** — defines the Class A/B/C scheme this
  walkthrough cites.
- **07_simulation_atomic_walkthrough** — the upstream producer of
  every parquet column read here.
- *Consumed by:* plan 09 (data dictionary), plan 24 (question tree),
  plan 25–37 (subsystem deep dives), plan 47 (reproduction ledger),
  plan 50 (defence package).

## 15. References

- `NNBAR_Detector/docs/reconstruction.md` — companion technical
  reference (≈ 828 lines). This walkthrough complements it: the
  README describes intent and external behaviour; this plan
  describes implementation and decision points.
- `docs/detector_fundamental_question_tree.md` — the
  reconstruction-side companion of which is plan 24.
