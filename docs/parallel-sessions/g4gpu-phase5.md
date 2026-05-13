# Lane: g4gpu-phase5 (Benchmark suite + L0 microarchitecture wins)

## Goal

Establish the measurement framework for line-by-line Geant4 acceleration, then
apply L0 (microarchitecture) optimizations to the CPU fallback path.

Without measurement we cannot prove "nobody beats us." Without measurement we
also cannot validate that an L1/L2 optimization didn't break physics.

Read the strategy root first: `docs/specs/g4gpu-line-by-line-acceleration.md`

## Repo

Work in: `/Volumes/MyDrive/nnbar/geant4-gpu/`
Branch: `lane/g4gpu-phase5`

## Subphase 5a — Benchmark suite

### Files to produce

`benchmarks/events/` — six canonical event drivers:

1. `gamma_100mev.cc` — 100 MeV gamma into a 1 m³ lead block (EM shower)
2. `muon_10gev.cc` — 10 GeV muon, 10 m of detector (MIP transport)
3. `nbar_carbon.cc` — antiproton at rest on a 12C nucleus (signal channel)
4. `cosmic_shower.cc` — CRY-generated cosmic muon at the cosmic veto
5. `optical_scintillator.cc` — 1 MeV electron in scintillator (optical photons)
6. `beam_neutron.cc` — 25 meV neutron in B4C beampipe (low-E neutron transport)

Each driver:
- Uses the existing `NNBAR_Detector` geometry or a stripped-down stand-in
  geometry committed in `benchmarks/geometries/`
- Runs 1000 events
- Records: total wall time, per-step time, hits histogram, primary kinematics
- Outputs Parquet files at `benchmarks/results/<event>_<commit>.parquet`

`benchmarks/run_baseline.sh` — orchestrator that runs all six on LUNARC via
SLURM and rsyncs results back. **All builds and runs on LUNARC, not locally.**

### Subphase 5b — Profiling harness

`benchmarks/profile_cpu.sh` — wraps each driver in `perf record`, dumps
`perf report --stdio` and `perf annotate` for the top 20 hot functions into
`benchmarks/profiles/<event>_cpu_<commit>.txt`.

`benchmarks/profile_gpu.sh` — wraps GPU-enabled drivers in
`ncu --set full --target-processes all` and dumps Nsight Compute reports.

### Subphase 5c — Validation harness

`benchmarks/validate.py`:
- Loads two Parquet files (reference + candidate)
- Runs KS test on: total deposited energy, leading particle KE, particle
  multiplicity, vertex position
- Asserts KL divergence ≤ 1% on each
- Returns nonzero on any tolerance breach
- Used as CI gate

### Subphase 5d — L0 microarchitecture wins

Only after 5a–5c are in place. Apply these in order, validating after each:

1. **Cross-section interpolator AVX-512 / NEON**: vectorize
   `G4PhysicsVector::Value()`-equivalent code. Target file
   `src/physics/CrossSectionInterpolator.cc`.
2. **Branchless surface tests**: rewrite `G4Box::DistanceToIn()` /
   `G4Tubs::DistanceToIn()` equivalents in `src/geometry/branchless_solids.cc`.
3. **Cache-line aligned tracks**: 64-byte align `Track` struct in
   `include/g4gpu/Track.hh`. Confirm via `alignof(Track)`.
4. **Prefetch ahead of touchable walks**: insert `__builtin_prefetch` in the
   navigation inner loop.

After each, run the benchmark suite. Commit only if speedup is positive AND
validation passes.

## Iteration cycle

1. Read this spec and `docs/specs/g4gpu-line-by-line-acceleration.md`
2. Mark `g4gpu-phase5` RUNNING in `docs/parallel-sessions/MASTER_PLAN.md`
3. Implement one subphase (5a, 5b, 5c, or 5d.N)
4. Verify on LUNARC:
   ```bash
   rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/geant4-gpu && cmake --build build -j8 && ctest --test-dir build"
   ```
5. Commit on `lane/g4gpu-phase5`, push to GitHub
6. If all subphases done, mark `g4gpu-phase5` DONE; else stop and re-iterate

## Acceptance

- All six benchmark events produce Parquet output on LUNARC
- `perf annotate` output committed for each event
- Validation harness passes on Geant4 baseline (sanity)
- L0 wins deliver ≥ 1.8× CPU speedup on at least four of the six events
- No validation regression

## Stop condition

After Subphase 5a + 5b + 5c (measurement framework) is in place, stop and
let the planner review before starting 5d. The measurement framework is
the load-bearing artifact; L0 wins follow.
