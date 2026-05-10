---
id: 19_simulation_validation_suite
title: Simulation validation suite — sanity, closure, regression
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 03_dataset_registry, 07_simulation_atomic_walkthrough, 12_physics_list_audit]
inputs:
  - {path: NNBAR_Detector/CMakeLists.txt, schema: source-observed build knobs}
outputs:
  - {path: NNBAR_Detector/tests/, schema: pytest test suite}
  - {path: docs/rebuild_plans/19_simulation_validation_suite.md, schema: this file}
acceptance:
  - {test: every source-observed CMake build knob has a paired smoke build + run, method: CI matrix, pass_when: every option green}
  - {test: per-SD sanity plots produced for nominal signal sample, method: §2 plots, pass_when: plots in plan 47 ledger}
  - {test: regression budget defined for events/sec, MB/event, hits/event, method: §3 thresholds, pass_when: no regressions on main}
risks:
  - {risk: optional GPU paths fail silently when no GPU is available on CI, mitigation: §4 GPU-conditional CI matrix}
  - {risk: validation suite drift, mitigation: §5 ownership rotation in plan 06}
estimated_effort: M
last_updated: 2026-05-10
---

# Simulation validation suite

*Charter.* The shared test harness that gates every simulation change.
Three layers: (1) sanity plots that flag obvious physics mistakes,
(2) per-component closure tests, (3) performance regression bounds.
Plan 53 (CI) runs the suite on every PR.

## 1. Existing tests

Current `NNBAR_Detector/tests/` inventory, read from the L3 worktree on
2026-05-10 after the Stage E expansion:

| Test file | Primary validation surface | Sanity plot / artifact | Regression budget | CI matrix dimension |
|---|---|---|---|---|
| `test_charged_reco.py` | plan-25 charged-track candidates and plan-26 direction/PID helpers | charged track-candidate tables and direction rows | truth columns forbidden; real sample schema stable | `reco-charged` |
| `test_ci_workflow.py` | plan-53 GitHub Actions contract | workflow YAML path/trigger audit | required fast checks listed for touched paths | `ci-contract` |
| `test_cli_response_matrix.py` | plan 42 response-matrix CLI and artifact writers | response parquet, covariance NPZ, metadata JSON | flags and output schemas stable | `response-matrix-cli` |
| `test_cli_summarize_flags.py` | plan 42 summarize `--all-runs` and output flags | offset-table manifest and summary table | event-offset concatenation stable | `summarize-cli` |
| `test_closure.py` | plan 40 per-leaf closure runner | closure JSON and K-S bias report | unbiased fixture green; biased fixture red | `reco-closure` |
| `test_dqm.py` | plan-66 offline DQM status lattice | run-quality table and manifest | fail/warn/pass semantics stable | `dqm-offline` |
| `test_electron_reco.py` | electron-pair candidate reconstruction | electron-pair candidate rows | configured entry cut enforced; missing TPC columns produce empty schema | `reco-electron` |
| `test_event_variables.py` | plan-36 event-shape variables | event-variable rows from charged/photon vectors | sparse inputs emit finite invalid sentinels | `event-variables` |
| `test_fast_mc.py` | plan 39 fast-MC smearing and closure fixtures | fast-MC closure report | fixed-seed deterministic; bias detected | `fast-mc` |
| `test_file_size_cap.py` | `CODING_STANDARDS.md` §1 file-size guard | scoped file-size report | modified source/test files stay <500 lines | `style-size-cap` |
| `test_golden_contract_matrix.py` | plan-53 synthetic/real output schema contract | golden schema matrix | reconstruction outputs match contract | `golden-contract` |
| `test_golden_regression.py` | plan-53 golden-output regression fixtures | golden reconstruction snapshot | snapshot stable unless fixture intentionally updated | `golden-regression` |
| `test_integration_real_sample.py` | real Geant4-output reconstruction schema integration | plan-09 §14 table set from checked real fixture | real sample reconstructs to expected columns | `real-sample-integration` |
| `test_kfit.py` | plan-35 π⁰ kinematic-fit rows | fit-status and covariance rows | missing covariance preserves raw row | `pi0-kfit` |
| `test_ladder_cli.py` | plan 38 truth-ladder CLI report writers | ladder run/factorise JSON reports | `python -m` entrypoints exit 0 | `truth-ladder-cli` |
| `test_ladder_factorise.py` | additive truth-gap factorisation | factorisation residual table | residual closes truth gap | `truth-ladder-core` |
| `test_ladder_leaves.py` | plan 24 leaf registry coverage | leaf-registry JSON dump | every leaf present in fixed order | `truth-ladder-core` |
| `test_ladder_run.py` | truth-substitution ladder execution | ladder metric report JSON | fixed sample/seed deterministic | `truth-ladder-core` |
| `test_ladder_substitute.py` | per-leaf truth substitution | substituted event table | explicit leaf outputs preferred | `truth-ladder-core` |
| `test_ledger_reproduction.py` | plan-47 ledger reproduction command smoke | golden subset command manifest | command strings remain runnable/schema-stable | `ledger-reproduction` |
| `test_photon_reco.py` | plan-31 photon/calorimeter reconstruction and plan-32 shower features | calorimeter cluster, photon, and shower-shape rows | truth columns forbidden; real sample schema stable | `reco-photon` |
| `test_pid_calibration.py` | charged PID threshold scan | PID scan CSV and ROC/score outputs | truth-separating config ranks first | `reco-pid` |
| `test_realism_audit.py` | plan 01/09 truth-read audit | audit JSON with violation list | undecorated Class B reads fail | `realism-audit` |
| `test_reconstruction_run_summary.py` | reconstruction run tables and thesis cut variables | summary tables and cut-variable rows | thesis calorimeter-direction variables present | `reco-summary` |
| `test_reconstruction_smoke.py` | end-to-end reconstruction smoke and thesis cutflow/object rules | `output/sanity/{edep,hits,vertex_z,timing}.png` plus reco tables | expected tables written; 395 lines on 2026-05-10, below the 500-line cap | `reco-smoke` |
| `test_reconstruction_validation.py` | validation report and readiness gates | validation JSON plus class-support table | readiness thresholds and all-run aggregation stable | `reco-validation` |
| `test_registry_integrity.py` | plan 03 dataset manifests and state machine | registry round-trip JSON / manifest hash report | illegal states/transitions rejected | `registry` |
| `test_selection.py` | plan-37 event selection and cut-flow accounting | cut-flow table and independent cut flags | cumulative counts follow plan-37 order | `selection-cutflow` |
| `test_statistics.py` | plan 04 bootstrap, jackknife, Wilson, F-C | statistical interval JSON / pull table | seed binding deterministic | `statistics` |
| `test_verify_citations.py` | A+ source-citation verifier | verifier pass/fail fixtures and temporary source snippets | out-of-range or wrong identifiers fail | `citation-verifier` |
| `test_vertex_reco.py` | plan-30 vertex projection, aggregation, and foil acceptance | vertex projection and aggregate rows | geometry-only acceptance uses plan-16 contract | `vertex-reco` |

Plan 53 runs these via pytest on every PR. The current inventory was
verified against 31 `test_*.py` files in the L3 `tests/` directory on
2026-05-10. The largest listed tests are below the 500-line cap in this
worktree (`test_reconstruction_smoke.py` 395 lines,
`test_photon_reco.py` 388 lines, `test_charged_reco.py` 351 lines), and
`test_file_size_cap.py` is now the explicit regression guard for
`CODING_STANDARDS.md` §1.

## 2. Sanity plots per SD

For every nominal-signal sample, automated plots:

- *Per-SD eDep distribution* (TPC, Scint, LeadGlass, PMT).
- *Per-SD hit-multiplicity distribution* per event.
- *Primary-particle direction map* (cos θ vs φ) at production.
- *Final-state pion multiplicity histogram* from `Particle_output`.
- *Vertex-z distribution* (should be 0 ± foil-thickness/2).

Plan 47 ledger embeds these plots; plan 53 CI checks they are
produced for every signal sample.

## 3. Performance regression budget

| Metric | Budget | Source |
|---|---|---|
| events/sec on `RelWithDebInfo` build | ≥ 50/s for nominal signal | measured baseline |
| disk usage / event | ≤ 1 MB | parquet writer cost |
| hits/event mean (nominal signal) | within ±10% of baseline | regression alarm |
| TPC SD CPU fraction | < 30% | profiling |

Codex-supervisor records baselines on the first frozen sample (plan
20) and tracks regressions thereafter.

## 4. CI matrix

Plan 53 owns the matrix; this plan supplies the dimensions:

- Python reconstruction dimensions: `reco-smoke`, `reco-validation`,
  `reco-pid`, `realism-audit`, `registry`, `statistics`,
  `truth-ladder-core`, `truth-ladder-cli`, `fast-mc`, and
  `reco-closure`.
- Source-observed CMake build knobs from `NNBAR_Detector/CMakeLists.txt`:
  `WITH_GEANT4_UIVIS` ∈ {OFF, ON} and `MCPL_BUILD` ∈ {0, 1}.
- Negative A+ check: the current L3 CMake tree has no
  `WITH_SCINTILLATION`, `WITH_CELERITAS`, `WITH_OPTICKS`, or
  `WITH_GARFIELD_GPU` knobs. Do not add these to CI until a source
  grep shows an actual option or cache variable.
- `WITH_GEANT4_UIVIS=OFF, MCPL_BUILD=0` is the default headless smoke
  build and should run on every PR.
- `WITH_GEANT4_UIVIS=ON, MCPL_BUILD=0` is an optional visualization
  build smoke; it may skip the run step on headless CI if Geant4 UI/Vis
  drivers are unavailable, but the configure step must fail loudly.
- `WITH_GEANT4_UIVIS=OFF, MCPL_BUILD=1` is the MCPL-input smoke build;
  it must use a tiny checked sample or fixture path from plan 03 before
  it becomes required.

Each combination runs at least the smoke tests; a small
`run_signal_quick` sample with ≤ 100 events.

### 4.1 Build-knob verifier transcript

The source-observed build-knob inventory is intentionally small because
the A+ examiner rejected invented CLI/build surface. Before changing the
matrix, re-run these checks from the L3 worktree:

```bash
grep -R "option\\|WITH_\\|MCPL_BUILD" -n CMakeLists.txt
find tests -maxdepth 1 -type f -name 'test_*.py' | sort
find tests -maxdepth 1 -type f -name 'test_*.py' | wc -l
wc -l tests/test_reconstruction_smoke.py
ls pytest.ini CMakeLists.txt tests
```

Current 2026-05-10 verifier evidence:

- `find tests -maxdepth 1 -type f -name 'test_*.py' | wc -l` returns 31 files,
  matching §1.
- `wc -l tests/test_reconstruction_smoke.py` returns 395 lines, so the
  file is below the 500-line cap in this L3 worktree.
- `grep -R "option\\|WITH_\\|MCPL_BUILD" -n CMakeLists.txt` returns
  only `WITH_GEANT4_UIVIS` and `MCPL_BUILD`; no separate `cmake/`
  directory is present in the L3 worktree.
- `ls pytest.ini CMakeLists.txt tests` resolves the CI config, build
  config, and test directory paths.

## 5. Acceptance criteria

- §1 list matches `NNBAR_Detector/tests/` directory contents.
- §2 sanity plots are auto-generated and embedded in plan 47.
- §3 budgets are recorded against the first frozen signal sample.
- §4 CI matrix runs on every PR.

## 6. Risks and mitigations

- *Risk:* CI environment differs from production (Geant4 data files,
  CUDA version).
  *Mitigation:* plan 11 records the production environment; CI uses
  Docker pinning.
- *Risk:* sanity plots become stale.
  *Mitigation:* plan 47 ledger references this plan's plots; a
  ledger row regen forces a plot regen.

## 7. Dependencies

- **03** — sample IDs for regression baselines.
- **07** — SD outputs being sanity-plotted.
- **12** — physics-list selections feed CI matrix.
- *Consumed by:* plan 47 (ledger), plan 53 (CI), plan 50 (defence
  package).

## 8. References

- pytest documentation; existing `pytest.ini` in repo.
