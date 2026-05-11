# OpenMC baseline bootstrap (worker-0, 2026-05-11)

## Scope

Compact bootstrap for `mcaccel-openmc-adapter` Iteration 1. The work was kept on LUNARC and in standalone benchmark/report artifacts; no NNBAR production code, build scripts, macros, SLURM production paths, or reconstruction code were modified.

## Source pins

- OpenMC source: `/projects/hep/fs10/shared/nnbar/billy/openmc`, tag `v0.15.3`, commit `27e38e894697`. The local tag choice was checked against upstream tags with `git ls-remote --tags --refs https://github.com/openmc-dev/openmc.git`; `v0.15.3` was the highest semantic tag returned on 2026-05-11.
- Benchmark models: `/projects/hep/fs10/shared/nnbar/billy/openmc-benchmarks`, commit `ba41bee54320` from `mit-crpg/benchmarks`.
- Build tree: `/projects/hep/fs10/shared/nnbar/billy/openmc/build-lunarc`.
- Run manifest copied to `benchmarks/openmc-baseline/manifest.json`; tabular result artifact written to `benchmarks/openmc-baseline/results.parquet`.

## LUNARC build evidence

- Configure command loaded `GCC/13.2.0`, `OpenMPI/4.1.6`, `HDF5/1.14.3`, `CMake/3.27.6`, and `Python/3.11.5`; CMake reported OpenMC `0.15.3`, MPI enabled, parallel HDF5 enabled, PNG enabled, DAGMC/libMesh/MCPL disabled.
- Build command: `cmake --build build-lunarc -j8`; wall time marker in the LUNARC log: `OPENMC_BUILD_SECONDS 45.32`.
- Verification: `ctest --test-dir build-lunarc --output-on-failure` ran 7 tests; 6 passed and `test_mcpl_stat_sum` reported an MCPL-library skip but returned a failing CTest status. The feature-compatible rerun `ctest --test-dir build-lunarc -E test_mcpl_stat_sum --output-on-failure` passed 6/6 in `OPENMC_CTEST_NO_MCPL_SECONDS 0.11`.

## Baseline run results

| Benchmark | Source | Status | Exit | Wall s | Output |
| --- | --- | --- | ---: | ---: | --- |
| HEU-MET-FAST-001 case 1 | mit-crpg/benchmarks icsbep/heu-met-fast-001/openmc/case-1 | blocked_or_failed | 255 | 0.603 | blocked before statepoint |
| PWR pin cell | openmc.examples.pwr_pin_cell (BEAVRS-derived) | blocked_or_failed | 255 | 0.515 | blocked before statepoint |
| C5G7 2D MOX/UO2 assembly proxy | mit-crpg/benchmarks c5g7/openmc/2d (multi-group) | completed | 0 | 1.324 | statepoint.5.h5 |

### Interpretation

- The two continuous-energy targets named by the lane spec, HEU-MET-FAST-001 and the PWR pin cell, were prepared with reduced particles/batches but stopped before transport because no `cross_sections.xml` was configured on LUNARC (`OPENMC_CROSS_SECTIONS` unset and no staged local OpenMC nuclear-data library found in the checked project paths). These rows are evidence of a data-staging blocker, not successful benchmark timings.
- The C5G7 2D MOX/UO2 multi-group case completed as a compact proxy for MOX-assembly transport plumbing because it carries its own `mgxs.h5` input. It produced `statepoint.5.h5`, `summary.h5`, and `Combined k-effective = 1.17463 +/- 0.00277` with total elapsed time `6.2070e-01 seconds` in the OpenMC log. This proxy does not replace the full requested k-inf MOX assembly benchmark.
- Next bootstrap step: stage an official OpenMC HDF5 nuclear-data library and set `OPENMC_CROSS_SECTIONS`, then rerun HEU-MET-FAST-001 and `openmc.examples.pwr_pin_cell` with production benchmark particle counts on a compute node. After that, replace the C5G7 proxy with the intended MOX assembly k-inf model or document the exact accepted benchmark source.

## Isolation check

All new local artifacts are under `benchmarks/openmc-baseline/` and this report. The remote OpenMC clone, benchmark clone, Python helper environment, and run directories live under `/projects/hep/fs10/shared/nnbar/billy/` and are separate from the NNBAR production detector tree. No G4GPU/OpenMC binary was linked into or invoked by the NNBAR production simulation pipeline.
