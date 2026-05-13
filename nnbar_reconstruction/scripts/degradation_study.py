#!/usr/bin/env python3
"""
NNBAR Reconstruction Degradation Study

Studies how reconstruction performance degrades under various conditions:
1. Hit position resolution (Gaussian smearing)
2. Hit efficiency (random hit dropping)
3. Noise hits (random background hits)
4. Combined effects

Usage:
    python degradation_study.py \
        --data_dir /path/to/simulation/output \
        --output_dir degradation_results

Author: NNBAR Collaboration
Date: 2026-01-12
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import time

import numpy as np
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nnbar_reconstruction.tracking.clustering import cluster_tpc_hits
from nnbar_reconstruction.tracking.track_fitting import fit_all_tracks, Track
from nnbar_reconstruction.tracking.signal_separation import compute_signal_probability
from nnbar_reconstruction.vertex.classical_vertex import reconstruct_vertex


@dataclass
class DegradationConfig:
    """Configuration for a degradation scenario."""
    name: str
    position_smear_cm: float = 0.0  # Gaussian sigma for position smearing
    hit_efficiency: float = 1.0     # Fraction of hits to keep (1.0 = all)
    noise_hits_per_event: int = 0   # Number of random noise hits to add
    description: str = ""


@dataclass
class DegradationResult:
    """Results from a degradation scenario."""
    config_name: str
    n_events: int
    # Clustering
    cluster_purity: float
    cluster_completeness: float
    n_clusters_per_event: float
    # Tracking
    track_efficiency: float
    track_fake_rate: float
    n_tracks_per_event: float
    # Vertex
    vertex_reco_rate: float
    vertex_resolution_r: float
    vertex_bias_r: float


def apply_position_smearing(
    tpc_df: pd.DataFrame,
    sigma_cm: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Apply Gaussian smearing to hit positions."""
    if sigma_cm <= 0:
        return tpc_df

    df = tpc_df.copy()
    n_hits = len(df)

    df['x'] = df['x'] + rng.normal(0, sigma_cm, n_hits)
    df['y'] = df['y'] + rng.normal(0, sigma_cm, n_hits)
    df['z'] = df['z'] + rng.normal(0, sigma_cm, n_hits)

    return df


def apply_hit_efficiency(
    tpc_df: pd.DataFrame,
    efficiency: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Randomly drop hits to simulate detector inefficiency."""
    if efficiency >= 1.0:
        return tpc_df

    mask = rng.random(len(tpc_df)) < efficiency
    return tpc_df[mask].copy()


def add_noise_hits(
    tpc_df: pd.DataFrame,
    n_noise: int,
    event_id: int,
    rng: np.random.Generator,
    r_min: float = 115.0,  # TPC inner radius
    r_max: float = 200.0,  # TPC outer radius
    z_min: float = -150.0,
    z_max: float = 150.0,
) -> pd.DataFrame:
    """Add random noise hits to the TPC data."""
    if n_noise <= 0:
        return tpc_df

    # Generate random positions in cylindrical coordinates
    r = np.sqrt(rng.uniform(r_min**2, r_max**2, n_noise))
    phi = rng.uniform(0, 2 * np.pi, n_noise)
    z = rng.uniform(z_min, z_max, n_noise)

    x = r * np.cos(phi)
    y = r * np.sin(phi)

    # Create noise DataFrame with required columns
    noise_df = pd.DataFrame({
        'Event_ID': event_id,
        'Track_ID': -1,  # Mark as noise
        'x': x,
        'y': y,
        'z': z,
    })

    # Add other columns with default values
    for col in tpc_df.columns:
        if col not in noise_df.columns:
            if tpc_df[col].dtype == np.float64:
                noise_df[col] = 0.0
            elif tpc_df[col].dtype == np.int64:
                noise_df[col] = 0
            else:
                noise_df[col] = tpc_df[col].iloc[0] if len(tpc_df) > 0 else None

    # Reorder columns to match
    noise_df = noise_df[tpc_df.columns]

    return pd.concat([tpc_df, noise_df], ignore_index=True)


def get_truth_vertex(particle_df: pd.DataFrame, event_id: int) -> Optional[np.ndarray]:
    """Get truth annihilation vertex from primary pions."""
    event_data = particle_df[particle_df['Event_ID'] == event_id]
    pions = event_data[event_data['Name'].isin(['pi+', 'pi-', 'pi0'])]

    if len(pions) == 0:
        return None

    return np.array([pions['x'].mean(), pions['y'].mean(), 0.0])


def get_true_tracks(tpc_df: pd.DataFrame, event_id: int, min_hits: int = 5) -> Dict[int, np.ndarray]:
    """Get true tracks from TPC data."""
    event_data = tpc_df[tpc_df['Event_ID'] == event_id]
    tracks = {}
    for track_id, group in event_data.groupby('Track_ID'):
        if track_id >= 0 and len(group) >= min_hits:  # Exclude noise (track_id=-1)
            tracks[int(track_id)] = group[['x', 'y', 'z']].values
    return tracks


def match_clusters_to_truth(
    labels: np.ndarray,
    track_ids: np.ndarray,
    true_tracks: Dict[int, np.ndarray],
) -> Tuple[float, float]:
    """Match clusters to true tracks."""
    unique_labels = set(labels) - {-1}
    if len(unique_labels) == 0 or len(true_tracks) == 0:
        return 0.0, 0.0

    purities = []
    completenesses = []

    for cluster_id in unique_labels:
        cluster_mask = labels == cluster_id
        cluster_track_ids = track_ids[cluster_mask]
        # Exclude noise hits
        cluster_track_ids = cluster_track_ids[cluster_track_ids >= 0]

        if len(cluster_track_ids) == 0:
            continue

        unique_ids, counts = np.unique(cluster_track_ids, return_counts=True)
        dominant_id = int(unique_ids[np.argmax(counts)])
        purity = counts.max() / len(cluster_track_ids)
        purities.append(purity)

        if dominant_id in true_tracks:
            n_true = len(true_tracks[dominant_id])
            completeness = counts.max() / n_true
            completenesses.append(completeness)

    return np.mean(purities) if purities else 0.0, np.mean(completenesses) if completenesses else 0.0


def match_tracks(
    reco_tracks: List[Track],
    true_tracks: Dict[int, np.ndarray],
    threshold: float = 10.0,
) -> Tuple[int, int]:
    """Match reconstructed to true tracks."""
    if not reco_tracks or not true_tracks:
        return 0, len(reco_tracks)

    matched = set()
    for track in reco_tracks:
        for tid, hits in true_tracks.items():
            if tid in matched:
                continue
            if np.linalg.norm(track.center - hits.mean(axis=0)) < threshold:
                matched.add(tid)
                break

    return len(matched), len(reco_tracks) - len(matched)


def process_event_with_degradation(
    event_id: int,
    tpc_df: pd.DataFrame,
    particle_df: pd.DataFrame,
    config: DegradationConfig,
    rng: np.random.Generator,
) -> Optional[Dict]:
    """Process single event with degradation applied."""
    event_tpc = tpc_df[tpc_df['Event_ID'] == event_id].copy()

    if len(event_tpc) < 10:
        return None

    # Get truth before degradation
    truth_vertex = get_truth_vertex(particle_df, event_id)
    true_tracks = get_true_tracks(tpc_df, event_id)
    original_track_ids = event_tpc['Track_ID'].values.copy()

    # Apply degradations
    degraded_tpc = event_tpc

    # 1. Position smearing
    if config.position_smear_cm > 0:
        degraded_tpc = apply_position_smearing(degraded_tpc, config.position_smear_cm, rng)

    # 2. Hit efficiency
    if config.hit_efficiency < 1.0:
        degraded_tpc = apply_hit_efficiency(degraded_tpc, config.hit_efficiency, rng)
        # Update track_ids to match remaining hits
        original_track_ids = degraded_tpc['Track_ID'].values

    # 3. Add noise
    if config.noise_hits_per_event > 0:
        degraded_tpc = add_noise_hits(degraded_tpc, config.noise_hits_per_event, event_id, rng)
        # Pad track_ids with -1 for noise hits
        n_noise = len(degraded_tpc) - len(original_track_ids)
        original_track_ids = np.concatenate([original_track_ids, np.full(n_noise, -1)])

    if len(degraded_tpc) < 10:
        return None

    result = {
        'event_id': int(event_id),
        'n_hits_original': len(event_tpc),
        'n_hits_degraded': len(degraded_tpc),
        'n_true_tracks': len(true_tracks),
    }

    # Clustering
    try:
        labels, clustered_df = cluster_tpc_hits(degraded_tpc)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

        result['n_clusters'] = n_clusters

        if len(true_tracks) > 0:
            purity, completeness = match_clusters_to_truth(labels, original_track_ids, true_tracks)
            result['cluster_purity'] = purity
            result['cluster_completeness'] = completeness
        else:
            result['cluster_purity'] = 0.0
            result['cluster_completeness'] = 0.0
    except Exception as e:
        return None

    # Track fitting
    try:
        tracks = fit_all_tracks(clustered_df, labels, relaxed_mode=True)
        result['n_tracks'] = len(tracks)

        if len(true_tracks) > 0 and len(tracks) > 0:
            n_matched, n_fakes = match_tracks(tracks, true_tracks)
            result['n_matched'] = n_matched
            result['track_efficiency'] = n_matched / len(true_tracks)
            result['track_fake_rate'] = n_fakes / len(tracks)
        else:
            result['track_efficiency'] = 0.0
            result['track_fake_rate'] = 1.0 if tracks else 0.0
    except Exception:
        tracks = []
        result['n_tracks'] = 0
        result['track_efficiency'] = 0.0

    # P-Signal and vertex
    signal_tracks = []
    for track in tracks:
        p = compute_signal_probability(track)
        track.p_signal = p
        track.is_signal = p > 0.5
        if track.is_signal:
            signal_tracks.append(track)

    result['n_signal_tracks'] = len(signal_tracks)

    if truth_vertex is not None and len(signal_tracks) >= 2:
        try:
            vertex_result = reconstruct_vertex(signal_tracks)
            if vertex_result is not None:
                diff = vertex_result.position - truth_vertex
                result['vertex_error_r'] = float(np.sqrt(diff[0]**2 + diff[1]**2))
                result['vertex_reconstructed'] = True
            else:
                result['vertex_reconstructed'] = False
        except Exception:
            result['vertex_reconstructed'] = False
    else:
        result['vertex_reconstructed'] = False

    return result


def run_degradation_study(
    tpc_df: pd.DataFrame,
    particle_df: pd.DataFrame,
    config: DegradationConfig,
    max_events: int = 100,
    seed: int = 42,
) -> DegradationResult:
    """Run degradation study for a single configuration."""
    rng = np.random.default_rng(seed)

    event_ids = sorted(tpc_df['Event_ID'].unique())[:max_events]

    results = []
    for event_id in event_ids:
        r = process_event_with_degradation(event_id, tpc_df, particle_df, config, rng)
        if r is not None:
            results.append(r)

    if not results:
        return DegradationResult(
            config_name=config.name, n_events=0,
            cluster_purity=0, cluster_completeness=0, n_clusters_per_event=0,
            track_efficiency=0, track_fake_rate=0, n_tracks_per_event=0,
            vertex_reco_rate=0, vertex_resolution_r=0, vertex_bias_r=0,
        )

    # Aggregate
    purities = [r['cluster_purity'] for r in results if r.get('n_true_tracks', 0) > 0]
    completenesses = [r['cluster_completeness'] for r in results if r.get('n_true_tracks', 0) > 0]
    efficiencies = [r['track_efficiency'] for r in results if r.get('n_true_tracks', 0) > 0]
    fake_rates = [r['track_fake_rate'] for r in results if r.get('n_tracks', 0) > 0]

    vertex_results = [r for r in results if r.get('vertex_reconstructed', False)]
    vertex_errors = [r['vertex_error_r'] for r in vertex_results]

    return DegradationResult(
        config_name=config.name,
        n_events=len(results),
        cluster_purity=np.mean(purities) if purities else 0.0,
        cluster_completeness=np.mean(completenesses) if completenesses else 0.0,
        n_clusters_per_event=np.mean([r['n_clusters'] for r in results]),
        track_efficiency=np.mean(efficiencies) if efficiencies else 0.0,
        track_fake_rate=np.mean(fake_rates) if fake_rates else 0.0,
        n_tracks_per_event=np.mean([r['n_tracks'] for r in results]),
        vertex_reco_rate=len(vertex_results) / len(results) if results else 0.0,
        vertex_resolution_r=np.mean(vertex_errors) if vertex_errors else 0.0,
        vertex_bias_r=np.std(vertex_errors) if vertex_errors else 0.0,
    )


def main():
    parser = argparse.ArgumentParser(description="NNBAR Reconstruction Degradation Study")
    parser.add_argument("--data_dir", required=True, help="Directory with simulation output")
    parser.add_argument("--output_dir", default="degradation_results", help="Output directory")
    parser.add_argument("--max_events", type=int, default=100, help="Max events per scenario")

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print("Loading simulation data...")
    tpc_df = pd.read_parquet(data_dir / "TPC_output_0.parquet")
    particle_df = pd.read_parquet(data_dir / "Particle_output_0.parquet")

    # Define degradation scenarios
    scenarios = [
        # Baseline
        DegradationConfig("baseline", description="No degradation"),

        # Position resolution studies
        DegradationConfig("pos_0.5cm", position_smear_cm=0.5, description="0.5 cm position smearing"),
        DegradationConfig("pos_1.0cm", position_smear_cm=1.0, description="1.0 cm position smearing"),
        DegradationConfig("pos_2.0cm", position_smear_cm=2.0, description="2.0 cm position smearing"),
        DegradationConfig("pos_5.0cm", position_smear_cm=5.0, description="5.0 cm position smearing"),

        # Hit efficiency studies
        DegradationConfig("eff_95pct", hit_efficiency=0.95, description="95% hit efficiency"),
        DegradationConfig("eff_90pct", hit_efficiency=0.90, description="90% hit efficiency"),
        DegradationConfig("eff_80pct", hit_efficiency=0.80, description="80% hit efficiency"),
        DegradationConfig("eff_70pct", hit_efficiency=0.70, description="70% hit efficiency"),

        # Noise studies
        DegradationConfig("noise_50", noise_hits_per_event=50, description="50 noise hits/event"),
        DegradationConfig("noise_100", noise_hits_per_event=100, description="100 noise hits/event"),
        DegradationConfig("noise_200", noise_hits_per_event=200, description="200 noise hits/event"),
        DegradationConfig("noise_500", noise_hits_per_event=500, description="500 noise hits/event"),

        # Combined scenarios
        DegradationConfig("realistic_good", position_smear_cm=0.5, hit_efficiency=0.95,
                         noise_hits_per_event=50, description="Realistic good conditions"),
        DegradationConfig("realistic_moderate", position_smear_cm=1.0, hit_efficiency=0.90,
                         noise_hits_per_event=100, description="Realistic moderate conditions"),
        DegradationConfig("realistic_challenging", position_smear_cm=2.0, hit_efficiency=0.80,
                         noise_hits_per_event=200, description="Realistic challenging conditions"),
    ]

    print(f"\nRunning {len(scenarios)} degradation scenarios...")
    print("=" * 70)

    all_results = []

    for i, config in enumerate(scenarios):
        print(f"\n[{i+1}/{len(scenarios)}] {config.name}: {config.description}")
        t0 = time.time()

        result = run_degradation_study(tpc_df, particle_df, config, args.max_events)
        all_results.append(result)

        print(f"  Cluster purity: {result.cluster_purity:.3f}, completeness: {result.cluster_completeness:.3f}")
        print(f"  Track efficiency: {result.track_efficiency:.3f}, fake rate: {result.track_fake_rate:.3f}")
        print(f"  Vertex reco rate: {result.vertex_reco_rate:.3f}, resolution: {result.vertex_resolution_r:.1f} cm")
        print(f"  Time: {time.time() - t0:.1f}s")

    # Summary table
    print("\n" + "=" * 70)
    print("DEGRADATION STUDY SUMMARY")
    print("=" * 70)
    print(f"{'Scenario':<25} {'Clust Pur':>10} {'Clust Comp':>10} {'Track Eff':>10} {'Vtx Res':>10}")
    print("-" * 70)

    for r in all_results:
        print(f"{r.config_name:<25} {r.cluster_purity:>10.3f} {r.cluster_completeness:>10.3f} "
              f"{r.track_efficiency:>10.3f} {r.vertex_resolution_r:>9.1f}cm")

    print("=" * 70)

    # Save results
    output_data = {
        'scenarios': [asdict(s) for s in scenarios],
        'results': [asdict(r) for r in all_results],
    }

    with open(output_dir / "degradation_results.json", 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nResults saved to {output_dir}/degradation_results.json")

    # Create summary CSV
    summary_df = pd.DataFrame([asdict(r) for r in all_results])
    summary_df.to_csv(output_dir / "degradation_summary.csv", index=False)
    print(f"Summary CSV saved to {output_dir}/degradation_summary.csv")


if __name__ == "__main__":
    main()
