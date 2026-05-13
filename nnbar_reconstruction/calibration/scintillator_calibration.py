"""
Scintillator Light Yield Calibration Module

Calibrates the relationship between deposited energy and detected photons
in the scintillator staves, accounting for light attenuation.

Key parameters:
- Light yield: 11,136 photons/MeV (from simulation)
- Attenuation length λ: fitted from data
- Position-dependent corrections

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
class StaveCalibration:
    """Calibration parameters for a single scintillator stave."""
    module_id: int
    layer_id: int
    stave_id: int

    # Light yield (photons per MeV at readout)
    light_yield: float = 11136.0

    # Attenuation length (cm)
    attenuation_length: float = 200.0

    # Position offset for attenuation calculation (cm)
    readout_position: float = 0.0

    # Energy resolution (σ/E at 1 MeV)
    resolution_1mev: float = 0.10

    # Linearity correction coefficients (E_true = a*E_meas + b)
    linearity_a: float = 1.0
    linearity_b: float = 0.0

    # Calibration quality metrics
    fit_chi2: float = -1.0
    n_events: int = 0


@dataclass
class ScintillatorCalibration:
    """Complete scintillator calibration."""
    stave_calibrations: Dict[Tuple[int, int, int], StaveCalibration] = field(
        default_factory=dict
    )

    # Global parameters
    nominal_light_yield: float = 11136.0  # photons/MeV
    nominal_attenuation: float = 200.0    # cm

    # Timing parameters
    timing_offset: float = 0.0            # ns
    timing_resolution: float = 1.0        # ns

    def get_stave(self, module_id: int, layer_id: int, stave_id: int) -> StaveCalibration:
        """Get calibration for a specific stave."""
        key = (module_id, layer_id, stave_id)
        if key not in self.stave_calibrations:
            # Return default calibration
            return StaveCalibration(module_id, layer_id, stave_id)
        return self.stave_calibrations[key]

    def set_stave(self, calib: StaveCalibration):
        """Set calibration for a stave."""
        key = (calib.module_id, calib.layer_id, calib.stave_id)
        self.stave_calibrations[key] = calib

    def save(self, path: str):
        """Save calibration to YAML file."""
        data = {
            'global': {
                'nominal_light_yield': self.nominal_light_yield,
                'nominal_attenuation': self.nominal_attenuation,
                'timing_offset': self.timing_offset,
                'timing_resolution': self.timing_resolution,
            },
            'staves': []
        }

        for key, cal in self.stave_calibrations.items():
            stave_data = {
                'module_id': cal.module_id,
                'layer_id': cal.layer_id,
                'stave_id': cal.stave_id,
                'light_yield': cal.light_yield,
                'attenuation_length': cal.attenuation_length,
                'readout_position': cal.readout_position,
                'resolution_1mev': cal.resolution_1mev,
                'linearity_a': cal.linearity_a,
                'linearity_b': cal.linearity_b,
                'fit_chi2': cal.fit_chi2,
                'n_events': cal.n_events,
            }
            data['staves'].append(stave_data)

        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    @classmethod
    def load(cls, path: str) -> 'ScintillatorCalibration':
        """Load calibration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        cal = cls()
        if 'global' in data:
            cal.nominal_light_yield = data['global'].get('nominal_light_yield', 11136.0)
            cal.nominal_attenuation = data['global'].get('nominal_attenuation', 200.0)
            cal.timing_offset = data['global'].get('timing_offset', 0.0)
            cal.timing_resolution = data['global'].get('timing_resolution', 1.0)

        if 'staves' in data:
            for stave_data in data['staves']:
                stave_cal = StaveCalibration(
                    module_id=stave_data['module_id'],
                    layer_id=stave_data['layer_id'],
                    stave_id=stave_data['stave_id'],
                    light_yield=stave_data.get('light_yield', 11136.0),
                    attenuation_length=stave_data.get('attenuation_length', 200.0),
                    readout_position=stave_data.get('readout_position', 0.0),
                    resolution_1mev=stave_data.get('resolution_1mev', 0.10),
                    linearity_a=stave_data.get('linearity_a', 1.0),
                    linearity_b=stave_data.get('linearity_b', 0.0),
                    fit_chi2=stave_data.get('fit_chi2', -1.0),
                    n_events=stave_data.get('n_events', 0),
                )
                cal.set_stave(stave_cal)

        return cal


def reconstruct_energy(
    photon_count: float,
    calibration: StaveCalibration,
    position_along_stave: float = 0.0,
) -> float:
    """
    Reconstruct deposited energy from detected photon count.

    Applies:
    1. Attenuation correction
    2. Light yield conversion
    3. Linearity correction

    Args:
        photon_count: Number of detected photons
        calibration: Stave calibration parameters
        position_along_stave: Distance from readout (cm)

    Returns:
        Reconstructed energy in MeV
    """
    # Attenuation correction
    attenuation_factor = np.exp(
        -position_along_stave / calibration.attenuation_length
    )

    # Corrected photon count at source
    photons_at_source = photon_count / (attenuation_factor + 1e-10)

    # Convert to energy
    energy_raw = photons_at_source / calibration.light_yield

    # Apply linearity correction
    energy_corrected = calibration.linearity_a * energy_raw + calibration.linearity_b

    return max(0.0, energy_corrected)


def expected_photons(
    energy_mev: float,
    calibration: StaveCalibration,
    position_along_stave: float = 0.0,
) -> float:
    """
    Calculate expected detected photons for given energy deposit.

    Args:
        energy_mev: Deposited energy in MeV
        calibration: Stave calibration parameters
        position_along_stave: Distance from readout (cm)

    Returns:
        Expected photon count at detector
    """
    # Photons generated at source
    photons_source = energy_mev * calibration.light_yield

    # Apply attenuation
    attenuation_factor = np.exp(
        -position_along_stave / calibration.attenuation_length
    )

    return photons_source * attenuation_factor


def energy_resolution(
    energy_mev: float,
    calibration: StaveCalibration,
) -> float:
    """
    Calculate energy resolution σ(E) at given energy.

    Resolution scales as 1/√E for scintillators.

    Args:
        energy_mev: Energy in MeV
        calibration: Stave calibration

    Returns:
        Resolution σ in MeV
    """
    if energy_mev <= 0:
        return 0.0

    # σ/E = resolution_1mev / √E
    relative_resolution = calibration.resolution_1mev / np.sqrt(energy_mev)

    return energy_mev * relative_resolution


# ============================================================================
# Calibration Fitting
# ============================================================================

def fit_light_yield_attenuation(
    data: pd.DataFrame,
    module_id: int,
    layer_id: int,
    stave_id: int,
    min_energy: float = 1.0,
) -> Optional[StaveCalibration]:
    """
    Fit light yield and attenuation length for a single stave.

    Args:
        data: DataFrame with columns:
            - 'photons': Detected photon count
            - 'energy_dep': Energy deposited (MeV)
            - 'position': Position along stave (cm)
            - 'Module_ID', 'Layer_ID', 'Stave_ID': Stave identifiers
        module_id, layer_id, stave_id: Stave to calibrate
        min_energy: Minimum energy for fitting (MeV)

    Returns:
        StaveCalibration or None if fit fails
    """
    from scipy.optimize import curve_fit

    # Filter data for this stave
    mask = (
        (data['Module_ID'] == module_id) &
        (data['Layer_ID'] == layer_id) &
        (data['Stave_ID'] == stave_id) &
        (data['energy_dep'] >= min_energy)
    )
    stave_data = data[mask]

    if len(stave_data) < 10:
        return None

    # Extract arrays
    E = stave_data['energy_dep'].values
    N = stave_data['photons'].values
    x = stave_data['position'].values if 'position' in stave_data.columns else np.zeros_like(E)

    # Model: N = light_yield * E * exp(-x / attenuation)
    def model(params, E, x):
        ly, lam = params
        return ly * E * np.exp(-x / lam)

    def residuals(params, E, x, N):
        return N - model(params, E, x)

    # Initial guess
    light_yield_init = N.sum() / E.sum() if E.sum() > 0 else 11136.0
    attenuation_init = 200.0

    # Fit using least squares
    from scipy.optimize import least_squares

    try:
        result = least_squares(
            residuals,
            x0=[light_yield_init, attenuation_init],
            args=(E, x, N),
            bounds=([1000, 50], [50000, 500]),
        )

        light_yield, attenuation = result.x
        chi2 = np.sum(result.fun ** 2) / (len(N) - 2)

        # Compute resolution
        predicted = model(result.x, E, x)
        residual_std = np.std(N - predicted)
        resolution_1mev = residual_std / light_yield

        calib = StaveCalibration(
            module_id=module_id,
            layer_id=layer_id,
            stave_id=stave_id,
            light_yield=float(light_yield),
            attenuation_length=float(attenuation),
            resolution_1mev=float(resolution_1mev),
            fit_chi2=float(chi2),
            n_events=len(stave_data),
        )

        return calib

    except Exception as e:
        print(f"Fit failed for stave ({module_id}, {layer_id}, {stave_id}): {e}")
        return None


def run_scintillator_calibration(
    data: pd.DataFrame,
    output_path: Optional[str] = None,
    min_energy: float = 1.0,
    min_events: int = 10,
) -> ScintillatorCalibration:
    """
    Run calibration for all scintillator staves.

    Args:
        data: DataFrame with scintillator hits
        output_path: Path to save calibration (optional)
        min_energy: Minimum energy for fitting
        min_events: Minimum events per stave

    Returns:
        ScintillatorCalibration object
    """
    calibration = ScintillatorCalibration()

    # Get unique stave IDs
    stave_ids = data.groupby(['Module_ID', 'Layer_ID', 'Stave_ID']).size()

    print(f"[Scintillator Calibration] Found {len(stave_ids)} staves")

    n_calibrated = 0
    n_failed = 0

    for (module_id, layer_id, stave_id), n_hits in stave_ids.items():
        if n_hits < min_events:
            continue

        stave_cal = fit_light_yield_attenuation(
            data, module_id, layer_id, stave_id, min_energy
        )

        if stave_cal is not None:
            calibration.set_stave(stave_cal)
            n_calibrated += 1
        else:
            n_failed += 1

    print(f"[Scintillator Calibration] Calibrated: {n_calibrated}, Failed: {n_failed}")

    # Compute global averages
    if calibration.stave_calibrations:
        light_yields = [c.light_yield for c in calibration.stave_calibrations.values()]
        attenuations = [c.attenuation_length for c in calibration.stave_calibrations.values()]

        calibration.nominal_light_yield = float(np.median(light_yields))
        calibration.nominal_attenuation = float(np.median(attenuations))

        print(f"[Scintillator Calibration] Median light yield: {calibration.nominal_light_yield:.0f} photons/MeV")
        print(f"[Scintillator Calibration] Median attenuation: {calibration.nominal_attenuation:.1f} cm")

    if output_path:
        calibration.save(output_path)
        print(f"[Scintillator Calibration] Saved to: {output_path}")

    return calibration


# ============================================================================
# Calibration Validation Plots
# ============================================================================

def plot_light_yield_linearity(
    data: pd.DataFrame,
    calibration: ScintillatorCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot photon count vs energy deposit (linearity check).
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: All staves combined
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
    ax.set_ylabel('Detected Photons', fontsize=12)
    ax.set_title('Scintillator Light Yield Linearity', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Right: Ratio vs energy
    ax = axes[1]
    mask = E > 1.0  # Avoid low-energy noise
    ratio = N[mask] / E[mask]

    ax.scatter(E[mask], ratio, s=1, alpha=0.3, c='blue')
    ax.axhline(calibration.nominal_light_yield, color='red', linestyle='--',
               label=f'Nominal: {calibration.nominal_light_yield:.0f}')

    ax.set_xlabel('Energy Deposit (MeV)', fontsize=12)
    ax.set_ylabel('Photons / MeV', fontsize=12)
    ax.set_title('Light Yield vs Energy', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, calibration.nominal_light_yield * 2)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


def plot_energy_resolution(
    data: pd.DataFrame,
    calibration: ScintillatorCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot energy resolution vs energy (1/√E behavior).
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Bin by energy
    E = data['energy_dep'].values
    N = data['photons'].values

    energy_bins = np.array([1, 2, 5, 10, 20, 50, 100, 200, 500, 1000])
    energy_centers = []
    resolutions = []

    for i in range(len(energy_bins) - 1):
        mask = (E >= energy_bins[i]) & (E < energy_bins[i + 1])
        if mask.sum() < 10:
            continue

        E_bin = E[mask]
        N_bin = N[mask]

        # Compute resolution in this bin
        ratio = N_bin / E_bin
        mean_ratio = np.mean(ratio)
        std_ratio = np.std(ratio)

        if mean_ratio > 0:
            relative_resolution = std_ratio / mean_ratio
            energy_centers.append(np.sqrt(energy_bins[i] * energy_bins[i + 1]))
            resolutions.append(relative_resolution)

    if energy_centers:
        ax.scatter(energy_centers, resolutions, s=50, c='blue', zorder=10)

        # Fit 1/√E
        E_arr = np.array(energy_centers)
        R_arr = np.array(resolutions)

        def model(E, a):
            return a / np.sqrt(E)

        from scipy.optimize import curve_fit
        try:
            popt, _ = curve_fit(model, E_arr, R_arr, p0=[0.1])
            E_fit = np.logspace(0, 3, 100)
            ax.plot(E_fit, model(E_fit, *popt), 'r-', linewidth=2,
                    label=f'σ/E = {popt[0]:.2f}/√E')
        except:
            pass

    ax.set_xscale('log')
    ax.set_xlabel('Energy (MeV)', fontsize=12)
    ax.set_ylabel('σ(E)/E', fontsize=12)
    ax.set_title('Scintillator Energy Resolution', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3, which='both')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


def plot_attenuation_profile(
    data: pd.DataFrame,
    calibration: ScintillatorCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot light attenuation vs position along stave.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    if 'position' not in data.columns:
        print("Position data not available for attenuation plot")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Normalize photons by energy
    E = data['energy_dep'].values
    N = data['photons'].values
    x = data['position'].values

    mask = E > 1.0
    ratio = N[mask] / E[mask]
    x_masked = x[mask]

    # Bin by position
    x_bins = np.linspace(x_masked.min(), x_masked.max(), 20)
    x_centers = []
    ratio_means = []
    ratio_stds = []

    for i in range(len(x_bins) - 1):
        bin_mask = (x_masked >= x_bins[i]) & (x_masked < x_bins[i + 1])
        if bin_mask.sum() < 5:
            continue

        x_centers.append((x_bins[i] + x_bins[i + 1]) / 2)
        ratio_means.append(np.mean(ratio[bin_mask]))
        ratio_stds.append(np.std(ratio[bin_mask]))

    if x_centers:
        ax.errorbar(x_centers, ratio_means, yerr=ratio_stds, fmt='o',
                    capsize=3, label='Data')

        # Fit exponential
        x_arr = np.array(x_centers)
        r_arr = np.array(ratio_means)

        def model(x, a, lam):
            return a * np.exp(-x / lam)

        from scipy.optimize import curve_fit
        try:
            popt, _ = curve_fit(model, x_arr, r_arr,
                               p0=[calibration.nominal_light_yield, 200])
            x_fit = np.linspace(x_arr.min(), x_arr.max(), 100)
            ax.plot(x_fit, model(x_fit, *popt), 'r-', linewidth=2,
                    label=f'Fit: λ = {popt[1]:.1f} cm')
        except:
            pass

    ax.set_xlabel('Position along stave (cm)', fontsize=12)
    ax.set_ylabel('Photons / MeV', fontsize=12)
    ax.set_title('Light Attenuation in Scintillator Staves', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


def plot_stave_uniformity(
    calibration: ScintillatorCalibration,
    save_path: Optional[str] = None,
):
    """
    Plot calibration uniformity across staves.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required for plotting")
        return

    if not calibration.stave_calibrations:
        print("No stave calibrations available")
        return None

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Light yield distribution
    ax = axes[0]
    light_yields = [c.light_yield for c in calibration.stave_calibrations.values()]

    ax.hist(light_yields, bins=30, histtype='step', linewidth=2)
    ax.axvline(calibration.nominal_light_yield, color='red', linestyle='--',
               label=f'Nominal: {calibration.nominal_light_yield:.0f}')
    ax.axvline(np.mean(light_yields), color='green', linestyle=':',
               label=f'Mean: {np.mean(light_yields):.0f}')

    ax.set_xlabel('Light Yield (photons/MeV)', fontsize=12)
    ax.set_ylabel('Number of Staves', fontsize=12)
    ax.set_title('Light Yield Distribution', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Attenuation length distribution
    ax = axes[1]
    attenuations = [c.attenuation_length for c in calibration.stave_calibrations.values()]

    ax.hist(attenuations, bins=30, histtype='step', linewidth=2)
    ax.axvline(calibration.nominal_attenuation, color='red', linestyle='--',
               label=f'Nominal: {calibration.nominal_attenuation:.1f} cm')
    ax.axvline(np.mean(attenuations), color='green', linestyle=':',
               label=f'Mean: {np.mean(attenuations):.1f} cm')

    ax.set_xlabel('Attenuation Length (cm)', fontsize=12)
    ax.set_ylabel('Number of Staves', fontsize=12)
    ax.set_title('Attenuation Length Distribution', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    return fig


__all__ = [
    "StaveCalibration",
    "ScintillatorCalibration",
    "reconstruct_energy",
    "expected_photons",
    "energy_resolution",
    "fit_light_yield_attenuation",
    "run_scintillator_calibration",
    "plot_light_yield_linearity",
    "plot_energy_resolution",
    "plot_attenuation_profile",
    "plot_stave_uniformity",
]
