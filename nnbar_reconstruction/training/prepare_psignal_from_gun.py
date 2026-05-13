#!/usr/bin/env python3
"""
Prepare P-Signal Training Data from Particle Gun Simulations

This script processes output from single particle gun simulations to create
training data for the P-Signal classifier.

Signal data: pi+, pi-, proton from origin (label=1)
Background data: Compton electrons from TPC surface (label=0)

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
import argparse


@dataclass
class TrackSample:
    """Training sample for P-Signal classifier."""
    event_id: int
    track_id: int
    hits: np.ndarray  # (N, 3) coordinates
    label: int  # 1 = signal, 0 = background
    particle_name: str
    n_hits: int
    source: str  # 'signal_pip', 'signal_pim', 'signal_proton', 'background_compton'


def load_tpc_data(data_dir: Path) -> pd.DataFrame:
    """Load TPC hits from parquet files in a directory."""
    parquet_files = list(data_dir.glob("TPC_output_*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No TPC parquet files found in {data_dir}")

    dfs = []
    for f in sorted(parquet_files):
        df = pd.read_parquet(f)
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def extract_tracks(tpc_data: pd.DataFrame, min_hits: int = 5) -> List[Dict]:
    """Extract individual tracks from TPC data."""
    tracks = []

    # Group by event and track
    grouped = tpc_data.groupby(['Event_ID', 'Track_ID'])

    for (event_id, track_id), track_hits in grouped:
        if len(track_hits) < min_hits:
            continue

        # Extract hit coordinates
        hits = track_hits[['x', 'y', 'z']].values.astype(np.float32)

        # Get particle info
        first_hit = track_hits.iloc[0]
        particle_name = str(first_hit.get('Name', 'unknown'))

        tracks.append({
            'event_id': int(event_id),
            'track_id': int(track_id),
            'hits': hits,
            'particle_name': particle_name,
            'n_hits': len(hits),
        })

    return tracks


def process_signal_data(data_dir: Path, source_name: str, min_hits: int = 5) -> List[TrackSample]:
    """Process signal particle gun data."""
    print(f"  Processing {source_name}...")

    tpc_data = load_tpc_data(data_dir)
    tracks = extract_tracks(tpc_data, min_hits=min_hits)

    samples = []
    for t in tracks:
        samples.append(TrackSample(
            event_id=t['event_id'],
            track_id=t['track_id'],
            hits=t['hits'],
            label=1,  # Signal
            particle_name=t['particle_name'],
            n_hits=t['n_hits'],
            source=source_name,
        ))

    print(f"    Extracted {len(samples)} signal tracks")
    return samples


def process_background_data(data_dir: Path, source_name: str, min_hits: int = 5) -> List[TrackSample]:
    """Process background (Compton electron) data."""
    print(f"  Processing {source_name}...")

    tpc_data = load_tpc_data(data_dir)
    tracks = extract_tracks(tpc_data, min_hits=min_hits)

    samples = []
    for t in tracks:
        samples.append(TrackSample(
            event_id=t['event_id'],
            track_id=t['track_id'],
            hits=t['hits'],
            label=0,  # Background
            particle_name=t['particle_name'],
            n_hits=t['n_hits'],
            source=source_name,
        ))

    print(f"    Extracted {len(samples)} background tracks")
    return samples


def save_dataset(samples: List[TrackSample], output_path: Path):
    """Save dataset to NPZ format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

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
            'n_hits': s.n_hits,
            'source': s.source,
        })

    np.savez_compressed(
        output_path,
        hits=np.array(hits_list, dtype=object),
        labels=np.array(labels, dtype=np.int32),
        metadata=json.dumps(metadata),
    )

    print(f"Saved dataset: {len(samples)} samples to {output_path}")

    labels_arr = np.array(labels)
    print(f"  Signal (label=1): {(labels_arr == 1).sum()} ({(labels_arr == 1).mean()*100:.1f}%)")
    print(f"  Background (label=0): {(labels_arr == 0).sum()} ({(labels_arr == 0).mean()*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Prepare P-Signal training data from particle gun simulations")
    parser.add_argument('--input', '-i', default='/home/billy/nnbar/simulation/training_data/psignal_raw',
                        help='Input directory with particle gun output')
    parser.add_argument('--output', '-o', default='/home/billy/nnbar/simulation/training_data',
                        help='Output directory for training data')
    parser.add_argument('--min-hits', type=int, default=5, help='Minimum hits per track')
    parser.add_argument('--split', type=float, default=0.8, help='Train/val split ratio')
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    print("=" * 60)
    print("P-Signal Training Data Preparation (Particle Gun)")
    print("=" * 60)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Min hits per track: {args.min_hits}")
    print(f"Train/val split: {args.split:.0%}/{1-args.split:.0%}")
    print()

    # Process signal data
    print("Loading Signal Data:")
    signal_samples = []

    signal_dirs = [
        ('signal_pip', 'signal_pip'),
        ('signal_pim', 'signal_pim'),
        ('signal_proton', 'signal_proton'),
    ]

    for dir_name, source_name in signal_dirs:
        data_path = input_dir / dir_name
        if data_path.exists():
            samples = process_signal_data(data_path, source_name, min_hits=args.min_hits)
            signal_samples.extend(samples)
        else:
            print(f"  WARNING: {data_path} not found, skipping")

    # Process background data
    print("\nLoading Background Data:")
    background_samples = []

    background_path = input_dir / 'background_compton'
    if background_path.exists():
        background_samples = process_background_data(background_path, 'background_compton', min_hits=args.min_hits)
    else:
        print(f"  WARNING: {background_path} not found, skipping")

    # Combine and shuffle
    all_samples = signal_samples + background_samples
    print(f"\nTotal samples: {len(all_samples)}")
    print(f"  Signal: {len(signal_samples)}")
    print(f"  Background: {len(background_samples)}")

    if len(all_samples) == 0:
        print("ERROR: No samples found!")
        return

    # Split train/val
    np.random.seed(42)
    indices = np.random.permutation(len(all_samples))
    n_train = int(len(all_samples) * args.split)

    train_samples = [all_samples[i] for i in indices[:n_train]]
    val_samples = [all_samples[i] for i in indices[n_train:]]

    print(f"\nSplit: {len(train_samples)} train, {len(val_samples)} val")

    # Save datasets
    print("\nSaving datasets:")
    save_dataset(train_samples, output_dir / "psignal_gun_train.npz")
    save_dataset(val_samples, output_dir / "psignal_gun_val.npz")

    print("\n" + "=" * 60)
    print("P-Signal training data preparation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
