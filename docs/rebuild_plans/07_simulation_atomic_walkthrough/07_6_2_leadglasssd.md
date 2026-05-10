---
id: 07_6_2_leadglasssd
title: Simulation atomic walkthrough §6.2 — LeadGlassSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `LeadGlassSD` sensitive detector (src/sensitive/LeadGlassSD.cc)

Status: detailed.

## Lifecycle methods

`LeadGlassSD` initializes `error_count` to zero, registers
`LeadGlassHitCollection`, stores the sensitive-detector name, and starts
with a null hit collection pointer (src/sensitive/LeadGlassSD.cc:30-39).
`Initialize` creates a new `NNbarHitsCollection` per event
(src/sensitive/LeadGlassSD.cc:45-50). `EndOfEvent` lazily caches
collection ID 0 and attaches the hit collection to the event HCE
(src/sensitive/LeadGlassSD.cc:175-181).

## `ProcessHits` filters and branches

`LeadGlassSD` is GPU/Celeritas defensive. It returns `false` if the
pre-step point is null, if the pre-step physical volume is absent or not
named `LeadGlassPV`, or if deposited energy is non-positive
(src/sensitive/LeadGlassSD.cc:53-68). Track data is optional; without a
track the SD keeps defaults such as `trackID = -1`, `proc = GPU`, zero
time/kinetic energy, zero Cerenkov photons, and origin volume `GPU`
(src/sensitive/LeadGlassSD.cc:72-84).

With a track, optical photons are dropped before hit creation
(src/sensitive/LeadGlassSD.cc:85-91). For non-optical tracks, the SD
records track ID, global time in ns, particle name, optional origin volume
and creator process, post-step kinetic energy, and counts Cerenkov optical
secondaries produced in the current step (src/sensitive/LeadGlassSD.cc:93-140).
The step-info branch records `1` for first step in volume and `0` for all
other accepted steps; there is no last-step distinction
(src/sensitive/LeadGlassSD.cc:169-170).

## Fields written to `NNbarHit`

| Field group | Values | Citation |
|---|---|---|
| identity / ancestry | name, track ID, parent ID, process, origin volume | (src/sensitive/LeadGlassSD.cc:72-84,93-134,155-159,168) |
| time / kinetic energy | global time in ns and post-step kinetic energy | (src/sensitive/LeadGlassSD.cc:93-95,136-140,157,166) |
| geometry index / position | `xHitID` from `GetReplicaNumber(1)`; position from touchable translation 0, or pre-step position fallback | (src/sensitive/LeadGlassSD.cc:143-151,160-163) |
| energy / length / photons | step length, total energy deposit, count of Cerenkov optical secondaries | (src/sensitive/LeadGlassSD.cc:65-70,101-115,164-167) |
| step tag | first-step flag only (`1` first, `0` otherwise) | (src/sensitive/LeadGlassSD.cc:169-170) |

The SD does not set current volume name, local position, particle
position, module/stave/group IDs, or a mean kinetic energy. Every accepted
hit is inserted once and returns `true` (src/sensitive/LeadGlassSD.cc:153-172).
