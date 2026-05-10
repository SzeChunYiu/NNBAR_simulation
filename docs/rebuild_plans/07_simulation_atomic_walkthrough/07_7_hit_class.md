---
id: 07_7_hit_class
title: Simulation atomic walkthrough §7 — NNbarHit class
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

## 7. Hit class (NNbarHit, include/hits/NNbarHit.hh, 158 lines)

`NNbarHit` is the universal hit object emitted by every SD. The class
exposes 30+ accessor pairs spanning particle identity, kinematics,
geometry indices, and SD-specific fields:

- *Particle identity*: `name`, `trackID`, `parentID`, `process`,
  `localTime`, `time`.
- *Position*: `posX`, `posY`, `posZ` (global midpoint);
  `posX_local`, `posY_local`, `posZ_local` (local frame, set by SDs
  that compute it); `posX_particle`, `posY_particle`, `posZ_particle`
  (particle production point).
- *Momentum direction*: `px`, `py`, `pz` (unit vector from
  pre-step momentum direction).
- *Energy*: `energyDeposit` (per step), `kinEnergy` (mean step KE).
- *Geometry indices*: `xHitID` (= layer / replica 0), `stave_ID_`,
  `group_ID_`, `module_ID_` (= replica 1 in TPC), `origin_rp` (origin
  region/plane).
- *SD-specific*: `photons` (TPC: electrons; scintillator: photons;
  semantic depends on SD; the field name is intentionally retained
  per `TPCSD.cc:149` comment).
- *Track length*: `TrackLength` (set from `aStep->GetStepLength()` in
  TPCSD).
- *Volume names*: `vol_name`, `origin_vol_name`.
- *Step info*: `step_info` (1 / 0 / 999 per TPCSD logic).

The `G4Allocator<NNbarHit>` pool is thread-local (lines 136, 139–155)
to support MT mode.

Plan 09 (data dictionary) maps each of these C++ fields to its
parquet output column name and unit, and assigns each to Class A / B / C.
