#!/usr/bin/env python3
"""
Diagnostic script to investigate vertex reconstruction errors.

Examines individual events to understand where projection errors come from.
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


def get_particle_info(particle_df: pd.DataFrame, event_id: int, track_id: int):
    """Get particle info for a track (if available)."""
    # Particle dataframe may not have track ID mapping
    return None, None, None


def analyze_event(event_id: int, tpc_df: pd.DataFrame, particle_df: pd.DataFrame):
    """Analyze a single event in detail."""
    print(f"\n{'='*60}")
    print(f"EVENT {event_id} ANALYSIS")
    print(f"{'='*60}")

    # Get event data
    event_tpc = tpc_df[tpc_df['Event_ID'] == event_id].copy()
    truth_vertex = get_truth_vertex(particle_df, event_id)

    print(f"\nTruth vertex: {truth_vertex}")
    print(f"Total hits: {len(event_tpc)}")

    # Get true track IDs
    true_track_ids = event_tpc['Track_ID'].unique()
    print(f"True tracks: {len(true_track_ids)}")

    # Analyze each true track
    print("\n--- TRUE TRACK ANALYSIS ---")
    for track_id in true_track_ids:
        track_hits = event_tpc[event_tpc['Track_ID'] == track_id]
        if len(track_hits) < 5:
            continue

        points = track_hits[['x', 'y', 'z']].values

        # Get particle info
        name, parent, origin = get_particle_info(particle_df, event_id, track_id)

        # Fit the true track
        try:
            fit = pca_line_fit(points, z_target=0.0)

            # Compare vertex projection to truth
            proj = fit['vertex']
            if proj is not None and truth_vertex is not None:
                error = np.sqrt((proj[0] - truth_vertex[0])**2 +
                               (proj[1] - truth_vertex[1])**2)

                print(f"\nTrue Track {track_id}:")
                print(f"  Hits: {len(track_hits)}")
                print(f"  Z range: {points[:,2].min():.1f} to {points[:,2].max():.1f}")
                print(f"  R range: {np.sqrt(points[:,0]**2 + points[:,1]**2).min():.1f} to {np.sqrt(points[:,0]**2 + points[:,1]**2).max():.1f}")
                print(f"  Linear fit projection: ({proj[0]:.2f}, {proj[1]:.2f}, {proj[2]:.2f})")
                print(f"  Projection error: {error:.2f} cm")

                # Also check PCA direction projection
                direction = fit['direction']
                head = fit['head']
                # Project from head in -direction to z=0
                if abs(direction[2]) > 0.01:
                    t = (0.0 - head[2]) / (-direction[2])
                    pca_proj = head + (-direction) * t
                    pca_error = np.sqrt((pca_proj[0] - truth_vertex[0])**2 +
                                       (pca_proj[1] - truth_vertex[1])**2)
                    print(f"  PCA projection: ({pca_proj[0]:.2f}, {pca_proj[1]:.2f}, {pca_proj[2]:.2f})")
                    print(f"  PCA error: {pca_error:.2f} cm")

        except Exception as e:
            print(f"  Track {track_id}: fit failed - {e}")

    # Now do clustering
    print("\n--- CLUSTERING ANALYSIS ---")
    labels, clustered_df = cluster_tpc_hits(event_tpc, use_cartesian=True, eps=2.0)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    print(f"Clusters found: {n_clusters}")
    print(f"Noise hits: {n_noise}")

    # Check cluster-to-track mapping
    print("\nCluster composition:")
    for cluster_id in sorted(set(labels)):
        if cluster_id == -1:
            continue
        cluster_mask = labels == cluster_id
        cluster_track_ids = event_tpc.iloc[np.where(cluster_mask)[0]]['Track_ID'].values
        unique_ids, counts = np.unique(cluster_track_ids, return_counts=True)
        print(f"  Cluster {cluster_id}: {sum(cluster_mask)} hits, from tracks {dict(zip(unique_ids, counts))}")

    # Fit tracks from clusters
    print("\n--- RECONSTRUCTED TRACK ANALYSIS ---")
    tracks = fit_all_tracks(clustered_df, labels, z_target=0.0, relaxed_mode=True)

    print(f"Fitted tracks: {len(tracks)}")

    for track in tracks:
        proj = track.vertex_projection
        if proj is not None and truth_vertex is not None:
            error = np.sqrt((proj[0] - truth_vertex[0])**2 +
                           (proj[1] - truth_vertex[1])**2)
            print(f"\nTrack {track.track_id}:")
            print(f"  Hits: {track.n_hits}")
            print(f"  Length: {track.length:.1f} cm")
            print(f"  RMS residual: {track.rms_residual:.3f} cm")
            print(f"  Linearity: {track.linearity:.3f}")
            print(f"  Head: ({track.head[0]:.1f}, {track.head[1]:.1f}, {track.head[2]:.1f})")
            print(f"  Vertex projection: ({proj[0]:.2f}, {proj[1]:.2f}, {proj[2]:.2f})")
            print(f"  Projection error: {error:.2f} cm")

    # Compute final vertex
    if len(tracks) >= 2:
        projections = []
        for track in tracks:
            if track.vertex_projection is not None:
                projections.append(track.vertex_projection)

        if len(projections) >= 2:
            projections = np.array(projections)
            vertex = np.mean(projections, axis=0)
            if truth_vertex is not None:
                final_error = np.sqrt((vertex[0] - truth_vertex[0])**2 +
                                     (vertex[1] - truth_vertex[1])**2)
                print(f"\n--- FINAL VERTEX ---")
                print(f"Reconstructed: ({vertex[0]:.2f}, {vertex[1]:.2f}, {vertex[2]:.2f})")
                print(f"Truth: ({truth_vertex[0]:.2f}, {truth_vertex[1]:.2f}, {truth_vertex[2]:.2f})")
                print(f"Final error: {final_error:.2f} cm")

    return


def main():
    data_dir = Path("/home/billy/nnbar/simulation/NNBAR_Detector/build/output/baseline_reference")

    print("Loading data...")
    tpc_df, particle_df = load_data(data_dir)

    # Get events with reasonable number of hits
    event_ids = sorted(tpc_df['Event_ID'].unique())

    # Analyze first few events in detail
    for i, event_id in enumerate(event_ids[:5]):
        event_tpc = tpc_df[tpc_df['Event_ID'] == event_id]
        if len(event_tpc) >= 20:
            analyze_event(event_id, tpc_df, particle_df)


if __name__ == "__main__":
    main()
