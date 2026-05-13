#!/bin/bash -l
#SBATCH -A lu2026-2-51
#SBATCH -p gpua40
#SBATCH --gres=gpu:a40:1
#SBATCH -t 03:00:00
#SBATCH -c 16
#SBATCH --mem=64G
#SBATCH -J mcaccel-adept
#SBATCH -o /projects/hep/fs10/shared/nnbar/billy/mcaccel-competitors/adept/slurm/adept-%j.out
#SBATCH -e /projects/hep/fs10/shared/nnbar/billy/mcaccel-competitors/adept/slurm/adept-%j.err

# AdePT compact baseline for the MCAccel competitor matrix.
# Run on LUNARC only, preferably through:
#   sbatch benchmarks/competitors/adept/build.sh
# It clones/builds AdePT, runs the Example1 TestEm3 GDML workload on one A40,
# and writes results.parquet plus JSON/log provenance under REMOTE_ROOT.

set -euo pipefail

BASE=${BASE:-/projects/hep/fs10/shared/nnbar/billy/mcaccel-competitors}
REMOTE_ROOT=${REMOTE_ROOT:-$BASE/adept}
ADEPT_REPO=${ADEPT_REPO:-https://github.com/apt-sim/AdePT.git}
ADEPT_REF=${ADEPT_REF:-master}
SRC=${ADEPT_SRC:-$BASE/AdePT}
BUILD=${ADEPT_BUILD:-$SRC/build-lunarc-a40}
RESULTS=${RESULTS:-$REMOTE_ROOT/results}
HIB=${HIB:-/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env}
EVENTS=${ADEPT_EVENTS:-8}
PARTICLES_PER_EVENT=${ADEPT_PARTICLES_PER_EVENT:-200}
export RESULTS
mkdir -p "$REMOTE_ROOT/slurm" "$RESULTS"

if ! hostname | grep -Eq '(^cosmos|^cn|^cg)'; then
  echo "ERROR: AdePT competitor builds must run on LUNARC, not locally." >&2
  exit 2
fi

if [ ! -d "$SRC/.git" ]; then
  git clone --depth 1 --filter=blob:none --branch "$ADEPT_REF" "$ADEPT_REPO" "$SRC"
else
  git -C "$SRC" fetch --depth 1 origin "$ADEPT_REF"
  git -C "$SRC" checkout --detach FETCH_HEAD
fi

ADEPT_VIEW=${ADEPT_VIEW:-/cvmfs/sft-nightlies.cern.ch/lcg/views/devAdePT/Mon/x86_64-el9-gcc13-opt/setup.sh}
if [ ! -r "$ADEPT_VIEW" ]; then
  ADEPT_VIEW=/cvmfs/sft.cern.ch/lcg/views/devAdePT/latest/x86_64-el9-gcc13-opt/setup.sh
fi
if [ ! -r "$ADEPT_VIEW" ]; then
  {
    echo "ERROR: no readable devAdePT LCG setup.sh found"
    echo "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "node=$(hostname)"
    echo "job_id=${SLURM_JOB_ID:-manual}"
    echo "partition=${SLURM_JOB_PARTITION:-manual}"
    echo "tried_primary=/cvmfs/sft-nightlies.cern.ch/lcg/views/devAdePT/Mon/x86_64-el9-gcc13-opt/setup.sh"
    echo "tried_fallback=/cvmfs/sft.cern.ch/lcg/views/devAdePT/latest/x86_64-el9-gcc13-opt/setup.sh"
    ls -ld /cvmfs /cvmfs/sft-nightlies.cern.ch /cvmfs/sft.cern.ch 2>&1 || true
  } | tee "$RESULTS/setup-blocker.txt" >&2
  exit 3
fi

set +u
# shellcheck disable=SC1090
source "$ADEPT_VIEW"
module load CUDA/12.8.0 expat/2.5.0 2>/dev/null || true
set -u
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-16}"
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}

{
  echo "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "job_id=${SLURM_JOB_ID:-manual}"
  echo "partition=${SLURM_JOB_PARTITION:-manual}"
  echo "node=$(hostname)"
  echo "workdir=$REMOTE_ROOT"
  echo "source_commit=$(git -C "$SRC" rev-parse HEAD)"
  echo "source_describe=$(git -C "$SRC" describe --tags --always --dirty 2>/dev/null || true)"
  echo "adept_view=$ADEPT_VIEW"
  echo "cmake=$(cmake --version | head -1)"
  echo "nvcc=$(nvcc --version | grep release || true)"
  echo "geant4=$(geant4-config --version 2>/dev/null || true)"
  echo "events=$EVENTS"
  echo "particles_per_event=$PARTICLES_PER_EVENT"
  echo "gpu_csv=name,uuid,driver_version,memory.total"
  nvidia-smi --query-gpu=name,uuid,driver_version,memory.total --format=csv,noheader || true
  echo "modules=$(module list 2>&1 | tr '\n' ';')"
} > "$RESULTS/provenance.txt"

cmake -S "$SRC" -B "$BUILD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_COMPILER=/sw/easybuild_milan/software/CUDA/12.8.0/bin/nvcc \
  -DCMAKE_CUDA_ARCHITECTURES=86 \
  -DADEPT_BUILD_EXAMPLES=ON \
  -DADEPT_BUILD_TESTING=OFF \
  > "$RESULTS/configure.log" 2>&1

cmake --build "$BUILD" --target example1 --parallel "${SLURM_CPUS_PER_TASK:-16}" \
  > "$RESULTS/build-example1.log" 2>&1

MACRO="$RESULTS/testem3_${EVENTS}evt.mac"
python3 - <<PY
from pathlib import Path
build = Path('$BUILD')
src = Path('$SRC')
macro = Path('$MACRO')
s = (build / 'example1.mac').read_text()
s = s.replace('/eventAction/verbose 2', '/eventAction/verbose 1')
s = s.replace('/gun/number 200', '/gun/number $PARTICLES_PER_EVENT')
s = s.replace('/run/beamOn 1', '/run/beamOn $EVENTS')
s = s.replace('/run/initialize', '/random/setSeeds 20260511 20260512\\n/run/initialize')
for token in [str(build / 'cms2018_sd.gdml'), 'cms2018_sd.gdml']:
    s = s.replace(token, str(src / 'examples/data/testEm3.gdml'))
if '/adept/setVecGeomGDML' not in s:
    s = s.replace(
        '/adept/setVerbosity 0',
        '/adept/setVerbosity 0\\n/adept/setVecGeomGDML '
        + str(src / 'examples/data/testEm3.gdml'),
    )
macro.write_text(s)
PY

EXE="$BUILD/BuildProducts/bin/example1"
/usr/bin/time -f "wall_seconds=%e\nmax_rss_kb=%M" -o "$RESULTS/example1-time.txt" \
  "$EXE" -m "$MACRO" > "$RESULTS/example1-output.log" 2> "$RESULTS/example1-stderr.log"

"$HIB/bin/python" - <<'PY'
import json
import math
import os
import pathlib
import re
import statistics

import pandas as pd

root = pathlib.Path(os.environ['RESULTS'])
prov = (root / 'provenance.txt').read_text()
stdout = (root / 'example1-output.log').read_text(errors='replace')
stderr = (root / 'example1-stderr.log').read_text(errors='replace')
time = dict(re.findall(r'(wall_seconds|max_rss_kb)=([^\n]+)', (root / 'example1-time.txt').read_text()))
edep = [float(x) for x in re.findall(r'Total energy deposited:\s*([0-9.eE+-]+)\s*MeV', stdout)]
wall = float(time.get('wall_seconds', 'nan'))
events = int(re.search(r'events=(\d+)', prov).group(1))
particles_per_event = int(re.search(r'particles_per_event=(\d+)', prov).group(1))


def match(pattern, default=''):
    m = re.search(pattern, prov)
    return m.group(1) if m else default


def finite(value):
    return value if math.isfinite(value) else None


rows = [{
    'project': 'AdePT',
    'benchmark': 'example1-testem3-10gev-e-minus',
    'status': 'captured',
    'events': events,
    'particles_per_event': particles_per_event,
    'primaries': events * particles_per_event,
    'wall_seconds': finite(wall),
    'throughput_events_per_s': finite(events / wall) if wall else None,
    'throughput_primaries_per_s': finite((events * particles_per_event) / wall) if wall else None,
    'max_rss_kb': int(time.get('max_rss_kb', '0')),
    'edep_mev_count': len(edep),
    'edep_mev_mean': statistics.fmean(edep) if edep else None,
    'edep_mev_min': min(edep) if edep else None,
    'edep_mev_max': max(edep) if edep else None,
    'edep_mev_std': statistics.stdev(edep) if len(edep) > 1 else 0.0 if edep else None,
    'source_commit': match(r'source_commit=(\S+)'),
    'source_describe': match(r'source_describe=([^\n]+)'),
    'geant4_version': match(r'geant4=([^\n]+)'),
    'node': match(r'node=(\S+)'),
    'partition': match(r'partition=(\S+)'),
    'gpu_uuid': (re.findall(r'GPU-[^,\n]+', prov) or [''])[0],
    'macro': str(root / f'testem3_{events}evt.mac'),
    'stdout_log': str(root / 'example1-output.log'),
    'stderr_log': str(root / 'example1-stderr.log'),
    'stderr_tail': '\n'.join(stderr.splitlines()[-20:]),
}]
pd.DataFrame(rows).to_parquet(root / 'results.parquet', index=False)
(root / 'summary.json').write_text(json.dumps(rows[0], indent=2) + '\n')
(root / 'edep_mev.json').write_text(json.dumps(edep, indent=2) + '\n')
PY

sha256sum "$RESULTS"/*.{json,txt,parquet,log,mac} 2>/dev/null > "$RESULTS/SHA256SUMS" || true
echo "ADEPT_BASELINE_OK results=$RESULTS/results.parquet"
