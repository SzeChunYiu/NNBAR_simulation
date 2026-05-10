---
id: 07_6_2_scintillatorsd
title: Simulation atomic walkthrough §6.2 — ScintillatorSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `ScintillatorSD` sensitive detector (src/sensitive/ScintillatorSD.cc)

Status: detailed.

## Lifecycle methods

`ScintillatorSD` registers `ScintillatorHitCollection`, stores the
sensitive-detector name, and initializes the hit collection pointer to
null (src/sensitive/ScintillatorSD.cc:27-36). `Initialize` creates a new
`NNbarHitsCollection` per event (src/sensitive/ScintillatorSD.cc:43-48).
`EndOfEvent` lazily caches collection ID 0 and adds the collection to the
event HCE (src/sensitive/ScintillatorSD.cc:185-196).

## `ProcessHits` filter and GPU-safe branches

This SD is written to tolerate Celeritas/GPU callbacks. It immediately
returns `false` if the pre-step point is null or if total deposited energy
is non-positive (src/sensitive/ScintillatorSD.cc:51-60). Track data is
optional: defaults are `unknown`, `GPU`, `trackID = -1`, zero time/energy,
and zero replica IDs until a valid `G4Track` or touchable is available
(src/sensitive/ScintillatorSD.cc:67-85).

When a track exists, optical photons are dropped before hit creation;
non-optical tracks fill particle name, track ID, global/local time,
track-length proxy `z - vertex.z`, optional origin volume, creator
process, and post-step kinetic energy (src/sensitive/ScintillatorSD.cc:86-130).
If touchable data exists, the SD extracts stave/layer/module replica
numbers, current volume name, touchable translation, and local coordinates
from the top navigation transform (src/sensitive/ScintillatorSD.cc:132-149).
There is no first/last-step filter: any non-optical, positive-energy step
that passes the safety checks inserts a hit.

## Fields written to `NNbarHit`

| Field group | Values | Citation |
|---|---|---|
| timing / identity | local time, global time, name, track ID, parent ID, process | (src/sensitive/ScintillatorSD.cc:70-80,94-129,153-159) |
| geometry IDs | stave ID from replica 0, layer ID via `SetXID`, module ID from replica 2 | (src/sensitive/ScintillatorSD.cc:132-140,160-162) |
| module/global positions | `SetPosX/Y/Z` receives touchable translation if available, otherwise pre-step position | (src/sensitive/ScintillatorSD.cc:61-65,83-84,140,163-165) |
| local and particle positions | local x/y/z from navigation transform; raw pre-step position stored as particle position | (src/sensitive/ScintillatorSD.cc:142-149,166-171) |
| volume / origin | current touchable volume and origin volume (or GPU defaults) | (src/sensitive/ScintillatorSD.cc:79-82,108-121,138-140,172-173) |
| step / length / energy | first-step flag (`1` first, `0` otherwise), `z - vertex.z` track-length proxy, energy deposit, post-step kinetic energy | (src/sensitive/ScintillatorSD.cc:98-129,174-178) |
| photon-equivalent count | integer `energyDeposit * 11136` stored in `photons` | (src/sensitive/ScintillatorSD.cc:151,179) |

Every accepted hit is inserted once and returns `true`
(src/sensitive/ScintillatorSD.cc:153-182). The photon count is a
calibration-style conversion performed even when optical photon transport
is disabled elsewhere; it is separate from actual optical-photon hits in
`PMTSD`.
