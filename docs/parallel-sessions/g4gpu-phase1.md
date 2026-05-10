# Lane: g4gpu-phase1

## Goal

Implement the muon physics CUDA kernel (MuonStepKernel.cu) for G4GPU Phase 1.
This is the core physics engine: Bethe-Bloch ionization, Highland MCS, and bremsstrahlung
stub — all running one thread per muon on the GPU.

## Repo

Work in: `/Volumes/MyDrive/nnbar/geant4-gpu/`
Branch: `lane/g4gpu-phase1`

## Read first

- `docs/SPEC.md` §Phase 1 — full physics formulas and code sketches
- `docs/VALIDATION.md` — V1/V2/V3 tests to implement
- `include/g4gpu/G4GPUTrackBuffer.hh` — TrackSOA layout (Phase 0 output)
- `include/g4gpu/G4GPUGeometry.hh` — geometry interface (stub returns large distance for now)
- `src/hits/G4GPUHitBuffer.cu` — NullStepKernel pattern to follow

## Files to produce

### 1. `include/g4gpu/MaterialData.hh` (NEW, <60 lines)

```cpp
struct MaterialData {
    float Z_over_A;    // Z/A (dimensionless)
    float I;           // mean excitation energy (MeV)
    float density;     // g/cm³ → convert to MeV/mm
    float X0;          // radiation length (mm), for MCS
    char  name[32];    // human-readable
};
```

Include a `__constant__ MaterialData d_materials[64]` device array populated at startup.
Pre-define at minimum: iron (Z/A=0.4656, I=286eV, density=7.874, X0=17.58mm).

### 2. `src/physics/MuonStepKernel.cu` (NEW, <400 lines)

One CUDA thread per muon. Each thread:
1. Load track from TrackSOA (position, direction, ekin, status)
2. If status != 0 (not alive): return immediately
3. Compute step length: `step = min(geo_limit, physics_limit)`
   - geo_limit = 10.0 mm (stub — real geometry in Phase 2)
   - physics_limit: sample from exponential using brem mean free path (stub: 1000 mm)
4. Apply Bethe-Bloch energy loss: `dEdx = BetheBloch(ekin, MUON_MASS, mat)`
   - `delta_E = dEdx * step` (mean loss)
   - Landau straggling: `delta_E += curand_normal(&rng) * 0.1f * delta_E` (Gaussian approx)
   - `ekin -= delta_E`; if ekin <= 0: status = 1 (stopped)
5. Apply Highland MCS: `theta0 = HighlandTheta0(p, beta, step/mat.X0)`
   - Sample theta from Gaussian(0, theta0), phi uniform [0, 2π]
   - Update direction via Rodrigues rotation
6. Advance position: `pos += dir * step`
7. Write back to TrackSOA

Include `__device__` functions (from SPEC.md):
- `BetheBloch(float ekin, float mass, const MaterialData& mat)` — exact formula from spec
- `HighlandTheta0(float p, float beta, float x_over_X0)` — exact formula from spec
- `RodriguesRotate(float3 dir, float3 axis, float angle)` — rotate dir around axis

Constants:
- `ME = 0.511f` MeV (electron mass)
- `MUON_MASS = 105.658f` MeV
- `K = 0.307075f` MeV cm²/mol

### 3. `include/g4gpu/MuonStepKernel.hh` (NEW, <40 lines)

Host-side launcher declaration:
```cpp
void LaunchMuonStepKernel(
    TrackSOA* d_tracks,
    curandState* d_rng,
    const MaterialData* d_mats,
    int n_tracks,
    cudaStream_t stream
);
```

### 4. `src/core/G4GPUTrackingManager.cc` — wire up muon kernel

Replace stub `LaunchKernels_()` with actual call to `LaunchMuonStepKernel` when
`pdg == 13 || pdg == -13` (muon PDG codes). Non-muon tracks: leave status=0 (alive, no update).

### 5. `tests/test_muon_range.cc` (NEW, <200 lines)

Per VALIDATION.md V3:
- Initialize 1000 muons at 1 GeV straight into iron (+z direction)
- Step loop: call LaunchMuonStepKernel repeatedly until all status==1 (stopped)
- Measure range = accumulated step distance
- Compare to PDG range for 1 GeV muon in iron: ~165 mm
- Accept: within 5% (relaxed from 2% until geometry is exact)
- Print: PASS/FAIL + measured range + PDG reference

### 6. `tests/test_mcs.cc` (NEW, <150 lines)

Per VALIDATION.md V2:
- Initialize 1000 muons at 1 GeV through 100 mm iron
- Record final theta_x = atan2(dx, dz)
- Compute RMS of theta_x
- Compare to Highland prediction: theta0 ≈ 6 mrad at 1 GeV in 100mm Fe
- Accept: RMS within 10% of Highland (relaxed for Phase 1, tighten in Phase 3)
- Print: PASS/FAIL + measured RMS + Highland prediction

## Build integration

Add to CMakeLists.txt:
```cmake
if(G4GPU_WITH_MUON)
    target_sources(G4GPU PRIVATE
        src/physics/MuonStepKernel.cu
    )
endif()
```

Add test executables:
```cmake
add_executable(test_muon_range tests/test_muon_range.cc)
target_link_libraries(test_muon_range PRIVATE G4GPU)

add_executable(test_mcs tests/test_mcs.cc)
target_link_libraries(test_mcs PRIVATE G4GPU)
```

## Iteration cycle

1. Write all files above
2. Build: `cd /Volumes/MyDrive/nnbar/geant4-gpu && cmake --build build -j4 2>&1 | tail -20`
   (nvcc must be in PATH; if not, check syntax with clang CUDA mode)
3. Fix compile errors
4. Commit on `lane/g4gpu-phase1`
5. Push to GitHub: `git push origin lane/g4gpu-phase1`

Runtime tests (test_muon_range, test_mcs) need LUNARC GPU — note them as "ready to run
on LUNARC gpua40" in the commit message. Do not block on GPU availability.

## Stop condition

Stop when:
- MuonStepKernel.cu compiles cleanly
- Both test files compile
- Committed and pushed to `lane/g4gpu-phase1`

Write "DONE: G4GPU Phase 1 committed on lane/g4gpu-phase1" then re-read MASTER_PLAN.md.
Think about what else might be missing or could be improved in the G4GPU design.

## Constraints

- Max 500 lines per .cu file
- All physics constants as named `constexpr float` at top of .cu
- No CPU fallback for physics (this IS the GPU implementation)
- curand state: initialize in a separate `InitRNGKernel` called once per event
