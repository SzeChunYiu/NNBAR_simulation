#!/usr/bin/env python3
"""
NNBAR Event Reconstruction - 500 Signal Events Analysis

Runs the full GPU-accelerated reconstruction chain on 500 signal events
from the HIBEAM simulation data.

Author: NNBAR Collaboration
"""

import sys
import os
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Initialize GPU backend early
from nnbar_reconstruction.utils.gpu_backend import get_backend
gpu = get_backend()
print(f"\n{'='*60}")
print("NNBAR Event Reconstruction - GPU-Accelerated")
print(f"{'='*60}")
print(f"GPU Available: {gpu.use_gpu}")
print(f"cuML Available: {gpu.has_cuml}")
print(f"cuDF Available: {gpu.has_cudf}")
print(f"{'='*60}\n")

from nnbar_reconstruction.tracking.clustering import cluster_tpc_hits, _use_gpu_clustering
from nnbar_reconstruction.tracking.track_fitting import fit_all_tracks, Track, pca_line_fit
from nnbar_reconstruction.vertex.classical_vertex import reconstruct_vertex


def load_hibeam_data(data_dir: str, n_events: int = 500) -> pd.DataFrame:
    """
    Load HIBEAM pulse data from parquet files.

    Args:
        data_dir: Path to pulses directory.
        n_events: Number of events to load.

    Returns:
        Combined DataFrame with all pulse data.
    """
    pulse_files = sorted(Path(data_dir).glob("pulses_*.parquet"))

    all_data = []
    events_loaded = 0

    for pf in pulse_files:
        df = pd.read_parquet(pf)

        # Filter to first n_events
        unique_events = df['event_id'].unique()
        remaining = n_events - events_loaded

        if remaining <= 0:
            break

        events_to_take = unique_events[:remaining]
        df_subset = df[df['event_id'].isin(events_to_take)]
        all_data.append(df_subset)

        events_loaded += len(events_to_take)

        if events_loaded >= n_events:
            break

    combined = pd.concat(all_data, ignore_index=True)
    print(f"Loaded {combined['event_id'].nunique()} events with {len(combined)} total hits")

    return combined


def load_truth_data(truth_dir: str) -> pd.DataFrame:
    """
    Load truth vertex data.

    Args:
        truth_dir: Path to truth directory.

    Returns:
        DataFrame with truth vertex positions.
    """
    truth_files = sorted(Path(truth_dir).glob("truth_*.parquet"))

    all_truth = []
    for tf in truth_files:
        df = pd.read_parquet(tf)
        all_truth.append(df)

    if all_truth:
        return pd.concat(all_truth, ignore_index=True)
    return pd.DataFrame()


def reconstruct_event_hibeam(
    event_id: int,
    hits: pd.DataFrame,
    truth_vertex: np.ndarray = None,
) -> dict:
    """
    Reconstruct a single event from HIBEAM pulse data.

    The data format uses:
    - dom_x, dom_y, dom_z: TPC hit positions
    - dom_t: Hit time
    - track_id: True track ID (for validation)
    - signal_bkg: 1 for signal, 0 for background

    Args:
        event_id: Event ID.
        hits: DataFrame with TPC hits for this event.
        truth_vertex: Truth vertex position [x, y, z] (optional).

    Returns:
        Dictionary with reconstruction results.
    """
    result = {
        'event_id': event_id,
        'success': False,
        'n_hits': len(hits),
    }

    if len(hits) < 5:
        result['reason'] = 'too_few_hits'
        return result

    # Prepare data for clustering (rename columns to standard format)
    tpc_data = hits.rename(columns={
        'dom_x': 'x',
        'dom_y': 'y',
        'dom_z': 'z',
        'dom_t': 't',
    }).copy()

    # Store truth track IDs for validation
    true_track_ids = hits['track_id'].values

    # 1. TPC Clustering (GPU-accelerated)
    try:
        labels, tpc_clustered = cluster_tpc_hits(tpc_data, refine=True)
    except Exception as e:
        result['reason'] = f'clustering_failed: {str(e)}'
        return result

    n_clusters = len(set(labels) - {-1})
    result['n_clusters'] = n_clusters
    result['n_noise'] = np.sum(labels == -1)

    if n_clusters == 0:
        result['reason'] = 'no_clusters'
        return result

    # 2. Track Fitting (GPU-accelerated)
    try:
        tracks = fit_all_tracks(tpc_clustered, labels, z_target=0.0)
    except Exception as e:
        result['reason'] = f'track_fitting_failed: {str(e)}'
        return result

    result['n_tracks'] = len(tracks)

    if len(tracks) == 0:
        result['reason'] = 'no_tracks'
        return result

    # 3. Compute clustering quality metrics
    # Compare reconstructed clusters to true track IDs
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

    # Filter out noise points
    valid_mask = labels >= 0
    if valid_mask.sum() > 0:
        ari = adjusted_rand_score(true_track_ids[valid_mask], labels[valid_mask])
        nmi = normalized_mutual_info_score(true_track_ids[valid_mask], labels[valid_mask])
        result['clustering_ari'] = ari
        result['clustering_nmi'] = nmi

    # 4. Vertex Reconstruction
    # Use all tracks with good quality
    good_tracks = [t for t in tracks if t.linearity > 0.9 and t.length > 10]

    if len(good_tracks) < 2:
        good_tracks = tracks[:min(len(tracks), 5)]  # Use best 5 tracks

    try:
        vertex_result = reconstruct_vertex(good_tracks, method='weighted', signal_only=False)
        result['vertex_valid'] = vertex_result.is_valid
        result['vertex_x'] = vertex_result.position[0]
        result['vertex_y'] = vertex_result.position[1]
        result['vertex_z'] = vertex_result.position[2]
        result['vertex_r'] = vertex_result.r
        result['n_tracks_to_vertex'] = vertex_result.n_tracks
    except Exception as e:
        result['vertex_valid'] = False
        result['vertex_error'] = str(e)

    # 5. Compare to truth vertex
    if truth_vertex is not None and result.get('vertex_valid', False):
        residual = np.linalg.norm(vertex_result.position - truth_vertex)
        result['vertex_residual'] = residual
        result['truth_x'] = truth_vertex[0]
        result['truth_y'] = truth_vertex[1]
        result['truth_z'] = truth_vertex[2]

        # Categorize reconstruction quality
        if residual < 1.0:
            result['reco_quality'] = 'excellent'
        elif residual < 5.0:
            result['reco_quality'] = 'good'
        elif residual < 20.0:
            result['reco_quality'] = 'fair'
        else:
            result['reco_quality'] = 'poor'

    # 6. Track-level metrics
    track_lengths = [t.length for t in tracks]
    track_linearity = [t.linearity for t in tracks]
    track_rms = [t.rms_residual for t in tracks]

    result['mean_track_length'] = np.mean(track_lengths) if track_lengths else 0
    result['mean_linearity'] = np.mean(track_linearity) if track_linearity else 0
    result['mean_rms'] = np.mean(track_rms) if track_rms else 0
    result['max_track_length'] = np.max(track_lengths) if track_lengths else 0

    # 7. True track statistics
    n_true_tracks = len(hits['track_id'].unique())
    n_signal_tracks = hits[hits['signal_bkg'] == 1]['track_id'].nunique()
    result['n_true_tracks'] = n_true_tracks
    result['n_signal_tracks'] = n_signal_tracks

    result['success'] = True

    return result


def run_reconstruction_500():
    """
    Run reconstruction on 500 signal events.
    """
    # Data paths
    base_dir = Path("/home/billy/nnbar/simulation/HIBEAM_Clustering_and_Vertex/data")
    data_dir = base_dir / "inference" / "signal100k_compton2_251208"
    pulse_dir = data_dir / "pulses"
    truth_dir = data_dir / "truth"

    # Output directory
    output_dir = Path("/home/billy/nnbar/simulation/nnbar_reconstruction/output")
    output_dir.mkdir(exist_ok=True)

    # Load data
    print("Loading pulse data...")
    pulse_data = load_hibeam_data(pulse_dir, n_events=500)

    print("Loading truth data...")
    truth_data = load_truth_data(truth_dir)

    # Create truth lookup
    truth_lookup = {}
    if len(truth_data) > 0 and 'event_id' in truth_data.columns:
        for _, row in truth_data.iterrows():
            event_id = row['event_id']
            if 'vertex_x' in truth_data.columns:
                truth_lookup[event_id] = np.array([
                    row['vertex_x'],
                    row['vertex_y'],
                    row['vertex_z']
                ])

    # Get unique events
    event_ids = sorted(pulse_data['event_id'].unique())
    print(f"\nReconstrucing {len(event_ids)} events...")
    print(f"Using GPU clustering: {_use_gpu_clustering()}")

    # Reconstruct events
    results = []
    start_time = time.time()

    for event_id in tqdm(event_ids, desc="Reconstructing"):
        event_hits = pulse_data[pulse_data['event_id'] == event_id].copy()

        truth_vertex = truth_lookup.get(event_id)

        result = reconstruct_event_hibeam(event_id, event_hits, truth_vertex)
        results.append(result)

    elapsed = time.time() - start_time

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Save results
    output_file = output_dir / "reconstruction_500_events.parquet"
    df.to_parquet(output_file, index=False)

    # Print summary
    print("\n" + "="*60)
    print("RECONSTRUCTION SUMMARY")
    print("="*60)

    n_total = len(df)
    n_success = df['success'].sum()

    print(f"Total events:     {n_total}")
    print(f"Successful:       {n_success} ({100*n_success/n_total:.1f}%)")
    print(f"Time elapsed:     {elapsed:.1f} s ({elapsed/n_total*1000:.1f} ms/event)")

    if 'n_tracks' in df.columns:
        print(f"\nTrack statistics:")
        print(f"  Mean tracks:    {df['n_tracks'].mean():.1f}")
        print(f"  Mean clusters:  {df['n_clusters'].mean():.1f}")

    if 'clustering_ari' in df.columns:
        print(f"\nClustering quality:")
        print(f"  Mean ARI:       {df['clustering_ari'].mean():.3f}")
        print(f"  Mean NMI:       {df['clustering_nmi'].mean():.3f}")

    if 'vertex_residual' in df.columns:
        residuals = df.loc[df['vertex_valid'] == True, 'vertex_residual']
        if len(residuals) > 0:
            print(f"\nVertex reconstruction:")
            print(f"  Valid vertices: {len(residuals)} ({100*len(residuals)/n_total:.1f}%)")
            print(f"  Mean residual:  {residuals.mean():.2f} cm")
            print(f"  Median:         {residuals.median():.2f} cm")
            print(f"  < 1 cm:         {(residuals < 1).sum()} ({100*(residuals < 1).sum()/len(residuals):.1f}%)")
            print(f"  < 5 cm:         {(residuals < 5).sum()} ({100*(residuals < 5).sum()/len(residuals):.1f}%)")
            print(f"  > 20 cm:        {(residuals > 20).sum()} ({100*(residuals > 20).sum()/len(residuals):.1f}%)")

    if 'reco_quality' in df.columns:
        print(f"\nReconstruction quality breakdown:")
        for qual in ['excellent', 'good', 'fair', 'poor']:
            count = (df['reco_quality'] == qual).sum()
            if count > 0:
                print(f"  {qual.capitalize():12} {count} ({100*count/n_total:.1f}%)")

    print(f"\nResults saved to: {output_file}")
    print("="*60)

    return df


if __name__ == "__main__":
    df = run_reconstruction_500()
