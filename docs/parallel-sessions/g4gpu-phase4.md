# Lane: g4gpu-phase4

## Goal

Implement the optical photon transport kernel for G4GPU using NVIDIA OptiX path tracing.
This replaces Geant4's serial CPU optical transport with parallel GPU path tracing —
the same algorithm used for real-time rendering in games, now applied to scintillation
photons in the NNBAR detector.

## Repo

Work in: `/Volumes/MyDrive/nnbar/geant4-gpu/`
Branch: `lane/g4gpu-phase4`

## Read first

- `docs/SPEC.md` §Phase 4 — optical photon kernel design
- `docs/VALIDATION.md` §V6 — detection efficiency + timing distribution tests
- `include/g4gpu/G4GPUHitBuffer.hh` — hit accumulation interface
- `src/geometry/RTXGeometry.*` — BVH to reuse for photon tracing

## Physics mapping (thesis + Geant4 → OptiX)

| Geant4 process | OptiX program | Implementation |
|---|---|---|
| G4OpBoundaryProcess — reflection/refraction | `__closesthit__` | Fresnel equations, sample reflected/transmitted |
| G4OpAbsorption — bulk absorption | Per-step | Beer-Lambert: `exp(-step/abs_length)` per material |
| G4OpRayleigh — Rayleigh scattering | `__closesthit__` or scatter kernel | Sample new direction |
| PMT hit detection | `__closesthit__` on PMT surface | atomicAdd to PMT hit buffer |
| Photon escaped | `__miss__` | Mark photon killed |

## Files to produce

### 1. `include/g4gpu/G4GPUOptical.hh` (NEW, <120 lines)

```cpp
#pragma once
#include <cuda_runtime.h>

struct PhotonSOA {
    float* x, *y, *z;           // position (mm)
    float* dx, *dy, *dz;        // direction (unit)
    float* wavelength;           // nm
    float* polarization_x, *polarization_y, *polarization_z;
    int*   status;               // 0=alive, 1=absorbed, 2=detected, 3=escaped
    int    size;
    int    capacity;
};

struct MaterialOpticalData {
    float refractive_index;      // n
    float absorption_length_mm;  // mean free path for absorption
    float rayleigh_length_mm;    // mean free path for Rayleigh scattering
    char  name[32];
};

struct PMTHitBuffer {
    float* edep;                 // always 1 photon = 1 hit
    float* time;
    int*   pmt_id;
    int    n_hits;
    int    capacity;
};

void LaunchOpticalPhotonKernel(
    PhotonSOA* d_photons,
    PMTHitBuffer* d_pmt_hits,
    MaterialOpticalData* d_opt_mats,
    void* bvh_handle,            // OptixTraversableHandle cast to void* for header purity
    curandState* d_rng,
    int n_photons,
    cudaStream_t stream
);
```

### 2. `src/optical/OpticalPhotonKernel.cu` (NEW, <400 lines)

OptiX raygen program — one ray per optical photon:
```cuda
extern "C" __global__ void __raygen__optical() {
    int idx = optixGetLaunchIndex().x;
    // Load photon from PhotonSOA
    // Launch ray with current pos+dir
    // On hit: apply Fresnel, sample reflection/transmission
    //         if absorbed: mark status=1
    //         if PMT surface: atomicAdd to PMT buffer, mark status=2
    // On miss: mark status=3 (escaped)
    // Loop up to MAX_BOUNCES=100
}
```

Fresnel coefficients:
```cuda
__device__ float FresnelReflectance(float cos_theta_i, float n1, float n2) {
    float sin_t2 = (n1/n2)*(n1/n2) * (1.0f - cos_theta_i*cos_theta_i);
    if (sin_t2 > 1.0f) return 1.0f;  // total internal reflection
    float cos_theta_t = sqrtf(1.0f - sin_t2);
    float rs = (n1*cos_theta_i - n2*cos_theta_t) / (n1*cos_theta_i + n2*cos_theta_t);
    float rp = (n2*cos_theta_i - n1*cos_theta_t) / (n2*cos_theta_i + n1*cos_theta_t);
    return 0.5f * (rs*rs + rp*rp);
}
```

### 3. `src/optical/ScintillationSampler.cu` (NEW, <150 lines)

Given energy deposition event (position, edep, material):
- Sample N_photons from Poisson(edep × photon_yield_per_MeV)
- Sample wavelengths from scintillation spectrum (Gaussian ~420nm ±10nm for plastic scint)
- Generate isotropic initial directions
- Populate PhotonSOA for GPU transport

### 4. CMakeLists.txt additions

```cmake
option(G4GPU_WITH_OPTICAL "Enable OptiX optical photon transport" OFF)
if(G4GPU_WITH_OPTICAL)
    find_package(OptiX REQUIRED)
    target_sources(G4GPU PRIVATE
        src/optical/OpticalPhotonKernel.cu
        src/optical/ScintillationSampler.cu
    )
    target_compile_definitions(G4GPU PUBLIC G4GPU_WITH_OPTICAL=1)
endif()
```

### 5. `tests/test_optical.cc` (NEW, <120 lines)

Per VALIDATION.md V6:
- If compiled without OptiX: print skip message, return 0
- Otherwise: generate 1000 photons at origin, pointing up (+y)
  in a glass sphere geometry. Count how many reach the PMT surface.
  Check detection efficiency > 0 (smoke test only in Phase 4).

## Stop condition

Compiles with `-DG4GPU_WITH_OPTICAL=OFF` (no OptiX needed for basic build).
Core algorithm (Fresnel, ScintillationSampler) code reviewed for correctness.
Committed and pushed on `lane/g4gpu-phase4`.
Write "DONE: G4GPU Phase 4 optical transport committed". Re-read MASTER_PLAN.md.

## Note on OptiX dependency

Phases 3 and 4 both require OptiX SDK. If OptiX is not available on the build machine:
- Write the header and source files completely
- Guard with `#ifdef G4GPU_WITH_OPTICAL` / `#ifdef G4GPU_WITH_RTX`
- Document in README how to activate when OptiX is available
- The physics and algorithm correctness can still be reviewed without compiling
