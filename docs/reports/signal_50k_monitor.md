# Signal 50k production monitor — job 3047773

Timestamp: 2026-05-12 13:19 CEST.

## Scheduler evidence

Guarded LUNARC checks found the already-submitted signal job completed
successfully; no new SLURM job was submitted.

- `squeue -j 3047773`: no active entry for the signal job after completion.
- `sacct -X -j 3047773`: `State=COMPLETED`, `ExitCode=0:0`, `Elapsed=01:08:16`, `Start=2026-05-12T11:44:56`, `End=2026-05-12T12:53:12`, `NodeList=cn135`.
- `slurm/signal-50k-3047773.out`: 56 MB at completion and ended with `ParquetOutputManager: Finalization complete`, `Run completed. Next run number: 1`, and the final `sig_foil_v3` Parquet listing.
- `slurm/signal-50k-3047773.err`: 219 bytes; tail only showed detector-position file loading messages.

## Remote output row counts

Remote `build_lunarc/output/sig_foil_v3/` contained non-stub Parquet outputs:

| File | Rows | Bytes |
| --- | ---: | ---: |
| `Beampipe_output_0.parquet` | 12,618,093 | 891,350,007 |
| `Carbon_output_0.parquet` | 72,736 | 6,093,161 |
| `GPUEnergy_output_0.parquet` | 0 | 663 |
| `Interaction_output_0.parquet` | 12,473,917 | 784,292,705 |
| `LeadGlass_output_0.parquet` | 576,154,866 | 10,780,512,562 |
| `PMT_output_0.parquet` | 0 | 1,146 |
| `Particle_output_0.parquet` | 402,468 | 13,180,671 |
| `Scintillator_output_0.parquet` | 95,070,163 | 7,236,028,724 |
| `Silicon_output_0.parquet` | 12,288,690 | 900,630,605 |
| `TPC_output_0.parquet` | 28,017,556 | 2,303,262,152 |

`Particle_output_0.parquet` has 402,468 rows, which is above the monitor gate of
40,000 rows.

## Local copy verification

The completed remote `sig_foil_v3` directory was copied to local
`build_lunarc/output/sig_foil_v3/`. The transfer needed resumable `rsync
--partial --append` retries after SSH EOF interruptions; the LUNARC socket was
reinitialized once, and no SLURM job was submitted. Final local byte sizes match
the remote byte sizes for all ten Parquet files, AppleDouble sidecars were
removed, and local PyArrow metadata reads reproduced the row counts above.

## Verification

- `rtk proxy bash scripts/validate-csup-queues.sh`: scanned 27 files / 36 prompt lines with 0 failures.
- Local PyArrow metadata check reproduced all ten row counts above and printed `SIGNAL_50K_LOCAL_PARQUET_OK`.

## Disposition

Mark the MASTER_PLAN signal 50k production monitor row `DONE`. The completed
remote and local outputs are available under `build_lunarc/output/sig_foil_v3/`
for downstream signal kinematics, cutflow, and thesis-ledger closure work.
