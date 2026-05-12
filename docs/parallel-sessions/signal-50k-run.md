# Lane: signal-50k-run

## Goal

Create and submit `slurm/signal_50k.sbatch` — a SLURM job that generates 50k
signal annihilation events using the existing MCPL input file on LUNARC and
writes output to `build_lunarc/output/sig_foil_v3/`.

This unblocks: `signal_kinematics_audit.py`, `pion_multiplicity_closure.py`,
`thesis_ledger_closure.py`, event-selection survival fractions, sensitivity
calculation, and pi0 multiplicity validation.

## MCPL input file

```
/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/mcpl_files/NNBAR_rwag_signal_GBL_jbar_100k_9009.mcpl
```

100k events available; we run 50k (first half) with seed 42.

## Output location

```
build_lunarc/output/sig_foil_v3/
```

Parquet outputs written by Geant4 go to:
`${PROJ}/build_lunarc/output/sig_foil_v3/`

## SLURM script to create: `NNBAR_Detector/slurm/signal_50k.sbatch`

```bash
#!/bin/bash
#SBATCH --job-name=nnbar-sig-50k
#SBATCH --output=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/sig_50k-%j.out
#SBATCH --error=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/sig_50k-%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=6:00:00
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --exclude=cn018

set -euo pipefail

PROJ=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim
MCPL_FILE=${PROJ}/mcpl_files/NNBAR_rwag_signal_GBL_jbar_100k_9009.mcpl
OUTPUT_DIR=${PROJ}/build_lunarc/output/sig_foil_v3
BIN=${PROJ}/build_lunarc/nnbar-detector-simulation.bin

if [ ! -f "${BIN}" ]; then
    echo "ERROR: binary not found at ${BIN}" >&2
    exit 1
fi
if [ ! -f "${MCPL_FILE}" ]; then
    echo "ERROR: MCPL file not found at ${MCPL_FILE}" >&2
    exit 1
fi

HIBENV=/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env
export CONDA_PREFIX="${HIBENV}"
export PATH="${CONDA_PREFIX}/bin:${PATH}"
set +u
for f in "${CONDA_PREFIX}"/etc/conda/activate.d/*.sh; do [ -f "${f}" ] && source "${f}"; done
set -u
export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${LD_LIBRARY_PATH:-}"

mkdir -p "${OUTPUT_DIR}"

cd "${PROJ}/build_lunarc"

echo "[signal_50k] Starting: 50k MCPL signal events, 4 threads"
echo "[signal_50k] MCPL: ${MCPL_FILE}"
echo "[signal_50k] Output: ${OUTPUT_DIR}"
echo "[signal_50k] Binary: ${BIN}"

/usr/bin/time -v "${BIN}" \
    --mcpl-input "${MCPL_FILE}" \
    --output-dir "${OUTPUT_DIR}" \
    --num-events 50000 \
    --num-threads 4 \
    --seed 42 \
    2>&1

echo "[signal_50k] COMPLETED"
ls -lh "${OUTPUT_DIR}/"*.parquet 2>/dev/null || echo "No parquet files found"
```

## Key notes for codex

1. Check the binary's actual CLI flags before writing the script. Run:
   `ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNNAR_Detector_sim/build_lunarc && ./nnbar-detector-simulation.bin --help 2>&1 | head -30"`
   
   The actual flags may differ — look at `src/main.cc` for the argument parsing.
   The macro-based invocation may be: `./nnbar-detector-simulation.bin -m macro/mcpl_signal.mac`

2. Check existing MCPL macros:
   `find NNBAR_Detector/macro -name "*mcpl*" -o -name "*signal*" | grep -v build`

3. The output folder name must be `sig_foil_v3` so `signal_kinematics_audit.py` finds it.

4. Set `particle_generator/set_folder_name studies/sig_foil_v3` in the macro if using macro-based invocation.

## Macro-based invocation (preferred)

Create `NNBAR_Detector/macro/studies/signal_mcpl_50k.mac`:
```
/run/initialize
/tracking/verbose 0

/particle_generator/set_folder_name studies/sig_foil_v3
/particle_generator/set_run_number 0
/particle_generator/set_event_number 0

/run/beamOn 50000
```

Then run: `./nnbar-detector-simulation.bin -m macro/studies/signal_mcpl_50k.mac`
with the MCPL input enabled via build flag `-DWITH_MCPL=ON` (already enabled in
the existing binary on LUNARC).

## Verification

```bash
# Check Parquet non-stub and row count
ssh lunarc "python3 -c \"
import pyarrow.parquet as pq
import pathlib
d = pathlib.Path('/projects/hep/fs10/shared/nnbar/billy/NNNAR_Detector_sim/build_lunarc/output/sig_foil_v3')
for f in sorted(d.glob('*.parquet')):
    t = pq.read_table(f)
    print(f.name, t.num_rows, 'rows', f.stat().st_size, 'bytes')
\""
```

Expected: Particle_output_0.parquet with ~50000 rows; multiple subdetector files.

## Stop condition

Write the sbatch script + mac file, commit, submit to LUNARC, verify job
appears in squeue. Do NOT wait for completion. Update MASTER_PLAN row to RUNNING.
