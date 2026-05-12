# G4GPU Phase 5 measurement-framework verification — 2026-05-12

Date: 2026-05-12 13:23 CEST
Lane: worker-3 / G4GPU isolated; lane-swapped from stale local `codex-tasks/g4gpu/worker-1.txt`
Scope: Phase 5 measurement-framework verification only; no NNBAR production paths touched.

## Why this iteration

Worker-3 had no active `codex-tasks/g4gpu/worker-3.txt` entry and no G4GPU
`NEXT` row. The closest G4GPU queue item was a Phase 5 measurement-framework
prompt in `codex-tasks/g4gpu/worker-1.txt`, but that line was only an
uncommitted local queue addition. The latest LUNARC/fork Phase 5 branch already
contained the canonical-example/measurement-framework work, so this compact
iteration avoided duplicate code and recorded a verification audit instead.

## Remote source state

```text
LUNARC path: /projects/hep/fs10/shared/nnbar/billy/geant4-gpu
Branch: lane/g4gpu-phase5
Verified head: d5ad3ce test(benchmarks): cover W5 W6 plan blocker
Pre-existing untracked path: benchmarks/reference/ (not touched)
```

No local `cmake`, compiler, CUDA executable, Geant4/G4GPU executable, or SLURM
command was run. The LUNARC socket guard ran before each remote operation. No
new SLURM job was submitted, and no new GPU SLURM job was submitted.

## Verification commands and results

First configure attempt failed because the remote shell was not run as a login
Bash shell, so Lmod did not place `nvcc` on `PATH`:

```text
CMakeDetermineCUDACompiler.cmake: Failed to find nvcc.
```

Root cause check under `bash -lc` showed the module stack is available and
loads CUDA correctly:

```text
module is a function
CUDA/12.8.0 available
/sw/easybuild_milan/software/CUDA/12.8.0/bin/nvcc
```

Rerun command, with Lmod initialized, configured and built the full tree:

```bash
ssh lunarc "bash -lc 'cd /projects/hep/fs10/shared/nnbar/billy/geant4-gpu && \
  module load GCC/13.2.0 CUDA/12.8.0 CMake/3.27.6 && \
  cmake -B build \
    -DCMAKE_CUDA_COMPILER=nvcc \
    -DGeant4_DIR=/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/lib/cmake/Geant4 \
    -DG4GPU_WITH_OPTICAL=OFF \
    -DG4GPU_WITH_RTX=OFF \
    -DG4GPU_BENCHMARK_PYTHON=/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/bin/python \
    . && \
  cmake --build build -j8'"
```

Build result:

```text
-- Build files have been written to: /projects/hep/fs10/shared/nnbar/billy/geant4-gpu/build
[100%] Built target test_mcs
```

A full login-node `ctest` is not a valid green signal for the CUDA runtime tests:
`g4gpu_stub`, `g4gpu_voxel_geometry`, `g4gpu_muon_range`, and `g4gpu_mcs`
failed on the login node with `CUDA driver version is insufficient for CUDA
runtime version`. That is an environment/gpu-allocation limitation, not a
measurement-framework regression.

The measurement-framework subset (tests #5--#22: L0 CPU helpers, benchmark
manifest, script syntax, validation harness, harness schema/builder/runner/
hardware/run tests, and all six benchmark smoke drivers) passed with the same
module environment:

```bash
ssh lunarc "bash -lc 'cd /projects/hep/fs10/shared/nnbar/billy/geant4-gpu && \
  module load GCC/13.2.0 CUDA/12.8.0 CMake/3.27.6 && \
  ctest --test-dir build --output-on-failure -I 5,22'"
```

```text
18/18 Test #22: g4gpu_benchmark_beam_neutron_smoke ...........   Passed    0.63 sec

100% tests passed, 0 tests failed out of 18
Total Test time (real) = 14.96 sec
```

## Disposition

Keep Phase 5 in `RUNNING`: the measurement-framework branch builds, and the
non-GPU measurement tests pass on LUNARC. A full all-tests green still requires
a GPU-node ctest allocation for tests #1--#4; this iteration deliberately did
not submit a new GPU SLURM job because existing G4GPU jobs were already pending
on priority/resources.
