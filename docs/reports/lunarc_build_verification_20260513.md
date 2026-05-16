# LUNARC build verification 20260513

## Handoff

- Role type: specialist-contractor (worker-0 / C++ GPU LUNARC lane).
- Manager / escalation: VALIDATOR.
- Branch / worktree: local `/Volumes/MyDrive/nnbar/nnbar/simulation` on `main`; remote `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim`.
- Writable lease used: `codex-tasks/sim/worker-0.txt`, `docs/parallel-sessions/MASTER_PLAN.md`, and this report only.
- Factory item: TEAM_PLAN artifact ledger / A1 worker-start blocker check.
- Blocker queue checked: `codex-tasks/sim/blockers.txt` contained no `/goal`; shared blocker queues inspected before lane-local work.

## Verification commands

All LUNARC commands were run after the required multiplexed-socket guard returned `Connected`.

1. Remote checkout identity:
   ```text
   cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim
   hostname = cosmos2.int.lunarc
   branch = work/20260514-g4gpu-phase8-validation-gate-guard
   HEAD = a9cd54a6091612e62e1f1cd4bc41abe97f04adf7
   ```
2. Active build binary hash:
   ```text
   sha256sum build_lunarc/nnbar-detector-simulation.bin
   6e8b1bbb1345b81e76d725a88582e7e316d18d802db716e9d1458e9dee9a8108  build_lunarc/nnbar-detector-simulation.bin
   stat build_lunarc/nnbar-detector-simulation.bin
   size=1109776 mtime=2026-05-12 13:46:11.468123820 +0200
   ```
3. Source patch marker grep:
   ```text
   grep -nE 'RadioactiveDecay|SetUserMinEkine|SetUserMaxTime|SetMaxAllowedStep|m_edepMutex|RC-3|RC-4|SetThresholdForVeryLongDecayTime' \
     src/core/PhysicsList.cc src/core/DetectorConstruction.cc src/core/SteppingAction.cc src/core/EventAction.cc
   ```
4. Binary runtime-marker check:
   ```text
   strings build_lunarc/nnbar-detector-simulation.bin | grep -nE 'RadioactiveDecay long-lived threshold|G4RadioactiveDecay not found'
   6712: G4RadioactiveDecay not found on GenericIon;
   6714:PhysicsList: RadioactiveDecay long-lived threshold set to 1 ms
   ```
5. Stale cosmic proton bin5 scheduler check:
   ```text
   squeue -u scyiu -o '%.18i %.32j %.10T %.10M %.12l %.20R' | egrep -i 'JOBID|cosmic|proton|bin5|3040180|3046812|3047597|3048056'
                JOBID                             NAME      STATE       TIME   TIME_LIMIT     NODELIST(REASON)
   ```

## RC patch presence

| Patch | Evidence | Disposition |
| --- | --- | --- |
| RC-1 radioactive-decay long-lived threshold | `src/core/PhysicsList.cc:154` calls `SetThresholdForVeryLongDecayTime(1.0e6 * ns)`; binary strings contain the runtime success/failure marker. | Present in source and represented in the active `build_lunarc` binary. |
| RC-2 max-step guard | `src/core/DetectorConstruction.cc:185,195,206,217,226,235,250` call `SetMaxAllowedStep(cosmicMaxStep)` for carbon, silicon, beampipe, TPC, scintillator, lead-glass, and shielding paths. | Present in source; build binary mtime is newer than `DetectorConstruction.cc` by about five minutes. |
| RC-3 global stepping mutex removal | `src/core/SteppingAction.cc:20-21` records the global mutex removal and delegates locking to `ParquetOutputManager` / `GeometryManager`; no active `G4AutoLock` marker appeared in the audited grep output. | Present at source level. |
| RC-4 min kinetic-energy / max-time recoil guards | `src/core/DetectorConstruction.cc:186-187,196-197,207-208,251-252` call `SetUserMinEkine(cosmicMinEkine)` and `SetUserMaxTime(cosmicMaxTime)` on under-protected carbon/silicon/beampipe/shielding paths. | Present in source; build binary mtime is newer than the RC-4 source mtime. |

## Result

PASS for the bounded verification request: the LUNARC checkout identity, active `build_lunarc` binary SHA-256, source-level RC1/RC2/RC3/RC4 markers, RC-1 runtime marker embedded in the binary, and absence of active/stale cosmic proton bin5 jobs in `squeue` were recorded.

Caveat: the remote checkout has unrelated dirty files and the build directory does not retain object files or a compile database next to `build_lunarc/nnbar-detector-simulation.bin`, so RC-2/RC-4 binary inclusion is inferred from source mtimes preceding the binary mtime plus the RC-1 embedded runtime marker. I did not rebuild or submit SLURM work in this iteration.
