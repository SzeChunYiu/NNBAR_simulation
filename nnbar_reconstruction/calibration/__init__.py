"""
Calibration Module for NNBAR Reconstruction.

Provides calibration for:
- Scintillator light yield and transport
- Lead glass Cerenkov photon yield
- TPC ionization and dE/dx
"""

from .scintillator_calibration import (
    StaveCalibration,
    ScintillatorCalibration,
    reconstruct_energy as scint_reconstruct_energy,
    expected_photons as scint_expected_photons,
    energy_resolution as scint_energy_resolution,
    run_scintillator_calibration,
    plot_light_yield_linearity,
    plot_attenuation_profile,
    plot_stave_uniformity,
)

from .leadglass_calibration import (
    LeadGlassModuleCalibration,
    LeadGlassCalibration,
    reconstruct_energy as lg_reconstruct_energy,
    expected_photons as lg_expected_photons,
    energy_resolution as lg_energy_resolution,
    shower_containment,
    run_leadglass_calibration,
    plot_cerenkov_linearity,
    plot_shower_profile,
    plot_module_uniformity,
)

from .tpc_calibration import (
    TPCLayerCalibration,
    TPCCalibration,
    PION_MASS,
    PROTON_MASS,
    KAON_MASS,
    MUON_MASS,
    bethe_bloch_dedx,
    generate_bethe_bloch_curve,
    calculate_dedx_per_layer,
    calculate_track_dedx,
    identify_particle_by_dedx,
    pion_proton_separation,
    run_tpc_calibration,
    plot_bethe_bloch_comparison,
    plot_w_value_distribution,
)

__all__ = [
    # Scintillator
    "StaveCalibration",
    "ScintillatorCalibration",
    "scint_reconstruct_energy",
    "scint_expected_photons",
    "scint_energy_resolution",
    "run_scintillator_calibration",
    "plot_light_yield_linearity",
    "plot_attenuation_profile",
    "plot_stave_uniformity",
    # Lead Glass
    "LeadGlassModuleCalibration",
    "LeadGlassCalibration",
    "lg_reconstruct_energy",
    "lg_expected_photons",
    "lg_energy_resolution",
    "shower_containment",
    "run_leadglass_calibration",
    "plot_cerenkov_linearity",
    "plot_shower_profile",
    "plot_module_uniformity",
    # TPC
    "TPCLayerCalibration",
    "TPCCalibration",
    "PION_MASS",
    "PROTON_MASS",
    "KAON_MASS",
    "MUON_MASS",
    "bethe_bloch_dedx",
    "generate_bethe_bloch_curve",
    "calculate_dedx_per_layer",
    "calculate_track_dedx",
    "identify_particle_by_dedx",
    "pion_proton_separation",
    "run_tpc_calibration",
    "plot_bethe_bloch_comparison",
    "plot_w_value_distribution",
]
