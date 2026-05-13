#!/usr/bin/env python3
"""
Analyze vertex projection errors to understand the source of resolution limits.

This script examines individual track projections and identifies the key factors
that determine vertex resolution.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nnbar_reconstruction.tracking.clustering import cluster_tpc_hits
from nnbar_reconstruction.tracking.track_fitting import fit_all_tracks, pca_line_fit


def load_data(data_dir: Path):
    """Load simulation data."""
    tpc = pd.read_parquet(data_dir / "TPC_output_0.parquet")
    particle = pd.read_parquet(data_dir / "Particle_output_0.parquet")
    return tpc, particle


def get_truth_vertex(particle_df: pd.DataFrame, event_id: int):
    """Get truth annihilation vertex from primary pions."""
    event_data = particle_df[particle_df['Event_ID'] == event_id]
    pions = event_data[event_data['Name'].isin(['pi+', 'pi-', 'pi0'])]
    if len(pions) == 0:
        return None
    x = pions['x'].mean()
    y = pions['y'].mean()
    z = pions['z'].mean() if 'z' in pions.columns else 0.0
    return np.array([x, y, z])


def analyze_all_events(data_dir: Path, max_events: int = 100):
    """Collect projection error statistics across events."""
    tpc_df, particle_df = load_data(data_dir)

    event_ids = sorted(tpc_df['Event_ID'].unique())[:max_events]

    all_track_errors = []
    all_event_results = []

    for event_id in event_ids:
        event_tpc = tpc_df[tpc_df['Event_ID'] == event_id].copy()
        truth_vertex = get_truth_vertex(particle_df, event_id)

        if truth_vertex is None or len(event_tpc) < 10:
            continue

        # Cluster and fit tracks
        labels, clustered_df = cluster_tpc_hits(event_tpc, use_cartesian=True, eps=2.0)
        tracks = fit_all_tracks(clustered_df, labels, z_target=0.0, relaxed_mode=True)

        if len(tracks) == 0:
            continue

        # Analyze each track's projection
        track_errors = []
        for track in tracks:
            proj = track.vertex_projection
            if proj is not None:
                error = np.sqrt((proj[0] - truth_vertex[0])**2 +
                               (proj[1] - truth_vertex[1])**2)

                # Compute geometric properties
                r_min = track.r_head
                r_vertex = np.sqrt(truth_vertex[0]**2 + truth_vertex[1]**2)
                extrapolation_distance = r_min - r_vertex

                track_errors.append(error)
                all_track_errors.append({
                    'event_id': event_id,
                    'track_id': track.track_id,
                    'error': error,
                    'n_hits': track.n_hits,
                    'length': track.length,
                    'r_min': r_min,
                    'r_max': track.r_tail,
                    'r_vertex': r_vertex,
                    'extrapolation': extrapolation_distance,
                    'linearity': track.linearity,
                    'rms': track.rms_residual,
                })

        # Final vertex - simple average
        if len(track_errors) >= 2:
            projections = np.array([t.vertex_projection for t in tracks if t.vertex_projection is not None])
            vertex = np.mean(projections, axis=0)
            final_error = np.sqrt((vertex[0] - truth_vertex[0])**2 +
                                 (vertex[1] - truth_vertex[1])**2)

            # Method 1: Median-based (robust to outliers)
            median_vertex = np.median(projections, axis=0)
            median_error = np.sqrt((median_vertex[0] - truth_vertex[0])**2 +
                                  (median_vertex[1] - truth_vertex[1])**2)

            # Method 2: Iterative outlier rejection
            iter_projs = projections.copy()
            for _ in range(3):
                if len(iter_projs) < 2:
                    break
                center = np.median(iter_projs, axis=0)
                dists = np.sqrt(np.sum((iter_projs - center)**2, axis=1))
                threshold = np.median(dists) * 2 + 1  # Keep within 2x median distance
                iter_projs = iter_projs[dists < threshold]
            if len(iter_projs) >= 1:
                iter_vertex = np.mean(iter_projs, axis=0)
                iter_error = np.sqrt((iter_vertex[0] - truth_vertex[0])**2 +
                                    (iter_vertex[1] - truth_vertex[1])**2)
            else:
                iter_error = final_error

            all_event_results.append({
                'event_id': event_id,
                'n_tracks': len(tracks),
                'final_error': final_error,
                'median_error': median_error,
                'iter_error': iter_error,
                'min_track_error': min(track_errors),
                'mean_track_error': np.mean(track_errors),
                'r_vertex': r_vertex,
            })

    return pd.DataFrame(all_track_errors), pd.DataFrame(all_event_results)


def main():
    data_dir = Path("/home/billy/nnbar/simulation/NNBAR_Detector/build/output/baseline_reference")

    print("Analyzing projection errors across events...")
    track_df, event_df = analyze_all_events(data_dir, max_events=50)

    print("\n" + "="*60)
    print("TRACK-LEVEL PROJECTION ERROR ANALYSIS")
    print("="*60)

    print(f"\nTotal tracks analyzed: {len(track_df)}")
    print(f"\nProjection error statistics:")
    print(f"  Mean: {track_df['error'].mean():.2f} cm")
    print(f"  Median: {track_df['error'].median():.2f} cm")
    print(f"  Std: {track_df['error'].std():.2f} cm")
    print(f"  Min: {track_df['error'].min():.2f} cm")
    print(f"  Max: {track_df['error'].max():.2f} cm")

    # Distribution
    bins = [0, 2, 5, 10, 20, 50, 100, 1000]
    print(f"\nError distribution:")
    for i in range(len(bins)-1):
        count = ((track_df['error'] >= bins[i]) & (track_df['error'] < bins[i+1])).sum()
        pct = 100 * count / len(track_df)
        print(f"  {bins[i]:3d}-{bins[i+1]:3d} cm: {count:4d} ({pct:5.1f}%)")

    # Correlation with geometric properties
    print(f"\nCorrelation with extrapolation distance: {track_df['error'].corr(track_df['extrapolation']):.3f}")
    print(f"Correlation with track length: {track_df['error'].corr(track_df['length']):.3f}")
    print(f"Correlation with n_hits: {track_df['error'].corr(track_df['n_hits']):.3f}")
    print(f"Correlation with RMS: {track_df['error'].corr(track_df['rms']):.3f}")

    # Good tracks vs bad tracks
    print("\n--- GOOD TRACKS (error < 5cm) ---")
    good = track_df[track_df['error'] < 5]
    print(f"Count: {len(good)}")
    print(f"Mean extrapolation: {good['extrapolation'].mean():.1f} cm")
    print(f"Mean r_min: {good['r_min'].mean():.1f} cm")

    print("\n--- BAD TRACKS (error > 20cm) ---")
    bad = track_df[track_df['error'] > 20]
    print(f"Count: {len(bad)}")
    print(f"Mean extrapolation: {bad['extrapolation'].mean():.1f} cm")
    print(f"Mean r_min: {bad['r_min'].mean():.1f} cm")

    print("\n" + "="*60)
    print("EVENT-LEVEL VERTEX RECONSTRUCTION")
    print("="*60)

    print(f"\nEvents analyzed: {len(event_df)}")

    print(f"\n1. SIMPLE MEAN (baseline):")
    print(f"   Mean error: {event_df['final_error'].mean():.2f} cm")
    print(f"   Median error: {event_df['final_error'].median():.2f} cm")

    print(f"\n2. MEDIAN-BASED (robust to outliers):")
    print(f"   Mean error: {event_df['median_error'].mean():.2f} cm")
    print(f"   Median error: {event_df['median_error'].median():.2f} cm")

    print(f"\n3. ITERATIVE OUTLIER REJECTION:")
    print(f"   Mean error: {event_df['iter_error'].mean():.2f} cm")
    print(f"   Median error: {event_df['iter_error'].median():.2f} cm")

    print(f"\n4. BEST TRACK per event (oracle - upper bound):")
    print(f"   Mean error: {event_df['min_track_error'].mean():.2f} cm")
    print(f"   Median error: {event_df['min_track_error'].median():.2f} cm")

    # Improvement summary
    simple_med = event_df['final_error'].median()
    median_med = event_df['median_error'].median()
    iter_med = event_df['iter_error'].median()
    best_med = event_df['min_track_error'].median()

    print(f"\n" + "-"*40)
    print(f"IMPROVEMENT SUMMARY:")
    print(f"  Baseline (mean):    {simple_med:.2f} cm")
    print(f"  Median-based:       {median_med:.2f} cm  ({(1 - median_med/simple_med)*100:+.1f}%)")
    print(f"  Iterative outlier:  {iter_med:.2f} cm  ({(1 - iter_med/simple_med)*100:+.1f}%)")
    print(f"  Best possible:      {best_med:.2f} cm  ({(1 - best_med/simple_med)*100:+.1f}%)")


if __name__ == "__main__":
    main()
