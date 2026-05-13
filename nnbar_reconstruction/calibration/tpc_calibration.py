"""
TPC Ionization and dE/dx Calibration Module

Calibrates the TPC ionization response:
- W-value: 23.6 eV per electron-ion pair (from simulation)
- dE/dx response vs particle type and momentum
- Bethe-Bloch validation

The TPC is critical for:
- Track finding
- Particle identification (pion vs proton)
- Momentum estimation via dE/dx

Author: NNBAR Collaboration
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import yaml

from ..utils.config import get_config


# Physical constants
ELECTRON_MASS = 0.511  # MeV/c^2
SPEED_OF_LIGHT = 29.979  # cm/ns
PION_MASS = 139.57  # MeV/c^2
PROTON_MASS = 938.27  # MeV/c^2
KAON_MASS = 493.68  # MeV/c^2
MUON_MASS = 105.66  # MeV/c^2


@dataclass
class TPCLayerCalibration:
    """Calibration parameters for a single TPC layer."""
    layer_id: int

    # Ionization parameters
    w_value: float = 23.6  # eV per electron-ion pair

    # Gain correction
    gain: float = 1.0

    # Pedestal
    pedestal: float = 0.0

    # Layer geometry
    inner_radius: float = 0.0  # cm
    outer_radius: float = 0.0  # cm
    thickness: float = 4.25    # cm (drift length per layer)

    # Calibration quality
    n_events: int = 0


@dataclass
class TPCCalibration:
    """Complete TPC calibration."""
    layer_calibrations: Dict[int, TPCLayerCalibration] = field(default_factory=dict)

    # Global parameters
    nominal_w_value: float = 23.6      # eV per electron-ion pair
    drift_velocity: float = 0.16       # cm/ns (typical for LAr, ~1.6 mm/μs)

    # dE/dx parameters for Bethe-Bloch
    Z_over_A: float = 0.451           # Z/A for argon
    mean_excitation: float = 188.0    # Mean excitation energy I (eV)
    density: float = 1.784e-3         # g/cm^3 (gaseous argon at STP)
    K: float = 0.307075               # MeV cm^2/mol

    # Truncated mean parameters
    truncation_low: float = 0.0       # Fraction to truncate from low end
    truncation_high: float = 0.4      # Fraction to truncate from high end

    def get_layer(self, layer_id: int) -> TPCLayerCalibration:
        """Get calibration for a specific layer."""
        if layer_id not in self.layer_calibrations:
            return TPCLayerCalibration(layer_id)
        return self.layer_calibrations[layer_id]

    def set_layer(self, calib: TPCLayerCalibration):
        """Set calibration for a layer."""
        self.layer_calibrations[calib.layer_id] = calib

    def save(self, path: str):
        """Save calibration to YAML file."""
        data = {
            'global': {
                'nominal_w_value': self.nominal_w_value,
                'drift_velocity': self.drift_velocity,
                'Z_over_A': self.Z_over_A,
                'mean_excitation': self.mean_excitation,
                'density': self.density,
                'K': self.K,
                'truncation_low': self.truncation_low,
                'truncation_high': self.truncation_high,
            },
            'layers': []
        }

        for layer_id, cal in self.layer_calibrations.items():
            layer_data = {
                'layer_id': cal.layer_id,
                'w_value': cal.w_value,
                'gain': cal.gain,
                'pedestal': cal.pedestal,
                'inner_radius': cal.inner_radius,
                'outer_radius': cal.outer_radius,
                'thickness': cal.thickness,
                'n_events': cal.n_events,
            }
            data['layers'].append(layer_data)

        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    @classmethod
    def load(cls, path: str) -> 'TPCCalibration':
        """Load calibration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        cal = cls()
        if 'global' in data:
            g = data['global']
            cal.nominal_w_value = g.get('nominal_w_value', 23.6)
            cal.drift_velocity = g.get('drift_velocity', 0.16)
            cal.Z_over_A = g.get('Z_over_A', 0.451)
            cal.mean_excitation = g.get('mean_excitation', 188.0)
            cal.density = g.get('density', 1.784e-3)
            cal.K = g.get('K', 0.307075)
            cal.truncation_low = g.get('truncation_low', 0.0)
            cal.truncation_high = g.get('truncation_high', 0.4)

        if 'layers' in data:
            for layer_data in data['layers']:
                layer_cal = TPCLayerCalibration(
                    layer_id=layer_data['layer_id'],
                    w_value=layer_data.get('w_value', 23.6),
                    gain=layer_data.get('gain', 1.0),
                    pedestal=layer_data.get('pedestal', 0.0),
                    inner_radius=layer_data.get('inner_radius', 0.0),
                    outer_radius=layer_data.get('outer_radius', 0.0),
                    thickness=layer_data.get('thickness', 4.25),
                    n_events=layer_data.get('n_events', 0),
                )
                cal.set_layer(layer_cal)

        return cal


# ============================================================================
# Bethe-Bloch Functions
# ============================================================================

def bethe_bloch_dedx(
    momentum: float,
    mass: float,
    calibration: TPCCalibration,
    charge: int = 1,
) -> float:
    """
    Calculate dE/dx using the Bethe-Bloch formula.

    Args:
        momentum: Particle momentum in MeV/c
        mass: Particle mass in MeV/c^2
        calibration: TPC calibration with medium parameters
        charge: Particle charge (units of e)

    Returns:
        dE/dx in MeV/cm
    """
    if momentum <= 0:
        return 0.0

    # Relativistic parameters
    E = np.sqrt(momentum**2 + mass**2)
    beta = momentum / E
    gamma = E / mass
    beta_gamma = beta * gamma

    if beta <= 0 or beta >= 1:
        return 0.0

    # Bethe-Bloch formula
    K = calibration.K
    z = charge
    Z_A = calibration.Z_over_A
    I = calibration.mean_excitation * 1e-6  # Convert eV to MeV
    rho = calibration.density

    # Tmax (maximum energy transfer per collision)
    me = ELECTRON_MASS
    Tmax = (2 * me * beta_gamma**2) / (1 + 2 * gamma * me / mass + (me / mass)**2)

    # Main Bethe-Bloch term
    ln_term = np.log(2 * me * beta_gamma**2 * Tmax / I**2)

    # Density correction (simplified, delta ~ 0 for low energies)
    delta = 0.0

    # Shell correction (simplified)
    C = 0.0

    dedx = K * z**2 * Z_A * rho / beta**2 * (0.5 * ln_term - beta**2 - delta/2 - C/Z_A)

    return max(0.0, dedx)


def generate_bethe_bloch_curve(
    mass: float,
    calibration: TPCCalibration,
    momentum_range: Tuple[float, float] = (50, 5000),
    n_points: int = 100,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Bethe-Bloch curve for a particle type.

    Args:
        mass: Particle mass in MeV/c^2
        calibration: TPC calibration
        momentum_range: (min, max) momentum in MeV/c
        n_points: Number of points

    Returns:
        (momenta, dedx) arrays
    """
    momenta = np.logspace(
        np.log10(momentum_range[0]),
        np.log10(momentum_range[1]),
        n_points
    )

    dedx = np.array([bethe_bloch_dedx(p, mass, calibration) for p in momenta])

    return momenta, dedx


# ============================================================================
# dE/dx Calculation
# ============================================================================

def electrons_to_energy(
    n_electrons: float,
    calibration: TPCLayerCalibration,
) -> float:
    """
    Convert electron count to energy deposit.

    Args:
        n_electrons: Number of ionization electrons
        calibration: Layer calibration

    Returns:
        Energy in MeV
    """
    # Subtract pedestal
    corrected = n_electrons - calibration.pedestal

    if corrected <= 0:
        return 0.0

    # Apply gain correction
    corrected *= calibration.gain

    # Convert using W-value (eV per ion pair)
    energy_ev = corrected * calibration.w_value
    energy_mev = energy_ev * 1e-6

    return energy_mev


def calculate_dedx_per_layer(
    layer_electrons: List[float],
    layer_lengths: List[float],
    calibration: TPCCalibration,
    truncate: bool = True,
) -> float:
    """
    Calculate dE/dx using truncated mean method.

    Args:
        layer_electrons: Electron count per layer
        layer_lengths: Track length per layer (cm)
        calibration: TPC calibration
        truncate: Whether to apply truncated mean

    Returns:
        dE/dx in MeV/cm
    """
    if len(layer_electrons) == 0 or len(layer_lengths) == 0:
        return 0.0

    # Convert electrons to energy
    energies = []
    for i, (n_e, dx) in enumerate(zip(layer_electrons, layer_lengths)):
        layer_cal = calibration.get_layer(i)
        E = electrons_to_energy(n_e, layer_cal)
        energies.append(E)

    energies = np.array(energies)
    lengths = np.array(layer_lengths)

    # Calculate dE/dx per layer
    valid = lengths > 0.1  # Minimum 1mm track length
    if not np.any(valid):
        return 0.0

    dedx_per_layer = energies[valid] / lengths[valid]

    if len(dedx_per_layer) == 0:
        return 0.0

    if truncate and len(dedx_per_layer) >= 3:
        # Sort and apply truncated mean
        sorted_dedx = np.sort(dedx_per_layer)
        n = len(sorted_dedx)

        low_cut = int(n * calibration.truncation_low)
        high_cut = int(n * (1 - calibration.truncation_high))

        if high_cut <= low_cut:
            high_cut = low_cut + 1

        truncated = sorted_dedx[low_cut:high_cut]
        return np.mean(truncated)
    else:
        return np.mean(dedx_per_layer)


def calculate_track_dedx(
    hits_df: pd.DataFrame,
    calibration: TPCCalibration,
    truncate: bool = True,
) -> Tuple[float, float]:
    """
    Calculate dE/dx for a track from hits DataFrame.

    Args:
        hits_df: DataFrame with columns:
            - 'electrons': Number of ionization electrons
            - 'Layer_ID': Layer identifier
            - 'x', 'y', 'z': Position (for path length calculation)
        calibration: TPC calibration
        truncate: Whether to apply truncated mean

    Returns:
        (dedx, dedx_error) tuple
    """
    if len(hits_df) < 3:
        return 0.0, 0.0

    # Group by layer
    layer_groups = hits_df.groupby('Layer_ID')

    layer_electrons = []
    layer_lengths = []

    sorted_layers = sorted(layer_groups.groups.keys())

    for layer_id in sorted_layers:
        group = layer_groups.get_group(layer_id)

        # Total electrons in layer
        n_e = group['electrons'].sum()

        # Approximate track length in layer
        if len(group) > 1:
            # Use hit positions to estimate path length
            x = group['x'].values
            y = group['y'].values
            z = group['z'].values

            # Sum distances between consecutive hits
            dx = np.diff(x)
            dy = np.diff(y)
            dz = np.diff(z)
            path_length = np.sum(np.sqrt(dx**2 + dy**2 + dz**2))

            # Minimum path length
            path_length = max(path_length, 0.5)
        else:
            # Single hit - use layer thickness
            layer_cal = calibration.get_layer(layer_id)
            path_length = layer_cal.thickness

        layer_electrons.append(n_e)
        layer_lengths.append(path_length)

    dedx = calculate_dedx_per_layer(
        layer_electrons, layer_lengths, calibration, truncate
    )

    # Estimate error from RMS of per-layer values
    if len(layer_electrons) >= 3:
        dedx_values = []
        for n_e, dx in zip(layer_electrons, layer_lengths):
            if dx > 0.1:
                dedx_values.append(n_e * calibration.nominal_w_value * 1e-6 / dx)

        if dedx_values:
            dedx_error = np.std(dedx_values) / np.sqrt(len(dedx_values))
        else:
            dedx_error = 0.0
    else:
        dedx_error = dedx * 0.2  # 20% error estimate

    return dedx, dedx_error


# ============================================================================
# Particle Identification via dE/dx
# ============================================================================

def identify_particle_by_dedx(
    dedx: float,
    momentum: float,
    calibration: TPCCalibration,
) -> Tuple[str, float]:
    """
    Identify particle type based on dE/dx and momentum.

    Args:
        dedx: Measured dE/dx in MeV/cm
        momentum: Measured/estimated momentum in MeV/c
        calibration: TPC calibration

    Returns:
        (particle_type, confidence) tuple
    """
    if dedx <= 0 or momentum <= 0:
        return "unknown", 0.0

    # Calculate expected dE/dx for each particle type
    particles = {
        'pion': PION_MASS,
        'proton': PROTON_MASS,
        'kaon': KAON_MASS,
        'muon': MUON_MASS,
    }

    chi2_values = {}
    for name, mass in particles.items():
        expected = bethe_bloch_dedx(momentum, mass, calibration)
        if expected > 0:
            # Assume 20% resolution
            sigma = 0.20 * expected
            chi2 = ((dedx - expected) / sigma) ** 2
            chi2_values[name] = chi2

    if not chi2_values:
        return "unknown", 0.0

    # Find best match
    best_particle = min(chi2_values, key=chi2_values.get)
    best_chi2 = chi2_values[best_particle]

    # Confidence based on chi2
    confidence = np.exp(-0.5 * best_chi2)

    return best_particle, float(confidence)


def pion_proton_separation(
    dedx: float,
    n_scintillator_layers: int,
    calibration: TPCCalibration,
) -> Tuple[str, float]:
    """
    Distinguish pion from proton using dE/dx and scintillator range.

    This is the hadronic range detector concept from the thesis.

    Args:
        dedx: Measured dE/dx in MeV/cm
        n_scintillator_layers: Number of scintillator layers traversed
        calibration: TPC calibration

    Returns:
        (particle_type, confidence) tuple
    """
    # Threshold table based on range (Table 8.1 from thesis)
    # threshold(n) separates pions from protons
    thresholds = {
        0: 4.0,   # MeV/cm
        1: 3.5,
        2: 3.2,
        3: 3.0,
        4: 2.8,
        5: 2.6,
    }

    n = min(n_scintillator_layers, 5)
    threshold = thresholds.get(n, 2.6)

    # Above threshold = proton (higher dE/dx)
    # Below threshold = pion
    if dedx > threshold:
        particle = "proton"
        # Confidence increases with distance from threshold
        confidence = 1.0 - np.exp(-(dedx - threshold) / 1.0)
    else:
        particle = "pion"
        confidence = 1.0 - np.exp(-(threshold - dedx) / 1.0)

    return particle, float(np.clip(confidence, 0.5, 0.99))


# ============================================================================
# Calibration Fitting
# ============================================================================

def fit_w_value(
    data: pd.DataFrame,
    layer_id: int,
) -> Optional[TPCLayerCalibration]:
    """
    Fit W-value for a TPC layer using known energy deposits.

    Args:
        data: DataFrame with columns:
            - 'electrons': Ionization electrons
            - 'energy_dep': True energy deposit (from truth)
            - 'Layer_ID': Layer identifier
        layer_id: Layer to calibrate

    Returns:
        TPCLayerCalibration or None
    """
    mask = (data['Layer_ID'] == layer_id) & (data['energy_dep'] > 0)
    layer_data = data[mask]

    if len(layer_data) < 10:
        return None

    E = layer_data['energy_dep'].values  # MeV
    N = layer_data['electrons'].values

    # W-value: N = E / W, so W = E / N (in MeV, need to convert)
    valid = N > 0
    if not np.any(valid):
        return None

    # W = E * 1e6 / N (convert MeV to eV)
    w_values = E[valid] * 1e6 / N[valid]

    w_mean = np.median(w_values)
    w_std = np.std(w_values)

    calib = TPCLayerCalibration(
        layer_id=layer_id,
        w_value=float(w_mean),
        n_events=len(layer_data),
    )

    return calib


def run_tpc_calibration(
    data: pd.DataFrame,
    output_path: Optional[str] = None,
    min_events: int = 10,
) -> TPCCalibration:
    """
    Run calibration for all TPC layers.

    Args:
        data: DataFrame with TPC hits
        output_path: Path to save calibration (optional)
        min_events: Minimum events per layer

    Returns:
        TPCCalibration object
    """
    calibration = TPCCalibration()

    # Get unique layer IDs
    layer_counts = data.groupby('Layer_ID').size()

    print(f"[TPC Calibration] Found {len(layer_counts)} layers")

    n_calibrated = 0

    for layer_id, n_hits in layer_counts.items():
        if n_hits < min_events:
            continue

        layer_cal = fit_w_value(data, layer_id)

        if layer_cal is not None:
            calibration.set_layer(layer_cal)
            n_calibrated += 1

    print(f"[TPC Calibration] Calibrated: {n_calibrated} layers")

    # Update global W-value
    if calibration.layer_calibrations:
        w_values = [c.w_value for c in calibration.layer_calibrations.values()]
        calibration.nominal_w_value = float(np.median(w_values))
        print(f"[TPC Calibration] Median W-value: {calibration.nominal_w_value:.2f} eV")

    if output_path:
        calibration.save(output_path)
        print(f"[TPC Calibration] Saved to: {output_path}")

    return calibration


# ============================================================================
# Validation Plots
# ============================================================================

def plot_bethe_bloch_comparison(
    data: pd.DataFrame,
    calibration: TPCCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot measured dE/dx vs momentum with Bethe-Bloch curves.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot measured data if available
    if 'dedx' in data.columns and 'momentum' in data.columns:
        mask = (data['momentum'] > 0) & (data['dedx'] > 0)
        ax.scatter(data.loc[mask, 'momentum'],
                   data.loc[mask, 'dedx'],
                   s=1, alpha=0.3, c='gray', label='Data')

    # Generate Bethe-Bloch curves
    particles = {
        'Pion': (PION_MASS, 'blue'),
        'Proton': (PROTON_MASS, 'red'),
        'Kaon': (KAON_MASS, 'green'),
        'Muon': (MUON_MASS, 'orange'),
    }

    for name, (mass, color) in particles.items():
        p, dedx = generate_bethe_bloch_curve(mass, calibration)
        ax.plot(p, dedx, color=color, linewidth=2, label=f'{name} (m={mass:.1f} MeV)')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Momentum (MeV/c)', fontsize=12)
    ax.set_ylabel('dE/dx (MeV/cm)', fontsize=12)
    ax.set_title('TPC dE/dx vs Momentum', fontsize=14)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, which='both')
    ax.set_xlim(50, 5000)
    ax.set_ylim(0.5, 20)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


def plot_w_value_distribution(
    calibration: TPCCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot W-value distribution across layers.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    if not calibration.layer_calibrations:
        print("No layer calibrations available")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    w_values = [c.w_value for c in calibration.layer_calibrations.values()]

    ax.hist(w_values, bins=20, histtype='step', linewidth=2)
    ax.axvline(calibration.nominal_w_value, color='red', linestyle='--',
               label=f'Nominal: {calibration.nominal_w_value:.2f} eV')
    ax.axvline(23.6, color='green', linestyle=':',
               label='Theory: 23.6 eV')

    ax.set_xlabel('W-value (eV)', fontsize=12)
    ax.set_ylabel('Number of Layers', fontsize=12)
    ax.set_title('TPC W-value Distribution', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


def plot_dedx_resolution(
    data: pd.DataFrame,
    calibration: TPCCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot dE/dx resolution vs number of measurement layers.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    if 'n_layers' in data.columns and 'dedx' in data.columns and 'dedx_true' in data.columns:
        # Compute resolution vs number of layers
        n_layer_bins = range(3, 21)
        resolutions = []

        for n in n_layer_bins:
            mask = data['n_layers'] == n
            if mask.sum() < 10:
                resolutions.append(np.nan)
                continue

            residuals = (data.loc[mask, 'dedx'] - data.loc[mask, 'dedx_true']) / data.loc[mask, 'dedx_true']
            resolutions.append(np.std(residuals))

        ax.scatter(n_layer_bins, resolutions, s=50, c='blue')

        # Fit 1/√N
        valid = ~np.isnan(resolutions)
        if np.sum(valid) > 3:
            n_arr = np.array(list(n_layer_bins))[valid]
            r_arr = np.array(resolutions)[valid]

            def model(n, a):
                return a / np.sqrt(n)

            from scipy.optimize import curve_fit
            try:
                popt, _ = curve_fit(model, n_arr, r_arr, p0=[0.5])
                n_fit = np.linspace(3, 20, 50)
                ax.plot(n_fit, model(n_fit, *popt), 'r-', linewidth=2,
                        label=f'Fit: {popt[0]:.2f}/√N')
            except:
                pass

    ax.set_xlabel('Number of Layers', fontsize=12)
    ax.set_ylabel('dE/dx Resolution (σ/E)', fontsize=12)
    ax.set_title('TPC dE/dx Resolution', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


__all__ = [
    "TPCLayerCalibration",
    "TPCCalibration",
    "PION_MASS",
    "PROTON_MASS",
    "KAON_MASS",
    "MUON_MASS",
    "bethe_bloch_dedx",
    "generate_bethe_bloch_curve",
    "electrons_to_energy",
    "calculate_dedx_per_layer",
    "calculate_track_dedx",
    "identify_particle_by_dedx",
    "pion_proton_separation",
    "fit_w_value",
    "run_tpc_calibration",
    "plot_bethe_bloch_comparison",
    "plot_w_value_distribution",
    "plot_dedx_resolution",
]
