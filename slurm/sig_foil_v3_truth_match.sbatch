#!/bin/bash
#SBATCH --job-name=nnbar-sig-truth
#SBATCH --account=lu2026-2-51
#SBATCH --partition=lu48
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc/slurm/sig-truth-match-%j.out
#SBATCH --error=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc/slurm/sig-truth-match-%j.err
#SBATCH --exclude=cn018

set -euo pipefail

NNBAR_ROOT=${NNBAR_ROOT:-/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim}
HIBENV=${HIBENV:-/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env}
DATA_DIR="${NNBAR_ROOT}/build_lunarc/output/sig_foil_v3"
OUTPUT_DIR="${NNBAR_ROOT}/build_lunarc/output/sig_foil_v3_reco"
LOG_DIR="${NNBAR_ROOT}/build_lunarc/slurm"

if [[ ! -d "${DATA_DIR}" ]]; then
    echo "ERROR: sig_foil_v3 data dir not found: ${DATA_DIR}" >&2
    exit 1
fi

export PATH="${HIBENV}/bin:${PATH}"
export LD_LIBRARY_PATH="${HIBENV}/lib:${LD_LIBRARY_PATH:-}"
export NNBAR_ROOT DATA_DIR OUTPUT_DIR

mkdir -p "${OUTPUT_DIR}" "${LOG_DIR}"
cd "${NNBAR_ROOT}"

echo "[sig-truth-match] Starting truth-matched signal mass bias analysis"
echo "[sig-truth-match] Data: ${DATA_DIR}"
echo "[sig-truth-match] Output: ${OUTPUT_DIR}/truth_matching_report.json"
echo "[sig-truth-match] $(date)"

python3 - <<'PYEOF'
import gc
import json
import math
import os
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

DATA_DIR = Path(os.environ["DATA_DIR"])
OUTPUT_DIR = Path(os.environ["OUTPUT_DIR"])
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONE_DEG = 25.0
CONE_RAD = math.radians(CONE_DEG)
SEED_MIN_MEV = 0.1
CLUSTER_MIN_MEV = 10.0
MASS_LO, MASS_HI = 60.0, 240.0
PI0_MASS_MEV = 134.9766
VERTEX = np.zeros(3)
EVENT_CHUNK = int(os.environ.get("TRUTH_MATCH_EVENT_CHUNK", "500"))
HIST_BINS = np.linspace(MASS_LO, MASS_HI, 37)


def read_existing_parquet(name, columns=None, filters=None):
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return pq.read_table(path, columns=columns, filters=filters).to_pandas()


def available_columns(name):
    return set(pq.ParquetFile(DATA_DIR / name).schema_arrow.names)


def choose_columns(name, wanted):
    cols = available_columns(name)
    missing = [c for c in wanted if c not in cols]
    if missing:
        raise RuntimeError(f"{name} missing required columns: {missing}")
    return wanted


def load_triggered_events():
    cols = available_columns("TPC_output_0.parquet")
    keep = ["Event_ID"]
    track_col = next((c for c in ("Track_ID", "TrackID", "track_id", "track") if c in cols), None)
    if track_col:
        keep.append(track_col)
    tpc = read_existing_parquet("TPC_output_0.parquet", columns=keep)
    n_total = int(tpc["Event_ID"].nunique())
    if track_col:
        counts = tpc.groupby("Event_ID", sort=False)[track_col].nunique()
    else:
        counts = tpc.groupby("Event_ID", sort=False).size()
    triggered = [int(eid) for eid in counts[counts >= 2].index]
    del tpc
    gc.collect()
    return n_total, triggered


def load_pi0_truth():
    cols = choose_columns(
        "Interaction_output_0.parquet",
        ["Event_ID", "Track_ID", "Parent_ID", "Name"],
    )
    truth = read_existing_parquet(
        "Interaction_output_0.parquet",
        columns=cols,
        filters=[("Name", "in", ["pi0", "gamma"])],
    )
    pi0 = truth[truth["Name"] == "pi0"][["Event_ID", "Track_ID"]].dropna()
    pi0_tracks = {(int(r.Event_ID), int(r.Track_ID)) for r in pi0.itertuples(index=False)}
    gammas = truth[truth["Name"] == "gamma"][["Event_ID", "Track_ID", "Parent_ID"]].dropna()
    gamma_parent = {}
    daughters_by_pi0 = {}
    for row in gammas.itertuples(index=False):
        key = (int(row.Event_ID), int(row.Track_ID))
        parent = int(row.Parent_ID)
        if (int(row.Event_ID), parent) in pi0_tracks:
            gamma_parent[key] = parent
            daughters_by_pi0.setdefault((int(row.Event_ID), parent), []).append(int(row.Track_ID))
    del truth, pi0, gammas
    gc.collect()
    return pi0_tracks, gamma_parent, daughters_by_pi0


def normalise_hits(df):
    if df.empty:
        return pd.DataFrame(columns=["x", "y", "z", "eDep", "Track_ID", "Parent_ID"])
    for col in ("Track_ID", "Parent_ID"):
        if col not in df.columns:
            df[col] = np.nan
    return df.dropna(subset=["x", "y", "z", "eDep"])


def dominant_identity(cluster_hits):
    by_track = cluster_hits.dropna(subset=["Track_ID"]).groupby("Track_ID", sort=False)["eDep"].sum()
    if by_track.empty:
        return None, None
    track = int(by_track.idxmax())
    subset = cluster_hits[cluster_hits["Track_ID"] == track]
    parent = None
    if "Parent_ID" in subset and subset["Parent_ID"].notna().any():
        parent = int(subset.groupby("Parent_ID", sort=False)["eDep"].sum().idxmax())
    return track, parent


def cluster_hits(vertex, scint_hits, lg_hits):
    parts = []
    for frame in (normalise_hits(scint_hits), normalise_hits(lg_hits)):
        if not frame.empty:
            parts.append(frame[["x", "y", "z", "eDep", "Track_ID", "Parent_ID"]])
    if not parts:
        return []
    hits = pd.concat(parts, ignore_index=True)
    avail = np.ones(len(hits), dtype=bool)
    clusters = []
    while True:
        energies = hits.loc[avail, "eDep"].to_numpy()
        if len(energies) == 0 or energies.max() < SEED_MIN_MEV:
            break
        seed_idx = hits.loc[avail, "eDep"].idxmax()
        seed_pos = hits.loc[seed_idx, ["x", "y", "z"]].to_numpy(dtype=float)
        seed_dir = seed_pos - vertex
        norm = np.linalg.norm(seed_dir)
        if norm < 1e-10:
            avail[seed_idx] = False
            continue
        seed_dir = seed_dir / norm
        hit_pos = hits.loc[avail, ["x", "y", "z"]].to_numpy(dtype=float)
        hit_dir = hit_pos - vertex
        norms = np.linalg.norm(hit_dir, axis=1, keepdims=True)
        norms[norms < 1e-10] = 1.0
        hit_dir = hit_dir / norms
        in_cone = np.dot(hit_dir, seed_dir) > math.cos(CONE_RAD)
        cluster_indices = hits.index[avail].to_numpy()[in_cone]
        if len(cluster_indices) == 0:
            avail[seed_idx] = False
            continue
        clust = hits.loc[cluster_indices]
        total_e = float(clust["eDep"].sum())
        if total_e < CLUSTER_MIN_MEV:
            avail[cluster_indices] = False
            continue
        pos = clust[["x", "y", "z"]].to_numpy(dtype=float)
        centroid = (pos * clust["eDep"].to_numpy()[:, None]).sum(0) / total_e
        direction = centroid - vertex
        dnorm = np.linalg.norm(direction)
        if dnorm < 1e-10:
            avail[cluster_indices] = False
            continue
        track, parent = dominant_identity(clust)
        clusters.append({
            "energy": total_e,
            "direction": direction / dnorm,
            "track_id": track,
            "parent_id": parent,
        })
        avail[cluster_indices] = False
    return clusters


def diphoton_mass(c1, c2):
    cos_theta = float(np.dot(c1["direction"], c2["direction"]))
    cos_theta = max(-1.0, min(1.0, cos_theta))
    return math.sqrt(max(0.0, 2.0 * c1["energy"] * c2["energy"] * (1.0 - cos_theta)))


def pi0_parent(event_id, cluster, pi0_tracks, gamma_parent):
    track = cluster.get("track_id")
    if track is not None and (event_id, int(track)) in gamma_parent:
        return gamma_parent[(event_id, int(track))]
    parent = cluster.get("parent_id")
    if parent is not None and (event_id, int(parent)) in pi0_tracks:
        return int(parent)
    return None


def event_chunks(events, size):
    for start in range(0, len(events), size):
        yield events[start:start + size]


print("Loading trigger and pi0 truth tables...", flush=True)
n_total_events, triggered_events = load_triggered_events()
pi0_tracks, gamma_parent, daughters_by_pi0 = load_pi0_truth()
print(f"Triggered events: {len(triggered_events)}/{n_total_events}", flush=True)
print(f"Truth pi0: {len(pi0_tracks)}; gamma daughters mapped: {len(gamma_parent)}", flush=True)

hit_cols = ["Event_ID", "Track_ID", "Parent_ID", "x", "y", "z", "eDep"]
choose_columns("LeadGlass_output_0.parquet", hit_cols)
choose_columns("Scintillator_output_0.parquet", hit_cols)

masses_all, masses_correct, masses_cross, masses_unknown = [], [], [], []
n_candidate_events = 0
empty = pd.DataFrame(columns=hit_cols)

for chunk_idx, chunk in enumerate(event_chunks(triggered_events, EVENT_CHUNK), 1):
    filters = [("Event_ID", "in", list(chunk))]
    lg = read_existing_parquet("LeadGlass_output_0.parquet", columns=hit_cols, filters=filters)
    sc = read_existing_parquet("Scintillator_output_0.parquet", columns=hit_cols, filters=filters)
    lg_by_event = {int(eid): grp for eid, grp in lg.groupby("Event_ID", sort=False)}
    sc_by_event = {int(eid): grp for eid, grp in sc.groupby("Event_ID", sort=False)}
    for event_id in chunk:
        clusters = cluster_hits(VERTEX, sc_by_event.get(event_id, empty), lg_by_event.get(event_id, empty))
        accepted_here = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                mass = diphoton_mass(clusters[i], clusters[j])
                if MASS_LO <= mass <= MASS_HI:
                    masses_all.append(mass)
                    p1 = pi0_parent(event_id, clusters[i], pi0_tracks, gamma_parent)
                    p2 = pi0_parent(event_id, clusters[j], pi0_tracks, gamma_parent)
                    if p1 is None or p2 is None:
                        masses_unknown.append(mass)
                    elif p1 == p2:
                        masses_correct.append(mass)
                    else:
                        masses_cross.append(mass)
                    accepted_here = True
                    break
            if accepted_here:
                break
        if accepted_here:
            n_candidate_events += 1
    print(
        f"Chunk {chunk_idx}: events={len(chunk)} accepted={n_candidate_events} "
        f"correct={len(masses_correct)} cross={len(masses_cross)} unknown={len(masses_unknown)}",
        flush=True,
    )
    del lg, sc, lg_by_event, sc_by_event
    gc.collect()


def stats(values):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return None, None
    return float(arr.mean()), float(arr.std())


def hist(values):
    counts, bins = np.histogram(np.asarray(values, dtype=float), bins=HIST_BINS)
    return [float(x) for x in bins.tolist()], [int(x) for x in counts.tolist()]

mean_all, sigma_all = stats(masses_all)
mean_correct, sigma_correct = stats(masses_correct)
mean_cross, sigma_cross = stats(masses_cross)
bins_correct, counts_correct = hist(masses_correct)
bins_cross, counts_cross = hist(masses_cross)
known = len(masses_correct) + len(masses_cross)
report = {
    "n_total_events": int(n_total_events),
    "n_triggered_events": int(len(triggered_events)),
    "n_pi0_truth": int(len(pi0_tracks)),
    "n_pi0_with_gamma_daughters": int(len(daughters_by_pi0)),
    "n_accepted_diphoton": int(len(masses_all)),
    "n_accepted_events": int(n_candidate_events),
    "n_correctly_paired": int(len(masses_correct)),
    "n_cross_paired": int(len(masses_cross)),
    "n_unknown_parentage": int(len(masses_unknown)),
    "cross_pair_fraction": float(len(masses_cross) / known) if known else None,
    "mass_mean_all_mev": mean_all,
    "mass_sigma_all_mev": sigma_all,
    "mass_mean_correct_pair_mev": mean_correct,
    "mass_mean_cross_pair_mev": mean_cross,
    "mass_sigma_correct_pair_mev": sigma_correct,
    "mass_sigma_cross_pair_mev": sigma_cross,
    "pi0_mass_true_mev": PI0_MASS_MEV,
    "cone_angle_deg": CONE_DEG,
    "cluster_min_mev": CLUSTER_MIN_MEV,
    "mass_window_mev": [MASS_LO, MASS_HI],
    "event_chunk_size": EVENT_CHUNK,
    "mass_hist_correct_bins": bins_correct,
    "mass_hist_correct_counts": counts_correct,
    "mass_hist_cross_bins": bins_cross,
    "mass_hist_cross_counts": counts_cross,
}
out_path = OUTPUT_DIR / "truth_matching_report.json"
out_path.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2), flush=True)
print(f"Written: {out_path}", flush=True)
PYEOF

echo "[sig-truth-match] Done: $(date)"
echo "SIG_FOIL_V3_TRUTH_MATCH_OK"
