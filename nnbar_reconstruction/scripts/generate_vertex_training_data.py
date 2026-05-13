#!/usr/bin/env python3
"""
Generate synthetic multi-pion events for vertex GNN training.

Creates events with 3-5 pions emanating from a common vertex with
realistic kinetic energies and directions. This provides essentially
unlimited training data for the vertex reconstruction model.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd
import argparse
from typing import List, Dict, Tuple
from sklearn.decomposition import PCA


# =============================================================================
# TPC Geometry Constants
# =============================================================================

TPC_INNER_RADIUS = 114.0   # cm (beampipe at 112 cm)
TPC_OUTER_RADIUS = 210.0   # cm
TPC_HALF_Z = 250.0         # cm
TPC_Z_MIN = -TPC_HALF_Z
TPC_Z_MAX = TPC_HALF_Z


# =============================================================================
# Track Generation
# =============================================================================

def generate_track_hits(
    vertex: np.ndarray,
    direction: np.ndarray,
    kinetic_energy_mev: float,
    pion_mass_mev: float = 139.57,
    hit_spacing: float = 1.5,      # cm between hits
    hit_sigma: float = 0.5,        # Position resolution in cm
) -> np.ndarray:
    """
    Generate TPC hits for a single pion track.

    Args:
        vertex: [x, y, z] starting position in cm
        direction: [dx, dy, dz] unit vector
        kinetic_energy_mev: Kinetic energy in MeV
        pion_mass_mev: Pion mass in MeV
        hit_spacing: Average spacing between hits
        hit_sigma: Position smearing

    Returns:
        (N, 3) array of hit positions
    """
    # Calculate approximate track length based on energy
    # Simple model: ~0.5 cm per MeV for charged pions in gas
    total_length = min(0.5 * kinetic_energy_mev, 150.0)  # Cap at 150 cm

    # Generate hit positions along the track
    n_hits = max(5, int(total_length / hit_spacing))
    t_values = np.linspace(0, total_length, n_hits)

    # Add some randomness to spacing
    t_values += np.random.normal(0, hit_spacing * 0.2, len(t_values))
    t_values = np.sort(t_values)
    t_values = t_values[t_values > 0]

    # Generate hit positions
    hits = []
    for t in t_values:
        # Position along track
        pos = vertex + t * direction

        # Check if within TPC volume
        r = np.sqrt(pos[0]**2 + pos[1]**2)
        if r < TPC_INNER_RADIUS or r > TPC_OUTER_RADIUS:
            continue
        if pos[2] < TPC_Z_MIN or pos[2] > TPC_Z_MAX:
            continue

        # Add position smearing
        pos += np.random.normal(0, hit_sigma, 3)
        hits.append(pos)

    return np.array(hits) if hits else np.zeros((0, 3))


def generate_event(
    n_pions: int = 4,
    vertex_xy_sigma: float = 50.0,   # Vertex spread in XY (cm)
    vertex_z_mean: float = 0.0,
    vertex_z_sigma: float = 20.0,
    ke_min: float = 50.0,            # Min kinetic energy (MeV)
    ke_max: float = 500.0,           # Max kinetic energy (MeV)
) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
    """
    Generate a multi-pion event with hits and track candidates.

    Args:
        n_pions: Number of pions to generate
        vertex_xy_sigma: Standard deviation for vertex XY position
        vertex_z_mean: Mean vertex Z position
        vertex_z_sigma: Standard deviation for vertex Z position
        ke_min: Minimum kinetic energy
        ke_max: Maximum kinetic energy

    Returns:
        Tuple of (all_hits, truth_vertex, track_candidates)
    """
    # Generate random vertex position near beampipe
    vx = np.random.normal(0, vertex_xy_sigma)
    vy = np.random.normal(0, vertex_xy_sigma)
    vz = np.random.normal(vertex_z_mean, vertex_z_sigma)

    # Ensure vertex is within beampipe radius (~50 cm)
    r_vertex = np.sqrt(vx**2 + vy**2)
    if r_vertex > 80:
        scale = 80 / r_vertex
        vx *= scale
        vy *= scale

    truth_vertex = np.array([vx, vy, vz])

    # Generate pion tracks
    all_hits = []
    track_candidates = []

    for i in range(n_pions):
        # Random isotropic direction
        phi = np.random.uniform(0, 2 * np.pi)
        cos_theta = np.random.uniform(-1, 1)
        sin_theta = np.sqrt(1 - cos_theta**2)

        direction = np.array([
            sin_theta * np.cos(phi),
            sin_theta * np.sin(phi),
            cos_theta
        ])

        # Random kinetic energy
        ke = np.random.uniform(ke_min, ke_max)

        # Generate track hits
        hits = generate_track_hits(truth_vertex, direction, ke)

        if len(hits) < 5:
            continue

        all_hits.append(hits)

        # Extract track candidate features
        candidate = extract_track_candidate(hits, truth_vertex)
        if candidate is not None:
            track_candidates.append(candidate)

    # Combine all hits
    if all_hits:
        combined_hits = np.vstack(all_hits)
    else:
        combined_hits = np.zeros((0, 3))

    return combined_hits, truth_vertex, track_candidates


def extract_track_candidate(hits: np.ndarray, truth_vertex: np.ndarray, z_target: float = 0.0) -> Dict:
    """Extract candidate features from track hits."""
    if len(hits) < 5:
        return None

    # PCA fit
    center = hits.mean(axis=0)
    pca = PCA(n_components=3)
    pca.fit(hits - center)
    direction = pca.components_[0]
    direction = direction / (np.linalg.norm(direction) + 1e-12)

    # Project along direction
    t = (hits - center) @ direction
    length = float(np.max(t) - np.min(t))

    # Perpendicular residuals
    perp = (hits - center) - np.outer(t, direction)
    rms = float(np.sqrt((perp**2).sum(axis=1).mean()))
    linearity = float(pca.explained_variance_ratio_[0])

    # Vertex projection at z=z_target
    if abs(direction[2]) > 1e-9:
        t_vtx = (z_target - center[2]) / direction[2]
        vx = float(center[0] + t_vtx * direction[0])
        vy = float(center[1] + t_vtx * direction[1])
    else:
        vx, vy = float("nan"), float("nan")

    if np.isnan(vx) or np.isnan(vy):
        return None

    return {
        'n_hits': len(hits),
        'vx': vx,
        'vy': vy,
        'vz': float(z_target),
        'length': length,
        'rms': rms,
        'linearity': linearity,
        'center_x': float(center[0]),
        'center_y': float(center[1]),
        'center_z': float(center[2]),
        'dir_x': float(direction[0]),
        'dir_y': float(direction[1]),
        'dir_z': float(direction[2]),
    }


# =============================================================================
# Data Generation
# =============================================================================

def generate_dataset(
    n_events: int = 10000,
    n_pions_min: int = 3,
    n_pions_max: int = 5,
    vertex_xy_sigma: float = 50.0,
    vertex_z_sigma: float = 20.0,
    ke_min: float = 50.0,
    ke_max: float = 500.0,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate a dataset of multi-pion events.

    Args:
        n_events: Number of events to generate
        n_pions_min: Minimum pions per event
        n_pions_max: Maximum pions per event
        vertex_xy_sigma: Vertex position spread in XY
        vertex_z_sigma: Vertex position spread in Z
        ke_min: Minimum kinetic energy
        ke_max: Maximum kinetic energy
        seed: Random seed

    Returns:
        Tuple of (candidates_df, truth_df)
    """
    np.random.seed(seed)

    all_candidates = []
    all_truth = []
    event_counter = 0

    print(f"Generating {n_events} events with {n_pions_min}-{n_pions_max} pions each...")

    for i in range(n_events):
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{n_events} events")

        n_pions = np.random.randint(n_pions_min, n_pions_max + 1)

        _, truth_vertex, candidates = generate_event(
            n_pions=n_pions,
            vertex_xy_sigma=vertex_xy_sigma,
            vertex_z_sigma=vertex_z_sigma,
            ke_min=ke_min,
            ke_max=ke_max,
        )

        if len(candidates) < 2:
            continue

        # Add event ID to candidates
        for c in candidates:
            c['event_id'] = event_counter
            all_candidates.append(c)

        # Record truth
        all_truth.append({
            'event_no': event_counter,
            'position_x': float(truth_vertex[0]),
            'position_y': float(truth_vertex[1]),
            'position_z': float(truth_vertex[2]),
        })

        event_counter += 1

    print(f"Generated {event_counter} valid events with {len(all_candidates)} candidates")

    return pd.DataFrame(all_candidates), pd.DataFrame(all_truth)


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic vertex training data")
    parser.add_argument("--n_events", type=int, default=10000, help="Number of events")
    parser.add_argument("--n_pions_min", type=int, default=3, help="Min pions per event")
    parser.add_argument("--n_pions_max", type=int, default=5, help="Max pions per event")
    parser.add_argument("--vertex_xy_sigma", type=float, default=50.0, help="Vertex XY spread (cm)")
    parser.add_argument("--vertex_z_sigma", type=float, default=20.0, help="Vertex Z spread (cm)")
    parser.add_argument("--ke_min", type=float, default=50.0, help="Min kinetic energy (MeV)")
    parser.add_argument("--ke_max", type=float, default=500.0, help="Max kinetic energy (MeV)")
    parser.add_argument("--out_dir", default="./output/synthetic", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Setup output directory
    script_dir = Path(__file__).parent
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = script_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SYNTHETIC VERTEX TRAINING DATA GENERATION")
    print("=" * 60)
    print(f"Events: {args.n_events}")
    print(f"Pions per event: {args.n_pions_min}-{args.n_pions_max}")
    print(f"Vertex XY sigma: {args.vertex_xy_sigma} cm")
    print(f"Vertex Z sigma: {args.vertex_z_sigma} cm")
    print(f"Kinetic energy: {args.ke_min}-{args.ke_max} MeV")
    print(f"Output: {out_dir}")

    # Generate data
    candidates_df, truth_df = generate_dataset(
        n_events=args.n_events,
        n_pions_min=args.n_pions_min,
        n_pions_max=args.n_pions_max,
        vertex_xy_sigma=args.vertex_xy_sigma,
        vertex_z_sigma=args.vertex_z_sigma,
        ke_min=args.ke_min,
        ke_max=args.ke_max,
        seed=args.seed,
    )

    # Save
    candidates_df.to_parquet(out_dir / "candidates.parquet", index=False)
    truth_df.to_parquet(out_dir / "truth.parquet", index=False)

    print(f"\nSaved to {out_dir}")
    print(f"  candidates.parquet: {len(candidates_df)} candidates")
    print(f"  truth.parquet: {len(truth_df)} events")

    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"Mean candidates per event: {len(candidates_df) / len(truth_df):.1f}")
    print(f"Mean n_hits: {candidates_df['n_hits'].mean():.1f}")
    print(f"Mean linearity: {candidates_df['linearity'].mean():.3f}")
    print(f"Mean track length: {candidates_df['length'].mean():.1f} cm")


if __name__ == "__main__":
    main()
