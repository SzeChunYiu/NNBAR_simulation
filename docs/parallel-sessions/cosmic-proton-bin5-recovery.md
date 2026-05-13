# Lane: cosmic-proton-bin5-recovery

## Goal

Produce a guarded recovery design for proton bin5 (high-energy 50--200 GeV
cosmic protons) after the original 1M job, the first 250k sharded recovery, and
the second cap-diagnostic array all failed to recover a valid production
Parquet. This compact unit is evidence and recovery planning only.

## Current blocker

Do **not** submit another proton-bin5 job from the old recovery scripts.
`docs/parallel-sessions/cosmic-proton-bin5-recovery-design.md` records the
current evidence and the required next diagnostic: a no-submit-by-default
thread/seed probe that compares the failed seed paths with `THREADS=1` and
`THREADS=4` before any production-scale recovery is attempted.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/parallel-sessions/cosmic-slurm-array.md`
4. `docs/parallel-sessions/cosmic-proton-bin5-recovery-design.md`
5. `CODING_STANDARDS.md`

## Writable scope

- `docs/parallel-sessions/MASTER_PLAN.md` status notes for this lane only
- `docs/parallel-sessions/cosmic-slurm-array.md` handoff notes for proton bin5
- this lane spec, for clarification
- a future guarded `NNBAR_Detector/slurm/cosmic_proton_bin5_thread_probe.sbatch`
  only after the planner explicitly queues that follow-up lane

Do not edit reconstruction code, G4GPU code, detector geometry, or broad cosmic
array scripts. Do not submit, edit, or reuse `cosmic_proton_bin5_recovery.sbatch`
for production.

## One compact-safe iteration

1. Run the LUNARC guard before any remote command:
   ```bash
   rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
   ```
2. Verify that no active duplicate proton-bin5 job exists:
   ```bash
   rtk proxy ssh lunarc "squeue -u scyiu -o '%.18i %.30j %.10T %.10M %.40R' | grep -Ei 'proton|pbin5|cosmic|3046812' || true"
   ```
3. Inspect the latest proton-bin5 job, output, and log evidence:
   ```bash
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && sacct -X -j 3046812 --format=JobID,State,ExitCode,Elapsed,MaxRSS%12 -P"
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && find build_lunarc/output/cosmic_proton_bin5 -maxdepth 2 -name Particle_output_0.parquet -printf '%p %s bytes\\n' | sort"
   ```
4. If the evidence still matches the cap/seed-dependent stall pattern, update
   `MASTER_PLAN.md` to keep the broad CRY array active but mark the proton-bin5
   recovery lane `BLOCKED` with the design linked.
5. Do not submit any SLURM job in this lane unless a later prompt explicitly
   authorizes the thread-probe follow-up and `sbatch --test-only` passes.

## Verification

Before committing:

```bash
rtk wc -l docs/parallel-sessions/cosmic-proton-bin5-recovery.md docs/parallel-sessions/cosmic-proton-bin5-recovery-design.md docs/parallel-sessions/cosmic-slurm-array.md docs/parallel-sessions/MASTER_PLAN.md
rtk proxy bash -lc 'git diff -- docs/parallel-sessions/cosmic-proton-bin5-recovery.md docs/parallel-sessions/cosmic-proton-bin5-recovery-design.md docs/parallel-sessions/cosmic-slurm-array.md docs/parallel-sessions/MASTER_PLAN.md'
```

If a future wrapper is added, also run `bash -n` locally and guarded
`sbatch --test-only` on LUNARC before any submission. Do not claim recovery from
queue state alone; cite `sacct`, output sizes, row counts, and log tails.

## Current guarded decision (2026-05-12 08:17 CEST)

Evidence gathered with the required LUNARC socket guard:

- `3046812` fully exited and is absent from `squeue`.
- `3046812_0`, `_3`, and `_4` completed and produced valid 100/250/500-row
  Parquet files.
- `3046812_1` and `_2` timed out at six hours after events 96 and 243;
  `3046812_5` and `_6` failed with exit `0:15` after events 491 and 962.
- The root proton-bin5 file, first recovery `shard0`--`shard3`, and failed
  cap-diagnostic outputs remain 4-byte invalid stubs.

Decision: the lane is `BLOCKED`, not ready for another production recovery.
The next proton-bin5 work must first implement the thread/seed probe described
in `cosmic-proton-bin5-recovery-design.md`; no `sbatch` submission was made in
this iteration.
