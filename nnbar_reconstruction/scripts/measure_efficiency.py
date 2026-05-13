#!/usr/bin/env python3
"""
NNBAR Reconstruction Efficiency Measurement

Measures stage-wise reconstruction efficiency:
1. Clustering efficiency: fraction of true track hits correctly clustered
2. Tracking efficiency: fraction of true tracks reconstructed
3. P-Signal efficiency: accuracy of signal vs background classification
4. Vertex efficiency: resolution of annihilation vertex reconstruction

Usage:
    python measure_efficiency.py \
        --data_dir /path/to/simulation/output \
        --psignal_model models/psignal/best.ckpt \
        --max_events 100

Author: NNBAR Collaboration
Date: 2026-01-12
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nnbar_reconstruction.tracking.clustering import (
    cluster_tpc_hits,
)
from nnbar_reconstruction.tracking.track_fitting import (
    fit_all_tracks,
    Track,
)
from nnbar_reconstruction.tracking.signal_separation import (
    load_psignal_model,
    compute_signal_probability,
)
from nnbar_reconstruction.vertex.classical_vertex import (
    reconstruct_vertex,
)


@dataclass
class EfficiencyMetrics:
    """Container for efficiency metrics."""
    n_events: int = 0
    n_true_tracks: int = 0
    n_clusters: int = 0
    n_noise_hits: int = 0
    cluster_purity_mean: float = 0.0
    cluster_completeness_mean: float = 0.0
    n_fitted_tracks: int = 0
    n_matched_tracks: int = 0
    track_efficiency: float = 0.0
    track_fake_rate: float = 0.0
    psignal_accuracy: float = 0.0
    psignal_precision: float = 0.0
    psignal_recall: float = 0.0
    vertex_resolution_xy: float = 0.0
    vertex_resolution_r: float = 0.0
    vertex_bias_x: float = 0.0
    vertex_bias_y: float = 0.0
    n_vertices_reconstructed: int = 0


def load_simulation_data(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load TPC, Interaction, and Particle data."""
    tpc = pd.read_parquet(data_dir / "TPC_output_0.parquet")
    interaction = pd.read_parquet(data_dir / "Interaction_output_0.parquet")
    particle = pd.read_parquet(data_dir / "Particle_output_0.parquet")
    return tpc, interaction, particle


def get_truth_vertex(particle_df: pd.DataFrame, event_id: int) -> Optional[np.ndarray]:
    """Get truth annihilation vertex from primary pions."""
    event_data = particle_df[particle_df['Event_ID'] == event_id]

    # Find primary pions - their position is the annihilation vertex
    pions = event_data[event_data['Name'].isin(['pi+', 'pi-', 'pi0'])]

    if len(pions) == 0:
        return None

    # Use the mean position of pions as vertex
    x = pions['x'].mean()
    y = pions['y'].mean()
    z = pions['z'].mean() if 'z' in pions.columns else 0.0

    return np.array([x, y, z])


def get_true_tracks(
    tpc_df: pd.DataFrame,
    event_id: int,
    min_hits: int = 5,
) -> Dict[int, np.ndarray]:
    """Get true tracks from TPC data."""
    event_data = tpc_df[tpc_df['Event_ID'] == event_id]

    tracks = {}
    for track_id, group in event_data.groupby('Track_ID'):
        if len(group) >= min_hits:
            hits = group[['x', 'y', 'z']].values
            tracks[int(track_id)] = hits

    return tracks


def match_clusters_to_truth(
    labels: np.ndarray,
    track_ids: np.ndarray,
    true_tracks: Dict[int, np.ndarray],
) -> Tuple[float, float]:
    """Match clusters to true tracks and compute purity/completeness."""
    unique_labels = set(labels) - {-1}
    if len(unique_labels) == 0:
        return 0.0, 0.0

    purities = []
    completenesses = []

    for cluster_id in unique_labels:
        cluster_mask = labels == cluster_id
        cluster_track_ids = track_ids[cluster_mask]

        if len(cluster_track_ids) == 0:
            continue

        # Find most common track ID in cluster
        unique_ids, counts = np.unique(cluster_track_ids, return_counts=True)
        dominant_id = int(unique_ids[np.argmax(counts)])
        purity = counts.max() / len(cluster_track_ids)
        purities.append(purity)

        # Completeness: fraction of true track hits in this cluster
        if dominant_id in true_tracks:
            n_true_hits = len(true_tracks[dominant_id])
            n_in_cluster = counts.max()
            completeness = n_in_cluster / n_true_hits
            completenesses.append(completeness)

    mean_purity = np.mean(purities) if purities else 0.0
    mean_completeness = np.mean(completenesses) if completenesses else 0.0

    return mean_purity, mean_completeness


def match_tracks(
    reco_tracks: List[Track],
    true_tracks: Dict[int, np.ndarray],
    distance_threshold: float = 10.0,
) -> Tuple[int, int]:
    """Match reconstructed tracks to true tracks."""
    n_matched = 0
    matched_true_ids = set()

    for track in reco_tracks:
        best_match = None
        best_dist = distance_threshold

        for track_id, true_hits in true_tracks.items():
            if track_id in matched_true_ids:
                continue

            # Compare track center to true track center
            true_center = true_hits.mean(axis=0)
            dist = np.linalg.norm(track.center - true_center)

            if dist < best_dist:
                best_dist = dist
                best_match = track_id

        if best_match is not None:
            n_matched += 1
            matched_true_ids.add(best_match)

    n_fakes = len(reco_tracks) - n_matched
    return n_matched, n_fakes


def process_event(
    event_id: int,
    tpc_df: pd.DataFrame,
    interaction_df: pd.DataFrame,
    particle_df: pd.DataFrame,
) -> Optional[Dict]:
    """Process a single event and return metrics."""
    event_tpc = tpc_df[tpc_df['Event_ID'] == event_id].copy()

    if len(event_tpc) < 10:
        return None

    # Get truth information
    truth_vertex = get_truth_vertex(particle_df, event_id)
    true_tracks = get_true_tracks(tpc_df, event_id)

    # Extract data
    track_ids = event_tpc['Track_ID'].values

    result = {
        'event_id': int(event_id),
        'n_hits': int(len(event_tpc)),
        'n_true_tracks': int(len(true_tracks)),
        'has_truth_vertex': truth_vertex is not None,
    }

    # 1. Clustering
    try:
        labels, clustered_df = cluster_tpc_hits(event_tpc)

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = (labels == -1).sum()

        result['n_clusters'] = n_clusters
        result['n_noise_hits'] = int(n_noise)

        # Match clusters to truth
        if len(true_tracks) > 0:
            purity, completeness = match_clusters_to_truth(labels, track_ids, true_tracks)
            result['cluster_purity'] = purity
            result['cluster_completeness'] = completeness
        else:
            result['cluster_purity'] = 0.0
            result['cluster_completeness'] = 0.0

    except Exception as e:
        print(f"  Event {event_id} clustering failed: {e}")
        return None

    # 2. Track fitting
    try:
        # fit_all_tracks expects a DataFrame
        tracks = fit_all_tracks(clustered_df, labels, relaxed_mode=True)
        result['n_fitted_tracks'] = len(tracks)

        # Match to truth
        if len(true_tracks) > 0 and len(tracks) > 0:
            n_matched, n_fakes = match_tracks(tracks, true_tracks)
            result['n_matched_tracks'] = n_matched
            result['n_fake_tracks'] = n_fakes
            result['track_efficiency'] = n_matched / len(true_tracks)
            result['track_fake_rate'] = n_fakes / len(tracks) if tracks else 0.0
        else:
            result['n_matched_tracks'] = 0
            result['track_efficiency'] = 0.0
            result['track_fake_rate'] = 0.0

    except Exception as e:
        print(f"  Event {event_id} tracking failed: {e}")
        tracks = []
        result['n_fitted_tracks'] = 0
        result['track_efficiency'] = 0.0

    # 3. P-Signal classification (heuristic)
    signal_tracks = []
    if len(tracks) > 0:
        for track in tracks:
            p_signal = compute_signal_probability(track)
            track.p_signal = p_signal
            track.is_signal = p_signal > 0.5
            if track.is_signal:
                signal_tracks.append(track)

        result['n_signal_tracks'] = len(signal_tracks)
        result['n_compton_tracks'] = len(tracks) - len(signal_tracks)
    else:
        result['n_signal_tracks'] = 0
        result['n_compton_tracks'] = 0

    # 4. Vertex reconstruction
    if truth_vertex is not None and len(signal_tracks) >= 2:
        try:
            vertex_result = reconstruct_vertex(signal_tracks)
            if vertex_result is not None:
                reco_vertex = vertex_result.position
                diff = reco_vertex - truth_vertex
                result['vertex_error_x'] = float(diff[0])
                result['vertex_error_y'] = float(diff[1])
                result['vertex_error_r'] = float(np.sqrt(diff[0]**2 + diff[1]**2))
                result['vertex_reconstructed'] = True
            else:
                result['vertex_reconstructed'] = False
        except Exception as e:
            print(f"  Event {event_id} vertex failed: {e}")
            result['vertex_reconstructed'] = False
    else:
        result['vertex_reconstructed'] = False

    return result


def main():
    parser = argparse.ArgumentParser(description="Measure NNBAR reconstruction efficiency")
    parser.add_argument("--data_dir", required=True, help="Directory with simulation output")
    parser.add_argument("--psignal_model", default=None, help="P-Signal model checkpoint")
    parser.add_argument("--max_events", type=int, default=100, help="Max events to process")
    parser.add_argument("--output", default="efficiency_results.json", help="Output JSON file")

    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    # Load P-Signal model if provided
    if args.psignal_model:
        load_psignal_model(args.psignal_model)

    # Load data
    print("Loading simulation data...")
    tpc_df, interaction_df, particle_df = load_simulation_data(data_dir)

    event_ids = sorted(tpc_df['Event_ID'].unique())
    if args.max_events:
        event_ids = event_ids[:args.max_events]

    print(f"Processing {len(event_ids)} events...")

    # Process events
    results = []
    for i, event_id in enumerate(event_ids):
        if (i + 1) % 20 == 0:
            print(f"  Event {i + 1}/{len(event_ids)}")

        result = process_event(event_id, tpc_df, interaction_df, particle_df)
        if result is not None:
            results.append(result)

    # Aggregate metrics
    print("\n" + "=" * 60)
    print("RECONSTRUCTION EFFICIENCY SUMMARY")
    print("=" * 60)

    metrics = EfficiencyMetrics()
    metrics.n_events = len(results)

    if results:
        # Clustering
        metrics.n_true_tracks = sum(r['n_true_tracks'] for r in results)
        metrics.n_clusters = sum(r['n_clusters'] for r in results)
        metrics.n_noise_hits = sum(r['n_noise_hits'] for r in results)
        purities = [r['cluster_purity'] for r in results if r['n_true_tracks'] > 0]
        completenesses = [r['cluster_completeness'] for r in results if r['n_true_tracks'] > 0]
        metrics.cluster_purity_mean = np.mean(purities) if purities else 0.0
        metrics.cluster_completeness_mean = np.mean(completenesses) if completenesses else 0.0

        print(f"\nClustering:")
        print(f"  Total true tracks: {metrics.n_true_tracks}")
        print(f"  Total clusters: {metrics.n_clusters}")
        print(f"  Total noise hits: {metrics.n_noise_hits}")
        print(f"  Mean cluster purity: {metrics.cluster_purity_mean:.3f}")
        print(f"  Mean cluster completeness: {metrics.cluster_completeness_mean:.3f}")

        # Tracking
        metrics.n_fitted_tracks = sum(r['n_fitted_tracks'] for r in results)
        metrics.n_matched_tracks = sum(r.get('n_matched_tracks', 0) for r in results)
        eff_values = [r.get('track_efficiency', 0) for r in results if r.get('n_true_tracks', 0) > 0]
        metrics.track_efficiency = np.mean(eff_values) if eff_values else 0.0
        fake_values = [r.get('track_fake_rate', 0) for r in results if r.get('n_fitted_tracks', 0) > 0]
        metrics.track_fake_rate = np.mean(fake_values) if fake_values else 0.0

        print(f"\nTracking:")
        print(f"  Total fitted tracks: {metrics.n_fitted_tracks}")
        print(f"  Total matched tracks: {metrics.n_matched_tracks}")
        print(f"  Mean track efficiency: {metrics.track_efficiency:.3f}")
        print(f"  Mean fake rate: {metrics.track_fake_rate:.3f}")

        # P-Signal (counts only since we don't have truth labels for signal/compton)
        n_sig = sum(r.get('n_signal_tracks', 0) for r in results)
        n_comp = sum(r.get('n_compton_tracks', 0) for r in results)
        print(f"\nP-Signal Classification:")
        print(f"  Signal tracks identified: {n_sig}")
        print(f"  Compton tracks identified: {n_comp}")

        # Vertex
        vertex_results = [r for r in results if r.get('vertex_reconstructed', False)]
        metrics.n_vertices_reconstructed = len(vertex_results)

        events_with_truth = sum(1 for r in results if r.get('has_truth_vertex', False))

        if vertex_results:
            errors_x = [r['vertex_error_x'] for r in vertex_results]
            errors_y = [r['vertex_error_y'] for r in vertex_results]
            errors_r = [r['vertex_error_r'] for r in vertex_results]

            metrics.vertex_resolution_xy = np.sqrt(np.mean(np.array(errors_x)**2 + np.array(errors_y)**2))
            metrics.vertex_resolution_r = np.mean(errors_r)
            metrics.vertex_bias_x = np.mean(errors_x)
            metrics.vertex_bias_y = np.mean(errors_y)

            print(f"\nVertex Reconstruction:")
            print(f"  Events with truth vertex: {events_with_truth}")
            print(f"  Vertices reconstructed: {metrics.n_vertices_reconstructed}")
            print(f"  Resolution (RMS xy): {metrics.vertex_resolution_xy:.2f} cm")
            print(f"  Mean radial error: {metrics.vertex_resolution_r:.2f} cm")
            print(f"  Bias (x, y): ({metrics.vertex_bias_x:.2f}, {metrics.vertex_bias_y:.2f}) cm")
        else:
            print(f"\nVertex Reconstruction:")
            print(f"  Events with truth vertex: {events_with_truth}")
            print(f"  No vertices reconstructed")

    print("\n" + "=" * 60)

    # Save results
    output = {
        'summary': {
            'n_events': metrics.n_events,
            'clustering': {
                'n_true_tracks': metrics.n_true_tracks,
                'n_clusters': metrics.n_clusters,
                'purity': metrics.cluster_purity_mean,
                'completeness': metrics.cluster_completeness_mean,
            },
            'tracking': {
                'n_fitted_tracks': metrics.n_fitted_tracks,
                'n_matched_tracks': metrics.n_matched_tracks,
                'efficiency': metrics.track_efficiency,
                'fake_rate': metrics.track_fake_rate,
            },
            'vertex': {
                'n_reconstructed': metrics.n_vertices_reconstructed,
                'resolution_xy': metrics.vertex_resolution_xy,
                'mean_radial_error': metrics.vertex_resolution_r,
                'bias_x': metrics.vertex_bias_x,
                'bias_y': metrics.vertex_bias_y,
            },
        },
        'per_event': results,
    }

    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
