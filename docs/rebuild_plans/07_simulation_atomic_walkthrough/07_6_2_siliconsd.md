---
id: 07_6_2_siliconsd
title: Simulation atomic walkthrough §6.2 — SiliconSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `SiliconSD` sensitive detector (src/sensitive/SiliconSD.cc)

Status: detailed.

## Lifecycle methods

`SiliconSD` registers `SiliconHitCollection`, stores the detector name,
and starts with a null collection pointer (src/sensitive/SiliconSD.cc:27-36).
`Initialize` creates a fresh `NNbarHitsCollection` for every event
(src/sensitive/SiliconSD.cc:43-47). `EndOfEvent` lazily caches collection
ID 0 and attaches the hit collection to the event HCE
(src/sensitive/SiliconSD.cc:145-151).

## `ProcessHits` filter and branches

Unlike the boundary-step SDs, `SiliconSD::ProcessHits` has no active
first/last-step or energy-deposit filter: the commented physical-volume
and 100 eV threshold checks are inactive, so every Geant4 step reaching
this SD creates one hit (src/sensitive/SiliconSD.cc:50-65,139-142).
The only active hit-classification branch is `step_info`: first steps in
the silicon volume get `1`; every other step gets `0`
(src/sensitive/SiliconSD.cc:114-119). The process label remains
`primary` unless `trackID > 1` and the parent ID is non-zero, in which
case the creator-process name is stored (src/sensitive/SiliconSD.cc:96-104).

## Fields written to `NNbarHit`

| Field group | Values | Citation |
|---|---|---|
| identity / ancestry | particle name, track ID, parent ID, process, origin volume | (src/sensitive/SiliconSD.cc:92-110,116-127) |
| time | global time in ns and local time in ns | (src/sensitive/SiliconSD.cc:86-90,121-124) |
| geometry indices | `xHitID` from `GetReplicaNumber(0)` on the pre-step touchable | (src/sensitive/SiliconSD.cc:82-85,128) |
| energy / direction | total step energy deposit, post-step kinetic energy, pre-step momentum direction | (src/sensitive/SiliconSD.cc:63-68,106-109,126,130-134) |
| position | global midpoint x/y/z from pre/post positions | (src/sensitive/SiliconSD.cc:68-76,135-137) |
| track length | raw Geant4 step length via `SetTrackLength(DX)` | (src/sensitive/SiliconSD.cc:66-68,126) |

The code computes `tracklength = z - origin_vertex_z` and writes it once
through `SetPosZ(tracklength)`, but the subsequent `SetPosZ(z)` overwrites
that value before insertion (src/sensitive/SiliconSD.cc:78-80,129-137).
`vol_name`, local position, module/stave/group IDs, and photon/electron
counts are not set by this SD. Each accepted hit is inserted exactly once
and `ProcessHits` returns `true` (src/sensitive/SiliconSD.cc:139-142).
