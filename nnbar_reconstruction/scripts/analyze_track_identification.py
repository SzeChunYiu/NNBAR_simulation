#!/usr/bin/env python3
"""
Track Identification Analysis for NNBAR Reconstruction

Analyzes how well tracks are identified, focusing on:
1. Primary vs secondary particle separation
2. Per-event track breakdown
3. Track quality vs particle type
4. Recommendations for improvement

Usage:
    python analyze_track_identification.py --input /path/to/simulation --output /path/to/analysis
"""

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict
from tqdm import tqdm
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nnbar_reconstruction.utils.data_loader import load_parquet_files, load_event_data
from nnbar_reconstruction.tracking.clustering import cluster_tpc_hits
from nnbar_reconstruction.tracking.track_fitting import fit_all_tracks
from nnbar_reconstruction.training.prepare_training_data import classify_track


@dataclass
class TrackAnalysis:
    """Detailed analysis of a single track."""
    event_id: int
    cluster_id: int  # Predicted cluster
    true_track_id: int  # True Track_ID from simulation
    n_hits: int
    particle_name: str
    parent_id: int
    is_primary: bool  # Parent_ID == 0
    is_signal: bool  # Primary charged pion
    classification: str  # SIGNAL, BACKGROUND
    purity: float  # Fraction of cluster from this track
    efficiency: float  # Fraction of track in this cluster
    hit_positions: Optional[np.ndarray] = None  # For visualization


@dataclass
class EventTrackSummary:
    """Summary of track identification for one event."""
    event_id: int
    n_tpc_hits: int
    n_true_tracks: int
    n_predicted_clusters: int
    n_noise_hits: int

    # Primary tracks
    n_primary_tracks: int
    n_primary_correctly_identified: int
    n_primary_fragmented: int  # Split into multiple clusters
    n_primary_merged: int  # Merged with other tracks

    # Secondary tracks
    n_secondary_tracks: int
    n_secondary_correctly_identified: int
    n_secondary_fragmented: int
    n_secondary_merged: int

    # Signal tracks (charged pions with parent_id=0)
    n_signal_tracks: int
    n_signal_correctly_identified: int

    # Quality metrics
    mean_purity: float
    mean_efficiency: float

    track_details: List[Dict]


def analyze_event_tracks(
    event_id: int,
    tpc_data: pd.DataFrame,
    pred_labels: np.ndarray,
) -> EventTrackSummary:
    """
    Analyze track identification for a single event.

    Args:
        event_id: Event identifier
        tpc_data: TPC hits with truth labels
        pred_labels: Predicted cluster labels

    Returns:
        EventTrackSummary with detailed track analysis
    """
    n_tpc_hits = len(tpc_data)
    n_noise = int((pred_labels == -1).sum())

    # Get unique clusters and tracks
    unique_clusters = set(pred_labels) - {-1}
    unique_tracks = tpc_data['Track_ID'].unique()

    n_predicted_clusters = len(unique_clusters)
    n_true_tracks = len(unique_tracks)

    # Analyze each true track
    track_details = []

    primary_tracks = 0
    primary_correct = 0
    primary_fragmented = 0
    primary_merged = 0

    secondary_tracks = 0
    secondary_correct = 0
    secondary_fragmented = 0
    secondary_merged = 0

    signal_tracks = 0
    signal_correct = 0

    purities = []
    efficiencies = []

    for track_id in unique_tracks:
        track_mask = tpc_data['Track_ID'] == track_id
        track_hits = tpc_data[track_mask]
        track_pred_labels = pred_labels[track_mask.values]

        n_hits = len(track_hits)
        if n_hits == 0:
            continue

        # Get particle info
        first_hit = track_hits.iloc[0]
        particle_name = first_hit.get('Name', 'unknown')
        parent_id = first_hit.get('Parent_ID', -1)

        is_primary = (parent_id == 0)
        classification = classify_track(
            parent_id,
            particle_name,
            first_hit.get('Proc', ''),
            first_hit.get('Origin', '')
        )
        is_signal = (classification == 'SIGNAL')

        # Count cluster assignments
        cluster_counts = Counter(track_pred_labels)
        non_noise_clusters = {k: v for k, v in cluster_counts.items() if k >= 0}

        if non_noise_clusters:
            best_cluster, best_count = max(non_noise_clusters.items(), key=lambda x: x[1])
            efficiency = best_count / n_hits
        else:
            best_cluster = -1
            best_count = 0
            efficiency = 0.0

        # Check if track is fragmented (split into multiple clusters)
        n_clusters_assigned = len(non_noise_clusters)
        is_fragmented = n_clusters_assigned > 1

        # Check if track's best cluster also contains other tracks (merged)
        if best_cluster >= 0:
            cluster_mask = pred_labels == best_cluster
            cluster_hits = tpc_data[cluster_mask]
            cluster_tracks = cluster_hits['Track_ID'].unique()
            is_merged = len(cluster_tracks) > 1

            # Purity: what fraction of the cluster is from this track?
            purity = best_count / cluster_mask.sum()
        else:
            is_merged = False
            purity = 0.0

        purities.append(purity)
        efficiencies.append(efficiency)

        # Correctly identified = high purity AND high efficiency
        is_correct = (purity > 0.8 and efficiency > 0.8)

        # Update counters
        if is_primary:
            primary_tracks += 1
            if is_correct:
                primary_correct += 1
            if is_fragmented:
                primary_fragmented += 1
            if is_merged:
                primary_merged += 1
        else:
            secondary_tracks += 1
            if is_correct:
                secondary_correct += 1
            if is_fragmented:
                secondary_fragmented += 1
            if is_merged:
                secondary_merged += 1

        if is_signal:
            signal_tracks += 1
            if is_correct:
                signal_correct += 1

        track_details.append({
            'track_id': int(track_id),
            'cluster_id': int(best_cluster),
            'n_hits': int(n_hits),
            'particle_name': particle_name,
            'parent_id': int(parent_id),
            'is_primary': is_primary,
            'is_signal': is_signal,
            'classification': classification,
            'purity': float(purity),
            'efficiency': float(efficiency),
            'n_clusters_assigned': int(n_clusters_assigned),
            'is_fragmented': is_fragmented,
            'is_merged': is_merged,
            'is_correctly_identified': is_correct,
        })

    return EventTrackSummary(
        event_id=event_id,
        n_tpc_hits=n_tpc_hits,
        n_true_tracks=n_true_tracks,
        n_predicted_clusters=n_predicted_clusters,
        n_noise_hits=n_noise,
        n_primary_tracks=primary_tracks,
        n_primary_correctly_identified=primary_correct,
        n_primary_fragmented=primary_fragmented,
        n_primary_merged=primary_merged,
        n_secondary_tracks=secondary_tracks,
        n_secondary_correctly_identified=secondary_correct,
        n_secondary_fragmented=secondary_fragmented,
        n_secondary_merged=secondary_merged,
        n_signal_tracks=signal_tracks,
        n_signal_correctly_identified=signal_correct,
        mean_purity=float(np.mean(purities)) if purities else 0.0,
        mean_efficiency=float(np.mean(efficiencies)) if efficiencies else 0.0,
        track_details=track_details,
    )


def run_track_analysis(
    input_dir: Path,
    output_dir: Path,
    max_events: Optional[int] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Run track identification analysis on all events.

    Args:
        input_dir: Directory with simulation parquet files
        output_dir: Directory for output files
        max_events: Maximum number of events to process
        verbose: Whether to print progress

    Returns:
        Summary statistics
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    if verbose:
        print(f"Loading simulation data from: {input_dir}")

    data = load_parquet_files(input_dir)
    tpc_data = data.get('tpc', pd.DataFrame())

    if len(tpc_data) == 0:
        raise ValueError(f"No TPC data found in {input_dir}")

    event_ids = sorted(tpc_data['Event_ID'].unique())

    if max_events:
        event_ids = event_ids[:max_events]

    if verbose:
        print(f"Analyzing {len(event_ids)} events...")

    # Process events
    all_summaries = []
    all_track_details = []

    # Aggregate statistics
    particle_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'fragmented': 0, 'merged': 0})

    for event_id in tqdm(event_ids, disable=not verbose):
        # Get event TPC data
        event_mask = tpc_data['Event_ID'] == event_id
        event_data = tpc_data[event_mask].copy()

        if len(event_data) == 0:
            continue

        # Run clustering
        pred_labels, clustered_data = cluster_tpc_hits(
            event_data,
            phi_weight=5.0,
            z_weight=1.0,
            min_samples=3,
            eps=2.0,
            use_cartesian=True,
        )

        # Analyze tracks
        summary = analyze_event_tracks(event_id, event_data, pred_labels)
        all_summaries.append(summary)

        # Aggregate track details
        for track in summary.track_details:
            all_track_details.append(track)

            # Update particle stats
            pname = track['particle_name']
            particle_stats[pname]['total'] += 1
            if track['is_correctly_identified']:
                particle_stats[pname]['correct'] += 1
            if track['is_fragmented']:
                particle_stats[pname]['fragmented'] += 1
            if track['is_merged']:
                particle_stats[pname]['merged'] += 1

    # Create summary DataFrame
    summary_data = []
    for s in all_summaries:
        row = {
            'event_id': s.event_id,
            'n_tpc_hits': s.n_tpc_hits,
            'n_true_tracks': s.n_true_tracks,
            'n_predicted_clusters': s.n_predicted_clusters,
            'n_noise_hits': s.n_noise_hits,
            'n_primary_tracks': s.n_primary_tracks,
            'n_primary_correctly_identified': s.n_primary_correctly_identified,
            'n_secondary_tracks': s.n_secondary_tracks,
            'n_secondary_correctly_identified': s.n_secondary_correctly_identified,
            'n_signal_tracks': s.n_signal_tracks,
            'n_signal_correctly_identified': s.n_signal_correctly_identified,
            'mean_purity': s.mean_purity,
            'mean_efficiency': s.mean_efficiency,
        }
        summary_data.append(row)

    summary_df = pd.DataFrame(summary_data)
    track_df = pd.DataFrame(all_track_details)

    # Save outputs
    summary_df.to_csv(output_dir / 'event_summary.csv', index=False)
    track_df.to_csv(output_dir / 'track_details.csv', index=False)

    # Create particle type analysis
    particle_analysis = []
    for pname, stats in sorted(particle_stats.items(), key=lambda x: -x[1]['total']):
        total = stats['total']
        particle_analysis.append({
            'particle': pname,
            'total': total,
            'correct': stats['correct'],
            'correct_rate': stats['correct'] / total if total > 0 else 0,
            'fragmented': stats['fragmented'],
            'fragmented_rate': stats['fragmented'] / total if total > 0 else 0,
            'merged': stats['merged'],
            'merged_rate': stats['merged'] / total if total > 0 else 0,
        })

    particle_df = pd.DataFrame(particle_analysis)
    particle_df.to_csv(output_dir / 'particle_type_analysis.csv', index=False)

    # Compute overall statistics
    total_primary = summary_df['n_primary_tracks'].sum()
    total_primary_correct = summary_df['n_primary_correctly_identified'].sum()
    total_secondary = summary_df['n_secondary_tracks'].sum()
    total_secondary_correct = summary_df['n_secondary_correctly_identified'].sum()
    total_signal = summary_df['n_signal_tracks'].sum()
    total_signal_correct = summary_df['n_signal_correctly_identified'].sum()

    stats = {
        'n_events': len(all_summaries),
        'total_tracks': len(all_track_details),

        'primary_tracks': int(total_primary),
        'primary_correct': int(total_primary_correct),
        'primary_correct_rate': total_primary_correct / total_primary if total_primary > 0 else 0,

        'secondary_tracks': int(total_secondary),
        'secondary_correct': int(total_secondary_correct),
        'secondary_correct_rate': total_secondary_correct / total_secondary if total_secondary > 0 else 0,

        'signal_tracks': int(total_signal),
        'signal_correct': int(total_signal_correct),
        'signal_correct_rate': total_signal_correct / total_signal if total_signal > 0 else 0,

        'mean_purity': float(summary_df['mean_purity'].mean()),
        'mean_efficiency': float(summary_df['mean_efficiency'].mean()),
    }

    # Save stats
    with open(output_dir / 'analysis_summary.json', 'w') as f:
        json.dump(stats, f, indent=2)

    # Print summary
    if verbose:
        print("\n" + "=" * 70)
        print("TRACK IDENTIFICATION ANALYSIS")
        print("=" * 70)
        print(f"Events analyzed: {stats['n_events']}")
        print(f"Total tracks: {stats['total_tracks']}")
        print()
        print("PRIMARY TRACKS (Parent_ID=0):")
        print(f"  Total: {stats['primary_tracks']}")
        print(f"  Correctly identified: {stats['primary_correct']} ({stats['primary_correct_rate']*100:.1f}%)")
        print()
        print("SECONDARY TRACKS (Parent_ID>0):")
        print(f"  Total: {stats['secondary_tracks']}")
        print(f"  Correctly identified: {stats['secondary_correct']} ({stats['secondary_correct_rate']*100:.1f}%)")
        print()
        print("SIGNAL TRACKS (Primary pi+, pi-):")
        print(f"  Total: {stats['signal_tracks']}")
        print(f"  Correctly identified: {stats['signal_correct']} ({stats['signal_correct_rate']*100:.1f}%)")
        print()
        print("OVERALL:")
        print(f"  Mean purity: {stats['mean_purity']*100:.1f}%")
        print(f"  Mean efficiency: {stats['mean_efficiency']*100:.1f}%")
        print()
        print("PARTICLE TYPE BREAKDOWN:")
        print("-" * 70)
        print(f"{'Particle':<15} {'Total':>8} {'Correct':>10} {'Correct%':>10} {'Fragmented%':>12}")
        print("-" * 70)
        for row in particle_analysis[:10]:  # Top 10
            p = row['particle']
            print(f"{p:<15} {row['total']:>8} {row['correct']:>10} "
                  f"{row['correct_rate']*100:>9.1f}% {row['fragmented_rate']*100:>11.1f}%")
        print("=" * 70)
        print(f"Output saved to: {output_dir}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Analyze track identification in NNBAR reconstruction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--input', '-i',
        type=Path,
        default=Path('/home/billy/nnbar/simulation/NNBAR_Detector/build/output/baseline_reference'),
        help='Input directory with simulation parquet files'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('/home/billy/nnbar/simulation/nnbar_reconstruction/output/track_analysis'),
        help='Output directory for analysis results'
    )

    parser.add_argument(
        '--max-events', '-n',
        type=int,
        default=None,
        help='Maximum number of events to process (default: all)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )

    args = parser.parse_args()

    run_track_analysis(
        input_dir=args.input,
        output_dir=args.output,
        max_events=args.max_events,
        verbose=not args.quiet,
    )


if __name__ == '__main__':
    main()
