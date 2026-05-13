# Lane: cosmic-bin5-rc1-threshold-activation

## Goal

Fix and verify the RC-1 radioactive-decay time-threshold activation for the
cosmic bin5 stall recovery. The 50-event verification job `3047558` completed,
but its stderr contains the fail-open warning:

```text
PhysicsList: WARNING — RadioactiveDecayBase process not found; long-lived isotope stall protection NOT active
```

Therefore proton/mu bin5 production is **not** unblocked yet. Do not submit any
production cosmic job in this lane.

## Evidence that triggered this follow-up

- `sacct -X -j 3047557,3047558` reports build job `3047557` and verification
  job `3047558` completed with exit `0:0`.
- `slurm/bin5-rc-verify-3047558.out` reports the 50-event check finished and
  wrote `build_lunarc/output/cosmic_proton_bin5/rc_verify_3047558/Particle_output_0.parquet`.
- `slurm/bin5-rc-verify-3047558.err` reports the warning above, so the intended
  long-lived-isotope protection did not attach to the actual Geant4 process.
- Premature production jobs `3047562_29` and `3047565_5` landed on holder node
  `cn018`, were canceled by the planner, and left only 4-byte stub outputs under
  `build_lunarc/output/cosmic_proton_5/` and `build_lunarc/output/cosmic_mu-_5/`.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/parallel-sessions/cosmic-bin5-stall-fix.md`
4. `docs/parallel-sessions/cosmic-proton-bin5-recovery.md`
5. `CLAUDE.md` holder-node rule

## Writable scope

Local nested checkout:

- `NNBAR_Detector/src/core/PhysicsList.cc`
- `NNBAR_Detector/include/core/PhysicsList.hh` only if the implementation needs a helper declaration

LUNARC source checkout:

- `src/core/PhysicsList.cc`
- `include/core/PhysicsList.hh` only if needed
- `slurm/bin5_rc_verify.sbatch` or a new RC-1 verification wrapper, only to make
  the warning fatal and to exclude holder node `cn018`

Coordination:

- `docs/parallel-sessions/MASTER_PLAN.md` row notes for this lane only
- this spec, for clarifications only
- the matching sim queue file to pop/claim this task

Do not edit reconstruction code, G4GPU code, detector geometry, broad cosmic
array scripts, or production cosmic queue entries. Do not submit proton/mu
production in this lane.

## Mandatory constraints

1. Run the LUNARC socket guard before every remote command batch:
   ```bash
   rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
   ```
2. Never run `nnbar-detector-simulation.bin` directly in a codex pane or on the
   holder node. Any Geant4 execution must use `sbatch`.
3. Every verification `sbatch` must exclude the holder node (`cn018`) before
   submission. Prefer adding `#SBATCH --exclude=cn018` to the verification
   wrapper and confirm with `scontrol show job` after submission.
4. Treat the warning text as a hard failure. A completed 50-event job is not
   sufficient unless stderr lacks the warning and the log contains a positive
   confirmation that the threshold was applied.

## One compact-safe iteration

1. Verify the current failing evidence:
   ```bash
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && grep -n 'RadioactiveDecayBase\|long-lived isotope' slurm/bin5-rc-verify-3047558.err slurm/bin5-rc-verify-3047558.out"
   ```
2. Inspect the current implementation and the installed Geant4 header names:
   ```bash
   rtk grep -n "RadioactiveDecay\|ConstructProcess\|SetThresholdForVeryLongDecayTime" NNBAR_Detector/src/core/PhysicsList.cc
   rtk proxy ssh lunarc "grep -n 'G4RadioactiveDecay(const G4String' /projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/include/Geant4/G4RadioactiveDecay.hh"
   ```
3. Fix the process lookup/API so the actual `G4RadioactiveDecay` process gets a
   1 ms `SetThresholdForVeryLongDecayTime` threshold after process construction.
   Do not leave a warn-and-continue path for the bin5 verification; fail the
   verification job if the process cannot be found.
4. Stage the same source change to LUNARC, build via `sbatch`, and run the
   50-event RC verification via `sbatch` with `--exclude=cn018` in effect.
5. Verify all of the following before updating `MASTER_PLAN.md`:
   - `sacct -X` for the build and verification jobs is `COMPLETED|0:0`.
   - `scontrol show job <verify-job>` shows `ExcNodeList=cn018` or equivalent.
   - Verification stderr has no `long-lived isotope stall protection NOT active`
     warning.
   - Verification log contains a positive threshold-applied message.
   - Output Parquet is non-stub and the wrapper log reports 50 rows.
6. If all checks pass, mark this lane `DONE` and leave production rows ready for
   a later compact production-submission lane. If any check fails, leave this
   lane `BLOCKED` with exact job IDs, warning text, and log paths.

## Verification commands

```bash
rtk wc -l docs/parallel-sessions/cosmic-bin5-rc1-threshold-activation.md docs/parallel-sessions/MASTER_PLAN.md
rtk bash scripts/validate-csup-queues.sh
rtk proxy bash -lc 'git diff -- docs/parallel-sessions/cosmic-bin5-rc1-threshold-activation.md docs/parallel-sessions/MASTER_PLAN.md codex-tasks/sim/worker-1.txt'
```

## Stop condition

Stop after one compact iteration: either the RC-1 threshold is verified active by
a holder-excluding `sbatch` job, or the failure remains documented and blocked.
Do not submit or re-submit proton/mu production jobs in this lane.
