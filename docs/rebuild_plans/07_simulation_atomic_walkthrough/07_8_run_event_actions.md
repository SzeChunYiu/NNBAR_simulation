---
id: 07_8_run_event_actions
title: Simulation atomic walkthrough §8 — run and event actions
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

## 8. Run and event actions

### 8.1 `RunAction` (src/core/RunAction.cc, ~12 KB)

(Read-target at `src/core/RunAction.cc`.) Key responsibilities:

- Open per-run parquet writers via `ParquetOutputManager` (§9) for
  every output stream the SDs feed.
- Set per-run RNG seed (Geant4 random-engine seed; pulled from
  `RNGWrapper` if used).
- Aggregate `NNbarRun` per-run accumulators (`src/hits/NNbarRun.cc`).
- Emit a per-run summary on `EndOfRun`.

The run number `run_number_global` (defined in `main.cc:59`) drives
the output-file naming convention `<TableName>_<run>.parquet`. Plan 47
run orchestration owns the seed-binding rule.

### 8.2 `EventAction` (src/core/EventAction.cc, 13.5 KB)

Key responsibilities:

- On `BeginOfEventAction`: increments `event_number_global`.
- On `EndOfEventAction`: pulls each SD's hit collection out of the
  `G4HCofThisEvent`, converts each `NNbarHit` to a parquet row, and
  appends to the appropriate writer.
- Records primary-particle truth into the `Particle` table.
- Records the Geant4 `Interaction` ancestry table (decay/process tree)
  for the event.

The exact column schema produced by `EventAction` per output file is
codified in plan 09. The event-action source is the *single* code
path that writes a thesis-quoted parquet column; any change to it
requires a paired plan-09 update and a DEC entry (plan 05).

### 8.3 `SteppingAction` (src/core/SteppingAction.cc, 6.9 KB)

Currently a thin wrapper used for diagnostic output and step-length
control. Plan 14 (validation suite) audits whether any step-level
filtering happens here that bypasses SD decisions.

### 8.4 `ActionInitialization` (src/core/ActionInitialization.cc)

Owns:

- `g_useParticleGun` global (`-g` flag toggle).
- Construction of `RunAction`, `EventAction`, `SteppingAction`,
  `PrimaryGeneratorAction`.
- MT-mode worker initialisation.
