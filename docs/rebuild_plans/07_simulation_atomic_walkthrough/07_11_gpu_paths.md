---
id: 07_11_gpu_paths
title: Simulation atomic walkthrough §11 — GPU paths
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

## 11. GPU paths

All three GPU paths are off by default. They exist as opt-in
performance accelerators.

### 11.1 `TPCDriftGPU` (src/gpu/TPCDriftGPU.cc, 13.8 KB)

CUDA / OpenMP / single-threaded fallback for TPC electron drift. Fed
by `TPCSD::ProcessHits` (line 109) when `WITH_GARFIELD_GPU=ON`.
Produces a separate per-event drift output consumed by
`TPCDriftManager`. Plan 17 owns the drift-physics audit.

### 11.2 `OpticalPhotonGPU` (src/gpu/OpticalPhotonGPU.cc, 13.3 KB)

Standalone GPU optical-photon propagator, distinct from the Opticks
integration. Used as a fallback or comparator when Opticks is
unavailable.

### 11.3 `GPUManager` (src/gpu/GPUManager.cc, 10.4 KB)

Coordinates GPU resource ownership across the run. Decides which GPU
path is active per event based on compile-time flags and runtime
conditions (CUDA presence, memory).

### 11.4 Celeritas / Opticks (src/physics/*)

`src/physics/CeleritasInterface.cc`,
`src/physics/CeleritasCalorimeter.cc`,
`src/physics/OpticksInterface.cc` provide the optional GPU EM and
optical-photon offload. Behaviour is documented in the Celeritas /
Opticks upstream projects; plan 12 (physics-list audit) decides
whether to use them in production sample regeneration.
