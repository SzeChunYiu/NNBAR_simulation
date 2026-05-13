"""
Vertex reconstruction evaluation for NNBAR.

Computes:
- Vertex resolution (RMS of residuals) for x, y, z
- Residual distributions and bias
- Comparison of GNN vs classical method
- Per-event detailed output for debugging

Usage:
    from nnbar_reconstruction.vertex.evaluate_vertex import (
        evaluate_vertex_reconstruction,
        compare_methods,
        save_vertex_report,
    )

    # Evaluate predictions
    metrics = evaluate_vertex_reconstruction(pred_vertices, true_vertices)

    # Compare GNN vs classical
    comparison = compare_methods(gnn_vertices, classical_vertices, true_vertices)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json
import datetime

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@dataclass
class VertexResidual:
    """Residual for a single vertex reconstruction."""
    event_id: int
    true_x: float
    true_y: float
    true_z: float
    pred_x: float
    pred_y: float
    pred_z: float
    residual_x: float
    residual_y: float
    residual_z: float
    residual_r: float  # Radial distance from true

    @property
    def residual_3d(self) -> float:
        """3D Euclidean distance."""
        return np.sqrt(self.residual_x**2 + self.residual_y**2 + self.residual_z**2)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class VertexMetrics:
    """Summary metrics for vertex reconstruction."""
    n_events: int

    # Resolution (RMS)
    resolution_x: float
    resolution_y: float
    resolution_z: float
    resolution_r: float
    resolution_3d: float

    # Bias (mean residual)
    bias_x: float
    bias_y: float
    bias_z: float

    # Standard deviation
    std_x: float
    std_y: float
    std_z: float

    # Median absolute deviation (more robust)
    mad_x: float
    mad_y: float
    mad_z: float

    # Percentiles
    p68_x: float  # ~1 sigma
    p68_y: float
    p68_z: float
    p95_x: float  # ~2 sigma
    p95_y: float
    p95_z: float

    def to_dict(self) -> Dict:
        return asdict(self)


def compute_vertex_residuals(
    pred_vertices: np.ndarray,
    true_vertices: np.ndarray,
    event_ids: Optional[np.ndarray] = None,
) -> List[VertexResidual]:
    """
    Compute per-event vertex residuals.

    Args:
        pred_vertices: (N, 3) array of predicted (x, y, z)
        true_vertices: (N, 3) array of true (x, y, z)
        event_ids: Optional array of event IDs

    Returns:
        List of VertexResidual objects
    """
    if event_ids is None:
        event_ids = np.arange(len(pred_vertices))

    residuals = []
    for i in range(len(pred_vertices)):
        dx = pred_vertices[i, 0] - true_vertices[i, 0]
        dy = pred_vertices[i, 1] - true_vertices[i, 1]
        dz = pred_vertices[i, 2] - true_vertices[i, 2]
        dr = np.sqrt(dx**2 + dy**2)

        residuals.append(VertexResidual(
            event_id=int(event_ids[i]),
            true_x=float(true_vertices[i, 0]),
            true_y=float(true_vertices[i, 1]),
            true_z=float(true_vertices[i, 2]),
            pred_x=float(pred_vertices[i, 0]),
            pred_y=float(pred_vertices[i, 1]),
            pred_z=float(pred_vertices[i, 2]),
            residual_x=float(dx),
            residual_y=float(dy),
            residual_z=float(dz),
            residual_r=float(dr),
        ))

    return residuals


def compute_vertex_metrics(residuals: List[VertexResidual]) -> VertexMetrics:
    """
    Compute summary metrics from vertex residuals.

    Args:
        residuals: List of VertexResidual objects

    Returns:
        VertexMetrics with resolution, bias, etc.
    """
    dx = np.array([r.residual_x for r in residuals])
    dy = np.array([r.residual_y for r in residuals])
    dz = np.array([r.residual_z for r in residuals])
    dr = np.array([r.residual_r for r in residuals])
    d3d = np.array([r.residual_3d for r in residuals])

    def mad(x):
        """Median absolute deviation."""
        return np.median(np.abs(x - np.median(x)))

    return VertexMetrics(
        n_events=len(residuals),
        # RMS (resolution)
        resolution_x=float(np.sqrt(np.mean(dx**2))),
        resolution_y=float(np.sqrt(np.mean(dy**2))),
        resolution_z=float(np.sqrt(np.mean(dz**2))),
        resolution_r=float(np.sqrt(np.mean(dr**2))),
        resolution_3d=float(np.sqrt(np.mean(d3d**2))),
        # Bias (mean)
        bias_x=float(np.mean(dx)),
        bias_y=float(np.mean(dy)),
        bias_z=float(np.mean(dz)),
        # Std
        std_x=float(np.std(dx)),
        std_y=float(np.std(dy)),
        std_z=float(np.std(dz)),
        # MAD
        mad_x=float(mad(dx)),
        mad_y=float(mad(dy)),
        mad_z=float(mad(dz)),
        # Percentiles (68% contains ~1 sigma for Gaussian)
        p68_x=float(np.percentile(np.abs(dx), 68)),
        p68_y=float(np.percentile(np.abs(dy), 68)),
        p68_z=float(np.percentile(np.abs(dz), 68)),
        p95_x=float(np.percentile(np.abs(dx), 95)),
        p95_y=float(np.percentile(np.abs(dy), 95)),
        p95_z=float(np.percentile(np.abs(dz), 95)),
    )


def evaluate_vertex_reconstruction(
    pred_vertices: np.ndarray,
    true_vertices: np.ndarray,
    event_ids: Optional[np.ndarray] = None,
) -> Tuple[VertexMetrics, List[VertexResidual]]:
    """
    Full evaluation of vertex reconstruction.

    Args:
        pred_vertices: (N, 3) predicted vertices
        true_vertices: (N, 3) true vertices
        event_ids: Optional event IDs

    Returns:
        Tuple of (summary metrics, per-event residuals)
    """
    residuals = compute_vertex_residuals(pred_vertices, true_vertices, event_ids)
    metrics = compute_vertex_metrics(residuals)
    return metrics, residuals


@dataclass
class MethodComparison:
    """Comparison of two vertex reconstruction methods."""
    method1_name: str
    method2_name: str
    method1_metrics: VertexMetrics
    method2_metrics: VertexMetrics
    improvement_x: float  # Positive = method1 better
    improvement_y: float
    improvement_z: float
    improvement_3d: float

    def to_dict(self) -> Dict:
        return {
            'method1_name': self.method1_name,
            'method2_name': self.method2_name,
            'method1_metrics': self.method1_metrics.to_dict(),
            'method2_metrics': self.method2_metrics.to_dict(),
            'improvement_x': self.improvement_x,
            'improvement_y': self.improvement_y,
            'improvement_z': self.improvement_z,
            'improvement_3d': self.improvement_3d,
        }


def compare_methods(
    method1_pred: np.ndarray,
    method2_pred: np.ndarray,
    true_vertices: np.ndarray,
    method1_name: str = 'GNN',
    method2_name: str = 'Classical',
) -> MethodComparison:
    """
    Compare two vertex reconstruction methods.

    Args:
        method1_pred: (N, 3) predictions from method 1
        method2_pred: (N, 3) predictions from method 2
        true_vertices: (N, 3) true vertices
        method1_name: Name of method 1
        method2_name: Name of method 2

    Returns:
        MethodComparison with relative improvements
    """
    metrics1, _ = evaluate_vertex_reconstruction(method1_pred, true_vertices)
    metrics2, _ = evaluate_vertex_reconstruction(method2_pred, true_vertices)

    # Improvement = (method2 - method1) / method2 * 100
    # Positive means method1 is better
    def improvement(v1, v2):
        if v2 == 0:
            return 0.0
        return (v2 - v1) / v2 * 100

    return MethodComparison(
        method1_name=method1_name,
        method2_name=method2_name,
        method1_metrics=metrics1,
        method2_metrics=metrics2,
        improvement_x=improvement(metrics1.resolution_x, metrics2.resolution_x),
        improvement_y=improvement(metrics1.resolution_y, metrics2.resolution_y),
        improvement_z=improvement(metrics1.resolution_z, metrics2.resolution_z),
        improvement_3d=improvement(metrics1.resolution_3d, metrics2.resolution_3d),
    )


def plot_residuals(
    residuals: List[VertexResidual],
    output_path: Optional[Path] = None,
    title_prefix: str = '',
) -> Optional[plt.Figure]:
    """
    Generate residual distribution plots.

    Args:
        residuals: List of VertexResidual objects
        output_path: Optional path to save figure
        title_prefix: Optional prefix for plot titles

    Returns:
        matplotlib Figure if successful, None if matplotlib unavailable
    """
    if not HAS_MATPLOTLIB:
        print("matplotlib not available, skipping plots")
        return None

    dx = np.array([r.residual_x for r in residuals])
    dy = np.array([r.residual_y for r in residuals])
    dz = np.array([r.residual_z for r in residuals])

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Row 1: Histograms
    for i, (d, label, color) in enumerate([
        (dx, 'X', 'blue'),
        (dy, 'Y', 'green'),
        (dz, 'Z', 'red')
    ]):
        ax = axes[0, i]
        ax.hist(d, bins=50, color=color, alpha=0.7, edgecolor='black')
        ax.axvline(0, color='black', linestyle='--', linewidth=1)
        ax.axvline(np.mean(d), color='orange', linestyle='-', linewidth=2, label=f'Mean: {np.mean(d):.2f}')
        rms = np.sqrt(np.mean(d**2))
        ax.set_xlabel(f'{label} Residual [cm]')
        ax.set_ylabel('Events')
        ax.set_title(f'{title_prefix}{label} Residual (RMS: {rms:.2f} cm)')
        ax.legend()
        ax.grid(True, alpha=0.3)

    # Row 2: 2D distributions
    ax = axes[1, 0]
    ax.scatter(dx, dy, alpha=0.5, s=5)
    ax.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax.axvline(0, color='black', linestyle='--', alpha=0.5)
    ax.set_xlabel('X Residual [cm]')
    ax.set_ylabel('Y Residual [cm]')
    ax.set_title(f'{title_prefix}X vs Y Residuals')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    # True vs predicted for X
    true_x = np.array([r.true_x for r in residuals])
    pred_x = np.array([r.pred_x for r in residuals])
    ax = axes[1, 1]
    ax.scatter(true_x, pred_x, alpha=0.5, s=5)
    lims = [min(true_x.min(), pred_x.min()), max(true_x.max(), pred_x.max())]
    ax.plot(lims, lims, 'r--', label='Perfect')
    ax.set_xlabel('True X [cm]')
    ax.set_ylabel('Predicted X [cm]')
    ax.set_title(f'{title_prefix}True vs Predicted X')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # True vs predicted for Y
    true_y = np.array([r.true_y for r in residuals])
    pred_y = np.array([r.pred_y for r in residuals])
    ax = axes[1, 2]
    ax.scatter(true_y, pred_y, alpha=0.5, s=5)
    lims = [min(true_y.min(), pred_y.min()), max(true_y.max(), pred_y.max())]
    ax.plot(lims, lims, 'r--', label='Perfect')
    ax.set_xlabel('True Y [cm]')
    ax.set_ylabel('Predicted Y [cm]')
    ax.set_title(f'{title_prefix}True vs Predicted Y')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        output_path = Path(output_path)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved residual plots to: {output_path}")

    return fig


def save_vertex_report(
    metrics: VertexMetrics,
    residuals: List[VertexResidual],
    output_dir: Path,
    method_name: str = 'vertex',
    comparison: Optional[MethodComparison] = None,
) -> Dict[str, Path]:
    """
    Save comprehensive vertex evaluation report for debugging.

    Creates:
    - {method_name}_summary.json: Overall metrics
    - {method_name}_residuals.csv: Per-event residuals
    - {method_name}_residuals.png: Residual plots
    - {method_name}_problem_events.csv: Events with large residuals

    Args:
        metrics: VertexMetrics summary
        residuals: Per-event residuals
        output_dir: Directory for output
        method_name: Name prefix for output files
        comparison: Optional method comparison

    Returns:
        Dictionary of saved file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_files = {}

    # Save summary JSON
    summary_data = {
        'generated_at': datetime.datetime.now().isoformat(),
        'method': method_name,
        'n_events': metrics.n_events,
        'metrics': metrics.to_dict(),
    }

    if comparison:
        summary_data['comparison'] = comparison.to_dict()

    summary_path = output_dir / f'{method_name}_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    saved_files['summary'] = summary_path

    # Save residuals CSV
    residuals_df = pd.DataFrame([r.to_dict() for r in residuals])
    residuals_path = output_dir / f'{method_name}_residuals.csv'
    residuals_df.to_csv(residuals_path, index=False)
    saved_files['residuals'] = residuals_path

    # Save plots
    if HAS_MATPLOTLIB:
        plot_path = output_dir / f'{method_name}_residuals.png'
        plot_residuals(residuals, plot_path, title_prefix=f'{method_name}: ')
        saved_files['plots'] = plot_path
        plt.close()

    # Identify problem events (residual_3d > 3 sigma)
    threshold_3d = 3 * metrics.resolution_3d
    problem_residuals = [r for r in residuals if r.residual_3d > threshold_3d]

    if problem_residuals:
        problem_df = pd.DataFrame([r.to_dict() for r in problem_residuals])
        problem_path = output_dir / f'{method_name}_problem_events.csv'
        problem_df.to_csv(problem_path, index=False)
        saved_files['problems'] = problem_path
        print(f"Found {len(problem_residuals)} problem events (residual > {threshold_3d:.1f} cm)")

    return saved_files


def print_vertex_summary(metrics: VertexMetrics, method_name: str = 'Vertex') -> None:
    """Print formatted vertex reconstruction summary."""
    print("\n" + "=" * 60)
    print(f"{method_name.upper()} RECONSTRUCTION SUMMARY")
    print("=" * 60)
    print(f"Number of events: {metrics.n_events}")
    print()
    print("Resolution (RMS) [cm]:")
    print(f"  X:  {metrics.resolution_x:.3f}")
    print(f"  Y:  {metrics.resolution_y:.3f}")
    print(f"  Z:  {metrics.resolution_z:.3f}")
    print(f"  R:  {metrics.resolution_r:.3f}")
    print(f"  3D: {metrics.resolution_3d:.3f}")
    print()
    print("Bias (mean residual) [cm]:")
    print(f"  X: {metrics.bias_x:+.3f}")
    print(f"  Y: {metrics.bias_y:+.3f}")
    print(f"  Z: {metrics.bias_z:+.3f}")
    print()
    print("68th percentile (|residual|) [cm]:")
    print(f"  X: {metrics.p68_x:.3f}")
    print(f"  Y: {metrics.p68_y:.3f}")
    print(f"  Z: {metrics.p68_z:.3f}")
    print()
    print("95th percentile (|residual|) [cm]:")
    print(f"  X: {metrics.p95_x:.3f}")
    print(f"  Y: {metrics.p95_y:.3f}")
    print(f"  Z: {metrics.p95_z:.3f}")
    print("=" * 60)


def print_comparison_summary(comparison: MethodComparison) -> None:
    """Print formatted method comparison summary."""
    m1 = comparison.method1_metrics
    m2 = comparison.method2_metrics

    print("\n" + "=" * 70)
    print(f"METHOD COMPARISON: {comparison.method1_name} vs {comparison.method2_name}")
    print("=" * 70)
    print()
    print(f"{'Metric':<20} {comparison.method1_name:>15} {comparison.method2_name:>15} {'Improvement':>15}")
    print("-" * 70)
    print(f"{'Resolution X [cm]':<20} {m1.resolution_x:>15.3f} {m2.resolution_x:>15.3f} {comparison.improvement_x:>14.1f}%")
    print(f"{'Resolution Y [cm]':<20} {m1.resolution_y:>15.3f} {m2.resolution_y:>15.3f} {comparison.improvement_y:>14.1f}%")
    print(f"{'Resolution Z [cm]':<20} {m1.resolution_z:>15.3f} {m2.resolution_z:>15.3f} {comparison.improvement_z:>14.1f}%")
    print(f"{'Resolution 3D [cm]':<20} {m1.resolution_3d:>15.3f} {m2.resolution_3d:>15.3f} {comparison.improvement_3d:>14.1f}%")
    print()
    print(f"Note: Positive improvement means {comparison.method1_name} is better")
    print("=" * 70)


if __name__ == "__main__":
    """Test vertex evaluation with synthetic data."""
    np.random.seed(42)

    # Generate synthetic data
    n_events = 100

    # True vertices from NNBAR geometry (annihilation in target)
    true_vertices = np.column_stack([
        np.random.normal(0, 5, n_events),   # x ~ N(0, 5cm)
        np.random.normal(0, 5, n_events),   # y ~ N(0, 5cm)
        np.zeros(n_events),                  # z = 0 (target plane)
    ])

    # Simulated GNN predictions (some noise + small bias)
    gnn_pred = true_vertices + np.column_stack([
        np.random.normal(0.5, 8, n_events),   # x: 8cm resolution, 0.5cm bias
        np.random.normal(-0.3, 7, n_events),  # y: 7cm resolution, -0.3cm bias
        np.random.normal(0, 2, n_events),     # z: 2cm resolution (easier)
    ])

    # Simulated classical predictions (larger errors)
    classical_pred = true_vertices + np.column_stack([
        np.random.normal(0.8, 12, n_events),   # x: 12cm resolution
        np.random.normal(-0.5, 11, n_events),  # y: 11cm resolution
        np.random.normal(0, 3, n_events),      # z: 3cm resolution
    ])

    # Evaluate GNN
    print("Evaluating GNN vertex reconstruction...")
    gnn_metrics, gnn_residuals = evaluate_vertex_reconstruction(
        gnn_pred, true_vertices, event_ids=np.arange(n_events)
    )
    print_vertex_summary(gnn_metrics, "GNN")

    # Evaluate Classical
    print("\nEvaluating classical vertex reconstruction...")
    classical_metrics, classical_residuals = evaluate_vertex_reconstruction(
        classical_pred, true_vertices, event_ids=np.arange(n_events)
    )
    print_vertex_summary(classical_metrics, "Classical")

    # Compare methods
    print("\nComparing methods...")
    comparison = compare_methods(gnn_pred, classical_pred, true_vertices, "GNN", "Classical")
    print_comparison_summary(comparison)

    # Save reports
    output_dir = Path("/home/billy/nnbar/simulation/nnbar_reconstruction/output/vertex_eval")
    print(f"\nSaving reports to: {output_dir}")

    gnn_files = save_vertex_report(
        gnn_metrics, gnn_residuals, output_dir,
        method_name='gnn', comparison=comparison
    )
    print(f"GNN files saved: {list(gnn_files.keys())}")

    classical_files = save_vertex_report(
        classical_metrics, classical_residuals, output_dir,
        method_name='classical'
    )
    print(f"Classical files saved: {list(classical_files.keys())}")
