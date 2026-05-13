#!/usr/bin/env python3
"""
Energy Deposition Analysis for NNBAR Reconstruction

Analyzes energy deposition in:
1. TPC (dE/dx)
2. Scintillator layers
3. Lead glass calorimeter

Compares reconstructed energy with truth kinetic energy to study
energy resolution and calibration.

Usage:
    python analyze_energy_deposition.py --input /path/to/simulation --output /path/to/analysis
"""

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
from tqdm import tqdm
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nnbar_reconstruction.utils.data_loader import load_parquet_files, load_event_data


@dataclass
class ParticleEnergyAnalysis:
    """Energy analysis for a single particle."""
    event_id: int
    track_id: int
    particle_name: str
    parent_id: int
    is_primary: bool

    # Truth values
    truth_ke: float  # Kinetic energy from simulation (MeV)

    # TPC energy
    tpc_n_hits: int
    tpc_edep: float  # Total energy deposited in TPC (MeV)
    tpc_electrons: float  # Total ionization electrons

    # Scintillator energy
    scint_n_hits: int
    scint_edep: float  # Total energy in scintillator (MeV)
    scint_layers: List[int]  # Which layers were hit

    # Lead glass energy
    calo_n_hits: int
    calo_edep: float  # Total energy in calorimeter (MeV)

    # Derived quantities
    total_edep: float  # Total deposited energy
    energy_ratio: float  # total_edep / truth_ke


def match_hits_to_particle(
    tpc_data: pd.DataFrame,
    scint_data: pd.DataFrame,
    calo_data: pd.DataFrame,
    particle_data: pd.DataFrame,
    event_id: int,
) -> List[ParticleEnergyAnalysis]:
    """
    Match detector hits to primary particles and analyze energy.

    Args:
        tpc_data: TPC hits for all events
        scint_data: Scintillator hits for all events
        calo_data: Lead glass hits for all events
        particle_data: Primary particle info
        event_id: Event to analyze

    Returns:
        List of ParticleEnergyAnalysis for each particle
    """
    results = []

    # Filter to this event
    event_particles = particle_data[particle_data['Event_ID'] == event_id]
    event_tpc = tpc_data[tpc_data['Event_ID'] == event_id]
    event_scint = scint_data[scint_data['Event_ID'] == event_id]
    event_calo = calo_data[calo_data['Event_ID'] == event_id]

    # For each particle in particle_output (these are primaries)
    for idx, particle in event_particles.iterrows():
        pname = particle['Name']
        pid = particle['PID']
        truth_ke = particle['KE']

        # For primary particles, Parent_ID concept is different
        # In particle_output, all entries are primaries from annihilation
        is_primary = True
        parent_id = 0

        # Find TPC hits for this particle
        # In TPC data, we match by particle Name and approximate position/time
        # The Track_ID in TPC corresponds to GEANT4's track ID
        # For primaries, we need to find which Track_ID corresponds to this particle

        # Strategy: Find TPC hits where Name matches and Parent_ID = 0
        tpc_hits = event_tpc[
            (event_tpc['Name'] == pname) &
            (event_tpc['Parent_ID'] == 0)
        ]

        # If there are multiple tracks with same particle name, use Track_ID
        if len(tpc_hits) > 0:
            track_ids = tpc_hits['Track_ID'].unique()
            # Group by track_id and pick the one with most hits (primary track)
            track_counts = tpc_hits.groupby('Track_ID').size()
            primary_track_id = track_counts.idxmax()
            tpc_hits = tpc_hits[tpc_hits['Track_ID'] == primary_track_id]
        else:
            primary_track_id = -1

        tpc_n_hits = len(tpc_hits)
        tpc_edep = tpc_hits['eDep'].sum() if len(tpc_hits) > 0 else 0.0
        tpc_electrons = tpc_hits['electrons'].sum() if 'electrons' in tpc_hits.columns and len(tpc_hits) > 0 else 0.0

        # Find scintillator hits for this particle
        # Match by Name and parent
        scint_hits = event_scint[
            (event_scint['Name'] == pname) if 'Name' in event_scint.columns else True
        ]
        scint_n_hits = len(scint_hits)
        scint_edep = scint_hits['eDep'].sum() if len(scint_hits) > 0 else 0.0
        scint_layers = list(scint_hits['Layer_ID'].unique()) if 'Layer_ID' in scint_hits.columns else []

        # Find lead glass hits for this particle
        calo_hits = event_calo[
            (event_calo['Name'] == pname) if 'Name' in event_calo.columns else True
        ]
        calo_n_hits = len(calo_hits)
        calo_edep = calo_hits['eDep'].sum() if len(calo_hits) > 0 else 0.0

        # Total deposited energy
        total_edep = tpc_edep + scint_edep + calo_edep
        energy_ratio = total_edep / truth_ke if truth_ke > 0 else 0.0

        results.append(ParticleEnergyAnalysis(
            event_id=event_id,
            track_id=int(primary_track_id) if primary_track_id >= 0 else -1,
            particle_name=pname,
            parent_id=parent_id,
            is_primary=is_primary,
            truth_ke=float(truth_ke),
            tpc_n_hits=tpc_n_hits,
            tpc_edep=float(tpc_edep),
            tpc_electrons=float(tpc_electrons),
            scint_n_hits=scint_n_hits,
            scint_edep=float(scint_edep),
            scint_layers=[int(l) for l in scint_layers],
            calo_n_hits=calo_n_hits,
            calo_edep=float(calo_edep),
            total_edep=float(total_edep),
            energy_ratio=float(energy_ratio),
        ))

    return results


def analyze_track_energy(
    tpc_data: pd.DataFrame,
    scint_data: pd.DataFrame,
    calo_data: pd.DataFrame,
    event_id: int,
) -> pd.DataFrame:
    """
    Analyze energy deposition for all TPC tracks in an event.

    Args:
        tpc_data: TPC hits for all events
        scint_data: Scintillator hits for all events
        calo_data: Lead glass hits for all events
        event_id: Event to analyze

    Returns:
        DataFrame with energy info per track
    """
    event_tpc = tpc_data[tpc_data['Event_ID'] == event_id]
    event_scint = scint_data[scint_data['Event_ID'] == event_id]
    event_calo = calo_data[calo_data['Event_ID'] == event_id]

    results = []

    for track_id in event_tpc['Track_ID'].unique():
        track_mask = event_tpc['Track_ID'] == track_id
        track_hits = event_tpc[track_mask]

        first_hit = track_hits.iloc[0]
        pname = first_hit['Name']
        parent_id = first_hit['Parent_ID']
        is_primary = (parent_id == 0)

        # TPC energy
        tpc_n_hits = len(track_hits)
        tpc_edep = track_hits['eDep'].sum()
        tpc_track_length = track_hits['trackl'].sum() if 'trackl' in track_hits.columns else 0.0
        tpc_electrons = track_hits['electrons'].sum() if 'electrons' in track_hits.columns else 0.0

        # Get truth KE from first hit
        truth_ke = first_hit['KE']

        # Compute dE/dx (truncated mean)
        if tpc_track_length > 0:
            dedx = tpc_edep / tpc_track_length
        else:
            dedx = 0.0

        results.append({
            'event_id': event_id,
            'track_id': track_id,
            'particle_name': pname,
            'parent_id': parent_id,
            'is_primary': is_primary,
            'truth_ke': truth_ke,
            'tpc_n_hits': tpc_n_hits,
            'tpc_edep': tpc_edep,
            'tpc_track_length': tpc_track_length,
            'tpc_electrons': tpc_electrons,
            'dedx': dedx,
        })

    return pd.DataFrame(results)


def run_energy_analysis(
    input_dir: Path,
    output_dir: Path,
    max_events: Optional[int] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Run energy deposition analysis on all events.

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
    scint_data = data.get('scintillator', pd.DataFrame())
    calo_data = data.get('leadglass', pd.DataFrame())
    particle_data = data.get('particles', pd.DataFrame())

    if len(tpc_data) == 0:
        raise ValueError(f"No TPC data found in {input_dir}")

    event_ids = sorted(tpc_data['Event_ID'].unique())

    if max_events:
        event_ids = event_ids[:max_events]

    if verbose:
        print(f"Analyzing {len(event_ids)} events...")
        print(f"  TPC hits: {len(tpc_data)}")
        print(f"  Scintillator hits: {len(scint_data)}")
        print(f"  Lead glass hits: {len(calo_data)}")
        print(f"  Primary particles: {len(particle_data)}")

    # Analyze tracks event by event
    all_tracks = []

    for event_id in tqdm(event_ids, disable=not verbose):
        track_df = analyze_track_energy(tpc_data, scint_data, calo_data, event_id)
        all_tracks.append(track_df)

    all_tracks_df = pd.concat(all_tracks, ignore_index=True)

    # Save track energy data
    all_tracks_df.to_csv(output_dir / 'track_energy.csv', index=False)

    # Analyze by particle type
    particle_stats = defaultdict(lambda: {'count': 0, 'ke_sum': 0, 'edep_sum': 0})

    for _, row in all_tracks_df.iterrows():
        pname = row['particle_name']
        particle_stats[pname]['count'] += 1
        particle_stats[pname]['ke_sum'] += row['truth_ke']
        particle_stats[pname]['edep_sum'] += row['tpc_edep']

    # Create particle summary
    particle_summary = []
    for pname, stats in sorted(particle_stats.items(), key=lambda x: -x[1]['count']):
        particle_summary.append({
            'particle': pname,
            'count': stats['count'],
            'mean_ke': stats['ke_sum'] / stats['count'] if stats['count'] > 0 else 0,
            'mean_edep': stats['edep_sum'] / stats['count'] if stats['count'] > 0 else 0,
            'energy_ratio': stats['edep_sum'] / stats['ke_sum'] if stats['ke_sum'] > 0 else 0,
        })

    particle_df = pd.DataFrame(particle_summary)
    particle_df.to_csv(output_dir / 'particle_energy_summary.csv', index=False)

    # Analyze primary pions specifically
    pion_tracks = all_tracks_df[
        (all_tracks_df['particle_name'].isin(['pi+', 'pi-'])) &
        (all_tracks_df['is_primary'])
    ]

    if len(pion_tracks) > 0:
        pion_stats = {
            'n_pions': len(pion_tracks),
            'mean_ke': float(pion_tracks['truth_ke'].mean()),
            'std_ke': float(pion_tracks['truth_ke'].std()),
            'mean_edep': float(pion_tracks['tpc_edep'].mean()),
            'std_edep': float(pion_tracks['tpc_edep'].std()),
            'mean_dedx': float(pion_tracks['dedx'].mean()),
            'std_dedx': float(pion_tracks['dedx'].std()),
            'energy_ratio': float(pion_tracks['tpc_edep'].sum() / pion_tracks['truth_ke'].sum()),
        }
    else:
        pion_stats = {}

    # Overall statistics
    stats = {
        'n_events': len(event_ids),
        'n_tracks': len(all_tracks_df),
        'n_primary_tracks': int((all_tracks_df['is_primary']).sum()),
        'pion_stats': pion_stats,
    }

    # Save stats
    with open(output_dir / 'energy_analysis_summary.json', 'w') as f:
        json.dump(stats, f, indent=2)

    # Print summary
    if verbose:
        print("\n" + "=" * 70)
        print("ENERGY DEPOSITION ANALYSIS")
        print("=" * 70)
        print(f"Events analyzed: {stats['n_events']}")
        print(f"Total tracks: {stats['n_tracks']}")
        print(f"Primary tracks: {stats['n_primary_tracks']}")
        print()

        if pion_stats:
            print("PRIMARY PION TRACKS:")
            print(f"  Count: {pion_stats['n_pions']}")
            print(f"  Mean KE (truth): {pion_stats['mean_ke']:.1f} ± {pion_stats['std_ke']:.1f} MeV")
            print(f"  Mean TPC eDep: {pion_stats['mean_edep']:.3f} ± {pion_stats['std_edep']:.3f} MeV")
            print(f"  Mean dE/dx: {pion_stats['mean_dedx']:.4f} MeV/cm")
            print(f"  Energy ratio (eDep/KE): {pion_stats['energy_ratio']:.4f}")
            print()

        print("PARTICLE TYPE BREAKDOWN:")
        print("-" * 70)
        print(f"{'Particle':<15} {'Count':>8} {'Mean KE':>12} {'Mean eDep':>12} {'Ratio':>8}")
        print("-" * 70)
        for row in particle_summary[:10]:
            print(f"{row['particle']:<15} {row['count']:>8} "
                  f"{row['mean_ke']:>11.1f} {row['mean_edep']:>11.4f} "
                  f"{row['energy_ratio']:>7.4f}")
        print("=" * 70)
        print(f"Output saved to: {output_dir}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Analyze energy deposition in NNBAR reconstruction',
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
        default=Path('/home/billy/nnbar/simulation/nnbar_reconstruction/output/energy_analysis'),
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

    run_energy_analysis(
        input_dir=args.input,
        output_dir=args.output,
        max_events=args.max_events,
        verbose=not args.quiet,
    )


if __name__ == '__main__':
    main()
