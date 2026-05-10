---
id: 07_6_2_tpcsd
title: Simulation atomic walkthrough §6.2 — TPCSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `TPCSD` sensitive detector (src/sensitive/TPCSD.cc)

Status: detailed.

## Lifecycle methods

`TPCSD` registers one `TPCHitCollection`, stores the detector name, and
starts with a null hit collection pointer (src/sensitive/TPCSD.cc:31-38).
`Initialize` creates a fresh `NNbarHitsCollection` for each event
(src/sensitive/TPCSD.cc:42-43). `EndOfEvent` lazily caches collection ID
0 and adds the collection to the event HCE (src/sensitive/TPCSD.cc:163-169).

## `ProcessHits` filter and branches

`TPCSD` records only TPC gas boundary steps: first step in volume or last
step in volume. Intermediate steps return `false` before any hit object is
created (src/sensitive/TPCSD.cc:45-53). Optical photons are rejected after
common step metadata is read and before hit insertion (src/sensitive/TPCSD.cc:98-124).

For non-optical boundary steps, the SD computes a Poisson-distributed
ionisation count from `energyDeposit / (23.6 eV)` and stores it in the
`NNbarHit::photons` field (src/sensitive/TPCSD.cc:98-104,149-151). When
`WITH_GARFIELD_GPU` is enabled and electrons are positive, the same
ionisation row is passed to `TPCDriftManager` with x/y/z, time, electron
count, TPC module index, layer index, and track ID
(src/sensitive/TPCSD.cc:106-120). The step-info decision records external
first steps as `1`, other external boundary steps as `0`, and tracks whose
origin volume is `TPC_1_layer_PV` or `TPC_2_layer_PV` as `999`
(src/sensitive/TPCSD.cc:153-158).

## Fields written to `NNbarHit`

| Field group | Values | Citation |
|---|---|---|
| identity / ancestry | particle name, track ID, parent ID, process, origin volume, current volume | (src/sensitive/TPCSD.cc:57-63,88-90,130-135) |
| position / time | midpoint of pre/post global positions; global time in ns | (src/sensitive/TPCSD.cc:68-79,136-139) |
| energy / direction | total step energy deposit, mean pre/post kinetic energy, pre-step momentum direction | (src/sensitive/TPCSD.cc:65-66,81-88,140-144) |
| geometry IDs | TPC layer from replica number 0; TPC module from replica number 1 | (src/sensitive/TPCSD.cc:92-95,146-147) |
| ionisation / track length | Poisson electron count stored via `SetPhotons`; raw step length stored as track length | (src/sensitive/TPCSD.cc:76,98-104,149-151) |
| step tag | external first-step `1`, external non-first boundary `0`, internally originated `999` | (src/sensitive/TPCSD.cc:153-158) |

`TPCSD` does not set local coordinates, particle-production positions, or
stave/group IDs. It is the only active SD that derives an electron-count
observable directly at hit time; the 23.6 eV W-value is distinct from the
Ar/CO2 gas-material note in the TPC builder.
