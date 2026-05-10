---
id: 07_6_2_tubesd
title: Simulation atomic walkthrough §6.2 — TubeSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `TubeSD` sensitive detector (src/sensitive/TubeSD.cc)

Status: detailed.

## Lifecycle methods

`TubeSD` registers `TubeHitCollection`, stores the sensitive-detector name,
and initializes its collection pointer to null (src/sensitive/TubeSD.cc:26-32).
`Initialize` creates a fresh `NNbarHitsCollection` for the event
(src/sensitive/TubeSD.cc:36-37). `EndOfEvent` lazily resolves collection
ID 0 once and attaches the collection to the event HCE
(src/sensitive/TubeSD.cc:123-128).

## `ProcessHits` filter and branches

`TubeSD` is a boundary-step recorder for beampipe volumes: only first or
last steps in a sensitive tube volume proceed; all intermediate steps
return `false` before hit creation (src/sensitive/TubeSD.cc:39-45). The
process string is `primary` for parent ID 0 and otherwise the track's
creator-process name (src/sensitive/TubeSD.cc:46-55). After common field
population, the first/last branch sets the same step-info convention as
`CarbonSD`:

| Branch | `NNbarHit::step_info` | Citation |
|---|---|---|
| first and last in volume | `2` | (src/sensitive/TubeSD.cc:100-104) |
| first step only | `0` | (src/sensitive/TubeSD.cc:106-110) |
| last step only | `1` | (src/sensitive/TubeSD.cc:112-116) |
| any other path | print `TubeSD ends here!`, return `false` | (src/sensitive/TubeSD.cc:118-120) |

There is no energy threshold, no optical-photon rejection, and no
ionisation/photon conversion in this SD.

## Fields written to `NNbarHit`

For every accepted boundary step, `TubeSD` writes:

| Field group | Values | Citation |
|---|---|---|
| identity / ancestry | particle name, track ID, parent ID, process, origin volume name | (src/sensitive/TubeSD.cc:48-55,78-89) |
| current volume | pre-step touchable volume name via `SetVolName` | (src/sensitive/TubeSD.cc:80,88) |
| position / time | global midpoint of pre/post-step positions; global time in ns | (src/sensitive/TubeSD.cc:59-69,90-93) |
| energy / direction | total step energy deposit, mean pre/post kinetic energy, pre-step momentum direction | (src/sensitive/TubeSD.cc:56-58,71-78,94-98) |
| step tag | first/last boundary code from the branch table above | (src/sensitive/TubeSD.cc:100-116) |

`TubeSD` does not set local coordinates, replica IDs, module IDs,
track length, or photon/electron counts. Each accepted hit is inserted
exactly once before returning `true`.
