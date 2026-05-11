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

Current handoff (2026-05-11 10:26 CEST): the 27-bin matrix patch was
committed in nested `NNBAR_Detector` on `main` and `lane/cosmic-slurm-array`
as `a344a47` (`fix(slurm): cover gamma cosmic bin 4`). The missing gamma
bin4 recovery was already submitted as job `3040275_10`. Do **not** submit a
duplicate unless `sacct` proves that job failed or was cancelled. Remaining
running blockers at this check: `3040180_24`, `3040180_25`, `3040259_4`,
`3040259_5`, `3040259_8`, `3040259_9`, and `3040275_10`. Completed retry
or formerly-blocking tasks at this check: `3040180_13`, `3040259_0`,
`3040259_1`, `3040259_2`, `3040259_3`, `3040259_6`, `3040259_7`,
`3040259_10`, and `3040259_11`.

Progress notes from log headers/tails at this check: `squeue -j
3040180,3040259,3040275 --array` and `sacct` show the same seven remaining
RUNNING blockers. Latest log event maxima from `tail -5000` are:
`3040180_24` proton bin4 (~786k events), `3040180_25` proton bin5 (~2.6k;
slow), `3040259_4` mu- bin4 (~367k), `3040259_5` mu- bin5 (~3.3k; slow),
`3040259_8` gamma bin2 (~742k), `3040259_9` gamma bin3 (~301k), and
`3040275_10` gamma bin4 (~63k). `3040275_10` is the only gamma bin4
recovery and must not be
resubmitted while RUNNING. `3040180_25` and `3040259_5` remain the known slow
high-energy jobs; wait for completion, failure, or cancellation before taking
recovery action.

Stop when the 27-bin nonzero matrix is covered and accounted for:
1. Monitor `3040180`, `3040259`, and `3040275` with `squeue`/`sacct`.
2. Do not resubmit gamma bin4 or recommit the 27-bin matrix unless `sacct`/git
   proves the documented job/commit is absent.
3. Mark `MASTER_PLAN.md` `DONE` only after every submitted task is complete, or
   leave it `RUNNING` with concrete remaining job IDs/blockers.

Write "DONE: cosmic array/recovery JOBID(s) submitted, 27 nonzero bins covered"
only if every submitted task is complete or explicitly handed off; otherwise
leave `MASTER_PLAN.md` `RUNNING` with the remaining job IDs.
