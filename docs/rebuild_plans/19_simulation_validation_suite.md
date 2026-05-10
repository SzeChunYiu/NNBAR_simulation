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

## 0.1 Wave 6 derivation — validation as physics closure

### Physics derivation

**What is physically measured.** The validation suite measures whether
the simulation and reconstruction preserve the load-bearing physical
invariants of the rebuild: source configuration, detector hit schemas,
energy deposits, particle multiplicities, vertex distributions,
statistical intervals, and analysis cut-flow semantics. A passing test
is not a physics result by itself; it is evidence that a specific
observable remains inside the contract needed for plan-47 reproduction.

**Estimator rationale.** Sanity plots are fast distributional
estimators for gross detector mistakes: eDep and hit-multiplicity
histograms expose material/SD failures, direction maps expose primary-
generator geometry errors, pion multiplicity histograms expose signal-
model drift, and vertex-z plots expose source-position mistakes.
Closure tests such as fast-MC, response matrix, ladder, and pull tests
validate estimator bias and uncertainty calibration before thesis rows
are interpreted. CI matrix builds then make those checks invariant
under source and build-option changes.

**Statistical character.** The suite combines deterministic contract
checks (schema, CLI, file-size, source-citation verifier) with
statistical checks (closure, golden real-sample outputs, performance).
Deterministic failures are hard gates. Statistical checks require
fixed seeds, bootstrap or fixture tolerances, and explicit budgets so
that random fluctuations do not mask regressions or create false
failures.

### Logic gaps

- **Regression budgets (50 events/s, 1 MB/event, ±10% hits/event,
  30% TPC CPU fraction).** Grounding: §3 records planning baselines.
  `OPEN:` replace with measured baselines from the first frozen plan-20
  signal sample and record machine/build metadata; target resolution
  date 2026-06-15.
- **Smoke sample size ≤100 events.** Grounding: §4 CI practicality.
  `OPEN:` show that the smoke sample still exercises every SD and
  schema row needed by the tests, or split a fast contract fixture from
  a slower physics-closure job; target resolution date 2026-06-22.
- **Sanity plot coverage.** Grounding: §2 enumerates plots but does
  not yet bind each plot to a concrete plan-47 artifact for every
  sample. `OPEN:` add ledger artifact ids and stale-plot invalidation
  rules once sample manifests are frozen; target resolution date
  2026-06-22.
- **Build-knob matrix.** Grounding: §4 uses only source-observed
  knobs; invented GPU/optical knobs are explicitly excluded. `OPEN:`
  promote additional knobs only after source grep and a passing smoke
  build exist; target resolution date 2026-06-29.
- **Per-test physics rationale.** Grounding: §1 lists validation
  surfaces. `OPEN:` tag each test in plan 53 with the plan id,
  observable, and failure owner so a red CI result maps to a concrete
  physics or contract risk; target resolution date 2026-06-22.

### Closure test for the derivation

1. Re-run the source/file verifiers in §4.1 and confirm the test
   inventory, line counts, and build knobs match the L3 worktree.
2. Run the deterministic contract tests (`realism`, `registry`,
   `citation-verifier`, CLI smoke, and file-size cap) and require exact
   pass/fail semantics.
3. Run closure/statistical tests with fixed seeds and archive their
   JSON/CSV artifacts under plan-47 ledger rows. Compare against the
   current golden outputs and reject unreviewed drift.
4. For each sanity plot in §2, assert both plot creation and source
   table freshness. A green pytest run without fresh plan-47 artifacts
   is not enough to claim thesis reproduction closure.

## 1. Existing tests

Current `NNBAR_Detector/tests/` inventory, read from the L3 worktree on
2026-05-10 after the Stage E expansion:

| Test file | Primary validation surface | Sanity plot / artifact | Regression budget | CI matrix dimension |
|---|---|---|---|---|
| `test_calorimeter_clusters_physics.py` | plan-31 calorimeter clustering physics derivation | cluster-merge and energy-sharing fixtures | physics parameters remain source/plan grounded | `reco-photon-physics` |
| `test_charged_physics.py` | plan-25 charged reconstruction physics derivation | public charged-function docstring gate | charged docstrings link plans and carry no OPEN markers | `reco-charged-physics` |
| `test_charged_pid_physics.py` | plan-29 charged PID physics derivation | truth-blind PID fixture | truth columns do not affect PID classification | `charged-pid-physics` |
| `test_charged_reco.py` | plan-25 charged-track candidates and plan-26 direction/PID helpers | charged track-candidate tables and direction rows | truth columns forbidden; real sample schema stable | `reco-charged` |
| `test_ci_workflow.py` | plan-53 GitHub Actions contract | workflow YAML path/trigger audit | required fast checks listed for touched paths | `ci-contract` |
| `test_cli_response_matrix.py` | plan 42 response-matrix CLI and artifact writers | response parquet, covariance NPZ, metadata JSON | flags and output schemas stable | `response-matrix-cli` |
| `test_cli_summarize_flags.py` | plan 42 summarize `--all-runs` and output flags | offset-table manifest and summary table | event-offset concatenation stable | `summarize-cli` |
| `test_closure.py` | plan 40 per-leaf closure runner | closure JSON and K-S bias report | unbiased fixture green; biased fixture red | `reco-closure` |
| `test_dedx_physics.py` | plan-27 dE/dx physics derivation | truncated-mean dE/dx fixture | truth columns do not affect dE/dx estimator | `dedx-physics` |
| `test_dqm.py` | plan-66 offline DQM status lattice | run-quality table and manifest | fail/warn/pass semantics stable | `dqm-offline` |
| `test_dqm_physics.py` | plan-66 DQM producer physics derivation | DQM docstring/link fixtures | quality/promotions stay plan-grounded | `dqm-physics` |
| `test_dqm_promotion.py` | plan-66 DQM promotion guardrails | DQM promotion/degrade fixture report | promotion requires explicit green provenance | `dqm-offline` |
| `test_electron_physics.py` | electron-pair reconstruction physics derivation | electron docstring link fixture | schema/reconstruction plan links remain present | `electron-physics` |
| `test_electron_reco.py` | electron-pair candidate reconstruction | electron-pair candidate rows | configured entry cut enforced; missing TPC columns produce empty schema | `reco-electron` |
| `test_event_variables.py` | plan-36 event-shape variables | event-variable rows from charged/photon vectors | sparse inputs emit finite invalid sentinels | `event-variables` |
| `test_event_variables_physics.py` | plan-36 event-variable physics derivation | event-shape fixture rows | physics definitions remain plan-grounded | `event-variables-physics` |
| `test_fast_mc.py` | plan 39 fast-MC smearing and closure fixtures | fast-MC closure report | fixed-seed deterministic; bias detected | `fast-mc` |
| `test_file_size_cap.py` | `CODING_STANDARDS.md` §1 file-size guard | scoped file-size report | modified source/test files stay <500 lines | `style-size-cap` |
| `test_golden_contract_matrix.py` | plan-53 synthetic/real output schema contract | golden schema matrix | reconstruction outputs match contract | `golden-contract` |
| `test_golden_regression.py` | plan-53 golden-output regression fixtures | golden reconstruction snapshot | snapshot stable unless fixture intentionally updated | `golden-regression` |
| `test_integration_real_sample.py` | real Geant4-output reconstruction schema integration | plan-09 §14 table set from checked real fixture | real sample reconstructs to expected columns | `real-sample-integration` |
| `test_kinematic_fit_physics.py` | plan-35 kinematic-fit physics derivation | kinematic-fit physics fixtures | mass/constraint assumptions remain plan-grounded | `pi0-kfit-physics` |
| `test_kfit.py` | plan-35 π⁰ kinematic-fit rows | fit-status and covariance rows | missing covariance preserves raw row | `pi0-kfit` |
| `test_ladder_cli.py` | plan 38 truth-ladder CLI report writers | ladder run/factorise JSON reports | `python -m` entrypoints exit 0 | `truth-ladder-cli` |
| `test_ladder_factorise.py` | additive truth-gap factorisation | factorisation residual table | residual closes truth gap | `truth-ladder-core` |
| `test_ladder_leaves.py` | plan 24 leaf registry coverage | leaf-registry JSON dump | every leaf present in fixed order | `truth-ladder-core` |
| `test_ladder_run.py` | truth-substitution ladder execution | ladder metric report JSON | fixed sample/seed deterministic | `truth-ladder-core` |
| `test_ladder_substitute.py` | per-leaf truth substitution | substituted event table | explicit leaf outputs preferred | `truth-ladder-core` |
| `test_ledger_reproduction.py` | plan-47 ledger reproduction command smoke | golden subset command manifest | command strings remain runnable/schema-stable | `ledger-reproduction` |
| `test_photon_objects_physics.py` | plan-33 photon-object physics derivation | photon-object fixture rows | conversion/isolation assumptions remain plan-grounded | `reco-photon-physics` |
| `test_photon_physics.py` | legacy photon reconstruction physics derivation | truth-blind photon/π0 fixture | truth columns do not affect legacy photon pairing | `photon-physics` |
| `test_photon_reco.py` | plan-31 photon/calorimeter reconstruction and plan-32 shower features | calorimeter cluster, photon, and shower-shape rows | truth columns forbidden; real sample schema stable | `reco-photon` |
| `test_physics_docstring_gate.py` | Wave-6 physics docstring gate | AST scan of public reconstruction functions | public functions include derivation/numerical-parameter blocks | `physics-docstring-gate` |
| `test_pid_calibration.py` | charged PID threshold scan | PID scan CSV and ROC/score outputs | truth-separating config ranks first | `reco-pid` |
| `test_pi0_pairing_physics.py` | plan-34 π⁰-pairing physics derivation | pairing fixture rows | invariant-mass and pairing assumptions remain plan-grounded | `pi0-pairing-physics` |
| `test_range_reco_physics.py` | plan-28 range reconstruction physics derivation | range fixture | truth columns do not affect range estimator | `range-physics` |
| `test_realism_audit.py` | plan 01/09 truth-read audit | audit JSON with violation list | undecorated Class B reads fail | `realism-audit` |
| `test_reconstruction_run_summary.py` | reconstruction run tables and thesis cut variables | summary tables and cut-variable rows | thesis calorimeter-direction variables present | `reco-summary` |
| `test_reconstruction_smoke.py` | end-to-end reconstruction smoke and thesis cutflow/object rules | `output/sanity/{edep,hits,vertex_z,timing}.png` plus reco tables | expected tables written; 395 lines on 2026-05-10, below the 500-line cap | `reco-smoke` |
| `test_reconstruction_validation.py` | validation report and readiness gates | validation JSON plus class-support table | readiness thresholds and all-run aggregation stable | `reco-validation` |
| `test_registry_integrity.py` | plan 03 dataset manifests and state machine | registry round-trip JSON / manifest hash report | illegal states/transitions rejected | `registry` |
| `test_selection.py` | plan-37 event selection and cut-flow accounting | cut-flow table and independent cut flags | cumulative counts follow plan-37 order | `selection-cutflow` |
| `test_selection_physics.py` | plan-37 event-selection physics derivation | selection-threshold fixture rows | cut ordering and threshold rationale remain plan-grounded | `selection-physics` |
| `test_shower_shape_physics.py` | plan-32 shower-shape physics derivation | shower-shape fixture rows | lateral/longitudinal shape assumptions remain plan-grounded | `reco-photon-physics` |
| `test_statistics.py` | plan 04 bootstrap, jackknife, Wilson, F-C | statistical interval JSON / pull table | seed binding deterministic | `statistics` |
| `test_track_fit_physics.py` | plan-26 track-fit physics derivation | track-fit fixture rows | scattering/pull assumptions remain plan-grounded | `track-fit-physics` |
| `test_verify_citations.py` | A+ source-citation verifier | verifier pass/fail fixtures and temporary source snippets | out-of-range or wrong identifiers fail | `citation-verifier` |
| `test_vertex_physics.py` | legacy vertex/event-row physics derivation | timing/vertex truth-blind fixture | truth columns do not affect timing annotations | `vertex-physics` |
| `test_vertex_reco.py` | plan-30 vertex projection, aggregation, and foil acceptance | vertex projection and aggregate rows | geometry-only acceptance uses plan-16 contract | `vertex-reco` |
| `test_vertex_reco_physics.py` | plan-30 vertex reconstruction physics derivation | foil-projection fixture | truth columns do not affect vertex chain | `vertex-reco-physics` |

Plan 53 runs these via pytest on every PR. The current inventory was
verified against 50 `test_*.py` files in the L3 `tests/` directory on
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
rtk proxy grep -R -n "option\\|WITH_\\|MCPL_BUILD" CMakeLists.txt
rtk proxy sh -c "find tests -maxdepth 1 -type f -name 'test_*.py' | sort"
rtk proxy sh -c "find tests -maxdepth 1 -type f -name 'test_*.py' | wc -l"
rtk proxy wc -l tests/test_reconstruction_smoke.py
rtk ls pytest.ini CMakeLists.txt tests
rtk proxy test ! -d cmake
```

Current 2026-05-10 verifier evidence:

- `rtk proxy sh -c "find tests -maxdepth 1 -type f -name 'test_*.py' | wc -l"` returns 50 files,
  matching §1.
- `rtk proxy wc -l tests/test_reconstruction_smoke.py` returns 395 lines, so the
  file is below the 500-line cap in this L3 worktree.
- `rtk proxy grep -R -n "option\\|WITH_\\|MCPL_BUILD" CMakeLists.txt`
  returns only `WITH_GEANT4_UIVIS` and `MCPL_BUILD`; `rtk proxy test
  ! -d cmake` confirms no separate `cmake/` directory is present in
  the L3 worktree.
- `rtk ls pytest.ini CMakeLists.txt tests` resolves the CI config, build
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
