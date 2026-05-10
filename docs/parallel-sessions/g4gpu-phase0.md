# Lane: g4gpu-phase0

## Goal

Implement G4GPU Phase 0 infrastructure: all C++/CUDA boilerplate files per the spec.
This is fresh code in a new repo — no existing code to break.

## Repo

Work in: `/Volumes/MyDrive/nnbar/geant4-gpu/`

All work goes there, NOT in the simulation repo.

## Spec

Read the full spec before writing any code:
- `docs/SPEC.md` — complete file list, class declarations, CMake config, build verification protocol
- `docs/DESIGN_BRIEF.md` — architecture overview and motivation

## Files to produce (all in /Volumes/MyDrive/nnbar/geant4-gpu/)

1. `CMakeLists.txt` — per SPEC.md §Phase 0 CMakeLists; targets SM 80,86 (not 89, avoid compile time)
2. `include/g4gpu/G4GPUTrackBuffer.hh` — TrackSOA struct + G4GPUTrackBuffer class declaration
3. `include/g4gpu/G4GPUTrackingManager.hh` — G4GPUTrackingManager class declaration
4. `include/g4gpu/G4GPUGeometry.hh` — abstract base class G4GPUGeometry with pure virtual:
   `virtual float DistanceToNextBoundary(float3 pos, float3 dir, int& next_vol) = 0;`
5. `include/g4gpu/G4GPUHitBuffer.hh` — HitSOA struct + G4GPUHitBuffer class declaration
6. `src/core/G4GPUTrackBuffer.cc` — pinned cudaMallocHost alloc + AoS→SoA conversion from G4Track
7. `src/core/G4GPUTrackingManager.cc` — HandOverOneTrack (append to buffer) + FlushEvent (H2D + kernel + D2H)
8. `src/geometry/VoxelGeometry.cc` — stub class body (Build() is empty, no CUDA yet)
9. `src/geometry/VoxelGeometry.hh` — VoxelGeometry : G4GPUGeometry header
10. `src/hits/G4GPUHitBuffer.cu` — NullStepKernel: `__global__ void NullStepKernel(int* status, int n)` that sets all status = 1
11. `tests/test_stub.cc` — CPU-side test: allocates TrackSOA, fills 1024 tracks, H2D, launches NullStepKernel, D2H, asserts all status==1

## Build verification (run these in order, fix until all pass)

```bash
cd /Volumes/MyDrive/nnbar/geant4-gpu

# Check 1: cmake configure (no GPU needed)
cmake -B build \
  -DCMAKE_CUDA_COMPILER=$(which nvcc 2>/dev/null || echo nvcc) \
  -DG4GPU_WITH_OPTICAL=OFF -DG4GPU_WITH_RTX=OFF \
  . 2>&1 | tail -20

# Check 2: compile
cmake --build build -j4 2>&1 | tail -30
```

If nvcc is not found on the local machine, just verify that:
- All `.cc` and `.hh` files are syntactically correct C++17
- The `.cu` file compiles with: `nvcc -std=c++17 -x cu src/hits/G4GPUHitBuffer.cu -I include -c 2>&1`

Geant4 install for CMake: `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/lib/cmake/Geant4`
(Use this in -DGeant4_DIR if cmake can't find Geant4 locally. If Geant4 not available locally, stub out the G4Track include guard with `#ifdef G4GPU_HAVE_GEANT4`.)

## Iteration cycle

1. Write the files per the spec (one pass, all files)
2. Run build verification checks
3. Fix errors until cmake configure + compile pass
4. Commit all files on branch `lane/g4gpu-phase0` in the geant4-gpu repo

## Commit format

```
feat(phase0): implement Phase 0 infrastructure skeleton

- TrackSOA SoA buffer with pinned host alloc
- G4GPUTrackingManager HandOverOneTrack + FlushEvent skeleton
- NullStepKernel stub verifying H2D/D2H transfer path
- CMakeLists targets SM 80, 86

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

## Stop condition

Stop after one complete implementation + commit. Write "DONE: Phase 0 committed on lane/g4gpu-phase0" to stdout.

## Key constraints

- Max 500 lines per file (split if needed)
- No dependencies beyond Geant4 + CUDA (no Boost, no Eigen)
- Stub any G4Track method not available if Geant4 is not installed locally — use `#ifndef G4GPU_STUB_G4TRACK` guards
- FlushEvent does NOT loop — it does ONE H2D cudaMemcpyAsync, ONE kernel launch, ONE cudaDeviceSynchronize, ONE D2H
