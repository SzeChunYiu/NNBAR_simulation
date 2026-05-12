#!/bin/bash
#SBATCH --job-name=nnbar-build
#SBATCH --output=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build-%j.out
#SBATCH --error=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build-%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=1:00:00
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48

set -euo pipefail

PROJ=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim
FINAL_BUILD=${PROJ}/build_lunarc
HIBENV=/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env
WORKROOT=${TMPDIR:-/tmp}/nnbar_build_${SLURM_JOB_ID:-manual_$$}
WORKSRC=${WORKROOT}/source
WORKBUILD=${WORKROOT}/build

cleanup() {
    rm -rf "${WORKROOT}"
}
trap cleanup EXIT

activate_hibeam_env() {
    export CONDA_PREFIX="${HIBENV}"
    export CONDA_DEFAULT_ENV="hibeam_env"
    export PATH="${CONDA_PREFIX}/bin:${PATH}"
    set +u
    for f in "${CONDA_PREFIX}"/etc/conda/activate.d/*.sh; do
        [ -f "${f}" ] && source "${f}"
    done
    set -u
    export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${LD_LIBRARY_PATH:-}"
    export CMAKE_PREFIX_PATH="${CONDA_PREFIX}:${CONDA_PREFIX}/x86_64-conda-linux-gnu/sysroot/usr:${CMAKE_PREFIX_PATH:-}"
    export Geant4_DIR="${CONDA_PREFIX}/lib/cmake/Geant4"
}

echo "[build] Activating conda-forge Geant4 toolchain..."
activate_hibeam_env

echo "[build] Geant4 setup: ${HIBENV}/bin/geant4.sh (conda no-op), config=${Geant4_DIR}"
"${HIBENV}/bin/geant4-config" --version
cmake --version | head -1
"${CXX}" --version | head -1

echo "[build] Configuring CMake in node-local scratch: ${WORKBUILD}"
rm -rf "${WORKROOT}"
mkdir -p "${WORKSRC}" "${WORKBUILD}" "${WORKROOT}/tmp"
export TMPDIR="${WORKROOT}/tmp"
echo "[build] Creating scratch source copy with stale bundled Arrow disabled..."
rsync -a --delete \
    --exclude .git \
    --exclude build \
    --exclude build_lunarc \
    --exclude /output/ \
    --exclude external/arrow-install \
    --exclude external/arrow-install-linux \
    --exclude external/arrow-src \
    "${PROJ}/" "${WORKSRC}/"
BOOST_STUB="${WORKROOT}/include"
mkdir -p "${BOOST_STUB}/boost"
cat > "${BOOST_STUB}/boost/lexical_cast.hpp" <<'EOF_BOOST'
#pragma once
#include <sstream>
#include <stdexcept>
#include <string>
#include <typeinfo>

namespace boost {
class bad_lexical_cast : public std::bad_cast {
public:
    const char* what() const noexcept override { return "bad lexical cast"; }
};

template <typename Target, typename Source>
Target lexical_cast(const Source& arg) {
    std::stringstream ss;
    ss << arg;
    Target result{};
    ss >> result;
    if (ss.fail()) {
        throw bad_lexical_cast();
    }
    return result;
}

template <>
inline std::string lexical_cast<std::string, std::string>(const std::string& arg) {
    return arg;
}
}
EOF_BOOST
export CPATH="${BOOST_STUB}:${CPATH:-}"
echo "[build] Added scratch Boost lexical_cast compatibility header: ${BOOST_STUB}"
cd "${WORKBUILD}"

cmake "${WORKSRC}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER="${CC}" \
    -DCMAKE_CXX_COMPILER="${CXX}" \
    -DCMAKE_PREFIX_PATH="${CMAKE_PREFIX_PATH}" \
    -DGeant4_DIR="${Geant4_DIR}" \
    -DWITH_GEANT4_UIVIS=OFF \
    -DWITH_GARFIELD=OFF \
    -DWITH_CUDA=OFF \
    -DWITH_GPU=OFF \
    -DWITH_CELERITAS=OFF \
    -DWITH_OPTICKS=OFF \
    -DWITH_DASHBOARD=OFF \
    -DMCPL_BUILD=ON \
    -DWITH_CRY=ON \
    -DCRY_DIR=/projects/hep/fs10/shared/nnbar/billy/packages/cry_v1.7 \
    2>&1 | tee "${PROJ}/slurm/cmake_configure.log"

echo "[build] Building with ${SLURM_CPUS_PER_TASK} cores..."
cmake --build . --parallel "${SLURM_CPUS_PER_TASK}" 2>&1 | tee "${PROJ}/slurm/make.log"

echo "[build] Copying final artifacts to ${FINAL_BUILD}"
# Preserve simulation outputs: only remove binaries, not output/ subdirectory
# rm -rf "${FINAL_BUILD}"  # <-- REPLACED: this wiped all simulation outputs on rebuild
rm -f "${FINAL_BUILD}/nnbar-detector-simulation" "${FINAL_BUILD}/nnbar-detector-simulation.bin"
mkdir -p "${FINAL_BUILD}"
cp -a "${WORKBUILD}/nnbar-detector-simulation" "${WORKBUILD}/nnbar-detector-simulation.bin" "${FINAL_BUILD}/"

echo "[build] Done. Binary: ${FINAL_BUILD}/nnbar-detector-simulation"
ls -lh "${FINAL_BUILD}/nnbar-detector-simulation" "${FINAL_BUILD}/nnbar-detector-simulation.bin"
file "${FINAL_BUILD}/nnbar-detector-simulation.bin"
