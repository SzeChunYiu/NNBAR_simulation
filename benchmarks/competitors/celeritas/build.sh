#!/bin/bash -l
#SBATCH -A lu2026-2-51
#SBATCH -p gpua40
#SBATCH --gres=gpu:a40:1
#SBATCH -t 02:00:00
#SBATCH -c 16
#SBATCH --mem=64G
#SBATCH -J mcaccel-celeritas
#SBATCH -o /projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-%j.out
#SBATCH -e /projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-%j.err

# Celeritas compact baseline for the MCAccel competitor matrix.
# Run on LUNARC only, preferably through:
#   sbatch benchmarks/competitors/celeritas/build.sh
# It clones Celeritas, builds only celer-sim, runs a small A40 simple-cms gamma
# workload, and writes results.parquet plus JSON provenance under REMOTE_ROOT.

set -euo pipefail

REMOTE_ROOT=${REMOTE_ROOT:-/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas}
CELERITAS_REPO=${CELERITAS_REPO:-https://github.com/celeritas-project/celeritas.git}
CELERITAS_REF=${CELERITAS_REF:-develop}
HIB=${HIB:-/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env}
SRC="$REMOTE_ROOT/source"
BUILD="$REMOTE_ROOT/build-a40"
RESULTS="$REMOTE_ROOT/results"
mkdir -p "$REMOTE_ROOT/slurm" "$RESULTS"

if ! hostname | grep -Eq '(^cosmos|^cn|^cg)'; then
  echo "ERROR: Celeritas competitor builds must run on LUNARC, not locally." >&2
  exit 2
fi

if [ ! -d "$SRC/.git" ]; then
  git clone --depth 1 --filter=blob:none --branch "$CELERITAS_REF" "$CELERITAS_REPO" "$SRC"
else
  git -C "$SRC" fetch --depth 1 origin "$CELERITAS_REF"
  git -C "$SRC" checkout --detach FETCH_HEAD
fi

module purge
module load GCC/13.2.0 CMake/3.27.6 Ninja/1.11.1 CUDA/12.8.0 Python/3.11.5
export CMAKE_PREFIX_PATH="$HIB:${CMAKE_PREFIX_PATH:-}"
export PATH="$HIB/bin:$PATH"
export LD_LIBRARY_PATH="$HIB/lib:${LD_LIBRARY_PATH:-}"
# Source conda activate.d scripts to set Geant4 data paths (geant4.sh is incompatible with conda)
# CONDA_PREFIX needed by the activate.d scripts; -u disabled so unset G4*DATA vars are handled
CONDA_PREFIX="$HIB"
export CONDA_PREFIX
set +u
for _g4act in "$HIB/etc/conda/activate.d"/activate-geant4-data-*.sh; do
  # shellcheck disable=SC1090
  [ -f "$_g4act" ] && source "$_g4act"
done
set -u
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-16}"
export CELER_LOG=${CELER_LOG:-info}
export CELER_DISABLE_PARALLEL=1

{
  echo "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "job_id=${SLURM_JOB_ID:-manual}"
  echo "partition=${SLURM_JOB_PARTITION:-manual}"
  echo "node=$(hostname)"
  echo "workdir=$REMOTE_ROOT"
  echo "source_commit=$(git -C "$SRC" rev-parse HEAD)"
  echo "source_describe=$(git -C "$SRC" describe --tags --always --dirty 2>/dev/null || true)"
  echo "cmake=$(cmake --version | head -1)"
  echo "ninja=$(ninja --version 2>/dev/null || true)"
  echo "nvcc=$(nvcc --version | grep release || true)"
  echo "geant4=$($HIB/bin/geant4-config --version 2>/dev/null || true)"
  echo "gpu_csv=name,uuid,driver_version,memory.total"
  nvidia-smi --query-gpu=name,uuid,driver_version,memory.total --format=csv,noheader || true
  echo "modules=$(module list 2>&1 | tr '\n' ';')"
} > "$RESULTS/provenance.txt"

cmake -S "$SRC" -B "$BUILD" -GNinja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$REMOTE_ROOT/install" \
  -DCMAKE_CUDA_ARCHITECTURES=86 \
  -DCELERITAS_USE_CUDA=ON \
  -DCELERITAS_USE_Geant4=ON \
  -DCELERITAS_USE_HepMC3=OFF \
  -DCELERITAS_USE_ROOT=OFF \
  -DCELERITAS_USE_MPI=OFF \
  -DCELERITAS_BUILD_TESTS=ON \
  -DCELERITAS_BUILD_DOCS=OFF \
  -DCELERITAS_BUILD_EXAMPLES=OFF \
  -DCELERITAS_USE_OpenMP=ON \
  > "$RESULTS/configure.log" 2>&1

cmake --build "$BUILD" --target celer-sim --parallel "${SLURM_CPUS_PER_TASK:-16}" \
  > "$RESULTS/build-celer-sim.log" 2>&1

EXE="$BUILD/bin/celer-sim"
if [ ! -x "$EXE" ]; then
  echo "ERROR: celer-sim executable not found at $EXE" >&2
  find "$BUILD" -maxdepth 3 -type f -name celer-sim -ls >&2 || true
  exit 127
fi
"$EXE" --config > "$RESULTS/celer-sim-config.json"
"$EXE" --device > "$RESULTS/celer-sim-device.json"

cat > "$RESULTS/simple-cms-gamma.inp.json" <<JSON
{
  "use_device": true,
  "geometry_file": "$SRC/app/data/simple-cms.gdml",
  "primary_options": {
    "_format": "primary-generator",
    "seed": 20260511,
    "pdg": [22],
    "num_events": 256,
    "primaries_per_event": 32,
    "energy": {"distribution": "delta", "params": [100.0]},
    "position": {"distribution": "box", "params": [-1.0, -1.0, -1.0, 1.0, 1.0, 1.0]},
    "direction": {"distribution": "isotropic", "params": []}
  },
  "seed": 20260511,
  "num_track_slots": 8192,
  "max_steps": 512,
  "initializer_capacity": 819200,
  "secondary_stack_factor": 3.0,
  "interpolation": "linear",
  "action_diagnostic": true,
  "step_diagnostic": true,
  "step_diagnostic_bins": 200,
  "write_step_times": true,
  "write_track_counts": true,
  "transporter_result": true,
  "action_times": true,
  "merge_events": true,
  "simple_calo": ["si_tracker", "em_calorimeter"],
  "physics_options": {
    "compton_scattering": true,
    "photoelectric": true,
    "rayleigh_scattering": true,
    "gamma_conversion": true,
    "gamma_general": false,
    "ionization": true,
    "annihilation": true,
    "brems": "all",
    "msc": "none",
    "coulomb_scattering": false,
    "eloss_fluctuation": true,
    "lpm": true
  },
  "slot_diagnostic_prefix": "$RESULTS/slot-diag-simple-cms-gamma-"
}
JSON

/usr/bin/time -f "wall_seconds=%e\nmax_rss_kb=%M" -o "$RESULTS/celer-sim-time.txt" \
  "$EXE" "$RESULTS/simple-cms-gamma.inp.json" > "$RESULTS/celer-sim-output.json" 2> "$RESULTS/celer-sim-stderr.log"

"$HIB/bin/python" - <<'PY'
import json, pathlib, re
import pandas as pd
root = pathlib.Path('/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/results')
out = json.loads((root / 'celer-sim-output.json').read_text())
prov = (root / 'provenance.txt').read_text()
time = dict(re.findall(r'(wall_seconds|max_rss_kb)=([^\n]+)', (root / 'celer-sim-time.txt').read_text()))
runner = out.get('result', {}).get('runner', {})
step_iters = runner.get('num_step_iterations', [])
track_counts = runner.get('track_counts', [])
wall = float(time.get('wall_seconds', 'nan'))
rows = [{
    'project': 'Celeritas',
    'benchmark': 'simple-cms-gamma-primary-celer-sim',
    'status': 'captured',
    'events': 256,
    'primaries_per_event': 32,
    'primaries': 256 * 32,
    'wall_seconds': wall,
    'throughput_events_per_s': 256 / wall,
    'throughput_primaries_per_s': (256 * 32) / wall,
    'max_rss_kb': int(time.get('max_rss_kb', '0')),
    'source_commit': re.search(r'source_commit=(\S+)', prov).group(1),
    'node': re.search(r'node=(\S+)', prov).group(1),
    'gpu_uuid': (re.findall(r'GPU-[^,\n]+', prov) or [''])[0],
    'num_step_iterations_first_stream': step_iters[0] if step_iters else None,
    'track_counts_steps': len(track_counts[0]) if track_counts else None,
    'output_json': str(root / 'celer-sim-output.json'),
    'input_json': str(root / 'simple-cms-gamma.inp.json'),
}]
pd.DataFrame(rows).to_parquet(root / 'results.parquet', index=False)
(root / 'summary.json').write_text(json.dumps(rows[0], indent=2) + '\n')
PY

sha256sum "$RESULTS"/*.{json,txt,parquet,log} 2>/dev/null > "$RESULTS/SHA256SUMS" || true
echo "CELERITAS_BASELINE_OK results=$RESULTS/results.parquet"
