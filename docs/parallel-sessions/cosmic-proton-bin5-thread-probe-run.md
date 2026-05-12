# Lane: cosmic-proton-bin5-thread-probe-run

> **For Codex:** REQUIRED SUB-SKILL: use `systematic-debugging` before
> submitting the diagnostic. This lane is the explicit authorization to run the
> guarded thread/seed probe only; it does not authorize production recovery.

## Goal

Submit exactly one guarded CRY proton bin5 thread/seed diagnostic array on
LUNARC using the already prepared
`slurm/cosmic_proton_bin5_thread_probe.sbatch` wrapper. Record the job id and
initial scheduler evidence, then stop so a later compact unit can inspect the
completed outputs.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/parallel-sessions/cosmic-proton-bin5-thread-probe.md`
4. `docs/parallel-sessions/cosmic-proton-bin5-recovery-design.md`
5. `docs/parallel-sessions/cosmic-slurm-array.md`
6. `CODING_STANDARDS.md`

## Writable scope

- `docs/parallel-sessions/MASTER_PLAN.md` status notes for this lane only.
- `docs/parallel-sessions/cosmic-slurm-array.md` proton-bin5 handoff notes.
- This lane spec, only for clarification if the safety checks are ambiguous.

Do not edit reconstruction code, detector C++ source, G4GPU code, old recovery
scripts, production macros, or existing output directories. Do not run
`cosmic_proton_bin5_recovery.sbatch` or any production recovery script.

## One compact-safe iteration

1. Run the LUNARC socket guard before every remote command group:
   ```bash
   rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
   ```
2. Verify the remote guarded wrapper is present and still syntax-valid:
   ```bash
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && test -f slurm/cosmic_proton_bin5_thread_probe.sbatch && bash -n slurm/cosmic_proton_bin5_thread_probe.sbatch"
   ```
3. Re-check the safety invariants before submission:
   ```bash
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && grep -F 'PROTON_BIN5_THREAD_PROBE_APPROVED:-NO' slurm/cosmic_proton_bin5_thread_probe.sbatch && grep -F '#SBATCH --array=0-7%2' slurm/cosmic_proton_bin5_thread_probe.sbatch && grep -F 'thread_probe_\${TASK_ID}' slurm/cosmic_proton_bin5_thread_probe.sbatch"
   rtk proxy ssh lunarc "squeue -u \$USER -o '%.18i %.45j %.10T %.10M %.40R' | grep -Ei 'pbin5-thread-probe|proton-bin5-thread-probe|cosmic-proton-bin5-thread-probe' || true"
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && find build_lunarc/output/cosmic_proton_bin5 -maxdepth 1 -type d -name 'thread_probe_*' -print | sort"
   ```
   If an active thread-probe job or non-empty `thread_probe_*` output already
   exists, do not submit. Mark this lane `BLOCKED` with the evidence.
4. Run `sbatch --test-only` once more and confirm it only reports a pseudo-job:
   ```bash
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && sbatch --test-only slurm/cosmic_proton_bin5_thread_probe.sbatch"
   ```
5. If steps 2--4 pass, submit exactly once with the guard variable set:
   ```bash
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && sbatch --parsable --export=ALL,PROTON_BIN5_THREAD_PROBE_APPROVED=YES slurm/cosmic_proton_bin5_thread_probe.sbatch"
   ```
6. Capture and commit the returned job id, immediate `squeue` state, and the
   exact later `sacct` plus row-count commands in `MASTER_PLAN.md` and
   `cosmic-slurm-array.md`. Keep the broad CRY array/proton recovery blocked
   until the diagnostic finishes and a later lane inspects row counts/logs.

## Stop condition

Stop after either:

- the guarded diagnostic array is submitted once and the job id plus immediate
  scheduler evidence are recorded, or
- a concrete safety blocker is recorded and no submission is made.

Do not wait for the full array to finish in this compact unit. Do not submit any
production-scale proton-bin5 recovery.
