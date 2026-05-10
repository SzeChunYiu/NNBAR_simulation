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
2026-05-10:

| Test file | Primary validation surface | Sanity plot / artifact | Regression budget | CI matrix dimension |
|---|---|---|---|---|
| `test_closure.py` | vertex closure and K-S bias detection | `output/validation/closure/vertex_pull.png` plus JSON summary | unbiased fixture green; biased fixture red; deterministic fixed inputs | `reco-closure` on Python versions |
| `test_cli_response_matrix.py` | plan 42 response-matrix CLI and artifact writers | response parquet, covariance NPZ, and metadata JSON per observable | registered flags present; artifacts schema-stable | `response-matrix-cli` |
| `test_cli_summarize_flags.py` | plan 42 summarize `--all-runs` and output flags | offset tables manifest plus summary table | event-offset concatenation stable; help lists remediation flags | `summarize-cli` |
| `test_fast_mc.py` | fast-MC smearing and closure fixtures | `output/validation/fast_mc/closure_pull.png` plus seed manifest | fixed-seed deterministic; deliberate bias detected | `fast-mc` on Python versions |
| `test_integration_real_sample.py` | real Geant4-output reconstruction schema integration | plan-09 section-14 table set from checked-in real sample fixture | real sample reconstructs to expected tables and columns | `real-sample-integration` |
| `test_ladder_cli.py` | plan 38 CLI report writers | ladder run/factorise JSON reports | report schema stable; `python -m` entrypoint exits 0 | `truth-ladder-cli` |
| `test_ladder_factorise.py` | additive truth-gap factorisation | factorisation residual table | residual closes truth gap; missing rungs rejected | `truth-ladder-core` |
| `test_ladder_leaves.py` | plan 24 leaf registry coverage | leaf-registry JSON dump | every leaf present in fixed order; unknown leaves fail | `truth-ladder-core` |
| `test_ladder_run.py` | truth-substitution ladder execution | ladder metric report JSON | fixed sample/seed deterministic; cumulative rung order stable | `truth-ladder-core` |
| `test_ladder_substitute.py` | synthetic truth substitution per leaf | substituted event table | explicit leaf outputs preferred; unavailable leaves rejected | `truth-ladder-core` |
| `test_pid_calibration.py` | charged PID threshold scan | `output/validation/pid/pid_scan.csv` and ROC/score plot | truth-separating config ranks first; single-class samples unusable | `reco-pid` |
| `test_realism_audit.py` | plan 01/09 truth-read audit | audit JSON with violation list | undecorated Class B reads fail; validation-only reads pass | `realism-audit` |
| `test_reconstruction_smoke.py` | end-to-end reconstruction smoke and thesis cuts | `output/sanity/{edep,hits,vertex_z,timing}.png` plus reco tables | expected tables written; thesis cutflow/object rules stable; file split required before edits because current file is >500 lines | `reco-smoke` across small samples |
| `test_reconstruction_validation.py` | validation report and readiness gates | validation JSON plus class-support table | readiness thresholds enforced; all-run aggregation stable | `reco-validation` |
| `test_registry_integrity.py` | plan 03 dataset manifests and state machine | registry round-trip JSON / manifest hash report | illegal states/transitions rejected; hash repair deterministic | `registry` |
| `test_statistics.py` | plan 04 bootstrap, jackknife, Wilson, F-C | statistical interval JSON / pull table | seed binding deterministic; reference intervals reproduced | `statistics` |
| `test_verify_citations.py` | A+ citation verifier for Python/C++ function and class references | verifier pass/fail fixtures and temporary source snippets | in-range citations pass; out-of-range or wrong identifier citations fail | `citation-verifier` |

Plan 53 runs these via pytest on every PR. The current inventory was
verified against 17 `test_*.py` files in the L3 `tests/` directory on
2026-05-10. The older simulation-source tests
(`test_cmake_configuration.py`, `test_cpp_static_safety.py`,
`test_geometry_audit.py`, and macro syntax tests) are no longer present
in that directory; if they return, this table must be updated in the
same commit. `test_reconstruction_smoke.py` was measured at 533 lines
during this inventory pass, so future edits to that test need a split
before growth.

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
wc -l tests/test_reconstruction_smoke.py
ls pytest.ini CMakeLists.txt tests
```

Current 2026-05-10 verifier evidence:

- `find tests -maxdepth 1 -type f -name 'test_*.py'` returns 17 files,
  matching §1.
- `wc -l tests/test_reconstruction_smoke.py` returns 533 lines, so the
  file is grandfathered and future edits must split it first.
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
