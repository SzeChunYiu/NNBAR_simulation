#!/usr/bin/env python3
"""
Process ALL available NNBAR events through clustering and candidate extraction.
Includes data augmentation by rotating events to expand training data.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd
import argparse
from typing import List, Dict, Tuple
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import PCA


# =============================================================================
# Clustering functions
# =============================================================================

def adaptive_epsilon(points: np.ndarray, k: int = 6, alpha: float = 1.5) -> float:
    """Compute adaptive epsilon using k-NN distances."""
    n = len(points)
    if n <= k + 1:
        return 2.0

    nn = NearestNeighbors(n_neighbors=min(k + 1, n))
    nn.fit(points)
    distances, _ = nn.kneighbors(points)

    k_distances = distances[:, min(k, n-1)]
    eps = alpha * np.median(k_distances)
    return max(eps, 0.5)


def transform_cylindrical(xyz: np.ndarray, phi_weight: float = 5.0, z_weight: float = 1.0) -> np.ndarray:
    """Transform to weighted cylindrical space for clustering."""
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    r = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return np.column_stack([r, phi * phi_weight, z * z_weight])


def pca_line_fit(P: np.ndarray, z_target: float = 0.0) -> Dict:
    """PCA line fitting with vertex projection."""
    if len(P) < 2:
        C = P.mean(axis=0) if len(P) > 0 else np.zeros(3)
        return {
            "center": C, "direction": np.array([0, 0, 1]),
            "length": 0.0, "rms": 0.0, "linearity": 0.0,
            "vx": float(C[0]), "vy": float(C[1]), "vz": float(z_target),
        }

    C = P.mean(axis=0)
    pca = PCA(n_components=min(3, len(P)))
    pca.fit(P - C)
    d = pca.components_[0]
    d = d / (np.linalg.norm(d) + 1e-12)

    t = (P - C) @ d
    tmin, tmax = float(np.min(t)), float(np.max(t))

    perp = (P - C) - np.outer(t, d)
    rms = float(np.sqrt((perp**2).sum(axis=1).mean()))
    linearity = float(pca.explained_variance_ratio_[0]) if len(pca.explained_variance_ratio_) > 0 else 0.0

    # Vertex projection at z=z_target
    if abs(d[2]) > 1e-9:
        t_vtx = (z_target - C[2]) / d[2]
        vx = float(C[0] + t_vtx * d[0])
        vy = float(C[1] + t_vtx * d[1])
    else:
        vx, vy = float("nan"), float("nan")

    return {
        "center": C, "direction": d, "length": float(tmax - tmin),
        "rms": rms, "linearity": linearity,
        "vx": vx, "vy": vy, "vz": float(z_target),
    }


def split_by_z_gap(xyz: np.ndarray, labels: np.ndarray, gap_threshold: float = 6.0) -> np.ndarray:
    """Split clusters with large z-gaps."""
    new_labels = labels.copy()
    max_label = labels.max() if labels.max() >= 0 else -1

    for cluster_id in set(labels):
        if cluster_id == -1:
            continue
        idx = np.where(labels == cluster_id)[0]
        if len(idx) < 8:
            continue

        P = xyz[idx]
        # PCA direction
        C = P.mean(axis=0)
        _, _, Vt = np.linalg.svd(P - C, full_matrices=False)
        d = Vt[0] / (np.linalg.norm(Vt[0]) + 1e-12)
        t = (P - C) @ d

        order = np.argsort(t)
        t_sorted = t[order]
        gaps = np.diff(t_sorted)

        if len(gaps) > 0 and np.max(gaps) >= gap_threshold:
            cut_at = np.argmax(gaps)
            if cut_at >= 3 and (len(order) - cut_at - 1) >= 3:
                max_label += 1
                new_labels[idx[order[cut_at + 1:]]] = max_label

    return new_labels


def split_by_perp_bimodality(xyz: np.ndarray, labels: np.ndarray, d_thresh: float = 2.0) -> np.ndarray:
    """Split clusters showing bimodal perpendicular distance."""
    new_labels = labels.copy()
    max_label = labels.max() if labels.max() >= 0 else -1

    for cluster_id in set(labels):
        if cluster_id == -1:
            continue
        idx = np.where(labels == cluster_id)[0]
        n = len(idx)
        if n < 10:
            continue

        P = xyz[idx]
        C = P.mean(axis=0)
        _, _, Vt = np.linalg.svd(P - C, full_matrices=False)
        d = Vt[0] / (np.linalg.norm(Vt[0]) + 1e-12)

        # Lateral direction
        u = np.cross(d, np.array([0.0, 0.0, 1.0]))
        if np.linalg.norm(u) < 1e-8:
            u = np.array([-d[1], d[0], 0.0])
        u = u / (np.linalg.norm(u) + 1e-12)

        s = (P - C) @ u

        # K-means for bimodality detection
        m1, m2 = np.percentile(s, [33.0, 66.0])
        for _ in range(8):
            d1 = (s - m1)**2
            d2 = (s - m2)**2
            lab = d1 <= d2
            if lab.sum() == 0 or lab.sum() == n:
                break
            m1 = float(s[lab].mean())
            m2 = float(s[~lab].mean())

        if m1 > m2:
            m1, m2 = m2, m1
            lab = ~lab

        w1 = float(lab.mean())
        if min(w1, 1 - w1) < 0.15:
            continue

        s1 = float(np.std(s[lab])) + 1e-12
        s2 = float(np.std(s[~lab])) + 1e-12
        ashman_d = abs(m1 - m2) / (np.sqrt(0.5 * (s1**2 + s2**2)) + 1e-12)

        if ashman_d >= d_thresh:
            thr = 0.5 * (m1 + m2)
            to_new = s > thr
            if min(int((~to_new).sum()), int(to_new.sum())) >= 3:
                max_label += 1
                new_labels[idx[to_new]] = max_label

    return new_labels


def cluster_event(xyz: np.ndarray, phi_weight: float = 5.0, z_weight: float = 1.0,
                  alpha: float = 1.5, min_samples: int = 3, refine: bool = True) -> np.ndarray:
    """Cluster TPC hits for a single event."""
    if len(xyz) < min_samples:
        return np.full(len(xyz), -1, dtype=int)

    # Cylindrical feature space
    X_cyl = transform_cylindrical(xyz, phi_weight, z_weight)
    eps = adaptive_epsilon(X_cyl, k=6, alpha=alpha)
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(X_cyl)

    if refine:
        labels = split_by_z_gap(xyz, labels, gap_threshold=6.0)
        labels = split_by_perp_bimodality(xyz, labels, d_thresh=2.0)

    return labels


def extract_candidates(xyz: np.ndarray, labels: np.ndarray, z_target: float = 0.0) -> List[Dict]:
    """Extract candidate track features for each cluster."""
    candidates = []
    unique_labels = [l for l in np.unique(labels) if l >= 0]

    for label in unique_labels:
        idx = np.where(labels == label)[0]
        P = xyz[idx]

        if len(P) < 3:
            continue

        fit = pca_line_fit(P, z_target=z_target)

        if np.isnan(fit['vx']) or np.isnan(fit['vy']):
            continue

        candidates.append({
            'cluster_id': int(label),
            'n_hits': len(P),
            'vx': fit['vx'],
            'vy': fit['vy'],
            'vz': fit['vz'],
            'length': fit['length'],
            'rms': fit['rms'],
            'linearity': fit['linearity'],
            'center_x': fit['center'][0],
            'center_y': fit['center'][1],
            'center_z': fit['center'][2],
            'dir_x': fit['direction'][0],
            'dir_y': fit['direction'][1],
            'dir_z': fit['direction'][2],
        })

    return candidates


# =============================================================================
# Data augmentation
# =============================================================================

def rotate_event_xy(xyz: np.ndarray, truth_xyz: np.ndarray, angle_rad: float) -> Tuple[np.ndarray, np.ndarray]:
    """Rotate event around z-axis."""
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)

    x_new = xyz[:, 0] * cos_a - xyz[:, 1] * sin_a
    y_new = xyz[:, 0] * sin_a + xyz[:, 1] * cos_a
    z_new = xyz[:, 2]

    tx_new = truth_xyz[0] * cos_a - truth_xyz[1] * sin_a
    ty_new = truth_xyz[0] * sin_a + truth_xyz[1] * cos_a
    tz_new = truth_xyz[2]

    return np.column_stack([x_new, y_new, z_new]), np.array([tx_new, ty_new, tz_new])


def flip_event_z(xyz: np.ndarray, truth_xyz: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Flip event along z-axis."""
    xyz_new = xyz.copy()
    xyz_new[:, 2] = -xyz_new[:, 2]
    truth_new = truth_xyz.copy()
    truth_new[2] = -truth_new[2]
    return xyz_new, truth_new


def augment_event(xyz: np.ndarray, truth_xyz: np.ndarray, n_augments: int = 8) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Generate augmented versions of an event."""
    augmented = [(xyz.copy(), truth_xyz.copy())]

    # Fixed rotations
    for angle in [np.pi/2, np.pi, 3*np.pi/2]:
        xyz_rot, truth_rot = rotate_event_xy(xyz, truth_xyz, angle)
        augmented.append((xyz_rot, truth_rot))

    # Random rotations
    np.random.seed(hash(xyz.tobytes()) % (2**32))  # Deterministic per event
    for i in range(n_augments - 4):
        angle = np.random.uniform(0, 2*np.pi)
        xyz_rot, truth_rot = rotate_event_xy(xyz, truth_xyz, angle)
        augmented.append((xyz_rot, truth_rot))

    return augmented


# =============================================================================
# Data loading
# =============================================================================

def load_all_data(data_dir: Path) -> List[Dict]:
    """Load all available NNBAR simulation data."""
    all_data = []

    # Check for simulation output directories
    output_dirs = list(data_dir.glob("**/TPC_output*.parquet"))
    print(f"Found {len(output_dirs)} TPC output files")

    for tpc_file in output_dirs:
        output_dir = tpc_file.parent
        particle_file = output_dir / "Particle_output_0.parquet"

        if not particle_file.exists():
            continue

        try:
            tpc = pd.read_parquet(tpc_file)
            particle = pd.read_parquet(particle_file)
        except Exception as e:
            print(f"Error loading {tpc_file}: {e}")
            continue

        if len(tpc) == 0:
            continue

        # Extract truth vertex from pions
        pions = particle[particle['Name'].isin(['pi+', 'pi-', 'pi0'])]

        for event_id in tpc['Event_ID'].unique():
            event_hits = tpc[tpc['Event_ID'] == event_id]
            event_pions = pions[pions['Event_ID'] == event_id]

            if len(event_hits) < 10 or len(event_pions) == 0:
                continue

            xyz = event_hits[['x', 'y', 'z']].values.astype(np.float32)
            truth_xyz = np.array([
                event_pions['x'].mean(),
                event_pions['y'].mean(),
                event_pions['z'].mean() if 'z' in event_pions.columns else 0.0
            ], dtype=np.float32)

            all_data.append({
                'source': output_dir.name,
                'event_id': event_id,
                'xyz': xyz,
                'truth_xyz': truth_xyz,
            })

    return all_data


# =============================================================================
# Main processing
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Process all NNBAR events")
    parser.add_argument("--data_dir", default="../NNBAR_Detector/build/output",
                        help="Directory containing simulation output")
    parser.add_argument("--out_dir", default="./output/processed",
                        help="Output directory")
    parser.add_argument("--n_augment", type=int, default=8,
                        help="Number of augmented versions per event")
    parser.add_argument("--no_augment", action="store_true",
                        help="Disable augmentation")
    parser.add_argument("--z_target", type=float, default=0.0,
                        help="Z coordinate for vertex projection")
    args = parser.parse_args()

    # Setup paths
    script_dir = Path(__file__).parent
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = script_dir / data_dir

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = script_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NNBAR Event Processing")
    print("=" * 60)
    print(f"Data directory: {data_dir}")
    print(f"Output directory: {out_dir}")
    print(f"Augmentation: {args.n_augment if not args.no_augment else 'disabled'}")

    # Load data
    print("\nLoading data...")
    all_data = load_all_data(data_dir)
    print(f"Loaded {len(all_data)} original events")

    if len(all_data) == 0:
        print("No data found!")
        return

    # Process events
    all_candidates = []
    all_truth = []
    event_counter = 0

    print("\nProcessing events...")
    for i, event_data in enumerate(all_data):
        if (i + 1) % 50 == 0:
            print(f"  Processing event {i + 1}/{len(all_data)}")

        # Original + augmented versions
        if args.no_augment:
            versions = [(event_data['xyz'], event_data['truth_xyz'])]
        else:
            versions = augment_event(event_data['xyz'], event_data['truth_xyz'], args.n_augment)

        for xyz, truth_xyz in versions:
            # Cluster
            labels = cluster_event(xyz)

            # Extract candidates
            candidates = extract_candidates(xyz, labels, z_target=args.z_target)

            if len(candidates) < 2:
                continue

            # Record candidates
            for c in candidates:
                c['event_id'] = event_counter
                all_candidates.append(c)

            # Record truth
            all_truth.append({
                'event_no': event_counter,
                'position_x': float(truth_xyz[0]),
                'position_y': float(truth_xyz[1]),
                'position_z': float(truth_xyz[2]),
            })

            event_counter += 1

    print(f"\nProcessed {event_counter} events (with augmentation)")
    print(f"Total candidates: {len(all_candidates)}")

    # Save data
    cand_df = pd.DataFrame(all_candidates)
    truth_df = pd.DataFrame(all_truth)

    cand_df.to_parquet(out_dir / "candidates.parquet", index=False)
    truth_df.to_parquet(out_dir / "truth.parquet", index=False)

    print(f"\nSaved to {out_dir}")
    print(f"  candidates.parquet: {len(cand_df)} rows")
    print(f"  truth.parquet: {len(truth_df)} rows")

    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"Mean candidates per event: {len(cand_df) / event_counter:.1f}")
    print(f"Mean n_hits: {cand_df['n_hits'].mean():.1f}")
    print(f"Mean linearity: {cand_df['linearity'].mean():.3f}")
    print(f"Mean track length: {cand_df['length'].mean():.1f} cm")


if __name__ == "__main__":
    main()
