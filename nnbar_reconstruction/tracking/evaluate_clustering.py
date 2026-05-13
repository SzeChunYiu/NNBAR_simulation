"""
Clustering evaluation metrics for TPC track finding.

Compares predicted cluster labels against true Track_ID labels
from simulation to evaluate clustering quality.

Metrics computed:
- Purity: average fraction of dominant track within each cluster
- Efficiency: average fraction of track hits correctly grouped
- Adjusted Rand Index (ARI): chance-adjusted clustering similarity
- V-measure: harmonic mean of homogeneity and completeness
- Normalized Mutual Information (NMI)

Usage:
    from nnbar_reconstruction.tracking.evaluate_clustering import (
        evaluate_clustering,
        evaluate_all_events,
        save_detailed_report,
    )

    # Evaluate single event
    metrics = evaluate_clustering(pred_labels, true_labels)

    # Evaluate all events and save detailed report
    results = evaluate_all_events(data_dir, output_dir)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import Counter
import json
import datetime

from sklearn.metrics import (
    adjusted_rand_score,
    normalized_mutual_info_score,
    v_measure_score,
    homogeneity_score,
    completeness_score,
)


@dataclass
class ClusteringMetrics:
    """Container for clustering evaluation metrics."""
    purity: float
    efficiency: float
    ari: float  # Adjusted Rand Index
    nmi: float  # Normalized Mutual Information
    v_measure: float
    homogeneity: float
    completeness: float
    n_clusters_pred: int
    n_clusters_true: int
    n_hits: int
    n_noise: int  # Hits labeled as noise (-1)

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class EventClusteringResult:
    """Detailed clustering result for a single event."""
    event_id: int
    metrics: ClusteringMetrics
    cluster_details: List[Dict[str, Any]]
    track_details: List[Dict[str, Any]]

    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'metrics': self.metrics.to_dict(),
            'cluster_details': self.cluster_details,
            'track_details': self.track_details,
        }


def compute_purity(pred_labels: np.ndarray, true_labels: np.ndarray) -> Tuple[float, List[Dict]]:
    """
    Compute clustering purity: fraction of each cluster from dominant true track.

    For each predicted cluster, find the most common true label and compute
    what fraction of the cluster belongs to that label.

    Args:
        pred_labels: Predicted cluster labels (-1 = noise)
        true_labels: True Track_ID labels

    Returns:
        Tuple of (mean purity, list of per-cluster details)
    """
    # Exclude noise points
    valid_mask = pred_labels >= 0
    if valid_mask.sum() == 0:
        return 0.0, []

    pred_valid = pred_labels[valid_mask]
    true_valid = true_labels[valid_mask]

    cluster_ids = np.unique(pred_valid)
    purities = []
    cluster_details = []

    for cid in cluster_ids:
        cluster_mask = pred_valid == cid
        true_in_cluster = true_valid[cluster_mask]

        # Count occurrences of each true label
        label_counts = Counter(true_in_cluster)
        dominant_label, dominant_count = label_counts.most_common(1)[0]

        cluster_size = len(true_in_cluster)
        purity = dominant_count / cluster_size
        purities.append(purity)

        cluster_details.append({
            'cluster_id': int(cid),
            'size': int(cluster_size),
            'purity': float(purity),
            'dominant_track_id': int(dominant_label),
            'dominant_count': int(dominant_count),
            'track_composition': {int(k): int(v) for k, v in label_counts.items()},
        })

    mean_purity = np.mean(purities) if purities else 0.0
    return float(mean_purity), cluster_details


def compute_efficiency(pred_labels: np.ndarray, true_labels: np.ndarray) -> Tuple[float, List[Dict]]:
    """
    Compute clustering efficiency: fraction of true track correctly grouped.

    For each true track, find the cluster containing most of its hits
    and compute what fraction of the track is in that cluster.

    Args:
        pred_labels: Predicted cluster labels (-1 = noise)
        true_labels: True Track_ID labels

    Returns:
        Tuple of (mean efficiency, list of per-track details)
    """
    track_ids = np.unique(true_labels)
    efficiencies = []
    track_details = []

    for tid in track_ids:
        track_mask = true_labels == tid
        pred_for_track = pred_labels[track_mask]

        # Count hits in each predicted cluster (including noise)
        cluster_counts = Counter(pred_for_track)

        # Find best cluster (excluding noise if there are non-noise options)
        non_noise_counts = {k: v for k, v in cluster_counts.items() if k >= 0}

        if non_noise_counts:
            best_cluster, best_count = max(non_noise_counts.items(), key=lambda x: x[1])
        else:
            best_cluster, best_count = -1, 0

        track_size = int(track_mask.sum())
        efficiency = best_count / track_size if track_size > 0 else 0.0
        efficiencies.append(efficiency)

        n_noise = cluster_counts.get(-1, 0)

        track_details.append({
            'track_id': int(tid),
            'size': track_size,
            'efficiency': float(efficiency),
            'best_cluster_id': int(best_cluster),
            'best_cluster_count': int(best_count),
            'n_noise': int(n_noise),
            'n_fragmented': len(non_noise_counts),  # Track split into how many clusters
            'cluster_distribution': {int(k): int(v) for k, v in cluster_counts.items()},
        })

    mean_efficiency = np.mean(efficiencies) if efficiencies else 0.0
    return float(mean_efficiency), track_details


def evaluate_clustering(
    pred_labels: np.ndarray,
    true_labels: np.ndarray,
) -> ClusteringMetrics:
    """
    Compute all clustering evaluation metrics.

    Args:
        pred_labels: Predicted cluster labels (-1 = noise)
        true_labels: True Track_ID labels

    Returns:
        ClusteringMetrics dataclass with all metrics
    """
    # Filter out noise for sklearn metrics (which don't handle -1 well)
    valid_mask = pred_labels >= 0
    n_noise = (~valid_mask).sum()

    if valid_mask.sum() < 2:
        # Not enough points to compute metrics
        return ClusteringMetrics(
            purity=0.0,
            efficiency=0.0,
            ari=0.0,
            nmi=0.0,
            v_measure=0.0,
            homogeneity=0.0,
            completeness=0.0,
            n_clusters_pred=0,
            n_clusters_true=len(np.unique(true_labels)),
            n_hits=len(pred_labels),
            n_noise=int(n_noise),
        )

    pred_valid = pred_labels[valid_mask]
    true_valid = true_labels[valid_mask]

    # Compute metrics
    purity, _ = compute_purity(pred_labels, true_labels)
    efficiency, _ = compute_efficiency(pred_labels, true_labels)

    ari = adjusted_rand_score(true_valid, pred_valid)
    nmi = normalized_mutual_info_score(true_valid, pred_valid)
    v_measure = v_measure_score(true_valid, pred_valid)
    homogeneity = homogeneity_score(true_valid, pred_valid)
    completeness = completeness_score(true_valid, pred_valid)

    n_clusters_pred = len(np.unique(pred_valid))
    n_clusters_true = len(np.unique(true_labels))

    return ClusteringMetrics(
        purity=float(purity),
        efficiency=float(efficiency),
        ari=float(ari),
        nmi=float(nmi),
        v_measure=float(v_measure),
        homogeneity=float(homogeneity),
        completeness=float(completeness),
        n_clusters_pred=int(n_clusters_pred),
        n_clusters_true=int(n_clusters_true),
        n_hits=len(pred_labels),
        n_noise=int(n_noise),
    )


def evaluate_event_clustering(
    event_id: int,
    pred_labels: np.ndarray,
    true_labels: np.ndarray,
) -> EventClusteringResult:
    """
    Compute detailed clustering evaluation for a single event.

    Includes per-cluster and per-track breakdowns for debugging.

    Args:
        event_id: Event identifier
        pred_labels: Predicted cluster labels
        true_labels: True Track_ID labels

    Returns:
        EventClusteringResult with full details
    """
    metrics = evaluate_clustering(pred_labels, true_labels)
    _, cluster_details = compute_purity(pred_labels, true_labels)
    _, track_details = compute_efficiency(pred_labels, true_labels)

    return EventClusteringResult(
        event_id=event_id,
        metrics=metrics,
        cluster_details=cluster_details,
        track_details=track_details,
    )


def evaluate_all_events(
    tpc_data: pd.DataFrame,
    pred_labels_column: str = 'cluster_id',
    true_labels_column: str = 'Track_ID',
    event_id_column: str = 'Event_ID',
) -> Tuple[pd.DataFrame, List[EventClusteringResult]]:
    """
    Evaluate clustering for all events in a DataFrame.

    Args:
        tpc_data: DataFrame with TPC hits including cluster labels
        pred_labels_column: Column name for predicted labels
        true_labels_column: Column name for true labels
        event_id_column: Column name for event ID

    Returns:
        Tuple of (summary DataFrame, list of detailed results)
    """
    event_ids = tpc_data[event_id_column].unique()

    all_results = []
    summary_rows = []

    for eid in event_ids:
        event_mask = tpc_data[event_id_column] == eid
        event_data = tpc_data[event_mask]

        pred_labels = event_data[pred_labels_column].values
        true_labels = event_data[true_labels_column].values

        result = evaluate_event_clustering(eid, pred_labels, true_labels)
        all_results.append(result)

        row = {'event_id': eid}
        row.update(result.metrics.to_dict())
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)

    return summary_df, all_results


def save_detailed_report(
    results: List[EventClusteringResult],
    output_dir: Path,
    summary_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Path]:
    """
    Save detailed clustering evaluation report for debugging.

    Creates:
    - summary.csv: Per-event metrics summary
    - detailed_results.json: Full per-cluster and per-track breakdowns
    - problem_events.csv: Events with poor clustering (purity or efficiency < 0.8)

    Args:
        results: List of EventClusteringResult objects
        output_dir: Directory to save reports
        summary_df: Optional pre-computed summary DataFrame

    Returns:
        Dictionary of saved file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_files = {}

    # Create summary DataFrame if not provided
    if summary_df is None:
        summary_rows = []
        for r in results:
            row = {'event_id': r.event_id}
            row.update(r.metrics.to_dict())
            summary_rows.append(row)
        summary_df = pd.DataFrame(summary_rows)

    # Save summary CSV
    summary_path = output_dir / 'clustering_summary.csv'
    summary_df.to_csv(summary_path, index=False)
    saved_files['summary'] = summary_path

    # Save detailed JSON report
    detailed_data = {
        'generated_at': datetime.datetime.now().isoformat(),
        'n_events': len(results),
        'mean_metrics': {
            'purity': summary_df['purity'].mean(),
            'efficiency': summary_df['efficiency'].mean(),
            'ari': summary_df['ari'].mean(),
            'nmi': summary_df['nmi'].mean(),
            'v_measure': summary_df['v_measure'].mean(),
        },
        'events': [r.to_dict() for r in results],
    }

    detailed_path = output_dir / 'clustering_detailed.json'
    with open(detailed_path, 'w') as f:
        json.dump(detailed_data, f, indent=2)
    saved_files['detailed'] = detailed_path

    # Identify problem events
    problem_mask = (summary_df['purity'] < 0.8) | (summary_df['efficiency'] < 0.8)
    problem_events = summary_df[problem_mask].copy()

    if len(problem_events) > 0:
        problem_path = output_dir / 'problem_events.csv'
        problem_events.to_csv(problem_path, index=False)
        saved_files['problems'] = problem_path
        print(f"Found {len(problem_events)} problem events (purity or efficiency < 0.8)")

    return saved_files


def print_clustering_summary(summary_df: pd.DataFrame) -> None:
    """Print a formatted summary of clustering evaluation."""
    print("\n" + "=" * 60)
    print("CLUSTERING EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Number of events: {len(summary_df)}")
    print(f"Total hits: {summary_df['n_hits'].sum():,}")
    print()
    print("Mean Metrics:")
    print(f"  Purity:      {summary_df['purity'].mean():.4f} ± {summary_df['purity'].std():.4f}")
    print(f"  Efficiency:  {summary_df['efficiency'].mean():.4f} ± {summary_df['efficiency'].std():.4f}")
    print(f"  ARI:         {summary_df['ari'].mean():.4f} ± {summary_df['ari'].std():.4f}")
    print(f"  NMI:         {summary_df['nmi'].mean():.4f} ± {summary_df['nmi'].std():.4f}")
    print(f"  V-measure:   {summary_df['v_measure'].mean():.4f} ± {summary_df['v_measure'].std():.4f}")
    print(f"  Homogeneity: {summary_df['homogeneity'].mean():.4f} ± {summary_df['homogeneity'].std():.4f}")
    print(f"  Completeness:{summary_df['completeness'].mean():.4f} ± {summary_df['completeness'].std():.4f}")
    print()
    print("Cluster counts:")
    print(f"  Pred clusters/event: {summary_df['n_clusters_pred'].mean():.1f} ± {summary_df['n_clusters_pred'].std():.1f}")
    print(f"  True tracks/event:   {summary_df['n_clusters_true'].mean():.1f} ± {summary_df['n_clusters_true'].std():.1f}")
    print(f"  Noise fraction:      {(summary_df['n_noise'] / summary_df['n_hits']).mean():.4f}")
    print("=" * 60)


if __name__ == "__main__":
    """Test clustering evaluation with real data if available."""
    import sys
    from pathlib import Path

    # Try to load and evaluate real data
    try:
        # Add parent to path for imports
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from nnbar_reconstruction.utils.data_loader import load_parquet_files
        from nnbar_reconstruction.tracking.clustering import cluster_tpc_hits

        data_dir = Path("/home/billy/nnbar/simulation/NNBAR_Detector/build/output/baseline_reference")

        if data_dir.exists():
            print("Loading simulation data...")
            data = load_parquet_files(data_dir, detectors=['tpc'])
            tpc_data = data['tpc']

            print(f"Loaded {len(tpc_data)} TPC hits")

            # Process first 10 events as test
            event_ids = tpc_data['Event_ID'].unique()[:10]

            all_results = []

            for eid in event_ids:
                event_mask = tpc_data['Event_ID'] == eid
                event_data = tpc_data[event_mask].copy()

                # Run clustering
                pred_labels, clustered_data = cluster_tpc_hits(event_data)
                true_labels = event_data['Track_ID'].values

                # Evaluate
                result = evaluate_event_clustering(eid, pred_labels, true_labels)
                all_results.append(result)

                print(f"Event {eid}: purity={result.metrics.purity:.3f}, "
                      f"efficiency={result.metrics.efficiency:.3f}, "
                      f"ARI={result.metrics.ari:.3f}")

            # Save detailed report
            output_dir = Path("/home/billy/nnbar/simulation/nnbar_reconstruction/output/clustering_eval")
            saved = save_detailed_report(all_results, output_dir)
            print(f"\nSaved reports to: {output_dir}")

        else:
            print(f"Data directory not found: {data_dir}")
            print("Running with synthetic data instead...")

            # Synthetic test
            np.random.seed(42)

            # Simulate 3 tracks with some overlap
            n_hits = 100
            true_labels = np.repeat([0, 1, 2], [40, 35, 25])

            # Perfect clustering
            pred_perfect = true_labels.copy()
            metrics_perfect = evaluate_clustering(pred_perfect, true_labels)
            print(f"\nPerfect clustering: purity={metrics_perfect.purity:.3f}, "
                  f"efficiency={metrics_perfect.efficiency:.3f}, ARI={metrics_perfect.ari:.3f}")

            # Imperfect clustering (some mixing)
            pred_mixed = true_labels.copy()
            pred_mixed[35:45] = 0  # Some track 1 points assigned to cluster 0
            metrics_mixed = evaluate_clustering(pred_mixed, true_labels)
            print(f"Mixed clustering: purity={metrics_mixed.purity:.3f}, "
                  f"efficiency={metrics_mixed.efficiency:.3f}, ARI={metrics_mixed.ari:.3f}")

            # With noise
            pred_noisy = true_labels.copy()
            pred_noisy[::10] = -1  # Every 10th hit is noise
            metrics_noisy = evaluate_clustering(pred_noisy, true_labels)
            print(f"Noisy clustering: purity={metrics_noisy.purity:.3f}, "
                  f"efficiency={metrics_noisy.efficiency:.3f}, ARI={metrics_noisy.ari:.3f}")

    except ImportError as e:
        print(f"Could not import required modules: {e}")
        print("Running basic synthetic test...")

        # Basic synthetic test
        np.random.seed(42)
        true_labels = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])
        pred_labels = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])

        metrics = evaluate_clustering(pred_labels, true_labels)
        print(f"Perfect match: {metrics}")
