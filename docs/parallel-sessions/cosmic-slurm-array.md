# Lane: cosmic-slurm-array

## Goal

Write and submit a SLURM array of 26 cosmic simulation jobs (5 particle types × 6 energy
bins, minus 4 zero-N combinations). Each job runs 1M events with CRY-generated
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
- `/Volumes/MyDrive/nnbar/nnbar/simulation/NNBAR_Detector/NNBAR_Detector_sim/slurm/run_signal.slurm` — template for run script

## Job matrix (26 jobs — skip N_{i,j}=0)

```
particles = [mu-, gamma, e-, neutron, proton]  (indices 0-4)
ebins     = [0-0.5, 0.5-1, 1-5, 5-10, 10-50, >50 GeV]  (indices 0-5)
skip: (gamma, bin4), (gamma, bin5), (e-, bin4), (e-, bin5)
```

## Files to produce (write locally then rsync to LUNARC)

### 1. `NNBAR_Detector/slurm/run_cosmic_array.slurm`

SLURM array script. Key parameters:
```bash
#SBATCH --array=0-25              # 26 jobs (renumbered after skipping zeros)
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
JOBS=(
  "0 0" "0 1" "0 2" "0 3" "0 4" "0 5"   # mu-: all 6 bins
  "1 0" "1 1" "1 2" "1 3"                 # gamma: bins 0-3 only
  "2 0" "2 1" "2 2" "2 3"                 # e-: bins 0-3 only
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

Stop when array job is submitted and queued (confirmed with squeue).
Write "DONE: cosmic array JOBID submitted, 26 jobs queued" then re-read MASTER_PLAN.md.
