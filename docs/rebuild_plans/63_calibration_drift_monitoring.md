---
id: 63_calibration_drift_monitoring
title: Calibration drift monitoring — run-year stability and triggers
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [01_realism_contract, 04_statistical_uncertainty, 17_field_calibration, 18_intercalibration, 19_simulation_validation_suite, 47_reproduction_ledger, 53_ci_regression_suite, 66_data_quality_monitoring]
inputs:
  - {path: docs/rebuild_plans/17_field_calibration.md, schema: TPC field and W-value contract}
  - {path: docs/rebuild_plans/18_intercalibration.md, schema: TPC/scintillator/lead-glass closure contract}
  - {path: docs/rebuild_plans/19_simulation_validation_suite.md, schema: sanity plots and regression budgets}
  - {path: docs/rebuild_plans/53_ci_regression_suite.md, schema: CI trigger and failure semantics}
  - {path: docs/rebuild_plans/66_data_quality_monitoring.md, schema: offline DQM quality-status contract}
outputs:
  - {path: docs/rebuild_plans/63_calibration_drift_monitoring.md, schema: this file}
  - {path: data/registry/calibration/drift_monitoring_<tag>.yml, schema: planned drift-monitoring registry}
acceptance:
  - {test: run-year schedule covers pre-run, daily, weekly, monthly, and post-run checks, method: §2 review, pass_when: every cadence has an owner and artifact}
  - {test: every Class C constant has warning/fail tolerance bands, method: §3 table, pass_when: no blank bands}
  - {test: failure trigger routes to a concrete action, method: §4 trigger map, pass_when: every fail state blocks or opens a ledger/CI action}
  - {test: DQM dependency is source-backed, method: §7 verifier, pass_when: plan 66 path resolves and old placeholder path is not cited}
risks:
  - {risk: calibration drift is mistaken for physics-model drift, mitigation: drift monitors are Class C-only and feed plan 45 before any physics retune}
  - {risk: CI cannot run full calibration samples, mitigation: CI uses smoke monitors while plan 47 owns full-row refresh}
estimated_effort: M
last_updated: 2026-05-10
---

# Calibration drift monitoring

*Charter.* Define how calibration constants are monitored across a
run year, how much drift is tolerated before action is required, and
how those actions propagate into CI, the reproduction ledger, and the
future online DQM plan. This is not a new reconstruction algorithm; it
is the operational wrapper around Class C constants from plan 01.

The monitoring model is intentionally conservative. A calibration drift
can downgrade a sample or ledger row, but it cannot silently retune a
physics selection.

## 1. Scope and constants

The first drift-monitoring registry covers constants already named in
plans 17 and 18:

| Constant group | Source plan | Primary observable | Class | First artifact |
|---|---|---|---|---|
| TPC drift field | plan 17 §2 | max field-map deviation over active volume | Class C | `output/calibration/tpc_field/summary.json` |
| TPC W-value policy | plan 17 §3 | electron-count scale relative to 23.6 eV production value | Class C | `output/calibration/tpc_w_value/summary.json` |
| TPC↔scintillator MIP closure | plan 18 §2 | residual between TPC and scintillator dE/dx | Class C | `output/calibration/mip_closure/summary.json` |
| Scintillator fast yield | plan 18 §3 | photons-per-MeV residual against 11136 fast-mode value | Class C | `output/calibration/scint_yield_reconciliation/summary.json` |
| Lead-glass linearity | plan 18 §4 | per-energy residual from `E_reco = a + b E_true` | Class C | `output/calibration/leadglass_linearity/summary.json` |
| Per-SD sanity plots and DQM status | plans 19 §2 and 66 | eDep/hit-multiplicity/vertex/final-state plot drift plus `quality_status` | Class C monitor | plan 47 plot rows and plan 66 `quality_manifest.json` |

Out of scope for v0.1:

- Real-detector calibration promotion. Plan 01 §7 defines the criteria
  for upgrading a Class C constant after data calibration exists.
- Online DQM implementation. Plan 66 now defines offline run-quality
  gates; online shift displays and live alarm routing remain
  post-commissioning operations work.
- Automatic threshold retuning. Threshold changes require a DEC entry
  and downstream ledger updates.

## 2. Run-year schedule

The schedule assumes a single nominal run year with a pre-run baseline,
periodic smoke checks, and post-run closure. Cadences are registry
metadata, not hard-coded CI cron values.

| Cadence | Owner | Inputs | Artifact | Action if missing |
|---|---|---|---|---|
| Pre-run baseline | Reproducibility WG | plan 23 calibration samples, plan 17 field scan | `baseline_<run>.yml` | block sample freeze |
| Every PR | Software Quality | smoke sample and plan 19 sanity plot subset | CI log plus smoke JSON | block merge on Tier 1 paths |
| Daily during production | Sim Production | latest smoke sample | `daily_<date>.json` | mark drift status unknown |
| Weekly during production | Reproducibility WG | MIP, scintillator-yield, lead-glass smoke closures | `weekly_<iso_week>.json` | open drift review issue |
| Monthly during production | Methodology Council | full calibration sample or largest available review sample | `monthly_<month>.json` | freeze new sample versions until reviewed |
| Post-run closure | Methodology Council | full plan 47 ledger refresh subset | `post_run_<run>.json` | keep affected thesis rows yellow/red |

Each artifact records:

- `run_id`
- `calibration_tag`
- input sample ids and hashes
- constants measured
- warning/fail status per §3
- linked plan 47 rows
- linked DEC entries, if the action changes a threshold or algorithm

## 3. Tolerance bands

The first tolerance bands are operational gates. They are deliberately
simple and can be tightened after real calibration data exists.

| Monitor | Green | Warning | Failure |
|---|---:|---:|---:|
| TPC field-map max deviation | < 1.0% | 1.0%--1.5% | > 1.5% |
| TPC W-value production scale | 23.6 eV identity | reference alternative shifts electron scale by 5%--15% | default changed without new dataset version |
| TPC↔scintillator MIP residual | < 5% | 5%--10% | > 10% |
| Scintillator fast-yield residual | < 5% | 5%--10% | > 10% or optical yield still zero when optical-mode row is requested |
| Lead-glass line residual per energy | < 5% | 5%--10% | > 10% |
| Per-SD hit/eDep plot drift | within plan 19 budget | outside budget but ledger row still explainable | outside budget and no ledger/systematics explanation |

Warnings keep a row eligible for `yellow` status in plan 47 if the
systematic bracket covers the drift. Failures block new `green` ledger
claims until the underlying calibration or uncertainty model is fixed.

## 4. Failure triggers and actions

| Trigger | Immediate action | Downstream action |
|---|---|---|
| Missing drift artifact | mark monitor `unknown` | block sample freeze if pre-run/monthly; warn for daily |
| Warning band exceeded | open calibration review | add or widen plan 45 nuisance before quoting new results |
| Failure band exceeded | block affected sample/ledger promotion | require DEC if changing a constant, threshold, or algorithm |
| Unsupported mode requested | fail closed | keep row `blocked-no-sample` or `mismatch`; do not fabricate fallback |
| CI smoke drift | Tier 1/Tier 2 failure per plan 53 | rerun smoke sample after fix; attach artifact to plan 47 row |
| Full ledger drift | set affected row yellow/red | reviewer defense package cites the drift and resolution |

No trigger directly edits physics selections. Selection changes remain
owned by the relevant reconstruction plan and must pass plan 04
uncertainty propagation plus plan 47 ledger comparison.

## 5. CI and DQM integration

Plan 53 consumes the drift monitors in two layers:

1. **PR smoke layer.** Run the smallest available monitor subset when
   `NNBAR_Detector/{src,include,macro,CMakeLists.txt}` or
   `nnbar_reconstruction/**` changes. This layer checks that artifacts
   exist and remain schema-compatible.
2. **Nightly/weekly layer.** Refresh weekly drift summaries and update
   plan 47 rows that already have a reproduced/mismatch artifact.

Plan 66 consumes the same monitor outputs through an offline DQM
quality-status contract:

- `quality_manifest.json` mirrors `quality_status` into the registry
  until plan 03 grows a native field.
- Drift-monitor artifacts provide the calibration side-channel for plan
  66 warning/failure reasons; plan 66 remains responsible for the
  dataset-level `pass|warn|fail` lattice.
- DQM must publish the same `run_id`, `calibration_tag`, and monitor
  names as the drift registry so comparisons are mechanical.
- Online warning states may page humans in a future operations layer,
  but only offline validated artifacts can change plan 47 status.

## 6. Registry schema

Draft registry entry:

```yaml
id: drift_monitoring_run_<run>
run_id: <run>
baseline_tag: <tag>
cadence: daily | weekly | monthly | post_run
inputs:
  samples: []
  artifacts: []
monitors:
  - name: tpc_field_uniformity
    value: null
    units: percent
    status: not-run
    warning_band: "1.0--1.5"
    failure_band: ">1.5"
linked_ledger_rows: []
decisions_required: []
```

The registry is append-only for published runs. Corrections create a new
entry with `supersedes: <old-id>` and preserve the old artifact hash.

## 7. A+ verifier transcript

Re-run before changing path claims in this plan:

```bash
ls docs/rebuild_plans/17_field_calibration.md \
   docs/rebuild_plans/18_intercalibration.md \
   docs/rebuild_plans/19_simulation_validation_suite.md \
   docs/rebuild_plans/47_reproduction_ledger.md \
   docs/rebuild_plans/53_ci_regression_suite.md \
   docs/rebuild_plans/66_data_quality_monitoring.md
test ! -e docs/rebuild_plans/66_dqm_and_online_monitoring.md
```

Current 2026-05-10 evidence: plans 17, 18, 19, 47, 53, and
`66_data_quality_monitoring.md` exist in the local plan set after the
L0 DQM handoff landed. The old placeholder
`66_dqm_and_online_monitoring.md` path does not exist and must not be
cited.

## 8. Acceptance criteria

- §2 schedule has one artifact per cadence and every artifact has an
  owner.
- §3 tolerance bands are populated for every constant group in §1.
- §4 trigger map routes every warning/failure to a CI, ledger,
  systematics, or DEC action.
- §5 links to the source-backed offline DQM plan and keeps future
  online operations out of scope.

## 9. Dependencies

- **01** — realism and Class C upgrade rules.
- **04** — uncertainty propagation and yellow/red ledger semantics.
- **17, 18, 19** — constants and monitor artifacts.
- **47** — row status updates.
- **53** — CI trigger semantics.
- **66** — offline DQM run-quality status and registry handoff.
- *Consumed by:* plan 45 (systematics), plan 47 (ledger), plan 66
  (offline DQM).
