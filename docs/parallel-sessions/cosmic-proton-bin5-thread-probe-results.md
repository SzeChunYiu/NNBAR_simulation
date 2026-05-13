# Lane: cosmic-proton-bin5-thread-probe-results

## Goal

Inspect the completed/active status and outputs of the guarded proton-bin5
thread/seed diagnostic array `3047491`, then update coordination docs with the
evidence needed before any production proton-bin5 recovery is considered.

## Writable scope

- `docs/parallel-sessions/MASTER_PLAN.md`
- `docs/parallel-sessions/cosmic-slurm-array.md`
- This lane spec, only for clarifying handoff notes if needed.
- Your own queue file only when the supervisor pops/claims this task.

## Forbidden scope

- Do **not** submit SLURM jobs.
- Do **not** run `cosmic_proton_bin5_recovery.sbatch` or any production recovery
  script.
- Do **not** remove, overwrite, merge, or rewrite any existing proton-bin5
  outputs.
- Do **not** edit production C++/Python code or nested `NNBAR_Detector` files.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/parallel-sessions/cosmic-slurm-array.md`
4. `docs/parallel-sessions/cosmic-proton-bin5-recovery-design.md`
5. `docs/parallel-sessions/cosmic-proton-bin5-thread-probe.md`
6. `docs/parallel-sessions/cosmic-proton-bin5-thread-probe-run.md`

## One compact iteration

1. Claim this row in `MASTER_PLAN.md` (`NEXT` → `RUNNING`) and commit only the
   claim/queue paths you touched.
2. Establish the LUNARC control socket before any remote command:
   ```bash
   rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
   ```
3. From the LUNARC checkout, gather scheduler state for `3047491`:
   ```bash
   rtk proxy ssh lunarc "squeue -j 3047491 --array -o '%i|%T|%M|%R' || true"
   rtk proxy ssh lunarc "sacct -X -j 3047491 --format=JobID%-18,JobName%36,State%14,Elapsed,ExitCode,NodeList%20 -P"
   ```
4. If any `3047491_*` tasks are still active, record the active/pending state in
   `cosmic-slurm-array.md`, keep this task `RUNNING` or mark it `BLOCKED` with
   the exact reason, and stop without waiting.
5. If the array has exited, inventory outputs and logs without modifying them:
   ```bash
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && /projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/bin/python - <<'PY'
from pathlib import Path
import pyarrow.parquet as pq
base = Path('build_lunarc/output/cosmic_proton_bin5')
for p in sorted(base.glob('thread_probe_*/Particle_output_0.parquet')):
    size = p.stat().st_size
    rows = 'stub' if size <= 4 else pq.ParquetFile(p).metadata.num_rows
    print(f'{p}|{size}|{rows}')
PY"
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && find build_lunarc/output/cosmic_proton_bin5 -maxdepth 2 -path '*thread_probe_*' -type f -name 'Particle_output_0.parquet' -ls | sort"
   ```
6. Interpret only the diagnostic evidence:
   - For each failed seed/cap path from `3046812_1`, `_2`, `_5`, and `_6`, state
     whether `THREADS=1` and `THREADS=4` both completed, both failed/timed out,
     or diverged.
   - State whether the evidence points to a thread-count problem, seed/cap path
     problem, timeout/finalization problem, or remains inconclusive.
   - Keep production recovery `BLOCKED` unless the evidence is sufficient to
     write a separate future recovery design. Do not design or submit recovery in
     this task.
7. Update `docs/parallel-sessions/cosmic-slurm-array.md` with a dated handoff
   containing exact `sacct` states, row counts/sizes, and the diagnostic
   interpretation.
8. Update `docs/parallel-sessions/MASTER_PLAN.md`:
   - Mark this task `DONE` if the array has exited and evidence is recorded.
   - Keep `Cosmic proton bin5 sharded recovery` `BLOCKED` unless a future design
     is explicitly queued.
9. Verify:
   ```bash
   rtk wc -l docs/parallel-sessions/cosmic-proton-bin5-thread-probe-results.md docs/parallel-sessions/cosmic-slurm-array.md docs/parallel-sessions/MASTER_PLAN.md
   rtk proxy bash scripts/validate-csup-queues.sh
   ```
10. Commit only the files you changed and stop.

## Handoff format

Report:

```text
THREAD_PROBE_RESULTS: job 3047491 [completed|active|blocked]
sacct states: ...
row counts: ...
diagnostic interpretation: ...
production recovery status: still BLOCKED / future design needed
verification: ...
```
