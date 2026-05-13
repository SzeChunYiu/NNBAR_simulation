#!/usr/bin/env python3
"""
NNBAR Event Reconstruction - Main Script

Runs the full reconstruction chain on simulation output:
1. Load Parquet data
2. Event pre-selection (time window)
3. TPC track finding
4. Vertex reconstruction
5. Charged/neutral object reconstruction
6. Particle identification
7. Event variables
8. Event selection

Usage:
    python run_reconstruction.py --input /path/to/simulation/output --output results.parquet

Author: NNBAR Collaboration
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nnbar_reconstruction.utils.config import load_config, get_config
from nnbar_reconstruction.utils.data_loader import (
    load_parquet_files,
    load_event_data,
    get_event_ids,
    get_truth_vertex,
    preprocess_tpc_data,
    preprocess_scintillator_data,
    preprocess_leadglass_data,
    EventIterator,
)

from nnbar_reconstruction.tracking.clustering import cluster_tpc_hits
from nnbar_reconstruction.tracking.track_fitting import fit_all_tracks, Track
from nnbar_reconstruction.tracking.signal_separation import (
    separate_signal_compton,
    compute_signal_probability,
)

from nnbar_reconstruction.vertex.classical_vertex import reconstruct_vertex, VertexResult

from nnbar_reconstruction.reconstruction.event_preselection import rolling_time_window_trigger
from nnbar_reconstruction.reconstruction.timing_window import apply_timing_cuts
from nnbar_reconstruction.reconstruction.charged_reconstruction import (
    reconstruct_charged_objects,
    identify_charged_particles,
)
from nnbar_reconstruction.reconstruction.neutral_reconstruction import (
    reconstruct_neutral_objects,
    find_pi0_candidates,
)

from nnbar_reconstruction.analysis.event_variables import (
    compute_event_variables,
    EventVariables,
)
from nnbar_reconstruction.analysis.event_selection import (
    apply_selection_cuts,
    SelectionResult,
)


def reconstruct_event(
    event_id: int,
    tpc_data: pd.DataFrame,
    scint_data: pd.DataFrame,
    lg_data: pd.DataFrame,
    truth_vertex: Optional[np.ndarray] = None,
    verbose: bool = False,
) -> Dict:
    """
    Full reconstruction of a single event.

    Args:
        event_id: Event ID.
        tpc_data: TPC hits DataFrame.
        scint_data: Scintillator hits DataFrame.
        lg_data: Lead glass hits DataFrame.
        truth_vertex: Truth vertex for validation (optional).
        verbose: Print progress.

    Returns:
        Dictionary with reconstruction results.
    """
    result = {
        'event_id': event_id,
        'success': False,
        'n_tpc_hits': len(tpc_data),
        'n_scint_hits': len(scint_data),
        'n_lg_hits': len(lg_data),
    }

    # Preprocess data
    tpc_data = preprocess_tpc_data(tpc_data)
    scint_data = preprocess_scintillator_data(scint_data)
    lg_data = preprocess_leadglass_data(lg_data)

    if verbose:
        print(f"Event {event_id}: {len(tpc_data)} TPC, {len(scint_data)} scint, {len(lg_data)} LG hits")

    # 1. Event pre-selection (time window)
    trigger_result = rolling_time_window_trigger(tpc_data, scint_data, lg_data)
    result['triggered'] = trigger_result['triggered']
    result['t0'] = trigger_result['t0']

    if not trigger_result['triggered']:
        return result

    # Filter by time window
    tpc_data = tpc_data[trigger_result['tpc_mask']]
    scint_data = scint_data[trigger_result['scint_mask']]
    lg_data = lg_data[trigger_result['lg_mask']]

    # 2. TPC track finding
    if len(tpc_data) < 3:
        result['n_tracks'] = 0
        return result

    labels, tpc_clustered = cluster_tpc_hits(tpc_data, refine=True)
    tracks = fit_all_tracks(tpc_clustered, labels, z_target=0.0)

    result['n_tracks'] = len(tracks)

    if len(tracks) == 0:
        return result

    # 3. Signal/Compton separation
    for track in tracks:
        track.p_signal = compute_signal_probability(track)
        track.is_signal = track.p_signal > 0.5

    signal_tracks, compton_tracks = separate_signal_compton(tracks)
    result['n_signal_tracks'] = len(signal_tracks)
    result['n_compton_tracks'] = len(compton_tracks)

    # 4. Vertex reconstruction
    vertex_result = reconstruct_vertex(tracks, method='weighted', signal_only=True)

    if not vertex_result.is_valid:
        # Try with all tracks if signal-only fails
        vertex_result = reconstruct_vertex(tracks, method='weighted', signal_only=False)

    result['vertex_valid'] = vertex_result.is_valid
    result['vertex_x'] = vertex_result.position[0]
    result['vertex_y'] = vertex_result.position[1]
    result['vertex_z'] = vertex_result.position[2]
    result['vertex_r'] = vertex_result.r
    result['n_tracks_to_vertex'] = vertex_result.n_tracks

    if truth_vertex is not None:
        result['truth_vertex_x'] = truth_vertex[0]
        result['truth_vertex_y'] = truth_vertex[1]
        result['truth_vertex_z'] = truth_vertex[2]
        result['vertex_residual'] = np.linalg.norm(vertex_result.position - truth_vertex)

    if not vertex_result.is_valid:
        return result

    vertex = vertex_result.position

    # 5. Apply timing cuts
    scint_timed = apply_timing_cuts(scint_data, vertex, trigger_result['t0'], 'scintillator')
    lg_timed = apply_timing_cuts(lg_data, vertex, trigger_result['t0'], 'leadglass')

    # 6. Charged object reconstruction
    charged_objects = reconstruct_charged_objects(
        signal_tracks, vertex, tpc_clustered, scint_timed, lg_timed
    )
    charged_objects = identify_charged_particles(charged_objects)

    result['n_charged'] = len(charged_objects)

    # 7. Neutral object reconstruction
    # Get masks of hits assigned to charged objects
    charged_scint_mask = np.zeros(len(scint_timed), dtype=bool)
    charged_lg_mask = np.zeros(len(lg_timed), dtype=bool)

    for obj in charged_objects:
        # Mark hits within cone as assigned
        # This is simplified - should use actual cone masks from reconstruction
        pass

    neutral_objects = reconstruct_neutral_objects(
        vertex, scint_timed, lg_timed,
        charged_scint_mask, charged_lg_mask
    )

    result['n_neutral'] = len(neutral_objects)

    # 8. Find pi0 candidates
    pi0_candidates = find_pi0_candidates(neutral_objects, vertex)
    result['n_pi0'] = len(pi0_candidates)

    # 9. Compute event variables
    ev = compute_event_variables(
        charged_objects, neutral_objects, vertex,
        n_tracks_to_vertex=vertex_result.n_tracks
    )

    result.update(ev.to_dict())

    # 10. Event selection
    selection = apply_selection_cuts(ev)
    result['passed_selection'] = selection.passed
    result['n_cuts_passed'] = selection.n_cuts_passed
    result['n_cuts_total'] = selection.n_cuts_total

    for cut_name, passed in selection.cut_results.items():
        result[f'cut_{cut_name}'] = passed

    result['success'] = True

    return result


def run_reconstruction(
    input_dir: str,
    output_file: Optional[str] = None,
    max_events: Optional[int] = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Run reconstruction on all events in input directory.

    Args:
        input_dir: Path to simulation output directory.
        output_file: Path to save results (optional).
        max_events: Maximum number of events to process.
        verbose: Print progress.

    Returns:
        DataFrame with reconstruction results.
    """
    print(f"Loading data from: {input_dir}")
    data = load_parquet_files(input_dir)

    event_ids = get_event_ids(data)
    print(f"Found {len(event_ids)} events")

    if max_events is not None:
        event_ids = event_ids[:max_events]
        print(f"Processing first {max_events} events")

    results = []

    for event_id in tqdm(event_ids, desc="Reconstructing"):
        event = load_event_data(data, event_id)

        truth_vertex = get_truth_vertex(event)

        result = reconstruct_event(
            event_id,
            event.tpc,
            event.scintillator,
            event.leadglass,
            truth_vertex,
            verbose=verbose,
        )

        results.append(result)

    df = pd.DataFrame(results)

    # Compute summary statistics
    n_total = len(df)
    n_triggered = df['triggered'].sum() if 'triggered' in df.columns else 0
    n_with_tracks = (df['n_tracks'] > 0).sum() if 'n_tracks' in df.columns else 0
    n_valid_vertex = df['vertex_valid'].sum() if 'vertex_valid' in df.columns else 0
    n_passed = df['passed_selection'].sum() if 'passed_selection' in df.columns else 0

    print("\n" + "=" * 60)
    print("Reconstruction Summary")
    print("=" * 60)
    print(f"Total events:        {n_total}")
    print(f"Triggered:           {n_triggered} ({100*n_triggered/n_total:.1f}%)")
    print(f"With tracks:         {n_with_tracks} ({100*n_with_tracks/n_total:.1f}%)")
    print(f"Valid vertex:        {n_valid_vertex} ({100*n_valid_vertex/n_total:.1f}%)")
    print(f"Passed selection:    {n_passed} ({100*n_passed/n_total:.1f}%)")

    if 'invariant_mass' in df.columns:
        masses = df.loc[df['success'], 'invariant_mass']
        if len(masses) > 0:
            print(f"\nInvariant mass:")
            print(f"  Mean:   {masses.mean():.1f} MeV ({masses.mean()/1000:.3f} GeV)")
            print(f"  Std:    {masses.std():.1f} MeV")
            print(f"  Median: {masses.median():.1f} MeV")

    if 'vertex_residual' in df.columns:
        residuals = df.loc[df['vertex_valid'], 'vertex_residual']
        if len(residuals) > 0:
            print(f"\nVertex residual (vs truth):")
            print(f"  Mean:   {residuals.mean():.2f} cm")
            print(f"  Median: {residuals.median():.2f} cm")

    print("=" * 60)

    if output_file is not None:
        df.to_parquet(output_file, index=False)
        print(f"\nResults saved to: {output_file}")

    return df


def main():
    parser = argparse.ArgumentParser(
        description="NNBAR Event Reconstruction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_reconstruction.py --input /path/to/sim/output --output results.parquet
    python run_reconstruction.py --input /path/to/sim/output --max-events 100 -v
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input directory containing simulation Parquet files'
    )

    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output Parquet file for results'
    )

    parser.add_argument(
        '--max-events', '-n',
        type=int,
        default=None,
        help='Maximum number of events to process'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed progress'
    )

    parser.add_argument(
        '--config', '-c',
        default=None,
        help='Path to configuration file'
    )

    args = parser.parse_args()

    # Load configuration
    if args.config:
        load_config(args.config)

    # Run reconstruction
    df = run_reconstruction(
        args.input,
        args.output,
        args.max_events,
        args.verbose,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
