---
id: 07_6_2_carbonsd
title: Simulation atomic walkthrough §6.2 — CarbonSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `CarbonSD` sensitive detector (src/sensitive/CarbonSD.cc)

Status: detailed.

## Lifecycle methods

`CarbonSD` registers one hit collection named `CarbonHitCollection`,
stores the sensitive-detector name, and clears the collection pointer in
its constructor (src/sensitive/CarbonSD.cc:27-36). `Initialize` allocates
a fresh `NNbarHitsCollection` for each event using that detector name and
collection name (src/sensitive/CarbonSD.cc:43-44). `EndOfEvent` lazily
caches collection ID 0 in a static `HCID` and adds the event collection to
the Geant4 `G4HCofThisEvent` container (src/sensitive/CarbonSD.cc:127-133).

## `ProcessHits` filter and branches

`ProcessHits` records only boundary steps: first step in the carbon volume,
last step in the carbon volume, or a single step that is both first and
last. Intermediate steps return `false` before any hit object is created
(src/sensitive/CarbonSD.cc:47-52). After filling the common fields, the
step-info branch inserts exactly one hit and returns `true`:

| Branch | `NNbarHit::step_info` | Citation |
|---|---|---|
| first and last in volume | `2` | (src/sensitive/CarbonSD.cc:106-110) |
| first step only | `0` | (src/sensitive/CarbonSD.cc:112-116) |
| last step only | `1` | (src/sensitive/CarbonSD.cc:118-122) |
| any other path | no insert, `false` | (src/sensitive/CarbonSD.cc:124) |

The process label is `primary` for parent ID 0; secondary tracks use the
creator process name (src/sensitive/CarbonSD.cc:53-62). There is no
optical-photon rejection, no energy threshold, no ionisation/electron
conversion, and no local-coordinate or replica-number extraction in this
SD.

## Fields written to `NNbarHit`

For each accepted boundary step, `CarbonSD` writes particle identity,
truth ancestry, kinematics, global midpoint position, and deposited
energy into `NNbarHit`:

| Field group | Values | Citation |
|---|---|---|
| identity / truth | particle name, track ID, parent ID, process, origin volume name | (src/sensitive/CarbonSD.cc:55-62,85-95) |
| position / time | midpoint of pre/post global positions; track global time in ns | (src/sensitive/CarbonSD.cc:66-76,96-99) |
| energy / direction | total step energy deposit, mean of pre/post kinetic energy, pre-step momentum direction | (src/sensitive/CarbonSD.cc:63-65,78-85,100-104) |
| step tag | `step_info` from the first/last branch table above | (src/sensitive/CarbonSD.cc:106-122) |

The SD does not set `vol_name`, local position, layer/module IDs,
photon/electron counts, or track length; downstream parquet fields for
those accessors therefore depend on `NNbarHit` defaults for carbon hits.
