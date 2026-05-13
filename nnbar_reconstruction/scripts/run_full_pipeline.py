#!/usr/bin/env python3
"""
NNBAR Full Reconstruction Pipeline

Orchestrates the complete reconstruction chain:
1. Load simulation data (TPC, Scintillator, LeadGlass, Particles)
2. Run TPC clustering
3. Fit tracks (PCA line fit)
4. Classify signal vs background
5. Reconstruct vertex (classical + GNN)
6. Evaluate clustering and vertex reconstruction
7. Save detailed per-event output for debugging

Output structure:
    output_dir/
    ├── clustering_eval/
    │   ├── clustering_summary.csv
    │   ├── clustering_detailed.json
    │   └── problem_events.csv
    ├── vertex_eval/
    │   ├── gnn_summary.json
    │   ├── gnn_residuals.csv
    │   ├── classical_summary.json
    │   └── classical_residuals.csv
    ├── events/
    │   ├── event_0001.json
    │   ├── event_0002.json
    │   └── ...
    └── pipeline_summary.json

Usage:
    python run_full_pipeline.py --input /path/to/simulation --output /path/to/output
    python run_full_pipeline.py --help
"""

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from tqdm import tqdm
import datetime
import sys
import traceback

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nnbar_reconstruction.utils.data_loader import (
    load_parquet_files,
    load_event_data,
    EventData,
)
from nnbar_reconstruction.tracking.clustering import cluster_tpc_hits
from nnbar_reconstruction.tracking.track_fitting import fit_all_tracks, Track
from nnbar_reconstruction.tracking.evaluate_clustering import (
    evaluate_event_clustering,
    save_detailed_report as save_clustering_report,
    print_clustering_summary,
    EventClusteringResult,
)
from nnbar_reconstruction.vertex.classical_vertex import (
    weighted_vertex_reconstruction,
    VertexResult,
)
from nnbar_reconstruction.vertex.evaluate_vertex import (
    evaluate_vertex_reconstruction,
    compare_methods,
    save_vertex_report,
    print_vertex_summary,
    print_comparison_summary,
)
from nnbar_reconstruction.training.prepare_training_data import classify_track


@dataclass
class EventReconstruction:
    """Complete reconstruction result for a single event."""
    event_id: int

    # Input summary
    n_tpc_hits: int
    n_true_tracks: int
    n_scint_hits: int
    n_calo_hits: int
    total_scint_energy: float
    total_calo_energy: float

    # Truth
    truth_vertex: np.ndarray

    # Clustering
    n_clusters: int
    n_noise_hits: int
    cluster_purity: float
    cluster_efficiency: float
    cluster_ari: float

    # Track fitting
    n_fitted_tracks: int
    n_signal_tracks: int
    fitted_track_ids: List[int]

    # Vertex (classical)
    classical_vertex: np.ndarray
    classical_n_tracks: int
    classical_chi2: float

    # Vertex (GNN) - optional
    gnn_vertex: Optional[np.ndarray] = None
    gnn_attention_weights: Optional[np.ndarray] = None

    # Errors
    error_messages: List[str] = None

    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        def to_native(x):
            """Convert numpy types to native Python types."""
            if isinstance(x, (np.integer,)):
                return int(x)
            elif isinstance(x, (np.floating,)):
                return float(x)
            elif isinstance(x, np.ndarray):
                return x.tolist()
            elif isinstance(x, list):
                return [to_native(i) for i in x]
            return x

        d = {
            'event_id': to_native(self.event_id),
            'n_tpc_hits': to_native(self.n_tpc_hits),
            'n_true_tracks': to_native(self.n_true_tracks),
            'n_scint_hits': to_native(self.n_scint_hits),
            'n_calo_hits': to_native(self.n_calo_hits),
            'total_scint_energy': float(self.total_scint_energy),
            'total_calo_energy': float(self.total_calo_energy),
            'truth_vertex': self.truth_vertex.tolist() if self.truth_vertex is not None else None,
            'n_clusters': to_native(self.n_clusters),
            'n_noise_hits': to_native(self.n_noise_hits),
            'cluster_purity': float(self.cluster_purity),
            'cluster_efficiency': float(self.cluster_efficiency),
            'cluster_ari': float(self.cluster_ari),
            'n_fitted_tracks': to_native(self.n_fitted_tracks),
            'n_signal_tracks': to_native(self.n_signal_tracks),
            'fitted_track_ids': to_native(self.fitted_track_ids),
            'classical_vertex': self.classical_vertex.tolist() if self.classical_vertex is not None else None,
            'classical_n_tracks': to_native(self.classical_n_tracks),
            'classical_chi2': float(self.classical_chi2) if np.isfinite(self.classical_chi2) else None,
            'error_messages': self.error_messages,
        }

        if self.gnn_vertex is not None:
            d['gnn_vertex'] = self.gnn_vertex.tolist()
        if self.gnn_attention_weights is not None:
            d['gnn_attention_weights'] = self.gnn_attention_weights.tolist()

        return d


def get_truth_vertex(particle_data: pd.DataFrame, event_id: int) -> Optional[np.ndarray]:
    """Extract truth vertex from particle data.

    The particle data contains primary particles from annihilation.
    The vertex (x, y, z) is the origin point of these particles.
    """
    if particle_data is None or len(particle_data) == 0:
        return None

    event_particles = particle_data[particle_data['Event_ID'] == event_id]

    if len(event_particles) == 0:
        return None

    # In this data format, the (x, y, z) columns are the vertex position
    # All primary particles share the same vertex
    if 'x' in event_particles.columns:
        x = event_particles['x'].iloc[0]
        y = event_particles['y'].iloc[0]
        z = event_particles['z'].iloc[0]
        return np.array([x, y, z])

    # If columns are named differently
    if 'vx' in event_particles.columns:
        vx = event_particles['vx'].iloc[0]
        vy = event_particles['vy'].iloc[0]
        vz = event_particles['vz'].iloc[0]
        return np.array([vx, vy, vz])

    return np.array([0.0, 0.0, 0.0])  # Default to target center


def filter_signal_tracks(tracks: List[Track], tpc_data: pd.DataFrame) -> List[Track]:
    """Filter tracks to keep only signal tracks for vertex reconstruction.

    Signal tracks are primary charged pions (Parent_ID=0, Name='pi+' or 'pi-').
    """
    signal_tracks = []

    # Check if we have the required columns
    has_parent_id = 'Parent_ID' in tpc_data.columns
    has_name = 'Name' in tpc_data.columns
    has_cluster_id = 'cluster_id' in tpc_data.columns

    if not has_cluster_id:
        # If no cluster labels, return all tracks with quality cuts
        return [t for t in tracks if t.n_hits >= 10 and t.length >= 5] or tracks

    for track in tracks:
        if track.track_id < 0:
            continue

        # Get hits for this cluster
        cluster_mask = tpc_data['cluster_id'] == track.track_id
        if cluster_mask.sum() == 0:
            continue

        cluster_data = tpc_data[cluster_mask].iloc[0]

        # If we have truth info, use it to classify
        if has_parent_id and has_name:
            parent_id = cluster_data.get('Parent_ID', -1)
            name = cluster_data.get('Name', '')
            proc = cluster_data.get('Proc', '')
            origin = cluster_data.get('Origin', '')

            classification = classify_track(parent_id, name, proc, origin)
            if classification == 'SIGNAL':
                signal_tracks.append(track)
        else:
            # Without truth info, include all tracks with sufficient quality
            # (This is the case in real data)
            if track.n_hits >= 10 and track.length >= 5:
                signal_tracks.append(track)

    return signal_tracks if signal_tracks else tracks


def process_single_event(
    event_data: EventData,
    include_gnn: bool = False,
    gnn_model=None,
) -> EventReconstruction:
    """
    Process a single event through the full reconstruction pipeline.

    Args:
        event_data: EventData container with all detector data
        include_gnn: Whether to run GNN vertex reconstruction
        gnn_model: Trained GNN model (required if include_gnn=True)

    Returns:
        EventReconstruction with all results
    """
    errors = []
    event_id = event_data.event_id
    tpc_data = event_data.tpc.copy()

    # Get truth vertex
    truth_vertex = None
    if event_data.particles is not None:
        truth_vertex = get_truth_vertex(event_data.particles, event_id)

    if truth_vertex is None:
        truth_vertex = np.array([0.0, 0.0, 0.0])
        errors.append("Could not determine truth vertex, using (0,0,0)")

    # Count inputs
    n_tpc_hits = len(tpc_data)
    n_true_tracks = len(tpc_data['Track_ID'].unique()) if 'Track_ID' in tpc_data.columns else 0
    n_scint_hits = len(event_data.scintillator)
    n_calo_hits = len(event_data.leadglass)

    # Handle empty events
    if n_tpc_hits == 0:
        return EventReconstruction(
            event_id=event_id,
            n_tpc_hits=0,
            n_true_tracks=0,
            n_scint_hits=n_scint_hits,
            n_calo_hits=n_calo_hits,
            total_scint_energy=event_data.total_scint_energy,
            total_calo_energy=event_data.total_calo_energy,
            truth_vertex=truth_vertex,
            n_clusters=0,
            n_noise_hits=0,
            cluster_purity=0.0,
            cluster_efficiency=0.0,
            cluster_ari=0.0,
            n_fitted_tracks=0,
            n_signal_tracks=0,
            fitted_track_ids=[],
            classical_vertex=np.array([0.0, 0.0, 0.0]),
            classical_n_tracks=0,
            classical_chi2=np.inf,
            error_messages=["No TPC hits in event"],
        )

    # Step 1: Clustering
    try:
        # Use explicit parameters to avoid config file dependency
        pred_labels, clustered_data = cluster_tpc_hits(
            tpc_data,
            phi_weight=5.0,
            z_weight=1.0,
            min_samples=3,
            eps=2.0,
            use_cartesian=True,
        )
        tpc_data = clustered_data

        n_clusters = len(set(pred_labels) - {-1})
        n_noise_hits = int((pred_labels == -1).sum())

        # Evaluate clustering
        if 'Track_ID' in tpc_data.columns:
            true_labels = tpc_data['Track_ID'].values
            cluster_result = evaluate_event_clustering(event_id, pred_labels, true_labels)
            cluster_purity = cluster_result.metrics.purity
            cluster_efficiency = cluster_result.metrics.efficiency
            cluster_ari = cluster_result.metrics.ari
        else:
            # No truth labels available
            cluster_purity = 0.0
            cluster_efficiency = 0.0
            cluster_ari = 0.0
            errors.append("No Track_ID column for clustering evaluation")

    except Exception as e:
        errors.append(f"Clustering failed: {str(e)}")
        n_clusters = 0
        n_noise_hits = n_tpc_hits
        cluster_purity = 0.0
        cluster_efficiency = 0.0
        cluster_ari = 0.0
        pred_labels = np.full(n_tpc_hits, -1)

    # Step 2: Track fitting
    try:
        labels = tpc_data['cluster_id'].values if 'cluster_id' in tpc_data.columns else pred_labels
        tracks = fit_all_tracks(tpc_data, labels, z_target=0.0, min_hits=3)
        n_fitted_tracks = len(tracks)
        fitted_track_ids = [t.track_id for t in tracks]
    except Exception as e:
        errors.append(f"Track fitting failed: {str(e)}")
        tracks = []
        n_fitted_tracks = 0
        fitted_track_ids = []

    # Step 3: Signal classification
    try:
        signal_tracks = filter_signal_tracks(tracks, tpc_data)
        n_signal_tracks = len(signal_tracks)
    except Exception as e:
        errors.append(f"Signal classification failed: {str(e)}")
        signal_tracks = tracks  # Use all tracks
        n_signal_tracks = len(tracks)

    # Step 4: Classical vertex reconstruction
    try:
        if len(signal_tracks) > 0:
            vertex_result = weighted_vertex_reconstruction(signal_tracks, target_z=0.0)
            classical_vertex = vertex_result.position
            classical_n_tracks = vertex_result.n_tracks
            classical_chi2 = vertex_result.chi2
        else:
            classical_vertex = np.array([0.0, 0.0, 0.0])
            classical_n_tracks = 0
            classical_chi2 = np.inf
            errors.append("No signal tracks for vertex reconstruction")
    except Exception as e:
        errors.append(f"Classical vertex failed: {str(e)}")
        classical_vertex = np.array([0.0, 0.0, 0.0])
        classical_n_tracks = 0
        classical_chi2 = np.inf

    # Step 5: GNN vertex (optional)
    gnn_vertex = None
    gnn_attention_weights = None

    if include_gnn and gnn_model is not None:
        try:
            # Prepare GNN input (would need proper feature extraction)
            # This is a placeholder - full implementation would use prepare_training_data
            pass
        except Exception as e:
            errors.append(f"GNN vertex failed: {str(e)}")

    return EventReconstruction(
        event_id=event_id,
        n_tpc_hits=n_tpc_hits,
        n_true_tracks=n_true_tracks,
        n_scint_hits=n_scint_hits,
        n_calo_hits=n_calo_hits,
        total_scint_energy=event_data.total_scint_energy,
        total_calo_energy=event_data.total_calo_energy,
        truth_vertex=truth_vertex,
        n_clusters=n_clusters,
        n_noise_hits=n_noise_hits,
        cluster_purity=cluster_purity,
        cluster_efficiency=cluster_efficiency,
        cluster_ari=cluster_ari,
        n_fitted_tracks=n_fitted_tracks,
        n_signal_tracks=n_signal_tracks,
        fitted_track_ids=fitted_track_ids,
        classical_vertex=classical_vertex,
        classical_n_tracks=classical_n_tracks,
        classical_chi2=classical_chi2,
        gnn_vertex=gnn_vertex,
        gnn_attention_weights=gnn_attention_weights,
        error_messages=errors if errors else None,
    )


def run_full_pipeline(
    input_dir: Path,
    output_dir: Path,
    max_events: Optional[int] = None,
    include_gnn: bool = False,
    save_per_event: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Run the full reconstruction pipeline on all events.

    Args:
        input_dir: Directory with simulation parquet files
        output_dir: Directory for output files
        max_events: Maximum number of events to process (None = all)
        include_gnn: Whether to run GNN vertex reconstruction
        save_per_event: Whether to save detailed per-event JSON files
        verbose: Whether to print progress

    Returns:
        Dictionary with summary statistics
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create output subdirectories
    clustering_dir = output_dir / 'clustering_eval'
    vertex_dir = output_dir / 'vertex_eval'
    events_dir = output_dir / 'events'

    clustering_dir.mkdir(exist_ok=True)
    vertex_dir.mkdir(exist_ok=True)
    if save_per_event:
        events_dir.mkdir(exist_ok=True)

    # Load data
    if verbose:
        print(f"Loading simulation data from: {input_dir}")

    data = load_parquet_files(input_dir)
    tpc_data = data.get('tpc', pd.DataFrame())
    particle_data = data.get('particles', None)

    if len(tpc_data) == 0:
        raise ValueError(f"No TPC data found in {input_dir}")

    event_ids = sorted(tpc_data['Event_ID'].unique())

    if max_events:
        event_ids = event_ids[:max_events]

    if verbose:
        print(f"Processing {len(event_ids)} events...")

    # Process events
    results = []
    clustering_results = []
    classical_vertices = []
    truth_vertices = []
    event_ids_processed = []

    for event_id in tqdm(event_ids, disable=not verbose):
        # Load event data
        event_data = load_event_data(data, event_id)

        # Process event
        try:
            result = process_single_event(event_data, include_gnn=include_gnn)
            results.append(result)

            # Collect for evaluation
            if result.truth_vertex is not None:
                truth_vertices.append(result.truth_vertex)
                classical_vertices.append(result.classical_vertex)
                event_ids_processed.append(event_id)

            # Save per-event JSON
            if save_per_event:
                event_file = events_dir / f'event_{event_id:06d}.json'
                with open(event_file, 'w') as f:
                    json.dump(result.to_dict(), f, indent=2)

        except Exception as e:
            if verbose:
                print(f"Error processing event {event_id}: {e}")
            traceback.print_exc()

    # Create summary dataframe
    summary_rows = []
    for r in results:
        row = r.to_dict()
        # Flatten arrays for CSV
        if row['truth_vertex']:
            row['truth_x'] = row['truth_vertex'][0]
            row['truth_y'] = row['truth_vertex'][1]
            row['truth_z'] = row['truth_vertex'][2]
        if row['classical_vertex']:
            row['classical_x'] = row['classical_vertex'][0]
            row['classical_y'] = row['classical_vertex'][1]
            row['classical_z'] = row['classical_vertex'][2]
        del row['truth_vertex']
        del row['classical_vertex']
        if 'gnn_vertex' in row:
            del row['gnn_vertex']
        if 'gnn_attention_weights' in row:
            del row['gnn_attention_weights']
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)

    # Save clustering summary
    clustering_summary_path = clustering_dir / 'clustering_metrics.csv'
    clustering_df = summary_df[['event_id', 'cluster_purity', 'cluster_efficiency', 'cluster_ari',
                                 'n_clusters', 'n_noise_hits', 'n_true_tracks']].copy()
    clustering_df.to_csv(clustering_summary_path, index=False)

    # Evaluate vertex reconstruction
    if len(truth_vertices) > 0:
        truth_arr = np.array(truth_vertices)
        classical_arr = np.array(classical_vertices)
        event_ids_arr = np.array(event_ids_processed)

        # Classical vertex evaluation
        classical_metrics, classical_residuals = evaluate_vertex_reconstruction(
            classical_arr, truth_arr, event_ids_arr
        )
        save_vertex_report(classical_metrics, classical_residuals, vertex_dir, 'classical')

        if verbose:
            print_vertex_summary(classical_metrics, "Classical Vertex")

    # Compute overall statistics
    stats = {
        'generated_at': datetime.datetime.now().isoformat(),
        'input_dir': str(input_dir),
        'output_dir': str(output_dir),
        'n_events_total': len(event_ids),
        'n_events_processed': len(results),
        'n_events_with_errors': sum(1 for r in results if r.error_messages),

        # Clustering stats
        'mean_cluster_purity': float(summary_df['cluster_purity'].mean()),
        'mean_cluster_efficiency': float(summary_df['cluster_efficiency'].mean()),
        'mean_cluster_ari': float(summary_df['cluster_ari'].mean()),

        # Track stats
        'mean_n_clusters': float(summary_df['n_clusters'].mean()),
        'mean_n_fitted_tracks': float(summary_df['n_fitted_tracks'].mean()),
        'mean_n_signal_tracks': float(summary_df['n_signal_tracks'].mean()),

        # Energy stats
        'mean_scint_energy': float(summary_df['total_scint_energy'].mean()),
        'mean_calo_energy': float(summary_df['total_calo_energy'].mean()),
    }

    if len(truth_vertices) > 0:
        stats['vertex_resolution_x'] = float(classical_metrics.resolution_x)
        stats['vertex_resolution_y'] = float(classical_metrics.resolution_y)
        stats['vertex_resolution_z'] = float(classical_metrics.resolution_z)
        stats['vertex_resolution_3d'] = float(classical_metrics.resolution_3d)

    # Save pipeline summary
    summary_path = output_dir / 'pipeline_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(stats, f, indent=2)

    # Save full event summary
    summary_df.to_csv(output_dir / 'event_summary.csv', index=False)

    if verbose:
        print("\n" + "=" * 60)
        print("PIPELINE SUMMARY")
        print("=" * 60)
        print(f"Events processed: {stats['n_events_processed']}")
        print(f"Events with errors: {stats['n_events_with_errors']}")
        print()
        print("Clustering:")
        print(f"  Mean purity:     {stats['mean_cluster_purity']:.3f}")
        print(f"  Mean efficiency: {stats['mean_cluster_efficiency']:.3f}")
        print(f"  Mean ARI:        {stats['mean_cluster_ari']:.3f}")
        print()
        if 'vertex_resolution_x' in stats:
            print("Vertex Resolution (RMS) [cm]:")
            print(f"  X: {stats['vertex_resolution_x']:.2f}")
            print(f"  Y: {stats['vertex_resolution_y']:.2f}")
            print(f"  Z: {stats['vertex_resolution_z']:.2f}")
            print(f"  3D: {stats['vertex_resolution_3d']:.2f}")
        print()
        print(f"Output saved to: {output_dir}")
        print("=" * 60)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Run full NNBAR reconstruction pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
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
        default=Path('/home/billy/nnbar/simulation/nnbar_reconstruction/output/pipeline_run'),
        help='Output directory for results'
    )

    parser.add_argument(
        '--max-events', '-n',
        type=int,
        default=None,
        help='Maximum number of events to process (default: all)'
    )

    parser.add_argument(
        '--no-per-event',
        action='store_true',
        help='Skip saving per-event JSON files (faster)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )

    args = parser.parse_args()

    run_full_pipeline(
        input_dir=args.input,
        output_dir=args.output,
        max_events=args.max_events,
        save_per_event=not args.no_per_event,
        verbose=not args.quiet,
    )


if __name__ == '__main__':
    main()
