# Lane: signal-50k-monitor

## Goal

Monitor the already-submitted signal 50k job `3047773` on LUNARC and record
evidence without submitting any new job.

## Scope

Writable:

- `docs/parallel-sessions/MASTER_PLAN.md`
- `docs/reports/signal_50k_monitor.md` if a short evidence report is needed
- local derived copies under `build_lunarc/output/sig_foil_v3/` only when the
  remote job is complete and the output is non-stub

Do not edit C++ source, macros, SLURM wrappers, reconstruction algorithms, or
other workers' queue files.

## Required LUNARC guard

Before any remote command, run:

```bash
rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
```

Then use `rtk proxy ssh lunarc "..."` for remote checks.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, `docs/parallel-sessions/MASTER_PLAN.md`,
   `docs/parallel-sessions/signal-50k-run.md`, and this spec.
2. Check `squeue` and `sacct -X -j 3047773` for the signal job state.
3. If the job is still running or pending:
   - tail the remote stdout/stderr if present,
   - record timestamp, scheduler state, node/reason, and any current event
     counter in `MASTER_PLAN.md`,
   - do not copy output or submit a replacement job.
4. If the job completed:
   - inspect remote `build_lunarc/output/sig_foil_v3/` Parquet files,
   - verify the main event row count is greater than 40000,
   - rsync only the completed signal output locally,
   - update `MASTER_PLAN.md` with the row count and DONE/BLOCKED status.
5. If the job failed, timed out, or produced stubs:
   - record exact `sacct` state/exit code and output evidence,
   - update `MASTER_PLAN.md` as BLOCKED with the smallest next recovery need,
   - do not resubmit in this lane.

## Verification command

```bash
rtk proxy bash scripts/validate-csup-queues.sh
```

If output was copied locally, also run a focused Python row-count check against
the copied Parquet file(s) and quote the row count in `MASTER_PLAN.md`.

## Stop condition

Stop after `MASTER_PLAN.md` records the current state of job `3047773` with
evidence and queue validation passes. No new SLURM job should be submitted.
