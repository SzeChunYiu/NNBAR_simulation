# Cosmic SLURM array — proton-bin5 recovery and thread-probe chronology

This companion document was split from
`docs/parallel-sessions/cosmic-slurm-array.md` to keep the umbrella lane doc
inside the repository file-size policy. It preserves the detailed 2026-05-12
proton-bin5 recovery, diagnostic, and thread-probe handoff history. The active
authorization rule remains: do not submit production proton-bin5 recovery until
the final `3047491` thread-probe `sacct`, logs, and Parquet row counts have been
inspected and interpreted.

### Current handoff (2026-05-12 06:16 CEST)

Guarded LUNARC refresh (`ssh -O check`, `squeue`, `sacct -X`, log tails, and
stub stat) found no active original 3040180/3040259/3040275 tasks. The updated
state is:

- Completed since the prior handoff: `3040259_9` gamma bin3.
- Timed out since the prior handoff: `3040259_5` mu- bin5 and `3040275_10`
  gamma bin4; `3040180_25` proton bin5 remains the original 12 h timeout.
- Proton bin5 root output is still a 4-byte invalid Parquet stub at
  `build_lunarc/output/cosmic_proton_bin5/Particle_output_0.parquet`.
- A first four-shard proton-bin5 recovery, `3041797_0-3`, already ran and all
  four shards timed out at 06:00:29.
- A second guarded diagnostic/recovery array, `3046812`, is already active:
  `_0` completed, `_1` and `_2` were running, and `_3`--`_6` were pending at
  this check.
- Worker-0 accidentally submitted a duplicate four-shard array, `3047155`,
  after `sbatch --test-only` passed but before noticing `3046812`; it was
  immediately canceled (`3047155_0-3` show `CANCELLED by 6350` after 9 s).

Stop/next-action rule: do **not** submit another proton-bin5 recovery while
`3046812` is active. The next compact iteration should inspect the 3046812
logs/outputs when it exits, then decide whether proton bin5 needs another
explicitly authorized recovery design. Separate follow-up specs are also needed
for the timed-out mu- bin5 (`3040259_5`) and gamma bin4 (`3040275_10`) bins.

### Current handoff (2026-05-12 06:38 CEST)

Guarded LUNARC refresh (`ssh -O check` via RTK) found proton-bin5 recovery
array `3046812` still active, so no new proton-bin5 submission is authorized:

- `squeue -j 3046812 --array`: `3046812_1` running for 05:30:51 and
  `3046812_2` running for 05:30:18 on `cn064`; `3046812_3`--`_6` pending on
  `JobArrayTaskLimit`.
- `sacct -X -j 3046812`: `_0` completed with exit `0:0`, `_1`/`_2` running,
  and `_3`--`_6` pending.
- Root proton-bin5 Parquet files remain 4-byte stubs, including
  `build_lunarc/output/cosmic_proton_bin5/Particle_output_0.parquet`.
- Diagnostic output exists for `second_diagnostic_cap100_rep0` (for example
  `Particle_output_0.parquet` is 12025 bytes), while `second_diagnostic_cap100_rep1`,
  `second_diagnostic_cap250_rep0`, and first recovery `shard0`--`shard3` files
  are still 4-byte stubs at this check.
- Log tails show very slow progress immediately before the 6 h limit:
  `3046812_1` reached event 96 and `3046812_2` reached event 243; stderr tails
  only show lead-glass position-file loading.

Stop/next-action rule remains: do **not** submit another proton-bin5 recovery
while `3046812` is active. Inspect `3046812` logs/outputs after it exits, then
write an explicitly authorized next recovery design if needed. Separate mu- bin5
and gamma bin4 recovery specs are still needed for `3040259_5` and `3040275_10`.

### Current handoff (2026-05-12 06:57 CEST)

Guarded LUNARC refresh (`rtk proxy bash -lc "ssh -O check lunarc ..."`) found
proton-bin5 diagnostic/recovery array `3046812` still active, so no new
proton-bin5 submission is authorized:

- `squeue -j 3046812`: `_1` running for 05:50:28 and `_2` running for
  05:49:55 on `cn064`; `_3`--`_6` remain pending on `JobArrayTaskLimit`.
- `sacct -X -j 3046812`: `_0` completed with exit `0:0`, `_1`/`_2` running,
  and `_3`--`_6` pending.
- Root proton-bin5 Parquet files remain 4-byte stubs; the only non-stub
  diagnostic output observed is
  `second_diagnostic_cap100_rep0/Particle_output_0.parquet` at 12025 bytes.
- Log tails still show very slow progress near the 6 h limit:
  `3046812_1` at event 96 and `3046812_2` at event 243, with stderr tails
  only showing lead-glass position-file loading.

Stop/next-action rule remains: do **not** submit another proton-bin5 recovery
while `3046812` is active. Inspect `3046812` logs/outputs after the full array
exits, then design any next recovery explicitly; separate mu- bin5 and gamma
bin4 recovery specs are still needed for `3040259_5` and `3040275_10`.

### Current handoff (2026-05-12 07:12 CEST)

Guarded LUNARC refresh (`rtk proxy bash -lc "ssh -O check lunarc ..."`, then
`squeue -j 3046812 --array` and `sacct -X -j 3046812`) found proton-bin5
diagnostic/recovery array `3046812` still active, so no new proton-bin5
submission is authorized:

- `3046812_0`, `_3`, and `_4` completed with exit `0:0`.
- `3046812_1` and `_2` timed out at `06:00:16` and `06:00:13` on `cn064`.
- `3046812_5` and `_6` were running on `cn018` for `00:04:29` and `00:03:25`
  at this check.
- Root `build_lunarc/output/cosmic_proton_bin5/Particle_output_0.parquet`
  remains a 4-byte invalid stub.
- Diagnostic outputs now include non-stub files for `second_diagnostic_cap100_rep0`
  (12025 bytes), `second_diagnostic_cap250_rep1` (23758 bytes), and
  `second_diagnostic_cap500_rep0` (43563 bytes); the first recovery
  `shard0`--`shard3` outputs and several other diagnostic reps remain 4-byte
  stubs.
- Log tails show `_1` stopped at event 96 and `_2` stopped at event 243 before
  the time limit, while `_5` reached event 491 and `_6` reached event 685 as
  they started their runs.

Stop/next-action rule remains: do **not** submit another proton-bin5 recovery
while `3046812` is active. Inspect `3046812` logs/outputs after the full array
exits, then design any next recovery explicitly; separate mu- bin5 and gamma
bin4 recovery specs are still needed for `3040259_5` and `3040275_10`.

### Current handoff (2026-05-12 07:32 CEST)

Guarded LUNARC refresh (`rtk proxy bash -lc "ssh -O check lunarc ..."`, then
`squeue -j 3046812 --array`, `sacct -X -j 3046812`, root stub stat, and output
inventory) found proton-bin5 diagnostic/recovery array `3046812` still active,
so no new proton-bin5 submission is authorized:

- `3046812_0`, `_3`, and `_4` completed with exit `0:0`.
- `3046812_1` and `_2` timed out at `06:00:16` and `06:00:13`.
- `3046812_5` and `_6` were running on `cn018` for `00:24:09` and `00:23:05`
  at this check.
- Root `build_lunarc/output/cosmic_proton_bin5/Particle_output_0.parquet`
  remains a 4-byte invalid stub.
- Diagnostic non-stub outputs remain limited to `second_diagnostic_cap100_rep0`
  (12025 bytes), `second_diagnostic_cap250_rep1` (23758 bytes), and
  `second_diagnostic_cap500_rep0` (43563 bytes). The root file, first recovery
  `shard0`--`shard3`, `second_diagnostic_cap100_rep1`,
  `second_diagnostic_cap250_rep0`, `second_diagnostic_cap500_rep1`, and
  `second_diagnostic_cap1000_rep0` are still 4-byte stubs.
- `3040180_25` proton bin5, `3040259_5` mu- bin5, and `3040275_10` gamma bin4
  remain `TIMEOUT`; canceled duplicate `3047155_0-3` remains canceled.

Stop/next-action rule remains: do **not** submit another proton-bin5 recovery
while `3046812` is active. Inspect `3046812` logs/outputs after the full array
exits, then design any next recovery explicitly; separate mu- bin5 and gamma
bin4 recovery specs are still needed for `3040259_5` and `3040275_10`.

### Current handoff (2026-05-12 07:56 CEST)

Guarded LUNARC refresh (`rtk proxy bash -lc "ssh -O check lunarc ..."`, then
`squeue`, `sacct -X`, output inventory, and log tails) found proton-bin5
second diagnostic/recovery array `3046812` still active. No new proton-bin5
submission is authorized:

- `3046812_0`, `_3`, and `_4` completed with exit `0:0`; `3046812_1` and
  `_2` timed out at `06:00:16` and `06:00:13`.
- `3046812_5` and `_6` remain running on `cn018` for `00:47:57` and
  `00:46:53` at this check.
- Root `build_lunarc/output/cosmic_proton_bin5/Particle_output_0.parquet`
  remains a 4-byte invalid stub.
- Diagnostic non-stub outputs remain limited to `second_diagnostic_cap100_rep0`
  (12025 bytes), `second_diagnostic_cap250_rep1` (23758 bytes), and
  `second_diagnostic_cap500_rep0` (43563 bytes). `second_diagnostic_cap500_rep1`
  and `second_diagnostic_cap1000_rep0` remain 4-byte stubs.
- Running stdout tails remained at event 491 for `_5` and event 962 for `_6`;
  stderr tails show only lead-glass position-file loading.

Stop/next-action rule remains: do **not** submit another proton-bin5 recovery
while `3046812` is active. Inspect `3046812` logs/outputs after the full array
exits, then design any next recovery explicitly; separate mu- bin5 and gamma
bin4 recovery specs are still needed for `3040259_5` and `3040275_10`.

### Current handoff (2026-05-12 08:12 CEST)

Guarded LUNARC refresh (`rtk proxy bash -lc "ssh -O check lunarc ..."`, then
`squeue -j 3046812 --array`, `sacct -X`, output inventory, and log tails)
found proton-bin5 diagnostic/recovery array `3046812` has fully exited; no
active duplicate proton-bin5 job remains in `squeue`:

- `3046812_0`, `_3`, and `_4` completed with exit `0:0`; `_1` and `_2` timed
  out at `06:00:16` and `06:00:13`; `_5` and `_6` failed with exit `0:15`
  after `00:55:44` and `00:54:40`.
- Root `build_lunarc/output/cosmic_proton_bin5/Particle_output_0.parquet`
  remains a 4-byte invalid stub.
- Diagnostic non-stub outputs are still limited to `second_diagnostic_cap100_rep0`
  (12025 bytes), `second_diagnostic_cap250_rep1` (23758 bytes), and
  `second_diagnostic_cap500_rep0` (43563 bytes); the first recovery shard files
  and cap100 rep1 / cap250 rep0 / cap500 rep1 / cap1000 rep0 remain 4-byte stubs.
- Stdout tails still stop at events 96 (`_1`), 243 (`_2`), 491 (`_5`), and
  962 (`_6`); stderr adds only the `_1`/`_2` time-limit cancellations and no
  new fatal message for `_5`/`_6` beyond Geant4/SLURM failure status.

Stop/next-action rule: do not submit a new proton-bin5 job from the old
recovery scripts. The next proton-bin5 iteration must write a fresh,
explicitly authorized recovery design that accounts for the cap/seed-dependent
stall/failure pattern above before any `sbatch` submission.

### Current handoff (2026-05-12 08:17 CEST)

Worker-0 completed the required fresh proton-bin5 recovery design in
`docs/parallel-sessions/cosmic-proton-bin5-recovery-design.md`; no SLURM job was
submitted. Guarded LUNARC evidence still shows `3046812` fully exited and absent
from `squeue`; valid diagnostic Parquet exists only for cap100 rep0 (100 rows),
cap250 rep1 (250 rows), and cap500 rep0 (500 rows). The root proton-bin5 output,
first recovery shards, and failed diagnostic outputs remain 4-byte stubs.

Stop/next-action rule: proton-bin5 production recovery is now BLOCKED until a
future explicitly queued thread/seed probe compares the failed seed paths at
`THREADS=1` and `THREADS=4` with a no-submit-by-default guard. Do not run
`cosmic_proton_bin5_recovery.sbatch` or any old proton-bin5 recovery script.


### Current handoff (2026-05-12 08:34 CEST)

Worker-0 prepared the future proton-bin5 thread/seed probe wrapper without
submitting a diagnostic job. The guarded script is committed in the nested
`NNBAR_Detector` repo as `b9a7989` and staged on LUNARC at
`slurm/cosmic_proton_bin5_thread_probe.sbatch`. It replays the failed
`3046812_1`, `_2`, `_5`, and `_6` seed/cap paths at `THREADS=1` and
`THREADS=4`, writes only to `output/cosmic_proton_bin5/thread_probe_*`, and
exits with code 2 unless `PROTON_BIN5_THREAD_PROBE_APPROVED=YES` is set.

Verification was syntax/guard/test-only only: local and remote `bash -n`
passed, the guard test exited 2, static seed/thread checks passed, and
`sbatch --test-only --array=0-7 slurm/cosmic_proton_bin5_thread_probe.sbatch`
returned pseudo-job `3047483`; `squeue`/`sacct` for `3047483` found no real job.
Do not run the probe until a later approved lane explicitly sets the guard.

### Current handoff (2026-05-12 08:40 CEST)

Worker-0 submitted the explicitly authorized proton-bin5 thread/seed diagnostic
array once, as SLURM job `3047491`. This is not a production recovery: it runs
only the guarded wrapper `slurm/cosmic_proton_bin5_thread_probe.sbatch` with
`PROTON_BIN5_THREAD_PROBE_APPROVED=YES`, comparing the failed `3046812_1`,
`3046812_2`, `3046812_5`, and `3046812_6` seed/cap paths at `THREADS=1` and
`THREADS=4`.

Pre-submit safety evidence:

- Remote wrapper exists in `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim`
  and `bash -n slurm/cosmic_proton_bin5_thread_probe.sbatch` passed.
- Guard/invariant greps confirmed `PROTON_BIN5_THREAD_PROBE_APPROVED:-NO`,
  `#SBATCH --array=0-7%2`, and `thread_probe_${TASK_ID}` output naming.
- The wrapper contains a no-overwrite check that exits if the target
  `thread_probe_${TASK_ID}` directory already contains files.
- No active `pbin5-thread-probe` job and no existing
  `build_lunarc/output/cosmic_proton_bin5/thread_probe_*` directories were
  present before submission.
- `sbatch --test-only slurm/cosmic_proton_bin5_thread_probe.sbatch` returned
  pseudo-job `3047490` and did not submit work.

Submission evidence:

- Command used:
  `sbatch --parsable --export=ALL,PROTON_BIN5_THREAD_PROBE_APPROVED=YES slurm/cosmic_proton_bin5_thread_probe.sbatch`
- Returned job id: `3047491`.
- Immediate `squeue -j 3047491 --array` showed `3047491_0` and `3047491_1`
  RUNNING on `cn018` at `0:01`; `3047491_2`--`3047491_7` were PENDING on
  `JobArrayTaskLimit`.
- Immediate `sacct -X -j 3047491` returned only the header, as expected just
  after submission.

Follow-up commands for the next compact unit after the array exits:

```bash
rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
rtk proxy ssh lunarc "sacct -X -j 3047491 --format=JobID%-18,JobName%36,State%14,Elapsed,ExitCode -P"
rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && /projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/bin/python - <<'PY'
from pathlib import Path
import pyarrow.parquet as pq
base = Path('build_lunarc/output/cosmic_proton_bin5')
for p in sorted(base.glob('thread_probe_*/Particle_output_0.parquet')):
    size = p.stat().st_size
    rows = 'stub' if size <= 4 else pq.ParquetFile(p).metadata.num_rows
    print(p, size, rows)
PY"
```

Stop/next-action rule: do not submit any production proton-bin5 recovery until
a later lane inspects `3047491` `sacct`, logs, and row counts and explains the
thread/seed behavior.

### Current handoff (2026-05-12 08:50 CEST)

Guarded LUNARC refresh found the proton-bin5 thread/seed diagnostic array
`3047491` is still active, so no production proton-bin5 recovery is authorized
and no SLURM job was submitted in this status-refresh iteration:

- `squeue -j 3047491 --array` reported `3047491_4` and `_5` RUNNING on
  `cn135` at about `0:12`, with `_6` and `_7` PENDING on `JobArrayTaskLimit`.
- `sacct -X -j 3047491` reported `_0` COMPLETED (`0:0`), `_1` FAILED
  (`0:9` after `00:09:28`), `_2` COMPLETED (`0:0`), `_3` FAILED (`0:9`
  after `00:06:02`), `_4`/`_5` RUNNING, and `_6`/`_7` PENDING.
- The Celeritas competitor job `3047497` is unrelated and remained PENDING on
  `Resources`; holder jobs `3041294` and `3041795` remained RUNNING.

Stop/next-action rule: do not submit any production proton-bin5 recovery while
`3047491` has active or pending tasks. A later result-inspection lane must wait
until the array exits, then inspect final `sacct`, logs, and `thread_probe_*`
row counts before designing any production recovery.

### Result-inspection active refresh (2026-05-12 09:13 CEST)

Worker-0 refreshed `3047491`; it had not exited, so result inspection remains
`RUNNING`. `squeue` showed `_4` and `_5` RUNNING on `cn135` at `23:43`, with `_6`
and `_7` PENDING on `JobArrayTaskLimit`. `sacct -X` showed `_0` COMPLETED
(`00:01:01`, exit `0:0`), `_1` FAILED (`00:09:28`, exit `0:9`), `_2` COMPLETED
(`00:02:23`, exit `0:0`), `_3` FAILED (`00:06:02`, exit `0:9`), `_4`/`_5`
RUNNING, and `_6`/`_7` PENDING. Partial row counts remain `thread_probe_0`
12025 bytes / 100 rows and `thread_probe_2` 23758 bytes / 250 rows;
`thread_probe_1`, `_3`, `_4`, and `_5` are 4-byte stubs, and `_6`/`_7` are not
present yet. Log tails remain `_4` at event 238 and `_5` at event 491; no
production recovery was submitted or output mutated.

Stop/next-action rule: wait for `_4`--`_7` to leave the queue, then inspect final
`sacct`, logs, and `thread_probe_*` Parquet row counts before any recovery design.

### Result-inspection active refresh (2026-05-12 09:20 CEST)

Worker-0 refreshed the explicitly authorized proton-bin5 thread/seed diagnostic
array `3047491`; it is still active, so final result interpretation and any
production recovery design remain blocked. No production SLURM job was submitted
and no existing proton-bin5 output was removed, overwritten, merged, or mutated.

- `squeue -j 3047491 --array` showed `_4` and `_5` RUNNING on `cn135` at
  `30:53` elapsed, with `_6` and `_7` PENDING on `JobArrayTaskLimit`.
- `sacct -X -j 3047491` showed `_0` COMPLETED (`00:01:01`, exit `0:0`),
  `_1` FAILED (`00:09:28`, exit `0:9`), `_2` COMPLETED (`00:02:23`, exit
  `0:0`), `_3` FAILED (`00:06:02`, exit `0:9`), `_4`/`_5` RUNNING
  (`00:30:54`), and `_6`/`_7` PENDING.
- Current row-count inventory is `thread_probe_0` 12025 bytes / 100 rows,
  `thread_probe_2` 23758 bytes / 250 rows, and `thread_probe_1`, `_3`, `_4`,
  `_5` as 4-byte stubs; `thread_probe_6` and `_7` are not present yet.
- Active log tails still stop at event 238 for `_4` (`THREADS=1`, cap 500,
  replaying `3046812_5`) and event 491 for `_5` (`THREADS=4`, cap 500,
  replaying `3046812_5`).

Stop/next-action rule: keep result inspection `RUNNING`; wait for `_4`--`_7`
to leave the queue, then inspect final `sacct`, logs, and `thread_probe_*`
Parquet row counts before drawing the THREADS=1 versus THREADS=4 conclusion.
Production proton-bin5 recovery remains blocked.
