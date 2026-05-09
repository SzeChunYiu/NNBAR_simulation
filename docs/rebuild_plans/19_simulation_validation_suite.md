---
id: 19_simulation_validation_suite
title: Simulation validation suite — sanity, closure, regression
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 03_dataset_registry, 07_simulation_atomic_walkthrough, 12_physics_list_audit]
inputs: []
outputs:
  - {path: NNBAR_Detector/tests/, schema: pytest test suite}
  - {path: docs/rebuild_plans/19_simulation_validation_suite.md, schema: this file}
acceptance:
  - {test: every WITH_* CMake option has a paired smoke build + run, method: CI matrix, pass_when: every option green}
  - {test: per-SD sanity plots produced for nominal signal sample, method: §2 plots, pass_when: plots in plan 47 ledger}
  - {test: regression budget defined for events/sec, MB/event, hits/event, method: §3 thresholds, pass_when: no regressions on main}
risks:
  - {risk: optional GPU paths fail silently when no GPU is available on CI, mitigation: §4 GPU-conditional CI matrix}
  - {risk: validation suite drift, mitigation: §5 ownership rotation in plan 06}
estimated_effort: M
last_updated: 2026-05-09
---

# Simulation validation suite

*Charter.* The shared test harness that gates every simulation change.
Three layers: (1) sanity plots that flag obvious physics mistakes,
(2) per-component closure tests, (3) performance regression bounds.
Plan 53 (CI) runs the suite on every PR.

## 1. Existing tests

`NNBAR_Detector/tests/`:

- `test_cmake_configuration.py` — CMake option permutations.
- `test_cpp_static_safety.py` — static checks on C++ source.
- `test_geometry_audit.py` — wraps the `geometry-audit` CLI.
- `test_reconstruction_smoke.py` — end-to-end reconstruction smoke.
- `test_reconstruction_validation.py` — validation report shape.
- `test_pid_calibration.py` — PID-threshold scan.
- `test_pi0_mass_study.py` — π⁰ mass-ladder.
- `test_charged_stress_study.py` — charged-stress evaluation.
- `test_pi0_fake_study.py` — π⁰ fake background.
- `test_study_macros.py` — macro-syntax validity.

Plan 53 runs these via pytest on every PR. Codex-supervisor extends
as new artifacts land.

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

- `WITH_SCINTILLATION` ∈ {OFF, ON}
- `MCPL_BUILD` ∈ {OFF, ON}
- `WITH_CELERITAS` ∈ {OFF} on CPU-only CI; {ON} on GPU CI when
  available
- `WITH_OPTICKS` similarly conditional
- `WITH_GARFIELD_GPU` similarly conditional

Each combination runs at least the smoke tests; a small
`run_signal_quick` sample with ≤ 100 events.

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
