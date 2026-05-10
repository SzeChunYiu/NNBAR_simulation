---
id: 07_6_2_pmtsd
title: Simulation atomic walkthrough §6.2 — PMTSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `PMTSD` sensitive detector (src/sensitive/PMTSD.cc)

Status: detailed.

## Lifecycle methods

`PMTSD` registers `PMTHitCollection`, stores the sensitive-detector name,
and initializes its hit collection pointer to null (src/sensitive/PMTSD.cc:25-34).
`Initialize` creates a fresh `NNbarHitsCollection` for each event
(src/sensitive/PMTSD.cc:40-45). `EndOfEvent` lazily caches collection ID
0 and attaches the hit collection to the event HCE
(src/sensitive/PMTSD.cc:133-144).

## `ProcessHits` filter and optical-photon branch

`PMTSD` assumes normal Geant4 pointers are present: it immediately reads
track, particle definition, pre-step touchable, and post-step point without
the GPU/null guards used by `ScintillatorSD` and `LeadGlassSD`
(src/sensitive/PMTSD.cc:48-99). The only accepted hits are optical photons
whose mean kinetic energy lies strictly between 2.53 eV and 2.695 eV
(src/sensitive/PMTSD.cc:96-103). Accepted photons create one hit, are
inserted, and then the track is killed with `fKillTrackAndSecondaries`
(src/sensitive/PMTSD.cc:102-124). All other particles or optical photons
outside the energy window return `false` (src/sensitive/PMTSD.cc:126-127).

The process label is `primary` for track ID 1 or parent ID 0; otherwise it
uses the creator-process name (src/sensitive/PMTSD.cc:80-94). There is no
energy-deposit threshold beyond the optical-photon energy-window cut.

## Fields written to `NNbarHit`

| Field group | Values | Citation |
|---|---|---|
| identity / ancestry | particle name, track ID, parent ID, process | (src/sensitive/PMTSD.cc:54-59,78-94,107-112) |
| timing | global and local track time as raw Geant4 time values | (src/sensitive/PMTSD.cc:74-77,107-110) |
| geometry / position | `xHitID` from touchable replica number 1; PMT position from touchable translation 0 | (src/sensitive/PMTSD.cc:64-70,113-116) |
| energy | total energy deposit and post-step kinetic energy | (src/sensitive/PMTSD.cc:61-62,96-99,119-120) |
| track action | accepted optical photon track is killed after insertion | (src/sensitive/PMTSD.cc:121-124) |

`PMTSD` does not set `step_info`, current or origin volume names, local
position, particle position, module/stave/group IDs, track length, or a
photon-count field. The hit itself represents one accepted optical photon.
