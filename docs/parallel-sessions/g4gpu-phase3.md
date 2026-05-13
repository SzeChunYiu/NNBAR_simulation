# Lane: g4gpu-phase3

## Goal

Implement the RTX geometry backend for G4GPU using NVIDIA OptiX 8+.
This provides hardware-accelerated BVH traversal via RT Cores — replacing G4Navigator
with the same silicon that powers real-time ray tracing in games.
This is the first use of RT Cores for HEP geometry navigation.

## Repo

Work in: `/Volumes/MyDrive/nnbar/geant4-gpu/`
Branch: `lane/g4gpu-phase3`

## Read first

- `docs/SPEC.md` §Phase 3 — RTX geometry spec with OptiX API sketch
- `docs/VALIDATION.md` §V5 — RTX accuracy test vs G4Navigator
- `include/g4gpu/G4GPUGeometry.hh` — abstract base to implement
- `src/geometry/VoxelGeometry.*` — the voxel backend to mirror the interface

## Prerequisite check — RESOLVED 2026-05-12

OptiX 9.0.0 SDK is installed at:
```
/projects/hep/fs10/shared/nnbar/billy/packages/optix-9.0/
```
Verified: `optix-9.0/include/optix.h` present (`OPTIX_READY`).

Pass to CMake as:
```bash
-DOptiX_INSTALL_DIR=/projects/hep/fs10/shared/nnbar/billy/packages/optix-9.0
```

Do NOT fall back to a stub — implement the full RTX backend using the real SDK.

## Files to produce

### 1. `include/g4gpu/RTXGeometry.hh` (NEW, <100 lines)

```cpp
#pragma once
#ifdef G4GPU_WITH_RTX
#include "G4GPUGeometry.hh"
#include <optix.h>

class RTXGeometry : public G4GPUGeometry {
public:
    RTXGeometry();
    ~RTXGeometry();

    void Build(G4VPhysicalVolume* world);
    float DistanceToNextBoundary(float3 pos, float3 dir, int& next_vol) override;

    OptixTraversableHandle GetBVH() const { return ias_handle_; }

private:
    OptixDeviceContext    context_ = nullptr;
    OptixTraversableHandle ias_handle_ = 0;
    CUdeviceptr            d_ias_buffer_ = 0;
    void BuildGAS_(G4VSolid* solid, int volume_id);
    void BuildIAS_();
};
#else
// Stub when compiled without OptiX
class RTXGeometry {
public:
    void Build(void*) {}
};
#endif
```

### 2. `src/geometry/RTXGeometry.cc` (NEW, <200 lines)

CPU-side: walk Geant4 geometry, tessellate each solid to triangles:
- `G4Box` → 12 triangles (6 faces × 2)
- `G4Tubs` → approximate with 32-sided polygon × 2 caps = ~96 triangles
- `G4Sphere` → UV sphere approximation
- General: use `G4TessellatedSolid` if available, else approximate

Build OptiX GAS per logical volume. Build IAS combining all volumes.
Record volume_id and material_id in SBT hit records.

### 3. `src/geometry/RTXGeometry.cu` (NEW, <200 lines)

OptiX programs:
```cuda
extern "C" __global__ void __raygen__boundary_query() {
    // Launch one ray, find first intersection
    // Write distance + volume_id to payload
}
extern "C" __global__ void __closesthit__record_boundary() {
    // Write t_hit and optixGetInstanceId() to payload
}
extern "C" __global__ void __miss__no_boundary() {
    // Set distance = 1e9 (no boundary found)
}
```

Host-side launcher: `float RTXDistanceToNextBoundary(float3 pos, float3 dir, int& next_vol)`.

### 4. CMakeLists.txt additions

```cmake
option(G4GPU_WITH_RTX "Enable RTX geometry backend (requires OptiX)" OFF)
if(G4GPU_WITH_RTX)
    find_package(OptiX REQUIRED)
    target_compile_definitions(G4GPU PUBLIC G4GPU_WITH_RTX=1)
    target_sources(G4GPU PRIVATE
        src/geometry/RTXGeometry.cc
        src/geometry/RTXGeometry.cu
    )
    target_link_libraries(G4GPU PUBLIC ${OptiX_LIBRARIES})
endif()
```

### 5. `tests/test_rtx_geometry.cc` (NEW, <100 lines)

Compile-time only if `G4GPU_WITH_RTX=ON`. Otherwise: empty test that prints
"RTX backend not compiled, skipping test" and returns 0.

## Stop condition

Full RTX backend compiles with `-DG4GPU_WITH_RTX=ON -DOptiX_INSTALL_DIR=/projects/hep/fs10/shared/nnbar/billy/packages/optix-9.0` on LUNARC (GCC/13.2.0 + CUDA/12.8.0 + gpua40 or gpua100 partition).
LUNARC GPU job passes `ctest -R rtx` (or at minimum the stub compile test).
Committed and pushed on `lane/g4gpu-phase3`.
Write "DONE: G4GPU Phase 3 RTX backend committed". Re-read MASTER_PLAN.md.
