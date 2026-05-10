---
id: 07_5_5_geometry_registration
title: Simulation atomic walkthrough §5.5 — geometry registration
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

### 5.5 Geometry registration

`DetectorConstruction.cc:188–246`:

- `nnbar::GeometryManager::Instance().Initialize()` populates a
  volume-lookup database for visualisation.
- `RegisterTPCGeometry()` (lines 248–303) registers all 12 TPC
  modules with positions, sizes, and drift directions:
  - 6 *front* modules at `z = -TPC_z/2`
  - 6 *back* modules at `z = +TPC_z/2`
  - Each ring of 6 has 2 Type II (top + bottom) and 4 Type I
    (left × 2, right × 2)
  - Drift direction encoded as `(axis, sign)` per module: e.g. Type
    II top drifts `-Y`, Type I left-back drifts `+X`.
- `RegisterGeometryParameters()` (lines 200–246) caches frequently-
  used dimensions (beampipe radii, TPC half-Z, TPC type widths) into
  `nnbar::GeometryParameters`. The values are converted to centimetres
  for downstream consumers.
