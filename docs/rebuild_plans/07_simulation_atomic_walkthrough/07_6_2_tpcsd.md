---
id: 07_6_2_tpcsd
title: Simulation atomic walkthrough §6.2 — TPCSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

### 6.2 `TPCSD` (src/sensitive/TPCSD.cc, 170 lines)

- `Initialize` creates the `NNbarHitsCollection` for the event
  (`TPCSD.cc:42–43`).
- `ProcessHits` is invoked per Geant4 step.
  - Only `IsFirstStepInVolume()` and `IsLastStepInVolume()` are
    recorded (`TPCSD.cc:52`). All intermediate steps are dropped.
    This is a deliberate sparse representation that matches the
    "track entry/exit" geometry assumed by the offline vertexing
    (`reconstruction.py`).
  - Per recorded step, the hit fields are:
    - `name` = particle PDG name (line 130).
    - `trackID`, `parentID`, `process` (creator-process name; "primary"
      if `parentID == 0`) — lines 60–63.
    - `posX/Y/Z` = midpoint of pre/post-step position
      (lines 71–75; `mm`).
    - `time` = global track time in `ns` (line 79).
    - `kinEnergy` = mean of pre/post-step KE (lines 82–86).
    - `px/py/pz` = pre-step momentum direction (line 88).
    - `vol_name` = current volume; `origin_vol_name` = origin volume
      (lines 89–90).
    - `xHitID` = `replicaNumber(0)` = TPC layer index (line 94).
    - `module_ID` = `replicaNumber(1)` = TPC module index (line 95).
    - `stepInfo` = `1` if first step from outside, `0` otherwise,
      `999` if origin is `TPC_1_layer_PV` or `TPC_2_layer_PV`
      (lines 154–158).
    - `electrons` = Poisson-distributed integer with mean
      `eDep / (23.6 eV)` (lines 98–104). Stored in the `photons` field
      of `NNbarHit` because the field name is reused (line 149–150
      comment: *"too lazy to add one more function"*). Plan 12 must
      reconcile the **TPC W-value** with the broader Ar/CO₂ mixture
      reference value of 26–27.4 eV — the licentiate's
      validation discussion already flags this as a discrepancy
      (cf. `docs/detector_fundamental_question_tree.md` §3).
- Optical photons (`particleName == "opticalphoton"`) are dropped
  early (line 122–124).
- If `WITH_GARFIELD_GPU`, ionisation rows are pushed into
  `nnbar::TPCDriftManager` for later GPU drift simulation
  (lines 106–120).
- `EndOfEvent` adds the hit collection to the event's HC store
  (lines 164–169).

The TPC SD is the only SD that derives a primary observable
(electron count) at hit time. All other SDs record raw eDep and let
the offline pipeline (or the optical-photon tracker) translate.
