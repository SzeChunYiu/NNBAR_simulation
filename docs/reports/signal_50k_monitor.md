# Signal 50k production monitor — job 3047773

Timestamp: 2026-05-12 12:49 CEST.

## Scheduler evidence

Guarded LUNARC checks found the already-submitted signal job still running; no
new SLURM job was submitted.

- `squeue -j 3047773`: `3047773 nnbar-signal-50k RUNNING 1:04:50/8:00:00` on `cn135`.
- `sacct -X -j 3047773`: `State=RUNNING`, `ExitCode=0:0`, `Elapsed=01:04:50`, `Start=2026-05-12T11:44:56`, `End=Unknown`, `NodeList=cn135`.
- `scontrol show job 3047773`: `JobState=RUNNING`, `Reason=None`, `RunTime=01:04:50`, `TimeLimit=08:00:00`, `EndTime=2026-05-12T19:44:56`, stdout/stderr under `slurm/signal-50k-3047773.{out,err}`.

## Log/output evidence

- `slurm/signal-50k-3047773.out` existed and was 53 MB at 12:49 CEST; tail showed active Geant4 event output with the latest observed starts/summaries including `Event 48318 starts` and `EVENT 47706 SUMMARY`.
- `slurm/signal-50k-3047773.err` existed and was 219 bytes; tail only showed detector-position file loading messages.
- Remote `build_lunarc/output/sig_foil_v3/` had growing detector Parquets, but `Particle_output_0.parquet` remained a 4-byte in-flight stub while the job was still running. No local copy was made.

## Current disposition

Keep the MASTER_PLAN row `RUNNING` until job `3047773` exits. A later monitor
iteration must re-check `squeue`/`sacct`, then only rsync `sig_foil_v3` after the
job completes and `Particle_output_0.parquet` has a verified row count above
40,000.
