# Lane: cosmic-slurm-array

## Goal

Write and submit a SLURM array covering all 27 nonzero cosmic simulation bins
(5 particle types × 6 energy bins, minus 3 zero-N combinations). Each job runs 1M events with CRY-generated
positions/directions and uniform energy within the bin. Weight is stored in Parquet.

## Prerequisite

The NNBAR detector binary MUST already be rebuilt with `-DWITH_CRY=ON` (lane cry-integration).
Check before proceeding:
```bash
ssh lunarc "ls /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc/nnbar-detector-simulation && \
  /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc/nnbar-detector-simulation --version 2>&1 | head -2"
```
If binary doesn't have CRY support, write "BLOCKED: waiting for cry-integration binary" and stop.

## Read first

- `docs/parallel-sessions/MASTER_PLAN.md`
- `docs/parallel-sessions/cry-integration.md` — the weight formula and N_{i,j} table
- `NNBAR_Detector/slurm/run_cosmic_array.slurm` — current submitted
  array script; local file existence verified on 2026-05-11

## Job matrix (27 jobs — skip only N_{i,j}=0)

```
particles = [mu-, gamma, e-, neutron, proton]  (indices 0-4)
ebins     = [0-0.5, 0.5-1, 1-5, 5-10, 10-50, >50 GeV]  (indices 0-5)
skip: (e-, bin4), (gamma, bin5), (e-, bin5)
```

## Files to produce (write locally then rsync to LUNARC)

### 1. `NNBAR_Detector/slurm/run_cosmic_array.slurm`

SLURM array script. Key parameters:
```bash
#SBATCH --array=0-26              # 27 jobs (renumbered after skipping zeros)
#SBATCH --job-name=nnbar-cosmic
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --output=.../slurm/cosmic-%A_%a.out
```

Map SLURM_ARRAY_TASK_ID → (particle_idx, ebin_idx) at the top:
```bash
# Ordered list of (particle_idx ebin_idx) pairs, skipping zero-N combinations
# per the Table 6.1 N_{i,j} matrix in cry-integration.md.
JOBS=(
  "0 0" "0 1" "0 2" "0 3" "0 4" "0 5"   # mu-: all 6 bins
  "1 0" "1 1" "1 2" "1 3" "1 4"         # gamma: bins 0-4; bin5 is zero
  "2 0" "2 1" "2 2" "2 3"                 # e-: bins 0-3; bins4-5 are zero
  "3 0" "3 1" "3 2" "3 3" "3 4" "3 5"   # neutron: all 6 bins
  "4 0" "4 1" "4 2" "4 3" "4 4" "4 5"   # proton: all 6 bins
)
PARTICLE_IDX=$(echo ${JOBS[$SLURM_ARRAY_TASK_ID]} | awk '{print $1}')
EBIN_IDX=$(echo ${JOBS[$SLURM_ARRAY_TASK_ID]} | awk '{print $2}')
PARTICLES=(mu- gamma e- neutron proton)
PARTICLE=${PARTICLES[$PARTICLE_IDX]}
EMIN_LIST=(0 0.5 1 5 10 50)
EMAX_LIST=(0.5 1 5 10 50 200)
EMIN=${EMIN_LIST[$EBIN_IDX]}
EMAX=${EMAX_LIST[$EBIN_IDX]}
```

Output dir per job: `output/cosmic_${PARTICLE}_bin${EBIN_IDX}/`

Macro generated in-job (same pattern as run_signal.slurm):
```
/run/initialize
/tracking/verbose 0
/cosmic/mode true
/cosmic/particle ${PARTICLE}
/cosmic/energyMin ${EMIN} GeV
/cosmic/energyMax ${EMAX} GeV
/cosmic/energyBin ${EBIN_IDX}
/cosmic/particleIdx ${PARTICLE_IDX}
/cosmic/dataPath /projects/hep/fs10/shared/nnbar/billy/packages/cry_v1.7/data
/run/beamOn 1000000
```

### 2. `NNBAR_Detector/slurm/submit_cosmic_array.sh`

Simple wrapper:
```bash
#!/bin/bash
cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim
sbatch slurm/run_cosmic_array.slurm
squeue -u scyiu -o '%.10i %.18j %.8T %.10M'
```

## Iteration cycle

1. Write the two files above
2. Rsync to LUNARC:
   ```bash
   rsync -av NNBAR_Detector/slurm/run_cosmic_array.slurm \
     NNBAR_Detector/slurm/submit_cosmic_array.sh \
     lunarc:/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/
   ```
3. Submit: `ssh lunarc "bash /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/submit_cosmic_array.sh"`
4. Verify jobs are queued: `ssh lunarc "squeue -u scyiu -o '%.10i %.18j %.8T %.10M'"`
5. Commit slurm scripts on branch `lane/cosmic-slurm-array`, merge to main

## Stop condition

Current handoff (2026-05-11 11:49 CEST): the 27-bin matrix patch was
committed in nested `NNBAR_Detector` on `main` and `lane/cosmic-slurm-array`
as `a344a47` (`fix(slurm): cover gamma cosmic bin 4`). The missing gamma
bin4 recovery was already submitted as job `3040275_10`. Do **not** submit a
duplicate unless `sacct` proves that job failed or was cancelled. Remaining
running blockers at this check: `3040180_24`, `3040180_25`, `3040259_4`,
`3040259_5`, `3040259_9`, and `3040275_10`. Completed retry
or formerly-blocking tasks remain: `3040180_13`, `3040259_0`,
`3040259_1`, `3040259_2`, `3040259_3`, `3040259_6`, `3040259_7`,
`3040259_8`, `3040259_10`, and `3040259_11`.

Progress notes from this check: `squeue -j 3040180,3040259,3040275 --array`
and `sacct -X -j 3040180,3040259,3040275` still show six RUNNING jobs, with
`3040180_24`/`3040180_25` at 09:35:26, `3040259_4`/`3040259_5`/`3040259_9`
at 03:17:51, and `3040275_10` at 03:06:30 elapsed. Fresh log tails reached
`3040180_24` proton bin4 (~914k events), `3040259_4` mu- bin4 (~629k),
`3040259_9` gamma bin3 (~514k), and `3040275_10` gamma bin4 (~111k). The
high-energy jobs `3040180_25` proton bin5 and `3040259_5` mu- bin5 remained
RUNNING with 12-hour limits, but their stdout files were stale/slow
(`cosmic-3040180_25.out` mtime 02:20 CEST with visible summaries only around
1.3k events; `cosmic-3040259_5.out` mtime 08:34 CEST with visible summaries
only around 1.3k events).
`3040275_10` is the only gamma bin4 recovery and must not be resubmitted
while RUNNING. `3040180_25` and `3040259_5` remain the known slow high-energy
jobs; wait for completion, failure, or cancellation before taking recovery
action.

Stop when the 27-bin nonzero matrix is covered and accounted for:
1. Monitor `3040180`, `3040259`, and `3040275` with `squeue`/`sacct`.
2. Do not resubmit gamma bin4 or recommit the 27-bin matrix unless `sacct`/git
   proves the documented job/commit is absent.
3. Mark `MASTER_PLAN.md` `DONE` only after every submitted task is complete, or
   leave it `RUNNING` with concrete remaining job IDs/blockers.

Write "DONE: cosmic array/recovery JOBID(s) submitted, 27 nonzero bins covered"
only if every submitted task is complete or explicitly handed off; otherwise
leave `MASTER_PLAN.md` `RUNNING` with the remaining job IDs.

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

