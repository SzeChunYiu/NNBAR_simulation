#!/bin/bash
#SBATCH --job-name=nnbar-sig-reco
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --cpus-per-task=1
#SBATCH --mem=128G
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
import sys, warnings, json, math, gc
warnings.filterwarnings('ignore')
import os, numpy as np, pandas as pd
from pathlib import Path
import pyarrow.parquet as pq

DATA_DIR = Path(os.environ.get('NNBAR_ROOT', '.')) / 'build_lunarc/output/sig_foil_v3'
OUTPUT_DIR = Path(os.environ.get('NNBAR_ROOT', '.')) / 'build_lunarc/output/sig_foil_v3_reco'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading TPC data (Event_ID + track columns only)...", flush=True)
tpc_table = pq.read_table(DATA_DIR / 'TPC_output_0.parquet')
tpc_cols = tpc_table.schema.names
# Select only Event_ID and whichever track column exists
id_cols = [c for c in tpc_cols if c == 'Event_ID']
track_col_candidates = [c for c in tpc_cols if c.lower() in ('track_id', 'trackid', 'track')]
track_col = track_col_candidates[0] if track_col_candidates else None
keep_cols = id_cols + ([track_col] if track_col else [])
tpc_df = tpc_table.select(keep_cols).to_pandas()
del tpc_table; gc.collect()
n_total = tpc_df['Event_ID'].nunique()
print(f"TPC: {len(tpc_df)} hits, {n_total} events", flush=True)

# TPC trigger: >=2 unique track IDs per event
print("Running TPC trigger (>= 2 tracks)...", flush=True)
if track_col:
    triggered_events = tpc_df.groupby('Event_ID')[track_col].nunique()
    triggered_events = triggered_events[triggered_events >= 2].index.tolist()
else:
    triggered_events = tpc_df.groupby('Event_ID').size()
    triggered_events = triggered_events[triggered_events >= 2].index.tolist()

n_triggered = len(triggered_events)
print(f"TPC trigger: {n_triggered}/{n_total} = {n_triggered/n_total:.3f}", flush=True)
del tpc_df; gc.collect()

result = {
    'n_total_events': int(n_total),
    'n_tpc_triggered': int(n_triggered),
    'tpc_trigger_efficiency': float(n_triggered/n_total),
}

# Load LeadGlass filtered to triggered events — only columns needed for clustering
print("Loading LeadGlass (filtered, 5 cols)...", flush=True)
triggered_set = set(int(x) for x in triggered_events)
_COLS = ['Event_ID', 'x', 'y', 'z', 'eDep']
lg_table = pq.read_table(DATA_DIR / 'LeadGlass_output_0.parquet',
                         filters=[('Event_ID', 'in', list(triggered_set))],
                         columns=_COLS)
lg_df = lg_table.to_pandas()
del lg_table; gc.collect()
print(f"LG: {len(lg_df)} hits, {lg_df['Event_ID'].nunique()} events", flush=True)

print("Loading Scintillator (filtered, 5 cols)...", flush=True)
scint_table = pq.read_table(DATA_DIR / 'Scintillator_output_0.parquet',
                            filters=[('Event_ID', 'in', list(triggered_set))],
                            columns=_COLS)
scint_df = scint_table.to_pandas()
del scint_table; gc.collect()
print(f"Scint: {len(scint_df)} hits", flush=True)

# Standalone pi0 reco: cone clustering + diphoton invariant mass
CONE_DEG = 25.0
CONE_RAD = math.radians(CONE_DEG)
SEED_MIN_MEV = 0.1
CLUSTER_MIN_MEV = 10.0
PI0_MASS_MEV = 134.9766
MASS_LO, MASS_HI = 60.0, 240.0
VERTEX = np.zeros(3)

def cluster_hits(vertex, scint_hits, lg_hits):
    """Minimal cone-clustering of neutral deposits."""
    combined = []
    for df, det in [(scint_hits, 'scint'), (lg_hits, 'lg')]:
        if len(df) > 0 and all(c in df.columns for c in ('x','y','z','eDep')):
            sub = df[['x','y','z','eDep']].copy()
            sub['det'] = det
            combined.append(sub)
    if not combined:
        return []
    all_hits = pd.concat(combined, ignore_index=True).dropna(subset=['x','y','z','eDep'])
    if len(all_hits) == 0:
        return []
    avail = np.ones(len(all_hits), dtype=bool)
    clusters = []
    while True:
        energies = all_hits.loc[avail, 'eDep'].values
        if len(energies) == 0 or energies.max() < SEED_MIN_MEV:
            break
        seed_idx = all_hits.loc[avail, 'eDep'].idxmax()
        seed_pos = all_hits.loc[seed_idx, ['x','y','z']].values.astype(float)
        seed_dir = seed_pos - vertex
        n = np.linalg.norm(seed_dir)
        if n < 1e-10:
            avail[seed_idx] = False
            continue
        seed_dir = seed_dir / n
        hit_pos = all_hits.loc[avail, ['x','y','z']].values
        hit_dir = hit_pos - vertex
        norms = np.linalg.norm(hit_dir, axis=1, keepdims=True)
        norms[norms < 1e-10] = 1.0
        hit_dir = hit_dir / norms
        cos_angles = np.dot(hit_dir, seed_dir)
        in_cone = cos_angles > math.cos(CONE_RAD)
        avail_indices = all_hits.index[avail].values
        cluster_indices = avail_indices[in_cone]
        if len(cluster_indices) == 0:
            avail[seed_idx] = False
            continue
        clust = all_hits.loc[cluster_indices]
        total_e = clust['eDep'].sum()
        if total_e < CLUSTER_MIN_MEV:
            for idx in cluster_indices: avail[idx] = False
            continue
        pos = clust[['x','y','z']].values
        centroid = (pos * clust['eDep'].values[:, None]).sum(0) / total_e
        direction = centroid - vertex
        dn = np.linalg.norm(direction)
        if dn < 1e-10:
            for idx in cluster_indices: avail[idx] = False
            continue
        direction = direction / dn
        clusters.append({'energy': total_e, 'direction': direction})
        for idx in cluster_indices: avail[idx] = False
    return clusters

def diphoton_mass(e1, d1, e2, d2):
    cos_theta = np.dot(d1, d2)
    cos_theta = max(-1.0, min(1.0, cos_theta))
    m2 = 2 * e1 * e2 * (1 - cos_theta)
    return math.sqrt(max(0, m2))

print("Running pi0 reconstruction...", flush=True)
lg_by_event = {eid: grp for eid, grp in lg_df.groupby('Event_ID')}
sc_by_event = {eid: grp for eid, grp in scint_df.groupby('Event_ID')}
empty = pd.DataFrame(columns=['x','y','z','eDep'])

n_pi0 = 0
pi0_masses = []
scint_total_e_list = []

for i, eid in enumerate(triggered_events):
    if i % 5000 == 0:
        print(f"  Event {i}/{n_triggered}", flush=True)
    lg_h = lg_by_event.get(eid, empty)
    sc_h = sc_by_event.get(eid, empty)
    # Simple scintillator total energy gate (>= 150 MeV, Ch.7 threshold)
    sc_e = sc_h['eDep'].sum() if len(sc_h) > 0 and 'eDep' in sc_h.columns else 0
    scint_total_e_list.append(sc_e)
    clusters = cluster_hits(VERTEX, sc_h, lg_h)
    if len(clusters) >= 2:
        for ci in range(len(clusters)):
            for cj in range(ci+1, len(clusters)):
                m = diphoton_mass(clusters[ci]['energy'], clusters[ci]['direction'],
                                  clusters[cj]['energy'], clusters[cj]['direction'])
                if MASS_LO <= m <= MASS_HI:
                    n_pi0 += 1
                    pi0_masses.append(m)
                    break
            else:
                continue
            break

print(f"Pi0 events: {n_pi0}/{n_triggered} = {n_pi0/n_triggered:.4f}", flush=True)
print(f"Combined efficiency: {n_pi0/n_total:.4f}", flush=True)

scint_e = np.array(scint_total_e_list)
# Scintillator gate: >= 150 MeV
n_scint_gated = int((scint_e >= 150).sum())

result.update({
    'n_pi0_candidate_events': int(n_pi0),
    'pi0_candidate_eff_of_triggered': float(n_pi0/n_triggered),
    'combined_signal_efficiency': float(n_pi0/n_total),
    'n_scint_energy_gated': n_scint_gated,
    'scint_gate_eff': float(n_scint_gated/n_triggered),
    'pi0_mass_mean_mev': float(np.mean(pi0_masses)) if pi0_masses else None,
    'pi0_mass_sigma_mev': float(np.std(pi0_masses)) if pi0_masses else None,
    'pi0_mass_median_mev': float(np.median(pi0_masses)) if pi0_masses else None,
    'n_pi0_masses': len(pi0_masses),
    'cone_angle_deg': CONE_DEG,
    'mass_window_mev': [MASS_LO, MASS_HI],
})

out_path = OUTPUT_DIR / 'reco_summary.json'
out_path.write_text(json.dumps(result, indent=2) + '\n')
print(f"Written: {out_path}", flush=True)
print(json.dumps(result, indent=2), flush=True)
PYEOF

echo "[sig-reco] Done: $(date)"
echo "SIG_FOIL_V3_RECO_OK"
