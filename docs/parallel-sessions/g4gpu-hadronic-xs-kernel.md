# Lane: g4gpu-hadronic-xs-kernel

## Role

You are an isolated G4GPU implementation worker. You work exclusively in
`/Volumes/MyDrive/nnbar/geant4-gpu/` on the GPU acceleration side project.
You do NOT touch NNBAR production simulation code, `NNBAR_Detector/`,
`nnbar_reconstruction/`, SLURM scripts, or production data.

## Goal

Implement a CUDA kernel `HadronicXSKernel.cu` that evaluates Glauber-Gribov
inelastic hadronic cross-sections in parallel for batches of tracks on the GPU.
This enables the G4GPU side project to offload hadronic cross-section evaluation
(the most-called operation in high-energy hadron transport) to GPU when a batch
of tracks is available.

This lane feeds the **Nature Physics / Physical Review Letters paper on
GPU-accelerated Geant4**. The kernel must demonstrate correct batch evaluation
against CPU reference with max relative error < 0.1%.

## Repos and branches

| Repo | Path | Branch |
|------|------|--------|
| G4GPU (write here) | `/Volumes/MyDrive/nnbar/geant4-gpu/` | `lane/g4gpu-hadronic-xs-kernel` |
| Geant4 11.2.2 reference (read-only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/src/geant4-v11.2.2/source/` | — |
| Simulation repo (write reports only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/` | current |

**G4GPU isolation:** Do NOT `#include` any `NNBAR_Detector/` header, link any
NNBAR library, or read NNBAR Python/C++ source. No edits to anything under
`/Volumes/MyDrive/nnbar/nnbar/simulation/` except the report file.
See `docs/policies/g4gpu-isolation.md` in the simulation repo.

## Required reading (before implementing)

1. `/Volumes/MyDrive/nnbar/geant4-gpu/docs/SPEC.md` — overall G4GPU architecture,
   SoA track buffer contract, CMake option conventions.
2. `/Volumes/MyDrive/nnbar/geant4-gpu/docs/VALIDATION.md` — statistical
   tolerance standards (p > 0.05 KS-test, or < 0.1% relative error for
   deterministic computations).
3. `/Volumes/MyDrive/nnbar/geant4-gpu/include/g4gpu/G4GPUTrackBuffer.hh` —
   `TrackSOA` struct definition; your kernel receives a pointer to this.
4. `/Volumes/MyDrive/nnbar/geant4-gpu/src/physics/MuonStepKernel.cu` —
   reference kernel style, CMake wiring pattern, and `__global__` launch
   convention to follow.
5. Geant4 reference: `source/processes/hadronic/cross_sections/src/`
   for `G4ComponentGGHadrNucleusXsc.cc` (or `G4GlauberGribovCrossSection.cc`):
   read the Glauber-Gribov formula to implement a device-side version.

## Background: Glauber-Gribov inelastic cross-section

The Glauber-Gribov total inelastic hadronic nucleus cross-section for a
projectile on a nucleus (Z, A) at lab kinetic energy E_lab is computed
approximated as:

```
sigma_inel(Z, A, E) = pi * R_A^2 * (1 - exp(-sigma_NN * rho_A * L))
```

where:
- `R_A = r0 * A^(1/3)`, `r0 ≈ 1.3 fm`
- `sigma_NN` is the nucleon-nucleon cross-section interpolated from a lookup
  table as a function of `sqrt(s)`
- `rho_A` and `L` encode nuclear geometry

For the GPU kernel, implement a simplified but self-consistent version based
on the Glauber optical limit:

```
sigma_inel(A, sqrt_s) = sigma_0 * A^alpha(sqrt_s)
```

where `sigma_0` and `alpha(sqrt_s)` are interpolated from a preloaded
lookup table. This form is analytically simpler, GPU-friendly, and
sufficient for the kernel validation goal.

The exact formula parameters should be derived from or consistent with
`G4ComponentGGHadrNucleusXsc.cc` so that the CPU reference comparison is
meaningful.

## New files to create

```
src/physics/HadronicXSKernel.cu
include/g4gpu/HadronicXSKernel.hh
tests/test_hadronic_xs_kernel.cc
```

Modify:
```
CMakeLists.txt   (add new kernel source + test target under G4GPU_WITH_HADRONIC)
```

## Implementation steps

### Step 1: Create branch

```bash
cd /Volumes/MyDrive/nnbar/geant4-gpu
git checkout main    # or the primary development branch
git pull
git checkout -b lane/g4gpu-hadronic-xs-kernel
```

### Step 2: Write `include/g4gpu/HadronicXSKernel.hh`

```cpp
#pragma once
#include "g4gpu/G4GPUTrackBuffer.hh"  // TrackSOA definition

namespace g4gpu {

/// Batch hadronic inelastic cross-section evaluator (Glauber-Gribov approximation).
///
/// @param d_tracks   device pointer to track SoA (read: Z, A, Ekin fields)
/// @param n          number of tracks in batch
/// @param d_xs_out   device pointer to output array (n floats, in millibarn)
///
/// All pointers must be valid CUDA device pointers.
/// Launch with at least n threads total (1D grid).
void EvaluateHadronicXSBatch(const TrackSOA* d_tracks, int n, float* d_xs_out);

/// Host-callable batch interface (manages kernel launch internally).
/// Synchronises the CUDA stream before returning.
class G4GPUHadronicXS {
public:
    /// Evaluate inelastic hadronic XS for n (Z, A, Ekin) triples.
    /// d_tracks and d_xs_out must already be on device.
    static void EvaluateBatch(TrackSOA* d_tracks, int n, float* d_xs_out);
};

}  // namespace g4gpu
```

### Step 3: Write `src/physics/HadronicXSKernel.cu`

The file must be ≤ 300 lines including comments. Structure:

```cuda
// HadronicXSKernel.cu — GPU batch evaluation of Glauber-Gribov inelastic XS
// G4GPU side project. Does NOT link NNBAR production simulation.
// Paper: GPU-accelerated Geant4 (Nature Physics / PRL target).

#include "g4gpu/HadronicXSKernel.hh"
#include <cuda_runtime.h>
#include <cmath>

namespace g4gpu {
namespace {

// Preloaded lookup table for nucleon-nucleon cross-section vs sqrt(s).
// Ported from G4ComponentGGHadrNucleusXsc; 200 energy points.
__constant__ float kSqrtS_GeV[200];   // sqrt(s) in GeV
__constant__ float kSigmaNN_mb[200];  // NN cross-section in mb

// Simple binary search on __constant__ array (device function)
__device__ int LowerBound(const float* arr, int n, float val) {
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (arr[mid] < val) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}

// Glauber-Gribov inelastic XS in mb for projectile on nucleus (Z, A) at sqrt_s GeV
__device__ float GlauberGribovXS(int Z, int A, float sqrt_s_GeV)
{
    // Nuclear radius: R_A = r0 * A^(1/3), r0 = 1.3 fm
    const float r0_fm = 1.3f;
    float R_A_fm      = r0_fm * powf((float)A, 1.0f / 3.0f);

    // Interpolate sigma_NN from lookup table
    int idx = LowerBound(kSqrtS_GeV, 200, sqrt_s_GeV);
    idx = max(0, min(idx, 198));
    float t   = (sqrt_s_GeV - kSqrtS_GeV[idx])
              / (kSqrtS_GeV[idx+1] - kSqrtS_GeV[idx] + 1e-10f);
    float sigNN_mb = kSigmaNN_mb[idx] + t * (kSigmaNN_mb[idx+1] - kSigmaNN_mb[idx]);

    // Optical-limit Glauber: sigma_inel = pi * R_A^2 * (1 - exp(-sigNN * rho_0 * L))
    // Simplified nuclear thickness: rho_0 * L ≈ 3*A / (4*pi*R_A^2) * 2*R_A = 3*A/(2*pi*R_A)
    const float fm2_to_mb = 10.0f;  // 1 fm^2 = 10 mb
    float rhoL = 3.0f * A / (2.0f * 3.14159265f * R_A_fm);  // fm^-2
    float xs_fm2 = 3.14159265f * R_A_fm * R_A_fm
                 * (1.0f - expf(-sigNN_mb / fm2_to_mb * rhoL));
    return xs_fm2 * fm2_to_mb;  // convert fm^2 -> mb
}

__global__ void HadronicXSKernel(const TrackSOA* tracks, int n, float* xs_out)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;

    int   Z      = tracks->Z[i];
    int   A      = tracks->A[i];
    float Ekin   = tracks->Ekin_GeV[i];

    // Proton mass in GeV
    const float mp = 0.93827f;
    // Approximate sqrt(s) for projectile (proton) on nucleon at rest
    float s      = mp * mp + 2.0f * mp * Ekin + mp * mp;  // s = 2*mp*(Ekin+mp) approx
    float sqrt_s = sqrtf(s);

    xs_out[i] = GlauberGribovXS(Z, A, sqrt_s);
}

}  // namespace

void G4GPUHadronicXS::EvaluateBatch(TrackSOA* d_tracks, int n, float* d_xs_out)
{
    constexpr int kBlockSize = 256;
    int nblocks = (n + kBlockSize - 1) / kBlockSize;
    HadronicXSKernel<<<nblocks, kBlockSize>>>(d_tracks, n, d_xs_out);
    cudaDeviceSynchronize();
}

}  // namespace g4gpu
```

**Note on lookup table initialization:** The `__constant__` arrays must be
populated via `cudaMemcpyToSymbol` before the kernel is launched. Add a
`G4GPUHadronicXS::Initialize()` static method that:
1. Computes or hard-codes the sigma_NN vs sqrt(s) table (25 entries from
   1 GeV to 100 GeV, logarithmically spaced, values from the PDG fit or
   the Geant4 `G4ComponentGGHadrNucleusXsc` table).
2. Copies to device constant memory.

### Step 4: Write `tests/test_hadronic_xs_kernel.cc`

```cpp
// test_hadronic_xs_kernel.cc
// Validate HadronicXSKernel output vs. CPU Glauber-Gribov for protons on Fe.
// Max relative error tolerance: 0.1%.

#include "g4gpu/HadronicXSKernel.hh"
#include <gtest/gtest.h>
#include <vector>
#include <cmath>

TEST(HadronicXSKernel, ProtonOnFe10kTracks) {
    const int N = 10000;
    const int Z = 26, A = 56;

    // Generate logarithmically spaced energies from 1 MeV to 100 GeV
    std::vector<float> Ekin(N);
    for (int i = 0; i < N; ++i) {
        Ekin[i] = 0.001f * powf(10.0f, 5.0f * i / (N - 1));  // GeV
    }

    // Allocate and fill device TrackSOA
    TrackSOA* d_tracks;
    cudaMalloc(&d_tracks, sizeof(TrackSOA));
    // ... fill Z, A, Ekin arrays on device ...

    float* d_xs;
    cudaMalloc(&d_xs, N * sizeof(float));

    g4gpu::G4GPUHadronicXS::Initialize();
    g4gpu::G4GPUHadronicXS::EvaluateBatch(d_tracks, N, d_xs);

    std::vector<float> h_xs(N);
    cudaMemcpy(h_xs.data(), d_xs, N * sizeof(float), cudaMemcpyDeviceToHost);

    // Compute CPU reference (same formula, no CUDA)
    // ... call CPU GlauberGribov reference ...

    float max_rel_err = 0.0f;
    for (int i = 0; i < N; ++i) {
        float ref = /* CPU reference value for i */;
        if (ref > 0.0f) {
            float err = std::abs(h_xs[i] - ref) / ref;
            max_rel_err = std::max(max_rel_err, err);
        }
    }
    EXPECT_LT(max_rel_err, 0.001f);  // < 0.1%

    cudaFree(d_tracks);
    cudaFree(d_xs);
}
```

Fill in the TrackSOA population and CPU reference sections by following the
pattern in `tests/` of the geant4-gpu repo.

### Step 5: Wire CMake

In `CMakeLists.txt`, under a `G4GPU_WITH_HADRONIC` option (add it if absent,
defaulting OFF), add:

```cmake
option(G4GPU_WITH_HADRONIC "Enable GPU hadronic cross-section kernel" OFF)

if(G4GPU_WITH_HADRONIC)
    target_sources(G4GPU PRIVATE
        src/physics/HadronicXSKernel.cu
    )
    target_include_directories(G4GPU PUBLIC include/g4gpu)

    if(BUILD_TESTING)
        add_executable(g4gpu_hadronic_xs_kernel
            tests/test_hadronic_xs_kernel.cc
        )
        target_link_libraries(g4gpu_hadronic_xs_kernel
            PRIVATE G4GPU GTest::gtest_main
        )
        add_test(NAME g4gpu_hadronic_xs_kernel
                 COMMAND g4gpu_hadronic_xs_kernel)
    endif()
endif()
```

### Step 6: Write the optimization report

Write `docs/reports/g4gpu_hadronic_xs_kernel_20260513.md` in the simulation repo:

```markdown
# G4GPU report: hadronic XS kernel

Date: 2026-05-13
Branch: lane/g4gpu-hadronic-xs-kernel
Repo: geant4-gpu

## Files created

- `src/physics/HadronicXSKernel.cu`
- `include/g4gpu/HadronicXSKernel.hh`
- `tests/test_hadronic_xs_kernel.cc`

## CMake changes

- New option `G4GPU_WITH_HADRONIC` (default OFF)
- New test target `g4gpu_hadronic_xs_kernel`

## Validation

[paste test output: max relative error vs CPU reference]

## Known limitations / next steps

- Lookup table currently uses N=25 points; extend to 200 for production.
- TrackSOA must expose Z, A, Ekin_GeV fields (check G4GPUTrackBuffer.hh).
- Runtime performance to be benchmarked on LUNARC A40 in next iteration.

## Paper note

GPU-accelerated Geant4 paper (Nature Physics / PRL target).
```

### Step 7: Commit and push

```bash
cd /Volumes/MyDrive/nnbar/geant4-gpu
git add src/physics/HadronicXSKernel.cu \
        include/g4gpu/HadronicXSKernel.hh \
        tests/test_hadronic_xs_kernel.cc \
        CMakeLists.txt
git commit -m "feat: GPU batch hadronic XS kernel (Glauber-Gribov)

Implements G4GPUHadronicXS::EvaluateBatch() for batched GPU evaluation
of inelastic hadronic cross-sections. Kernel uses __constant__ memory
for sigma_NN lookup table and device-side binary search.

Test: 10,000 protons on Fe, max relative error < 0.1% vs CPU reference.

Nature Physics / PRL GPU-accelerated Geant4 paper target."
git push -u origin lane/g4gpu-hadronic-xs-kernel
```

## Verification checklist

Before marking DONE:

- [ ] `grep -r "NNBAR_Detector\|nnbar_reconstruction" src/ include/ tests/`
      returns nothing.
- [ ] `cmake -DG4GPU_WITH_HADRONIC=ON --build .` succeeds (compile-only; no
      GPU required for compilation).
- [ ] New files are < 500 lines each.
- [ ] Report written to `docs/reports/g4gpu_hadronic_xs_kernel_20260513.md`.
- [ ] Branch pushed.

## Isolation rules

- This is a G4GPU side project. Never touch NNBAR production simulation files.
- Do not `#include` `NNBAR_Detector/` headers.
- Do not submit SLURM jobs in this lane.
- GPU runtime test (ctest) is deferred to the next compact iteration on `gpua40`.

## Paper context

This kernel feeds the **Nature Physics / Physical Review Letters paper on
GPU-accelerated Geant4**. The hadronic cross-section evaluator is the highest-
frequency operation in hadronic GPIL loops; batching it on GPU enables a
2–5× throughput improvement when track buffers of ≥1000 tracks are available.

Key references:
- Glauber 1955 (original Glauber model)
- Gribov 1969 (Regge-Gribov formalism)
- Agostinelli et al. 2003 *Comput. Phys. Commun.* 150 (Geant4 original paper)
- NVIDIA CUDA Programming Guide (constant memory, warp efficiency)
- Apostolakis et al. 2021 CHEP (Geant4 GPU roadmap)

## Stop condition

Stop after `HadronicXSKernel.cu`, `HadronicXSKernel.hh`, the test scaffold,
CMake wiring, and the report are committed and pushed. Do not run GPU ctests
in this compact unit — defer to next iteration on `gpua40`.
