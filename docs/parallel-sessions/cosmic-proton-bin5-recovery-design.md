# Cosmic Proton Bin5 Recovery Design — 2026-05-12

> **For Codex:** REQUIRED SUB-SKILL: use `systematic-debugging` before changing
> scripts or submitting any additional proton-bin5 job. This document is a
> recovery design and blocker disposition, not a submission authorization.

**Goal:** recover the CRY proton bin5 (`particleIdx=4`, `energyBin=5`,
50--200 GeV) 1,000,000-event sample without repeating the failed 250k-shard or
cap-diagnostic patterns.

**Architecture:** treat proton-bin5 as a root-cause investigation before a
production run. The next executable artifact must be a guarded, no-submit-by-
default diagnostic that isolates whether the failure is seed/event dependent,
thread dependent, or output-finalization dependent. Production sharding remains
blocked until that diagnostic explains the current failure mode.

**Tech stack:** NNBAR Geant4/CRY binary on LUNARC, SLURM `lu48`, Parquet output
via the NNBAR detector `ParquetOutputManager`, and RTK-guarded SSH commands.

---

## Current evidence

Guarded LUNARC refresh at 2026-05-12 08:17 CEST found no active proton-bin5
duplicate in `squeue`; only the supervisor holder jobs and unrelated GNN
pending jobs remained active.

| Task | cap | replicate | seeds | state | elapsed | output rows | last event / note |
| --- | ---: | ---: | --- | --- | --- | ---: | --- |
| `3046812_0` | 100 | 0 | `1106432,2132266` | `COMPLETED` | `00:00:33` | 100 | finalized |
| `3046812_1` | 100 | 1 | `1211161,2262629` | `TIMEOUT` | `06:00:16` | stub | event 96 |
| `3046812_2` | 250 | 0 | `1318440,2395842` | `TIMEOUT` | `06:00:13` | stub | event 243 |
| `3046812_3` | 250 | 1 | `1423169,2526205` | `COMPLETED` | `00:01:09` | 250 | finalized |
| `3046812_4` | 500 | 0 | `1532148,2661318` | `COMPLETED` | `00:01:43` | 500 | finalized |
| `3046812_5` | 500 | 1 | `1636877,2791681` | `FAILED` | `00:55:44` | stub | event 491 |
| `3046812_6` | 1000 | 0 | `1750106,2931544` | `FAILED` | `00:54:40` | stub | event 962 |

The root `build_lunarc/output/cosmic_proton_bin5/Particle_output_0.parquet`,
the first four 250k recovery shards, and failed diagnostic replicas remain
4-byte invalid stubs. The three successful diagnostic Parquet files contain
exactly 100, 250, and 500 rows, respectively.

## Root-cause classification

The failure is not explained by requested event count alone: cap 100, 250, and
500 each have at least one successful or partially successful seed path, while
other seed paths stall or fail before completing the same or smaller cap. The
current evidence supports a seed/event-dependent long tail, possibly amplified
by four-thread execution, rather than a missing CRY input, missing binary, or
simple walltime underestimate.

Output durability is also a blocker. The detector initializes the Parquet files
at run start, but valid files are only guaranteed after
`RunAction::EndOfRunAction` calls `ParquetOutputManager::Finalize`, which closes
the stream writers. Jobs killed by timeout or signal therefore preserve only
4-byte stubs even after hundreds of generated events.

No fresh production submission is justified until the next diagnostic answers:

1. Does the same seed pair complete with `-t 1` but fail with `-t 4`?
2. Is the failure a single pathological event, finalization, or external signal?
3. What event cap keeps the 95th percentile walltime below the requested limit?
4. Can future production shards lose at most one small shard, not 250k events?

## Recommended next compact unit

Create one guarded diagnostic script, not a production recovery script:

- File: `NNBAR_Detector/slurm/cosmic_proton_bin5_thread_probe.sbatch`
- Default behavior: exit before running unless
  `PROTON_BIN5_THREAD_PROBE_APPROVED=YES` is set in the submitted environment.
- Array layout: replay the four problematic seed/cap pairs from `3046812_1`,
  `_2`, `_5`, and `_6` with both `THREADS=1` and `THREADS=4` (8 tasks total).
- Event cap: keep each task at the original diagnostic cap for comparability;
  do not raise caps or submit production statistics.
- Walltime: request enough time to distinguish single-thread progress from the
  current 55--360 minute failures, but keep the run diagnostic-only.
- Outputs: write to new folders under
  `output/cosmic_proton_bin5/thread_probe_<task>`; never overwrite root,
  `shard*`, or `second_diagnostic_*` folders.
- Logging: print task id, cap, seeds, thread count, output folder, macro path,
  `date`, `hostname`, and a final `sacct`/output-size follow-up command.

Only after this thread probe completes should a later lane choose between:

1. a small-shard production array using the safest observed thread count and a
   row-count manifest, or
2. a C++ output/checkpoint change that prevents timeout-created 4-byte stubs, or
3. a code-level Geant4/CRY investigation if the same seed consistently hangs.

## Verification for this design iteration

Evidence commands run in this iteration:

```bash
rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo Connected || /Users/billy/lunarc-init.sh'
rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && squeue -u scyiu --format='%.18i %.30j %.8T %.10M %.12l %.20R' && sacct -X -j 3046812 --format=JobID%-15,JobName%30,State%15,Elapsed,ExitCode,MaxRSS%12 -P"
rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && /projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/bin/python - <<'PY'
from pathlib import Path
import pyarrow.parquet as pq
for p in sorted(Path('build_lunarc/output/cosmic_proton_bin5').glob('*/Particle_output_0.parquet')):
    print(p, p.stat().st_size, 'stub' if p.stat().st_size <= 4 else pq.ParquetFile(p).metadata.num_rows)
PY"
rtk proxy bash -lc "grep -n 'void ParquetOutputManager::Finalize' NNBAR_Detector/src/output/ParquetOutputManager.cc && grep -n 'void RunAction::EndOfRunAction' NNBAR_Detector/src/core/RunAction.cc"
```

Stop condition for the current proton-bin5 lane: mark proton bin5 `BLOCKED`
with this design linked. Do not run `sbatch` for proton bin5 until a future
explicitly authorized thread-probe lane exists and passes `sbatch --test-only`.
