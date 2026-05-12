#!/bin/bash
#SBATCH --job-name=nnbar-bin5-rc-verify
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --exclude=cn018
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/bin5-rc-verify-%j.out
#SBATCH --error=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/bin5-rc-verify-%j.err

# Verification test for RC-1/RC-2/RC-3 cosmic proton bin5 stall fix.
# Seeds 1636877,2791681 previously caused indefinite stall at events 238 and 491.
# With fixes applied, all 50 events should complete in < 5 min.

set -euo pipefail

NNBAR_ROOT=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim
BUILD_DIR=${NNBAR_ROOT}/build_lunarc
CRY_DIR=/projects/hep/fs10/shared/nnbar/billy/packages/cry_v1.7
HIBENV=/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env

SEED1=1636877
SEED2=2791681
EVENTS=50
THREADS=1
OUTPUT_NAME="cosmic_proton_bin5/rc_verify_${SLURM_JOB_ID}"
OUTPUT_DIR="${BUILD_DIR}/output/${OUTPUT_NAME}"
MACRO="${BUILD_DIR}/cosmic_proton_bin5_rc_verify.mac"

activate_hibeam_env() {
    export CONDA_PREFIX="${HIBENV}"
    export CONDA_DEFAULT_ENV="hibeam_env"
    export PATH="${CONDA_PREFIX}/bin:${PATH}"
    set +u
    for f in "${CONDA_PREFIX}"/etc/conda/activate.d/*.sh; do
        [ -f "${f}" ] && source "${f}"
    done
    set -u
    export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${CRY_DIR}/lib:${LD_LIBRARY_PATH:-}"
    export Geant4_DIR="${CONDA_PREFIX}/lib/cmake/Geant4"
    export CRY_DIR="${CRY_DIR}"
}

activate_hibeam_env
cd "${BUILD_DIR}"

for lnk in data config macro; do
    [[ -L "${lnk}" ]] && current=$(readlink "${lnk}") || current=""
    [[ "${current}" == "${NNBAR_ROOT}/${lnk}" ]] || ln -sfn "${NNBAR_ROOT}/${lnk}" "${lnk}"
done
mkdir -p "${OUTPUT_DIR}" slurm

cat > "${MACRO}" <<MACRO
/random/setSeeds ${SEED1} ${SEED2}
/run/initialize
/tracking/verbose 0
/particle_generator/set_folder_name ${OUTPUT_NAME}
/cosmic/mode true
/cosmic/particle proton
/cosmic/energyMin 50 GeV
/cosmic/energyMax 200 GeV
/cosmic/energyBin 5
/cosmic/particleIdx 4
/cosmic/dataPath ${CRY_DIR}/data
/run/beamOn ${EVENTS}
MACRO

echo "[rc-verify] $(date -Is) — RC-1/RC-2/RC-3 stall fix verification"
echo "[rc-verify] Seeds=${SEED1},${SEED2}  Events=${EVENTS}  Threads=${THREADS}"
echo "[rc-verify] Binary: $(ls -lh ${BUILD_DIR}/nnbar-detector-simulation)"
echo "[rc-verify] Macro:"
cat "${MACRO}"

time "${BUILD_DIR}/nnbar-detector-simulation" -m "${MACRO}" -t ${THREADS} -g

echo "[rc-verify] Simulation complete — checking output"
${HIBENV}/bin/python3 - <<'PY'
from pathlib import Path
import pyarrow.parquet as pq, sys
import os

build = os.environ.get("BUILD_DIR", "/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc")
base = Path(build) / "output" / "cosmic_proton_bin5"
found = sorted(base.glob("rc_verify_*/Particle_output_0.parquet"))
if not found:
    print("ERROR: no output parquet found", file=sys.stderr)
    sys.exit(1)
for p in found:
    sz = p.stat().st_size
    if sz <= 4:
        print(f"STUB output (size={sz}): {p}", file=sys.stderr)
        sys.exit(1)
    rows = pq.ParquetFile(p).metadata.num_rows
    print(f"OK: {p}  size={sz}  rows={rows}")
PY
