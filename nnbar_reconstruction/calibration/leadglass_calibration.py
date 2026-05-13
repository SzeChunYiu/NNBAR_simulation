"""
Lead Glass Cerenkov Photon Calibration Module

Calibrates the relationship between deposited electromagnetic energy
and detected Cerenkov photons in lead glass calorimeter modules.

Unlike scintillators, lead glass produces Cerenkov radiation proportional
to the number of charged particles above the Cerenkov threshold.

Key parameters:
- Cerenkov photon yield (from Geant4 physics)
- Module-by-module calibration constants
- Shower containment corrections

Author: NNBAR Collaboration
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import yaml

from ..utils.config import get_config


@dataclass
class LeadGlassModuleCalibration:
    """Calibration parameters for a single lead glass module."""
    module_id: int

    # Cerenkov photon yield (photons per MeV)
    cerenkov_yield: float = 200.0

    # Energy scale factor (for absolute calibration)
    energy_scale: float = 1.0

    # Pedestal (ADC counts or equivalent)
    pedestal: float = 0.0

    # Energy resolution parameters: σ/E = a/√E ⊕ b
    resolution_stochastic: float = 0.05  # a term
    resolution_constant: float = 0.02    # b term

    # Position of module center (cm)
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0

    # Edge correction (for shower leakage)
    edge_correction: float = 1.0

    # Calibration quality
    fit_chi2: float = -1.0
    n_events: int = 0


@dataclass
class LeadGlassCalibration:
    """Complete lead glass calorimeter calibration."""
    module_calibrations: Dict[int, LeadGlassModuleCalibration] = field(
        default_factory=dict
    )

    # Global parameters
    nominal_cerenkov_yield: float = 200.0    # photons/MeV
    nominal_resolution_stochastic: float = 0.05
    nominal_resolution_constant: float = 0.02

    # Timing parameters
    timing_offset: float = 0.0               # ns
    timing_resolution: float = 2.0           # ns

    # Shower parameters
    moliere_radius: float = 3.5              # cm
    radiation_length: float = 1.76           # cm

    def get_module(self, module_id: int) -> LeadGlassModuleCalibration:
        """Get calibration for a specific module."""
        if module_id not in self.module_calibrations:
            return LeadGlassModuleCalibration(module_id)
        return self.module_calibrations[module_id]

    def set_module(self, calib: LeadGlassModuleCalibration):
        """Set calibration for a module."""
        self.module_calibrations[calib.module_id] = calib

    def save(self, path: str):
        """Save calibration to YAML file."""
        data = {
            'global': {
                'nominal_cerenkov_yield': self.nominal_cerenkov_yield,
                'nominal_resolution_stochastic': self.nominal_resolution_stochastic,
                'nominal_resolution_constant': self.nominal_resolution_constant,
                'timing_offset': self.timing_offset,
                'timing_resolution': self.timing_resolution,
                'moliere_radius': self.moliere_radius,
                'radiation_length': self.radiation_length,
            },
            'modules': []
        }

        for module_id, cal in self.module_calibrations.items():
            module_data = {
                'module_id': cal.module_id,
                'cerenkov_yield': cal.cerenkov_yield,
                'energy_scale': cal.energy_scale,
                'pedestal': cal.pedestal,
                'resolution_stochastic': cal.resolution_stochastic,
                'resolution_constant': cal.resolution_constant,
                'position_x': cal.position_x,
                'position_y': cal.position_y,
                'position_z': cal.position_z,
                'edge_correction': cal.edge_correction,
                'fit_chi2': cal.fit_chi2,
                'n_events': cal.n_events,
            }
            data['modules'].append(module_data)

        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    @classmethod
    def load(cls, path: str) -> 'LeadGlassCalibration':
        """Load calibration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        cal = cls()
        if 'global' in data:
            g = data['global']
            cal.nominal_cerenkov_yield = g.get('nominal_cerenkov_yield', 200.0)
            cal.nominal_resolution_stochastic = g.get('nominal_resolution_stochastic', 0.05)
            cal.nominal_resolution_constant = g.get('nominal_resolution_constant', 0.02)
            cal.timing_offset = g.get('timing_offset', 0.0)
            cal.timing_resolution = g.get('timing_resolution', 2.0)
            cal.moliere_radius = g.get('moliere_radius', 3.5)
            cal.radiation_length = g.get('radiation_length', 1.76)

        if 'modules' in data:
            for mod_data in data['modules']:
                mod_cal = LeadGlassModuleCalibration(
                    module_id=mod_data['module_id'],
                    cerenkov_yield=mod_data.get('cerenkov_yield', 200.0),
                    energy_scale=mod_data.get('energy_scale', 1.0),
                    pedestal=mod_data.get('pedestal', 0.0),
                    resolution_stochastic=mod_data.get('resolution_stochastic', 0.05),
                    resolution_constant=mod_data.get('resolution_constant', 0.02),
                    position_x=mod_data.get('position_x', 0.0),
                    position_y=mod_data.get('position_y', 0.0),
                    position_z=mod_data.get('position_z', 0.0),
                    edge_correction=mod_data.get('edge_correction', 1.0),
                    fit_chi2=mod_data.get('fit_chi2', -1.0),
                    n_events=mod_data.get('n_events', 0),
                )
                cal.set_module(mod_cal)

        return cal


def reconstruct_energy(
    photon_count: float,
    calibration: LeadGlassModuleCalibration,
) -> float:
    """
    Reconstruct deposited energy from detected Cerenkov photon count.

    Args:
        photon_count: Number of detected Cerenkov photons
        calibration: Module calibration parameters

    Returns:
        Reconstructed energy in MeV
    """
    # Subtract pedestal
    corrected = photon_count - calibration.pedestal

    if corrected <= 0:
        return 0.0

    # Convert to energy
    energy_raw = corrected / calibration.cerenkov_yield

    # Apply energy scale
    energy = energy_raw * calibration.energy_scale

    # Apply edge correction
    energy *= calibration.edge_correction

    return max(0.0, energy)


def expected_photons(
    energy_mev: float,
    calibration: LeadGlassModuleCalibration,
) -> float:
    """
    Calculate expected Cerenkov photons for given energy deposit.

    Args:
        energy_mev: Deposited energy in MeV
        calibration: Module calibration parameters

    Returns:
        Expected Cerenkov photon count
    """
    return (energy_mev * calibration.cerenkov_yield /
            calibration.energy_scale + calibration.pedestal)


def energy_resolution(
    energy_mev: float,
    calibration: LeadGlassModuleCalibration,
) -> float:
    """
    Calculate energy resolution σ(E) at given energy.

    Resolution: σ/E = a/√E ⊕ b

    Args:
        energy_mev: Energy in MeV
        calibration: Module calibration

    Returns:
        Resolution σ in MeV
    """
    if energy_mev <= 0:
        return 0.0

    a = calibration.resolution_stochastic
    b = calibration.resolution_constant

    # Quadrature sum
    relative = np.sqrt((a / np.sqrt(energy_mev))**2 + b**2)

    return energy_mev * relative


def shower_containment(
    energy_mev: float,
    distance_to_edge: float,
    calibration: LeadGlassCalibration,
) -> float:
    """
    Calculate shower containment correction factor.

    For showers near module edges, some energy leaks out.

    Args:
        energy_mev: Total shower energy (MeV)
        distance_to_edge: Distance from shower axis to nearest edge (cm)
        calibration: Global calibration

    Returns:
        Containment fraction (0-1)
    """
    Rm = calibration.moliere_radius

    # Simple model: 95% contained within 2 Moliere radii
    if distance_to_edge > 2 * Rm:
        return 1.0

    # Linear interpolation for edge effects
    if distance_to_edge < Rm:
        return 0.7 + 0.25 * (distance_to_edge / Rm)

    return 0.95 - 0.05 * (2 * Rm - distance_to_edge) / Rm


# ============================================================================
# Calibration Fitting
# ============================================================================

def fit_cerenkov_yield(
    data: pd.DataFrame,
    module_id: int,
    min_energy: float = 10.0,
) -> Optional[LeadGlassModuleCalibration]:
    """
    Fit Cerenkov yield for a single lead glass module.

    Args:
        data: DataFrame with columns:
            - 'photons': Detected Cerenkov photon count
            - 'energy_dep': Energy deposited (MeV)
            - 'Module_ID': Module identifier
        module_id: Module to calibrate
        min_energy: Minimum energy for fitting (MeV)

    Returns:
        LeadGlassModuleCalibration or None if fit fails
    """
    from scipy.optimize import curve_fit

    # Filter data
    mask = (data['Module_ID'] == module_id) & (data['energy_dep'] >= min_energy)
    mod_data = data[mask]

    if len(mod_data) < 10:
        return None

    E = mod_data['energy_dep'].values
    N = mod_data['photons'].values

    # Linear fit: N = yield * E + pedestal
    def model(E, yield_val, pedestal):
        return yield_val * E + pedestal

    try:
        popt, pcov = curve_fit(
            model, E, N,
            p0=[200.0, 0.0],
            bounds=([50, -100], [1000, 100])
        )

        yield_val, pedestal = popt
        yield_err = np.sqrt(pcov[0, 0]) if pcov[0, 0] > 0 else 0

        # Compute resolution
        predicted = model(E, *popt)
        residuals = N - predicted

        # Fit resolution as function of energy
        relative_residuals = residuals / predicted
        a_est = np.std(relative_residuals) * np.sqrt(np.mean(E))

        # Chi-squared
        chi2 = np.sum(residuals**2) / (len(E) - 2)

        # Get position if available
        pos_x = mod_data['x'].mean() if 'x' in mod_data.columns else 0.0
        pos_y = mod_data['y'].mean() if 'y' in mod_data.columns else 0.0
        pos_z = mod_data['z'].mean() if 'z' in mod_data.columns else 0.0

        calib = LeadGlassModuleCalibration(
            module_id=module_id,
            cerenkov_yield=float(yield_val),
            pedestal=float(pedestal),
            resolution_stochastic=float(min(a_est, 0.20)),  # Cap at 20%
            position_x=float(pos_x),
            position_y=float(pos_y),
            position_z=float(pos_z),
            fit_chi2=float(chi2),
            n_events=len(mod_data),
        )

        return calib

    except Exception as e:
        print(f"Fit failed for module {module_id}: {e}")
        return None


def run_leadglass_calibration(
    data: pd.DataFrame,
    output_path: Optional[str] = None,
    min_energy: float = 10.0,
    min_events: int = 10,
) -> LeadGlassCalibration:
    """
    Run calibration for all lead glass modules.

    Args:
        data: DataFrame with lead glass hits
        output_path: Path to save calibration (optional)
        min_energy: Minimum energy for fitting
        min_events: Minimum events per module

    Returns:
        LeadGlassCalibration object
    """
    calibration = LeadGlassCalibration()

    # Get unique module IDs
    module_counts = data.groupby('Module_ID').size()

    print(f"[Lead Glass Calibration] Found {len(module_counts)} modules")

    n_calibrated = 0
    n_failed = 0

    for module_id, n_hits in module_counts.items():
        if n_hits < min_events:
            continue

        mod_cal = fit_cerenkov_yield(data, module_id, min_energy)

        if mod_cal is not None:
            calibration.set_module(mod_cal)
            n_calibrated += 1
        else:
            n_failed += 1

    print(f"[Lead Glass Calibration] Calibrated: {n_calibrated}, Failed: {n_failed}")

    # Compute global averages
    if calibration.module_calibrations:
        yields = [c.cerenkov_yield for c in calibration.module_calibrations.values()]
        stochastic = [c.resolution_stochastic for c in calibration.module_calibrations.values()]

        calibration.nominal_cerenkov_yield = float(np.median(yields))
        calibration.nominal_resolution_stochastic = float(np.median(stochastic))

        print(f"[Lead Glass Calibration] Median Cerenkov yield: {calibration.nominal_cerenkov_yield:.0f} photons/MeV")
        print(f"[Lead Glass Calibration] Median resolution (a): {calibration.nominal_resolution_stochastic:.3f}")

    if output_path:
        calibration.save(output_path)
        print(f"[Lead Glass Calibration] Saved to: {output_path}")

    return calibration


# ============================================================================
# Calibration Validation Plots
# ============================================================================

def plot_cerenkov_linearity(
    data: pd.DataFrame,
    calibration: LeadGlassCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot Cerenkov photons vs energy deposit (linearity check).
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: All modules combined
    ax = axes[0]
    E = data['energy_dep'].values
    N = data['photons'].values

    ax.scatter(E, N, s=1, alpha=0.3, c='blue')

    # Fit line
    mask = E > 0
    slope = N[mask].sum() / E[mask].sum()
    x_fit = np.linspace(0, E.max(), 100)
    ax.plot(x_fit, slope * x_fit, 'r-', linewidth=2,
            label=f'Fit: {slope:.0f} photons/MeV')

    ax.set_xlabel('Energy Deposit (MeV)', fontsize=12)
    ax.set_ylabel('Cerenkov Photons', fontsize=12)
    ax.set_title('Lead Glass Cerenkov Linearity', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Right: Per-module overlay
    ax = axes[1]
    for module_id in np.unique(data['Module_ID'].values)[:10]:  # Show first 10
        mask = data['Module_ID'] == module_id
        ax.scatter(data.loc[mask, 'energy_dep'],
                   data.loc[mask, 'photons'],
                   s=2, alpha=0.5, label=f'Module {module_id}')

    ax.set_xlabel('Energy Deposit (MeV)', fontsize=12)
    ax.set_ylabel('Cerenkov Photons', fontsize=12)
    ax.set_title('Per-Module Linearity', fontsize=14)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


def plot_energy_resolution(
    data: pd.DataFrame,
    calibration: LeadGlassCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot energy resolution vs energy for lead glass.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    E = data['energy_dep'].values
    N = data['photons'].values

    # Bin by energy
    energy_bins = np.array([10, 20, 50, 100, 200, 500, 1000, 2000])
    energy_centers = []
    resolutions = []

    for i in range(len(energy_bins) - 1):
        mask = (E >= energy_bins[i]) & (E < energy_bins[i + 1])
        if mask.sum() < 10:
            continue

        E_bin = E[mask]
        N_bin = N[mask]

        # Compute resolution
        ratio = N_bin / E_bin
        mean_ratio = np.mean(ratio)
        std_ratio = np.std(ratio)

        if mean_ratio > 0:
            relative_resolution = std_ratio / mean_ratio
            energy_centers.append(np.sqrt(energy_bins[i] * energy_bins[i + 1]))
            resolutions.append(relative_resolution)

    if energy_centers:
        ax.scatter(energy_centers, resolutions, s=50, c='blue', zorder=10, label='Data')

        # Fit a/√E ⊕ b
        E_arr = np.array(energy_centers)
        R_arr = np.array(resolutions)

        def model(E, a, b):
            return np.sqrt((a / np.sqrt(E))**2 + b**2)

        from scipy.optimize import curve_fit
        try:
            popt, _ = curve_fit(model, E_arr, R_arr, p0=[0.05, 0.02])
            E_fit = np.logspace(1, 3.5, 100)
            ax.plot(E_fit, model(E_fit, *popt), 'r-', linewidth=2,
                    label=f'Fit: {popt[0]:.2f}/√E ⊕ {popt[1]:.2f}')
        except:
            pass

    ax.set_xscale('log')
    ax.set_xlabel('Energy (MeV)', fontsize=12)
    ax.set_ylabel('σ(E)/E', fontsize=12)
    ax.set_title('Lead Glass Energy Resolution', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3, which='both')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


def plot_shower_profile(
    data: pd.DataFrame,
    calibration: LeadGlassCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot shower lateral profile (energy vs distance from shower axis).
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    # This requires position information
    if 'x' not in data.columns or 'y' not in data.columns:
        print("Position data not available for shower profile")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Group hits by event (need event_id column)
    if 'event_id' not in data.columns:
        # Just plot radial distribution of all hits
        r = np.sqrt(data['x']**2 + data['y']**2)
        E = data['energy_dep'].values

        r_bins = np.linspace(0, 50, 25)
        E_profile = []

        for i in range(len(r_bins) - 1):
            mask = (r >= r_bins[i]) & (r < r_bins[i + 1])
            E_profile.append(E[mask].mean() if mask.sum() > 0 else 0)

        r_centers = (r_bins[:-1] + r_bins[1:]) / 2
        ax.bar(r_centers, E_profile, width=np.diff(r_bins)[0] * 0.9)

    ax.set_xlabel('Radial Distance (cm)', fontsize=12)
    ax.set_ylabel('Mean Energy Deposit (MeV)', fontsize=12)
    ax.set_title('Lead Glass Shower Profile', fontsize=14)
    ax.axvline(calibration.moliere_radius, color='red', linestyle='--',
               label=f'Moliere radius: {calibration.moliere_radius:.1f} cm')
    ax.axvline(2 * calibration.moliere_radius, color='orange', linestyle='--',
               label=f'2 × Moliere radius')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


def plot_module_uniformity(
    calibration: LeadGlassCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot calibration uniformity across modules.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    if not calibration.module_calibrations:
        print("No module calibrations available")
        return None

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Cerenkov yield distribution
    ax = axes[0]
    yields = [c.cerenkov_yield for c in calibration.module_calibrations.values()]

    ax.hist(yields, bins=30, histtype='step', linewidth=2)
    ax.axvline(calibration.nominal_cerenkov_yield, color='red', linestyle='--',
               label=f'Nominal: {calibration.nominal_cerenkov_yield:.0f}')
    ax.axvline(np.mean(yields), color='green', linestyle=':',
               label=f'Mean: {np.mean(yields):.0f}')

    ax.set_xlabel('Cerenkov Yield (photons/MeV)', fontsize=12)
    ax.set_ylabel('Number of Modules', fontsize=12)
    ax.set_title('Cerenkov Yield Distribution', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Resolution distribution
    ax = axes[1]
    resolutions = [c.resolution_stochastic for c in calibration.module_calibrations.values()]

    ax.hist(resolutions, bins=30, histtype='step', linewidth=2)
    ax.axvline(calibration.nominal_resolution_stochastic, color='red', linestyle='--',
               label=f'Nominal: {calibration.nominal_resolution_stochastic:.3f}')

    ax.set_xlabel('Stochastic Resolution (a)', fontsize=12)
    ax.set_ylabel('Number of Modules', fontsize=12)
    ax.set_title('Resolution Distribution', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


__all__ = [
    "LeadGlassModuleCalibration",
    "LeadGlassCalibration",
    "reconstruct_energy",
    "expected_photons",
    "energy_resolution",
    "shower_containment",
    "fit_cerenkov_yield",
    "run_leadglass_calibration",
    "plot_cerenkov_linearity",
    "plot_energy_resolution",
    "plot_shower_profile",
    "plot_module_uniformity",
]
