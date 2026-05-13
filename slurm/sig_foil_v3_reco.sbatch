#!/bin/bash
#SBATCH --job-name=nnbar-sig-reco
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/sig-reco-%j.out
#SBATCH --error=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/sig-reco-%j.err
#SBATCH --exclude=cn018

set -euo pipefail

NNBAR_ROOT=${NNBAR_ROOT:-/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim}
HIBENV=${HIBENV:-/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env}
DATA_DIR="${NNBAR_ROOT}/build_lunarc/output/sig_foil_v3"
OUTPUT_DIR="${NNBAR_ROOT}/build_lunarc/output/sig_foil_v3_reco"

if [[ ! -d "${DATA_DIR}" ]]; then
    echo "ERROR: sig_foil_v3 data dir not found: ${DATA_DIR}" >&2
    exit 1
fi

export PATH="${HIBENV}/bin:${PATH}"
export LD_LIBRARY_PATH="${HIBENV}/lib:${LD_LIBRARY_PATH:-}"

mkdir -p "${OUTPUT_DIR}"
cd "${NNBAR_ROOT}"

echo "[sig-reco] Starting signal reconstruction on sig_foil_v3"
echo "[sig-reco] Data: ${DATA_DIR}"
echo "[sig-reco] Output: ${OUTPUT_DIR}"
echo "[sig-reco] $(date)"

python3 - <<'PYEOF'
import sys, warnings, json
sys.path.insert(0, '/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim')
warnings.filterwarnings('ignore')
import os, numpy as np, pandas as pd
from pathlib import Path

DATA_DIR = Path(os.environ.get('NNBAR_ROOT', '.')) / 'build_lunarc/output/sig_foil_v3'
OUTPUT_DIR = Path(os.environ.get('NNBAR_ROOT', '.')) / 'build_lunarc/output/sig_foil_v3_reco'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

from nnbar_reconstruction.reconstruction.event_preselection import (
    rolling_time_window_trigger, filter_hits_by_time
)
from nnbar_reconstruction.reconstruction.neutral_reconstruction import (
    reconstruct_neutral_objects, find_pi0_candidates
)
from nnbar_reconstruction.reconstruction.charged_reconstruction import (
    reconstruct_charged_objects
)
from nnbar_reconstruction.reconstruction.object_identification import (
    identify_objects
)

print("Loading TPC data...", flush=True)
tpc_df = pd.read_parquet(DATA_DIR / 'TPC_output_0.parquet')
print(f"TPC: {len(tpc_df)} hits, {tpc_df['Event_ID'].nunique()} events", flush=True)

print("Loading Particle data...", flush=True)
prt_df = pd.read_parquet(DATA_DIR / 'Particle_output_0.parquet')
n_total = prt_df['Event_ID'].nunique()
print(f"Signal events: {n_total}", flush=True)

# Step 1: TPC trigger preselection
print("Running TPC trigger...", flush=True)
tpc_by_event = tpc_df.groupby('Event_ID')
triggered_events = []
for eid, group in tpc_by_event:
    n_tracks = group['track_id'].nunique() if 'track_id' in group.columns else group['Track_ID'].nunique() if 'Track_ID' in group.columns else len(group)
    if n_tracks >= 2:
        triggered_events.append(eid)
n_triggered = len(triggered_events)
print(f"TPC trigger: {n_triggered}/{n_total} = {n_triggered/n_total:.3f}", flush=True)

# Write checkpoint
result = {
    'n_total_events': int(n_total),
    'n_tpc_triggered': int(n_triggered),
    'tpc_trigger_efficiency': float(n_triggered/n_total),
}

print("Loading LeadGlass data (this may take a while)...", flush=True)
import gc
# Only load events that passed TPC trigger
triggered_set = set(triggered_events)

# Load LeadGlass in chunks using parquet row groups
lg_path = DATA_DIR / 'LeadGlass_output_0.parquet'
import pyarrow.parquet as pq
lg_table = pq.read_table(lg_path, filters=[('Event_ID', 'in', list(triggered_set))])
lg_df = lg_table.to_pandas()
print(f"LG data loaded: {len(lg_df)} hits for {lg_df['Event_ID'].nunique()} events", flush=True)

print("Loading Scintillator data...", flush=True)
scint_path = DATA_DIR / 'Scintillator_output_0.parquet'
scint_table = pq.read_table(scint_path, filters=[('Event_ID', 'in', list(triggered_set))])
scint_df = scint_table.to_pandas()
print(f"Scint data loaded: {len(scint_df)} hits", flush=True)

print("Running reconstruction on triggered events...", flush=True)
vertex = np.zeros(3)
lg_groups = {eid: grp for eid, grp in lg_df.groupby('Event_ID')}
scint_groups = {eid: grp for eid, grp in scint_df.groupby('Event_ID')}
HIT_COLS = ('x', 'y', 'z', 'eDep')
empty_hits = pd.DataFrame(columns=HIT_COLS)

def hit_view(df):
    cols = [c for c in HIT_COLS if c in df.columns]
    return df[cols] if cols else empty_hits

n_pi0_events = 0
n_full_reco_events = 0
pi0_masses = []

for i, eid in enumerate(triggered_events):
    if i % 1000 == 0:
        print(f"  Processing event {i}/{n_triggered}...", flush=True)
    lg_hits = hit_view(lg_groups.get(eid, empty_hits))
    scint_hits = hit_view(scint_groups.get(eid, empty_hits))
    neutral_objects = reconstruct_neutral_objects(vertex, scint_hits, lg_hits)
    candidates = find_pi0_candidates(neutral_objects, vertex)
    if len(candidates) > 0:
        n_pi0_events += 1
        best = max(candidates, key=lambda c: c[2])
        pi0_masses.append(best[2])
        n_full_reco_events += 1

print(f"Pi0 candidates: {n_pi0_events}/{n_triggered} = {n_pi0_events/n_triggered:.3f}", flush=True)
print(f"Combined signal efficiency: {n_pi0_events/n_total:.3f}", flush=True)

result.update({
    'n_pi0_candidate_events': int(n_pi0_events),
    'pi0_candidate_efficiency_of_triggered': float(n_pi0_events/n_triggered),
    'combined_signal_efficiency': float(n_pi0_events/n_total),
    'pi0_mass_mean_mev': float(np.mean(pi0_masses)) if pi0_masses else None,
    'pi0_mass_sigma_mev': float(np.std(pi0_masses)) if pi0_masses else None,
    'n_pi0_masses': len(pi0_masses),
})

output_path = Path(os.environ.get('NNBAR_ROOT', '.')) / 'build_lunarc/output/sig_foil_v3_reco/reco_summary.json'
import json
output_path.write_text(json.dumps(result, indent=2) + '\n')
print(f"Written: {output_path}", flush=True)
print(json.dumps(result, indent=2), flush=True)
PYEOF

echo "[sig-reco] Done: $(date)"
echo "SIG_FOIL_V3_RECO_OK"
