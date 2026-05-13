# Lane: celeritas-monitor-rollover

## Goal
Prevent the Celeritas pending-job monitor report from crossing the 500-line cap.
`docs/reports/g4gpu_celeritas_3047497_monitor_20260512.md` is already 455
lines after the 12:59 CEST refresh.

## Scope
- Editable: Celeritas monitor report markdown under `docs/reports/`,
  `docs/parallel-sessions/MASTER_PLAN.md` only if status text needs the new
  report path.
- Forbidden: benchmark scripts, G4GPU source, NNBAR production code/data,
  SLURM submission/cancellation.

## Required steps
1. Do not delete evidence from the existing report.
2. Create a rollover report (for example
   `docs/reports/g4gpu_celeritas_3047497_monitor_20260512_part2.md`) for the
   next refresh, or split a summary/index plus dated shards if cleaner.
3. Preserve the current disposition: job 3047497 remains pending until stdout,
   stderr, or `results/results.parquet` exists.
4. Update MASTER_PLAN only to point future monitor refreshes at the rollover
   path; do not promote benchmark timing.

## Verification
Run:

```bash
rtk proxy wc -l docs/reports/g4gpu_celeritas_3047497_monitor_20260512*.md
rtk proxy bash scripts/validate-csup-queues.sh
```

## Stop condition
Stop after the report rollover path is documented and all touched markdown files
remain below 500 lines.
