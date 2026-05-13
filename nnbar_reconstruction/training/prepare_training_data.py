#!/usr/bin/env python3
"""
NNBAR Reconstruction Training Data Preparation

Prepares training datasets for:
1. P-Signal classifier (signal vs background track classification)
2. Vertex GNN (vertex position regression)
3. Clustering evaluation (ground truth cluster labels)

Based on analysis documented in SECONDARY_PARTICLE_HANDLING.md

Author: NNBAR Collaboration
Date: 2026-01-12
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
from tqdm import tqdm


@dataclass
class TrackSample:
    """Training sample for P-Signal classifier."""
    event_id: int
    track_id: int
    hits: np.ndarray  # (N, 3) coordinates
    label: int  # 1 = signal, 0 = background
    particle_name: str
    parent_id: int
    n_hits: int
    origin: str
    proc: str


@dataclass
class VertexSample:
    """Training sample for Vertex GNN."""
    event_id: int
    track_features: np.ndarray  # (C, 12) candidate features
    track_positions: np.ndarray  # (C, 3) candidate projected vertices
    track_mask: np.ndarray  # (C,) valid mask
    truth_vertex: np.ndarray  # (3,) truth position
    n_tracks: int


def classify_track(parent_id: int, name: str, proc: str, origin: str) -> str:
    """
    Classify track as SIGNAL or BACKGROUND.

    Based on SECONDARY_PARTICLE_HANDLING.md Section 3 and physics expert analysis.

    Key finding: Muons from pion decay have ~60 deg direction change on average,
    making them unreliable for vertex reconstruction. Only 22% are within 10 deg
    of parent pion direction.
    """
    # PRIMARY: Direct from annihilation (charged particles only)
    if parent_id == 0 and name in ['pi+', 'pi-', 'proton', 'K+', 'K-']:
        return 'SIGNAL'

    # MUONS: Exclude from vertex fit due to large decay angle (~60 deg)
    # Only 22% of muons are within 10 deg of parent pion direction
    if name in ['mu+', 'mu-']:
        return 'BACKGROUND'  # Changed from SIGNAL_LIKE based on physics analysis

    # BACKGROUND: Spallation products
    spallation_particles = ['Al27', 'Mg26', 'Mg25', 'Ar40', 'O16', 'Si28',
                           'deuteron', 'triton', 'alpha', 'He3', 'Li6', 'Li7',
                           'Be7', 'Be9', 'B10', 'B11', 'C11', 'C10']
    if name in spallation_particles and parent_id > 0:
        # Check if from material interaction
        material_origins = ['Beampipe', 'silicon', 'Steel', 'Lead']
        if any(mat in str(origin) for mat in material_origins):
            return 'BACKGROUND'

    # BACKGROUND: Low-energy electrons (Compton/delta-rays)
    if name in ['e-', 'e+']:
        return 'BACKGROUND'

    # DEFAULT: Treat as background for safety
    return 'BACKGROUND'


def get_binary_label(classification: str) -> int:
    """Convert classification to binary label for P-Signal.

    Only SIGNAL tracks (primaries) should be used for vertex reconstruction.
    """
    if classification == 'SIGNAL':
        return 1
    return 0


def extract_track_features(hits: np.ndarray) -> np.ndarray:
    """
    Extract 12 features from track hits for Vertex GNN input.

    Features:
    1-3: Spatial extent (dx, dy, dz)
    4-7: PCA shape (elongation_1, elongation_2, sphericity, dominant_mode)
    8: Density (log(n_hits/volume))
    9: Time spread (0 if not available)
    10: x/X0 (0 placeholder)
    11: Highland theta0 estimate
    12: Surface radial position
    """
    if len(hits) < 3:
        return np.zeros(12, dtype=np.float32)

    # Spatial extent
    dx = hits[:, 0].max() - hits[:, 0].min()
    dy = hits[:, 1].max() - hits[:, 1].min()
    dz = hits[:, 2].max() - hits[:, 2].min()

    # Centroid
    centroid = hits.mean(axis=0)

    # PCA for shape analysis
    centered = hits - centroid
    cov = np.cov(centered.T)
    eigvals = np.sort(np.linalg.eigvalsh(cov))[::-1]
    w1, w2, w3 = eigvals[0], eigvals[1], max(eigvals[2], 1e-10)
    total = w1 + w2 + w3 + 1e-10

    elongation_1 = (w1 - w2) / (w1 + 1e-10)
    elongation_2 = (w2 - w3) / (w1 + 1e-10)
    sphericity = w3 / (w1 + 1e-10)
    dominant_mode = w1 / total

    # Density
    volume = max(dx * dy * dz, 1e-6)
    density = np.log(len(hits) / volume)

    # Time spread (placeholder)
    time_std = 0.0

    # Material (placeholder)
    x_over_X0 = 0.0

    # Highland scattering estimate
    track_length = np.sqrt(dx**2 + dy**2 + dz**2)
    X0_argon = 14.0  # cm
    p_estimate = 500.0  # MeV/c assumption
    highland_theta0 = (13.6 / p_estimate) * np.sqrt(max(track_length / X0_argon, 0.1))

    # Radial position
    r_surface = np.sqrt(centroid[0]**2 + centroid[1]**2)

    features = np.array([
        dx, dy, dz,
        elongation_1, elongation_2, sphericity, dominant_mode,
        density, time_std,
        x_over_X0, highland_theta0, r_surface,
    ], dtype=np.float32)

    return features


def project_track_to_z(hits: np.ndarray, z_target: float = 0.0) -> np.ndarray:
    """
    Project track to z=z_target using PCA direction.

    Returns projected (x, y, z) position.
    """
    if len(hits) < 3:
        return np.array([0, 0, z_target], dtype=np.float32)

    centroid = hits.mean(axis=0)
    centered = hits - centroid

    # PCA direction
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    direction = vh[0]

    # Ensure direction has z component
    if abs(direction[2]) < 0.01:
        # Track parallel to z=0, use centroid
        return np.array([centroid[0], centroid[1], z_target], dtype=np.float32)

    # Project to z_target
    t = (z_target - centroid[2]) / direction[2]
    projected = centroid + t * direction

    return projected.astype(np.float32)


def prepare_psignal_dataset(
    tpc_data: pd.DataFrame,
    min_hits: int = 5,
) -> List[TrackSample]:
    """
    Prepare P-Signal training dataset.

    Args:
        tpc_data: TPC hits DataFrame
        min_hits: Minimum hits per track

    Returns:
        List of TrackSample objects
    """
    samples = []

    # Group by event and track
    grouped = tpc_data.groupby(['Event_ID', 'Track_ID'])

    for (event_id, track_id), track_hits in tqdm(grouped, desc="Preparing P-Signal data"):
        if len(track_hits) < min_hits:
            continue

        first_hit = track_hits.iloc[0]

        # Extract info
        parent_id = int(first_hit['Parent_ID'])
        name = str(first_hit['Name'])
        proc = str(first_hit.get('Proc', 'unknown'))
        origin = str(first_hit.get('Origin', 'unknown'))

        # Classify
        classification = classify_track(parent_id, name, proc, origin)
        label = get_binary_label(classification)

        # Extract hit coordinates
        hits = track_hits[['x', 'y', 'z']].values.astype(np.float32)

        samples.append(TrackSample(
            event_id=int(event_id),
            track_id=int(track_id),
            hits=hits,
            label=label,
            particle_name=name,
            parent_id=parent_id,
            n_hits=len(track_hits),
            origin=origin,
            proc=proc,
        ))

    return samples


def prepare_vertex_dataset(
    tpc_data: pd.DataFrame,
    particle_data: pd.DataFrame,
    min_tracks: int = 2,
    max_tracks: int = 20,
    min_hits_per_track: int = 10,
) -> List[VertexSample]:
    """
    Prepare Vertex GNN training dataset.

    Args:
        tpc_data: TPC hits DataFrame
        particle_data: Primary particle DataFrame
        min_tracks: Minimum tracks per event
        max_tracks: Maximum tracks to include
        min_hits_per_track: Minimum hits for track to be included

    Returns:
        List of VertexSample objects
    """
    samples = []

    event_ids = tpc_data['Event_ID'].unique()

    for event_id in tqdm(event_ids, desc="Preparing Vertex data"):
        # Get truth vertex from primary particles
        event_particles = particle_data[particle_data['Event_ID'] == event_id]
        if len(event_particles) == 0:
            continue

        truth_vertex = event_particles[['x', 'y', 'z']].iloc[0].values.astype(np.float32)

        # Get TPC tracks
        event_tpc = tpc_data[tpc_data['Event_ID'] == event_id]

        # Group by track
        tracks = []
        for track_id, track_hits in event_tpc.groupby('Track_ID'):
            if len(track_hits) < min_hits_per_track:
                continue

            # Check if signal track
            first_hit = track_hits.iloc[0]
            classification = classify_track(
                int(first_hit['Parent_ID']),
                str(first_hit['Name']),
                str(first_hit.get('Proc', '')),
                str(first_hit.get('Origin', '')),
            )

            if classification == 'BACKGROUND':
                continue

            hits = track_hits[['x', 'y', 'z']].values

            # Extract features and projected vertex
            features = extract_track_features(hits)
            projected = project_track_to_z(hits, z_target=0.0)

            tracks.append({
                'features': features,
                'position': projected,
            })

        if len(tracks) < min_tracks:
            continue

        # Limit to max_tracks
        if len(tracks) > max_tracks:
            tracks = tracks[:max_tracks]

        n_tracks = len(tracks)

        # Pad to max_tracks
        track_features = np.zeros((max_tracks, 12), dtype=np.float32)
        track_positions = np.zeros((max_tracks, 3), dtype=np.float32)
        track_mask = np.zeros(max_tracks, dtype=bool)

        for i, t in enumerate(tracks):
            track_features[i] = t['features']
            track_positions[i] = t['position']
            track_mask[i] = True

        samples.append(VertexSample(
            event_id=int(event_id),
            track_features=track_features,
            track_positions=track_positions,
            track_mask=track_mask,
            truth_vertex=truth_vertex,
            n_tracks=n_tracks,
        ))

    return samples


def prepare_clustering_labels(
    tpc_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare ground truth clustering labels.

    The true cluster for each hit is defined by Track_ID.
    """
    # Add cluster label (Track_ID is the true cluster)
    labels = tpc_data[['Event_ID', 'Track_ID', 'x', 'y', 'z']].copy()
    labels = labels.rename(columns={'Track_ID': 'true_cluster'})

    return labels


def save_psignal_dataset(samples: List[TrackSample], output_path: Path):
    """Save P-Signal dataset to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as NPZ for efficient loading
    hits_list = []
    labels = []
    metadata = []

    for s in samples:
        hits_list.append(s.hits)
        labels.append(s.label)
        metadata.append({
            'event_id': s.event_id,
            'track_id': s.track_id,
            'particle_name': s.particle_name,
            'parent_id': s.parent_id,
            'n_hits': s.n_hits,
            'origin': s.origin,
            'proc': s.proc,
        })

    # Save hits with variable length
    np.savez_compressed(
        output_path,
        hits=np.array(hits_list, dtype=object),
        labels=np.array(labels, dtype=np.int32),
        metadata=json.dumps(metadata),
    )

    print(f"Saved P-Signal dataset: {len(samples)} samples to {output_path}")

    # Print statistics
    labels_arr = np.array(labels)
    print(f"  Signal (label=1): {(labels_arr == 1).sum()} ({(labels_arr == 1).mean()*100:.1f}%)")
    print(f"  Background (label=0): {(labels_arr == 0).sum()} ({(labels_arr == 0).mean()*100:.1f}%)")


def save_vertex_dataset(samples: List[VertexSample], output_path: Path):
    """Save Vertex GNN dataset to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    track_features = np.stack([s.track_features for s in samples])
    track_positions = np.stack([s.track_positions for s in samples])
    track_masks = np.stack([s.track_mask for s in samples])
    truth_vertices = np.stack([s.truth_vertex for s in samples])
    n_tracks = np.array([s.n_tracks for s in samples])
    event_ids = np.array([s.event_id for s in samples])

    np.savez_compressed(
        output_path,
        track_features=track_features,
        track_positions=track_positions,
        track_masks=track_masks,
        truth_vertices=truth_vertices,
        n_tracks=n_tracks,
        event_ids=event_ids,
    )

    print(f"Saved Vertex dataset: {len(samples)} samples to {output_path}")
    print(f"  Mean tracks per event: {n_tracks.mean():.1f}")
    print(f"  Truth vertex mean: ({truth_vertices.mean(axis=0)})")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Prepare NNBAR reconstruction training data")
    parser.add_argument('--input', '-i', required=True, help='Input directory with Parquet files')
    parser.add_argument('--output', '-o', required=True, help='Output directory for training data')
    parser.add_argument('--split', type=float, default=0.8, help='Train/val split ratio')
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("NNBAR Training Data Preparation")
    print("="*60)

    # Load data
    print("\nLoading TPC data...")
    tpc_data = pd.read_parquet(input_dir / "TPC_output_0.parquet")
    print(f"  {len(tpc_data)} TPC hits loaded")

    print("\nLoading Particle data...")
    particle_data = pd.read_parquet(input_dir / "Particle_output_0.parquet")
    print(f"  {len(particle_data)} primary particles loaded")

    # Prepare P-Signal dataset
    print("\n" + "-"*40)
    print("Preparing P-Signal Dataset...")
    psignal_samples = prepare_psignal_dataset(tpc_data, min_hits=5)

    # Split train/val
    n_train = int(len(psignal_samples) * args.split)
    np.random.seed(42)
    indices = np.random.permutation(len(psignal_samples))
    train_samples = [psignal_samples[i] for i in indices[:n_train]]
    val_samples = [psignal_samples[i] for i in indices[n_train:]]

    save_psignal_dataset(train_samples, output_dir / "psignal_train.npz")
    save_psignal_dataset(val_samples, output_dir / "psignal_val.npz")

    # Prepare Vertex dataset
    print("\n" + "-"*40)
    print("Preparing Vertex GNN Dataset...")
    vertex_samples = prepare_vertex_dataset(tpc_data, particle_data)

    # Split train/val
    n_train = int(len(vertex_samples) * args.split)
    indices = np.random.permutation(len(vertex_samples))
    train_samples = [vertex_samples[i] for i in indices[:n_train]]
    val_samples = [vertex_samples[i] for i in indices[n_train:]]

    save_vertex_dataset(train_samples, output_dir / "vertex_train.npz")
    save_vertex_dataset(val_samples, output_dir / "vertex_val.npz")

    # Prepare clustering labels
    print("\n" + "-"*40)
    print("Preparing Clustering Labels...")
    cluster_labels = prepare_clustering_labels(tpc_data)
    cluster_labels.to_parquet(output_dir / "clustering_labels.parquet")
    print(f"Saved clustering labels: {len(cluster_labels)} hits")

    print("\n" + "="*60)
    print("Training data preparation complete!")
    print(f"Output directory: {output_dir}")
    print("="*60)


if __name__ == "__main__":
    main()
