---
id: 66_data_quality_monitoring
title: Data quality monitoring — offline run-quality gates
version: 0.1
status: draft
owner: Software Quality
depends_on: [00_README, 03_dataset_registry, 04_statistical_uncertainty, 17_field_calibration, 18_intercalibration, 30_subsystem_vertex, 43_signal_efficiency, 53_ci_regression_suite]
outputs:
  - {path: docs/rebuild_plans/66_data_quality_monitoring.md, schema: this file}
  - {path: output/dqm/<dataset_id>/run_quality.parquet, schema: per-run DQM table}
  - {path: output/dqm/<dataset_id>/quality_manifest.json, schema: DQM provenance and registry handoff}
acceptance:
  - {test: every monitored variable has source table, threshold, severity, and owner, method: §3 review, pass_when: table complete}
  - {test: every reconstructed run receives a pass/warn/fail quality status, method: §4 artifact review, pass_when: no missing run ids}
  - {test: plan 53 CI consumes the DQM status for frozen-sample refreshes, method: §6 review, pass_when: gating semantics defined}
risks:
  - {risk: monitoring thresholds become hidden analysis cuts, mitigation: §5 keeps DQM status separate from event selection and requires plan 05 approval before any threshold gates physics}
  - {risk: registry schema lacks quality_status until the registry owner wires it, mitigation: §7 defines the field contract and a backward-compatible manifest mirror}
estimated_effort: M
last_updated: 2026-05-10
---

# Data quality monitoring

*Charter.* Provide an offline data-quality gate for reconstructed
simulation runs before they enter efficiency, unfolding, ledger, or
thesis-facing comparisons. DQM answers a different question from event
selection: not *does this event look signal-like?* but *is this run
healthy enough that downstream numbers should trust its detector
response?*

This plan is offline-only. Online shift displays and live alarm routing
are post-commissioning Operations deliverables; the rebuild only needs
machine-readable run-quality artifacts for CI, registry, and ledger use.

## 1. Design principles

1. **DQM never changes an event variable in place.** It writes a
   per-run quality status and diagnostic metrics. Selection plans may
   consume only the status after a plan 05 decision approves that use.
2. **Every threshold has an owner and source plan.** Thresholds below
   are initial production gates for simulation-quality review, not
   hidden retuning knobs.
3. **Warnings are sticky.** A warning in a calibration side-channel is
   carried into the registry and plan 47 even if the physics number is
   still usable.
4. **Failures block promotion, not reconstruction.** A failing run can
   still be reconstructed for debugging, but it cannot be frozen or
   quoted until the failure is waived in governance.
5. **Truth labels are validation-only.** Vertex residual and PID
   validation metrics may compare to truth after outputs are frozen;
   DQM pass/fail must remain separate from production reconstruction
   decisions.

## 2. Inputs and current verified CLI surface

The DQM job starts from the same reconstructed tables used by plans 41,
43, and 47. The existing help-verified L3 CLI can create those tables:

```bash
python -m nnbar_reconstruction.cli summarize \
    NNBAR_Detector/output/<dataset_id> --all-runs \
    --tables-dir output/reco/<dataset_id>/ \
    --table output/reco/<dataset_id>/runs.csv \
    --json output/reco/<dataset_id>/summary.json
```

The same help-verified CLI can produce validation metrics when truth
labels are available:

```bash
python -m nnbar_reconstruction.cli validate-reco \
    NNBAR_Detector/output/<dataset_id> --all-runs \
    --json output/dqm/<dataset_id>/validation.json
```

The offline DQM producer is now help-verified as a live L3 CLI surface:

```bash
python -m nnbar_reconstruction.cli dqm \
    --dataset-id <dataset_id> \
    --run <run_or_combined_run_id> \
    --out-dir output/dqm/<dataset_id>/ \
    output/reco/<dataset_id>/
```

Current source hooks are `dqm` (`nnbar_reconstruction/cli.py:271-288`),
`evaluate_run_quality` (`nnbar_reconstruction/dqm/quality.py:55-120`), and
`quality_manifest` (`nnbar_reconstruction/dqm/quality.py:123-147`). The live command reads
the reconstructed CSV tables and writes §4 artifacts. Validation JSON
and registry-manifest hash ingestion remain follow-up L3 implementation
gates; until those flags exist, steps below keep them as separate
assertions rather than inventing CLI arguments.

Required input artifacts:

| Input | Producer | Required fields |
|---|---|---|
| `runs.csv` | `summarize` | run id, event count, cut-flow summaries, bootstrap summary if requested |
| `events.csv` | `summarize --tables-dir` | event id, vertex fields, calorimeter energies, selection booleans |
| `charged.csv` | `summarize --tables-dir` | dE/dx, range, charged PID, charged-candidate counts |
| `photons.csv` / `pi0.csv` | `summarize --tables-dir` | photon energy, pi0 mass, selected pi0 counts |
| `vertices.csv` | `summarize --tables-dir` | vertex position, radial spread, projected/skipped track counts |
| `validation.json` | `validate-reco` | truth-matched accuracy/F1 and class counts when labels exist |
| plan 03 manifest | registry | dataset id, run list, sample status, hashes, geometry/config ids |

## 3. Monitored variables and thresholds

Thresholds are intentionally simple and auditable. They are not final
physics calibration constants; they are run-health sentinels that decide
whether a run is `pass`, `warn`, or `fail` before promotion.

The mandatory per-run DQM variable families are **TPC gain**,
**scintillator yield**, **lead-glass linearity**, and **vertex
residual**. The table below implements them as explicit proxy columns
because the current offline reconstruction tables do not yet carry
dedicated calibration-channel products for every run.

| Variable | Source | Threshold | Severity | Owner | Rationale |
|---|---|---|---|---|---|
| `event_count` | `runs.csv` | run has at least one reconstructed event and matches manifest count | fail | registry owner | empty or count-mismatched runs cannot be frozen |
| `tpc_gain_proxy` | `charged.csv` / TPC summary | median `dedx_mev_per_cm` finite and within plan 18 MIP closure envelope | warn outside envelope, fail if non-finite | Tracking POG | catches TPC W-value/gain drift from plans 17/18 |
| `tpc_hit_coverage` | `charged.csv` | nonzero charged candidates in calibration samples expected to contain TPC tracks | warn if low, fail if zero | Tracking POG | detects broken TPC table joins or track grouping |
| `scintillator_yield_proxy` | `events.csv` | finite scintillator energy and nonnegative timing/out-of-time split | warn for large drift vs plan 18 yield closure, fail if negative or NaN | Calibration POG | protects C.3/range and S.1/S.5 energy gates |
| `leadglass_linearity_proxy` | `photons.csv`, `pi0.csv`, `events.csv` | finite lead-glass energy; pi0 mass peak tracked when enough pi0s exist | warn if residual exceeds plan 18 closure band, fail if all photon energy is NaN | Photon POG | catches lead-glass response or table-writing failures |
| `vertex_residual_proxy` | `vertices.csv` plus validation truth when available | vertex radial spread finite; validation residual within plan 30/40 tolerance | warn outside tolerance, fail if no vertices in signal/calibration samples | Tracking POG | prevents edge/vertex pathologies from contaminating plan 43 |
| `selection_cutflow_monotonicity` | `runs.csv` / `events.csv` | cumulative counts never increase in cut order | fail | Analysis WG | catches cut-flow aggregation bugs |
| `manifest_hash_match` | plan 03 manifest | every consumed input hash matches registry | fail | Software Quality | protects reproducibility and append-only frozen samples |
| `dqm_schema_version` | DQM manifest | schema equals this plan version or declared compatible successor | fail on unknown major version | Software Quality | prevents stale readers from accepting incompatible tables |

Severity semantics:

- `pass` — metric is present and inside the threshold.
- `warn` — metric is present but outside the advisory band; downstream
  quoting must carry the warning in plan 47.
- `fail` — run cannot be frozen, promoted, or used in thesis-facing
  numbers without a governance waiver.
- `not_applicable` — metric is not defined for this dataset type, with
  a required reason string.

## 4. Output schema and pass/fail flag

The offline DQM producer writes one row per run and one summary row per
dataset. A run-level failure makes the dataset summary `fail` unless a
waiver id is attached.

### 4.1 Run table: `run_quality.parquet`

| Column | Dtype | Meaning |
|---|---|---|
| `dataset_id` | string | plan 03 dataset id |
| `run` | int | run number or synthetic combined-run id |
| `quality_status` | enum | `pass`, `warn`, `fail`, or `not_applicable` |
| `quality_reasons` | list[string] | all variable-level warning/failure labels |
| `event_count` | int | reconstructed events for the run |
| `tpc_gain_proxy` | float/null | median or calibration-normalised dE/dx proxy |
| `scintillator_yield_proxy` | float/null | scintillator yield/energy proxy |
| `leadglass_linearity_proxy` | float/null | lead-glass response or pi0-mass proxy |
| `vertex_residual_proxy` | float/null | radial spread or validation residual proxy |
| `cutflow_monotonic` | bool | cumulative selection counts are monotone |
| `hash_status` | enum | `pass` or `fail` against plan 03 hashes |
| `waiver_id` | string/null | governance waiver if status is promoted despite fail |

### 4.2 Dataset manifest: `quality_manifest.json`

```json
{
  "dataset_id": "sig_foil_500MeV_v3",
  "schema_version": "66_data_quality_monitoring@v0.1",
  "quality_status": "pass|warn|fail",
  "n_runs": 0,
  "n_pass": 0,
  "n_warn": 0,
  "n_fail": 0,
  "source_hashes": {},
  "threshold_profile": "simulation_v0.1",
  "waivers": []
}
```

The `quality_status` summary is the value mirrored into the plan 03
registry once the registry owner extends the manifest schema. Until that
schema update lands, the DQM manifest is the backward-compatible source
of truth and plan 03 references it by path.

## 5. Offline procedure

1. Resolve the dataset id through plan 03. If the registry entry is
   missing or hash verification fails, emit dataset `fail` immediately
   with reason `manifest_hash_match`.
2. Run the verified `summarize` command in §2, writing tables under
   `output/reco/<dataset_id>/` and the per-run CSV.
3. Run the verified `validate-reco` command when the dataset carries
   truth labels suitable for validation. If validation is not applicable,
   record `not_applicable` with the dataset-type reason.
4. Run the verified `dqm` command in §2 over the reconstructed CSV
   tables. It writes `run_quality.parquet` and `quality_manifest.json`
   under `output/dqm/<dataset_id>/`.
5. **Blocked L3 implementation gate:** extend the DQM producer to ingest
   validation JSON and the plan 03 registry manifest, or join those
   artifacts in a wrapper, before frozen-sample promotion can rely on
   validation residuals and hash checks.
6. Assert every run from the registry has exactly one row in
   `run_quality.parquet` and every row has a nonempty `quality_status`.
7. Assert dataset-level `quality_status` follows the lattice
   `fail > warn > pass`; `not_applicable` is variable-level only.
8. Store DQM artifact hashes in `quality_manifest.json` and mirror the
   summary status into registry metadata when the plan 03 field exists.

## 6. CI integration with plan 53

Plan 53 Tier 1 keeps the existing plan-set and registry checks. DQM
adds three CI hooks:

| CI hook | Trigger | Command surface | Failure behavior |
|---|---|---|---|
| DQM schema lint | changes to this plan, DQM producer, or output schema readers | parse `run_quality.parquet` fixture and `quality_manifest.json` fixture | Tier 1 failure blocks merge |
| Frozen-sample DQM refresh | changes to reconstruction, calibration, geometry, or frozen registry entries | run summarize/validate plus DQM producer on a smoke-size frozen sample | Tier 2 failure blocks matching code paths |
| Weekly DQM drift report | scheduled Tier 3 | rerun DQM on all green/yellow ledger samples | opens issue and flips affected ledger rows to red or yellow |

A DQM `fail` blocks a new sample from becoming `frozen`. A DQM `warn`
allows freeze only if plan 47 records the warning and the Methodology
Council accepts the residual risk. A DQM `pass` is necessary but not
sufficient for physics promotion; subsystem and ledger gates still have
to pass.

## 7. Registry integration

The plan 03 manifest needs a run-quality field with this shape:

```yaml
quality_status: pass | warn | fail | not_applicable
quality_manifest: output/dqm/<dataset_id>/quality_manifest.json
quality_checked_at: <ISO-8601 timestamp>
quality_schema: 66_data_quality_monitoring@v0.1
quality_waivers: []
```

Registry rules:

- `frozen` samples must have `quality_status` equal to `pass` or
  governance-waived `warn`.
- `draft` samples may carry `fail`, but plan 47 cannot quote them.
- `superseded` and `retired` samples retain their last quality status
  for citation traceability.
- If a DQM rerun changes status after freeze, plan 47 rows that consume
  the sample are downgraded until the discrepancy is investigated.

Because plan 03 is a foundation file owned outside L0, this plan does
not edit the registry schema directly. It defines the field contract and
uses `quality_manifest.json` as the transitional handoff artifact.

## 8. Ledger and analysis boundaries

DQM status is a precondition, not a replacement for analysis closure.

| Consumer | Required DQM condition | Additional gate |
|---|---|---|
| plan 43 signal efficiency | dataset status `pass` or accepted `warn` | factorisation/product closure still required |
| plan 41 N-1 / ROC | all input samples not `fail` | scan artifacts and tolerances still required |
| plan 42 unfolding | response-matrix input sample not `fail` | closure and regularisation gates still required |
| plan 47 ledger | status copied into every row's provenance block | row-specific reproduction still decides green/yellow/red |
| plan 50 defence package | all quoted samples have DQM artifacts | limitations and waivers rendered for reviewers |

A warning must not disappear in rendered tables. It is reported beside
statistical and systematic uncertainties so reviewers can distinguish a
healthy run from a usable-but-qualified run.

## 9. Implementation handoff and blocker contract

The DQM producer itself is help-verified, and the current L3 regression
coverage already exercises the producer path: healthy-run `pass`
coverage in `test_evaluate_run_quality_passes_healthy_fixture`
(`tests/test_dqm.py:36-44`), empty-run `fail` coverage in
`test_evaluate_run_quality_fails_empty_or_negative_energy_run`
(`tests/test_dqm.py:46-52`), manifest lattice coverage in
`test_quality_manifest_uses_fail_warn_pass_lattice`
(`tests/test_dqm.py:55-69`), and CLI artifact coverage in
`test_dqm_cli_writes_run_table_and_manifest`
(`tests/test_dqm.py:72-89`). Validation-JSON ingestion,
registry-manifest hash checking, registry write-back, and
`not_applicable` status coverage remain explicit follow-up gates.
Until those surfaces exist, the current command writes the DQM artifacts
and the wrapper or promotion job must keep validation and registry
checks as separate assertions.

L3/software handoff requirements:

1. Extend the DQM producer or a verified wrapper to read
   `validation.json` and the plan 03 manifest, then populate
   `vertex_residual_proxy`, `hash_status`, `source_hashes`, and
   waiver fields without inventing new CLI flags in this plan.
2. Extend the current DQM fixture tests for `run_quality.parquet` and
   `quality_manifest.json` so they also exercise `not_applicable`
   status and the future validation/registry hash joins; keep the
   existing lattice `fail > warn > pass` test green.
3. Add a registry-mirror handoff that writes the §7 `quality_status`,
   `quality_manifest`, `quality_checked_at`, `quality_schema`, and
   `quality_waivers` fields only after plan 03 accepts the schema.
4. Add CI smoke coverage for a frozen-sample DQM refresh using the
   verified summarize/validate/dqm command sequence from §5.
5. Any new command-line surface must be help-verified under the A+
   examiner gate before this plan names it. Until then, the missing
   validation/registry joins remain software requirements, not runnable
   instructions.

### 9.1 DQM promotion manifest schema

The DQM producer or verified wrapper must write a promotion manifest
that makes registry and ledger consumption explicit:

```yaml
schema_version: 66_data_quality_monitoring@stage-e1
dataset_id: <plan-03 dataset id>
run_quality_hash: <sha256 of run_quality.parquet>
quality_manifest_hash: <sha256 of quality_manifest.json>
reco_table_hashes: {runs: <sha256>, events: <sha256>, charged: <sha256>, photons: <sha256>, pi0: <sha256>, vertices: <sha256>}
validation_json_hash: <sha256|null>
registry_manifest_hash: <sha256|null>
quality_status: pass | warn | fail
status_lattice: fail_over_warn_over_pass
waiver_ids: []
registry_writeback_status: pending_plan03_schema | mirrored | not_applicable
ci_hooks_required: [schema_lint, frozen_sample_refresh, weekly_drift_report]
producer_help_verified: true
```

The promotion manifest is invalid if any reconstructed run lacks a row,
if the dataset status does not follow the `fail > warn > pass` lattice,
or if registry write-back is marked `mirrored` before plan 03 accepts
the schema fields in §7.

## 10. Acceptance criteria

- §3 threshold table has variable, source, threshold, severity, owner,
  and rationale for each required DQM variable.
- §4 artifacts include one run row per registry run and a dataset-level
  `quality_status` summary.
- §5 procedure uses only help-verified existing CLI surface, including
  the current `dqm` producer; validation/registry joins remain separate
  software requirements until their surfaces are help-verified.
- §6 CI hooks define trigger and failure behavior.
- §7 registry handoff field is specified without editing plan 03 in L0.
- §8 consumers distinguish DQM status from analysis closure.
- §9 handoff is complete: current DQM regression tests are cited,
  validation ingestion, registry hash checking, registry write-back,
  remaining fixture-test coverage, CI smoke coverage, a required
  promotion manifest schema, and the no-invented-CLI rule are all
  specified.

## 11. Dependencies

- **03** — dataset registry and frozen/draft/superseded status.
- **04** — uncertainty handling for DQM drift summaries.
- **17** — TPC W-value and gain-saturation limitations.
- **18** — TPC/scintillator/lead-glass calibration closures.
- **30** — vertex residual and V.5 foil-compatibility semantics.
- **43** — signal-efficiency samples consuming DQM status.
- **53** — CI tiering and failure semantics.
