# Lane: g4gpu-phase2

## Goal

Implement the Voxel Geometry backend for G4GPU (VoxelGeometry.cc + VoxelGeometry.cu).
This replaces the stub `geo_limit = 10mm` in the muon step kernel with real
geometry-aware step limiting via 3DDA ray march on GPU.

## Repo

Work in: `/Volumes/MyDrive/nnbar/geant4-gpu/`
Branch: `lane/g4gpu-phase2`

## Read first

- `docs/SPEC.md` §Phase 2 — VoxelGeometry spec with 3DDA algorithm
- `docs/VALIDATION.md` §V4 — voxel geometry accuracy test
- `include/g4gpu/G4GPUGeometry.hh` — abstract base class to implement
- `src/physics/MuonStepKernel.cu` — where `DistanceToNextBoundary()` will be called

## Files to produce

### 1. `include/g4gpu/VoxelGeometry.hh` (NEW, <120 lines)

```cpp
#pragma once
#include "G4GPUGeometry.hh"
#include <cstdint>

struct VoxelGrid {
    float  origin_x, origin_y, origin_z;   // grid origin (mm)
    float  voxel_size;                       // isotropic voxel size (mm)
    int    nx, ny, nz;                       // grid dimensions
    uint8_t* material_id;                    // flat [nx*ny*nz] device array
    uint16_t* volume_id;                     // flat [nx*ny*nz] device array
};

class VoxelGeometry : public G4GPUGeometry {
public:
    explicit VoxelGeometry(float voxel_mm = 1.0f);
    ~VoxelGeometry();

    // Build from Geant4 geometry (CPU, call at startup)
    // Walks the geometry tree, probes each voxel center, stores material_id
    void Build(G4VPhysicalVolume* world);

    // Returns device-side VoxelGrid handle (set after Build())
    const VoxelGrid& DeviceGrid() const { return d_grid_; }

    // G4GPUGeometry interface (stub for CPU; real impl is in .cu)
    float DistanceToNextBoundary(float3 pos, float3 dir, int& next_vol) override;

private:
    float voxel_mm_;
    VoxelGrid h_grid_;   // host
    VoxelGrid d_grid_;   // device (after cudaMemcpy)
    void AllocDevice_();
    void CopyToDevice_();
};
```

### 2. `src/geometry/VoxelGeometry.cc` (EXPAND from stub, <300 lines)

Implement `Build(G4VPhysicalVolume* world)`:
1. Determine bounding box from world volume solid
2. Allocate `h_grid_.material_id` and `h_grid_.volume_id` (flat arrays)
3. For each voxel centre: use `G4Navigator::LocateGlobalPointAndSetup()` to find volume
4. Store `material_id` = index into material table (build material table as vector)
5. Call `CopyToDevice_()` → `cudaMemcpy` flat arrays to device

Material table: `std::vector<MaterialData>` built during step 3.
Export as `__constant__` array to device via `cudaMemcpyToSymbol`.

### 3. `src/geometry/VoxelGeometry.cu` (NEW, <200 lines)

CUDA device functions:

```cuda
__device__ float DistanceToNextVoxelBoundary(
    float3 pos, float3 dir, const VoxelGrid grid,
    int& out_material_id
) {
    // Amanatides & Woo (1987) 3DDA algorithm
    // 1. Compute initial voxel indices from pos
    // 2. Compute tDelta (step size per axis in t-space)
    // 3. Compute tMax (distance to first boundary per axis)
    // 4. Step: advance along axis with smallest tMax
    // 5. Stop when material_id changes → return t, set out_material_id
}
```

Also expose a CPU-callable launcher used by `VoxelGeometry::DistanceToNextBoundary()`.

### 4. Wire into MuonStepKernel.cu

Replace `geo_limit = 10.0f` stub with:
```cuda
int next_mat_id;
float geo_limit = DistanceToNextVoxelBoundary(pos, dir, d_grid, next_mat_id);
// Use next_mat_id to update material for next step
```

### 5. `tests/test_voxel_geometry.cc` (NEW, <150 lines)

Per VALIDATION.md V4:
- Build a simple 3-volume geometry (vacuum box, iron sphere inside, vacuum outside)
- Probe 10,000 random points
- Compare VoxelGeometry material_id vs brute-force lookup
- Accept: 100% agreement in interior voxels (boundary voxels may differ by ≤1 voxel)
- Print: PASS/FAIL + disagreement count

## Build additions

```cmake
target_sources(G4GPU PRIVATE
    src/geometry/VoxelGeometry.cc
    src/geometry/VoxelGeometry.cu
)
add_executable(test_voxel_geometry tests/test_voxel_geometry.cc)
target_link_libraries(test_voxel_geometry PRIVATE G4GPU)
```

## Iteration cycle

1. Write all files
2. Build: `cd /Volumes/MyDrive/nnbar/geant4-gpu && cmake --build build -j4 2>&1 | tail -20`
3. Fix compile errors
4. Commit on `lane/g4gpu-phase2`, push to GitHub

## Stop condition

Compiles cleanly. Commit pushed. Write "DONE: G4GPU Phase 2 voxel geometry committed".
Re-read MASTER_PLAN.md.
