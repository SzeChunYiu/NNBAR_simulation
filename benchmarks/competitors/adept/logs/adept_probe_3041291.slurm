#!/usr/bin/env bash
#SBATCH --job-name=adept-probe
#SBATCH --account=lu2026-2-51
#SBATCH --partition=gpua40i
#SBATCH --gres=gpu:a40:1
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=/projects/hep/fs10/shared/nnbar/billy/mcaccel-competitors/adept_probe_%j.out
#SBATCH --error=/projects/hep/fs10/shared/nnbar/billy/mcaccel-competitors/adept_probe_%j.err
set -euo pipefail
base=/projects/hep/fs10/shared/nnbar/billy/mcaccel-competitors
src=$base/AdePT
build=$src/build-lunarc-a40
cd "$src"
set +u
source /cvmfs/sft.cern.ch/lcg/views/devAdePT/latest/x86_64-el9-gcc13-opt/setup.sh
module load CUDA/12.8.0 expat/2.5.0
set -u
nvidia-smi --query-gpu=uuid,name,driver_version --format=csv,noheader || true
cmake -S . -B "$build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_COMPILER=/sw/easybuild_milan/software/CUDA/12.8.0/bin/nvcc \
  -DCMAKE_CUDA_ARCHITECTURES=86 \
  -DADEPT_BUILD_EXAMPLES=ON \
  -DADEPT_BUILD_TESTING=OFF
cmake --build "$build" -j "${SLURM_CPUS_PER_TASK:-8}"
macro=$build/mcaccel_testem3_1evt.mac
cp "$build/example1.mac" "$macro"
python3 - <<PY
from pathlib import Path
p=Path('$macro')
s=p.read_text()
s=s.replace('/eventAction/verbose 2','/eventAction/verbose 0')
s=s.replace('cms2018_sd.gdml','testEm3.gdml')
s=s.replace('/run/beamOn 1','/run/beamOn 1')
p.write_text(s)
PY
/usr/bin/time -p "$build/BuildProducts/bin/example1" -m "$macro" > "$base/adept_probe_run.log" 2> "$base/adept_probe_time.err"
