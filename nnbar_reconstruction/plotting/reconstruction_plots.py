"""
Plotting functions for NNBAR reconstruction results.

Key plots:
- Invariant mass distribution (target: peak at 1.88 GeV)
- Sphericity distribution
- Vertex resolution
- dE/dx vs momentum (particle ID)
"""

import numpy as np
from typing import Optional, List, Tuple
import pandas as pd

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def check_matplotlib():
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib required for plotting. Install with: pip install matplotlib")


def plot_invariant_mass(
    df: pd.DataFrame,
    column: str = 'invariant_mass',
    bins: int = 50,
    range: Tuple[float, float] = (0, 3000),
    fit_gaussian: bool = True,
    save_path: Optional[str] = None,
) -> Optional[plt.Figure]:
    """
    Plot invariant mass distribution.

    Target: Peak at ~1880 MeV (2 * nucleon mass) with minimal width.

    Args:
        df: DataFrame with reconstruction results.
        column: Column name for invariant mass.
        bins: Number of histogram bins.
        range: (min, max) range in MeV.
        fit_gaussian: Whether to fit a Gaussian to the peak.
        save_path: Path to save figure.

    Returns:
        matplotlib Figure or None.
    """
    check_matplotlib()

    masses = df.loc[df['success'] == True, column].dropna()

    if len(masses) == 0:
        print("No valid masses to plot")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Histogram
    counts, bin_edges, _ = ax.hist(
        masses, bins=bins, range=range,
        histtype='step', linewidth=2, color='blue',
        label=f'Reconstructed (N={len(masses)})'
    )

    # Mark target mass
    target_mass = 1880  # MeV
    ax.axvline(target_mass, color='red', linestyle='--', linewidth=2,
               label=f'Target: {target_mass} MeV (2m_n)')

    # Fit Gaussian if requested
    if fit_gaussian and len(masses) > 10:
        from scipy.optimize import curve_fit
        from scipy.stats import norm

        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        # Initial guess
        mu0 = masses.mean()
        sigma0 = masses.std()
        A0 = counts.max()

        def gaussian(x, A, mu, sigma):
            return A * np.exp(-0.5 * ((x - mu) / sigma)**2)

        try:
            popt, _ = curve_fit(gaussian, bin_centers, counts, p0=[A0, mu0, sigma0])
            A, mu, sigma = popt

            x_fit = np.linspace(range[0], range[1], 200)
            y_fit = gaussian(x_fit, A, mu, sigma)
            ax.plot(x_fit, y_fit, 'r-', linewidth=2,
                    label=f'Gaussian: $\mu$={mu:.0f} MeV, $\sigma$={sigma:.0f} MeV')
        except:
            pass

    # Statistics
    mean = masses.mean()
    std = masses.std()
    median = masses.median()

    stats_text = f'Mean: {mean:.0f} MeV\nStd: {std:.0f} MeV\nMedian: {median:.0f} MeV'
    ax.text(0.95, 0.95, stats_text, transform=ax.transAxes,
            verticalalignment='top', horizontalalignment='right',
            fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.set_xlabel('Invariant Mass (MeV)', fontsize=12)
    ax.set_ylabel('Events', fontsize=12)
    ax.set_title('NNBAR Reconstruction - Invariant Mass', fontsize=14)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

    # Secondary x-axis in GeV
    ax2 = ax.twiny()
    ax2.set_xlim(range[0]/1000, range[1]/1000)
    ax2.set_xlabel('Invariant Mass (GeV)', fontsize=12)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


def plot_sphericity(
    df: pd.DataFrame,
    column: str = 'sphericity',
    bins: int = 40,
    save_path: Optional[str] = None,
) -> Optional[plt.Figure]:
    """
    Plot sphericity distribution.

    Signal events should be isotropic (high sphericity).
    Background tends to be pencil-like (low sphericity).

    Args:
        df: DataFrame with reconstruction results.
        column: Column name for sphericity.
        bins: Number of histogram bins.
        save_path: Path to save figure.

    Returns:
        matplotlib Figure or None.
    """
    check_matplotlib()

    sphericity = df.loc[df['success'] == True, column].dropna()

    if len(sphericity) == 0:
        print("No valid sphericity values to plot")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(sphericity, bins=bins, range=(0, 1),
            histtype='step', linewidth=2, color='blue',
            label=f'All events (N={len(sphericity)})')

    # Mark cut value
    cut_value = 0.2
    ax.axvline(cut_value, color='red', linestyle='--', linewidth=2,
               label=f'Cut: S > {cut_value}')

    # Fill signal region
    ax.axvspan(cut_value, 1, alpha=0.1, color='green', label='Signal region')

    ax.set_xlabel('Sphericity', fontsize=12)
    ax.set_ylabel('Events', fontsize=12)
    ax.set_title('NNBAR Reconstruction - Event Sphericity', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    return fig


def plot_vertex_resolution(
    df: pd.DataFrame,
    column: str = 'vertex_residual',
    bins: int = 50,
    range: Tuple[float, float] = (0, 50),
    save_path: Optional[str] = None,
) -> Optional[plt.Figure]:
    """
    Plot vertex resolution (distance from truth).

    Args:
        df: DataFrame with reconstruction results.
        column: Column name for vertex residual.
        bins: Number of histogram bins.
        range: (min, max) range in cm.
        save_path: Path to save figure.

    Returns:
        matplotlib Figure or None.
    """
    check_matplotlib()

    if column not in df.columns:
        print(f"Column '{column}' not found in DataFrame")
        return None

    residuals = df.loc[df['vertex_valid'] == True, column].dropna()

    if len(residuals) == 0:
        print("No valid vertex residuals to plot")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(residuals, bins=bins, range=range,
            histtype='step', linewidth=2, color='blue',
            label=f'N={len(residuals)}')

    # Statistics
    mean = residuals.mean()
    median = residuals.median()
    rms = np.sqrt((residuals**2).mean())

    ax.axvline(mean, color='red', linestyle='-', linewidth=2, label=f'Mean: {mean:.2f} cm')
    ax.axvline(median, color='green', linestyle='--', linewidth=2, label=f'Median: {median:.2f} cm')

    stats_text = f'Mean: {mean:.2f} cm\nMedian: {median:.2f} cm\nRMS: {rms:.2f} cm'
    ax.text(0.95, 0.95, stats_text, transform=ax.transAxes,
            verticalalignment='top', horizontalalignment='right',
            fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.set_xlabel('Vertex Residual (cm)', fontsize=12)
    ax.set_ylabel('Events', fontsize=12)
    ax.set_title('NNBAR Reconstruction - Vertex Resolution', fontsize=14)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    return fig


def plot_dedx_vs_momentum(
    momenta_pion: np.ndarray,
    dedx_pion: np.ndarray,
    momenta_proton: np.ndarray,
    dedx_proton: np.ndarray,
    data_momenta: Optional[np.ndarray] = None,
    data_dedx: Optional[np.ndarray] = None,
    save_path: Optional[str] = None,
) -> Optional[plt.Figure]:
    """
    Plot dE/dx vs momentum for particle identification.

    Shows Bethe-Bloch curves for pions and protons.

    Args:
        momenta_pion: Momentum array for pion curve (MeV/c).
        dedx_pion: dE/dx array for pion curve.
        momenta_proton: Momentum array for proton curve.
        dedx_proton: dE/dx array for proton curve.
        data_momenta: Measured momenta (optional).
        data_dedx: Measured dE/dx (optional).
        save_path: Path to save figure.

    Returns:
        matplotlib Figure or None.
    """
    check_matplotlib()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Bethe-Bloch curves
    ax.plot(momenta_pion, dedx_pion, 'b-', linewidth=2, label='Pion (Bethe-Bloch)')
    ax.plot(momenta_proton, dedx_proton, 'r-', linewidth=2, label='Proton (Bethe-Bloch)')

    # Data points
    if data_momenta is not None and data_dedx is not None:
        ax.scatter(data_momenta, data_dedx, s=10, alpha=0.5, c='gray', label='Data')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Momentum (MeV/c)', fontsize=12)
    ax.set_ylabel('dE/dx (MeV/cm)', fontsize=12)
    ax.set_title('Particle Identification: dE/dx vs Momentum', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3, which='both')

    ax.set_xlim(50, 5000)
    ax.set_ylim(0.5, 20)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    return fig


def plot_selection_efficiency(
    df: pd.DataFrame,
    is_signal: np.ndarray,
    cut_names: Optional[List[str]] = None,
    save_path: Optional[str] = None,
) -> Optional[plt.Figure]:
    """
    Plot selection efficiency as function of sequential cuts.

    Args:
        df: DataFrame with reconstruction results.
        is_signal: Boolean array indicating signal events.
        cut_names: Names of cuts (columns starting with 'cut_').
        save_path: Path to save figure.

    Returns:
        matplotlib Figure or None.
    """
    check_matplotlib()

    if cut_names is None:
        cut_names = [col for col in df.columns if col.startswith('cut_')]

    if len(cut_names) == 0:
        print("No cut columns found")
        return None

    # Compute cumulative efficiency
    n_signal = is_signal.sum()
    n_background = len(is_signal) - n_signal

    signal_eff = [1.0]
    background_rej = [0.0]

    cumulative_mask = np.ones(len(df), dtype=bool)

    for cut_name in cut_names:
        if cut_name in df.columns:
            cumulative_mask = cumulative_mask & df[cut_name].values

            sig_passed = (cumulative_mask & is_signal).sum()
            bkg_passed = (cumulative_mask & ~is_signal).sum()

            signal_eff.append(sig_passed / n_signal if n_signal > 0 else 0)
            background_rej.append(1 - bkg_passed / n_background if n_background > 0 else 1)

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(cut_names) + 1)
    labels = ['Initial'] + [c.replace('cut_', '') for c in cut_names]

    ax.plot(x, signal_eff, 'b-o', linewidth=2, markersize=8, label='Signal Efficiency')
    ax.plot(x, background_rej, 'r-s', linewidth=2, markersize=8, label='Background Rejection')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_xlabel('Cut', fontsize=12)
    ax.set_ylabel('Efficiency / Rejection', fontsize=12)
    ax.set_title('Event Selection: Signal Efficiency vs Background Rejection', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    return fig


if __name__ == "__main__":
    # Test plotting with mock data
    check_matplotlib()

    # Generate Bethe-Bloch curves
    from ..reconstruction.object_identification import generate_dedx_lookup_table

    momenta_pion, dedx_pion = generate_dedx_lookup_table(139.57)
    momenta_proton, dedx_proton = generate_dedx_lookup_table(938.27)

    fig = plot_dedx_vs_momentum(momenta_pion, dedx_pion, momenta_proton, dedx_proton)
    plt.show()
