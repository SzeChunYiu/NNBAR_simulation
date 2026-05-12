"""
Event Selection for NNBAR analysis.

Implements Section 9.5 from thesis (Table 9.1):
Sequential cuts optimized for signal efficiency vs background rejection.

Target: ~68% signal efficiency with ~100% background rejection.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .event_variables import EventVariables, event_variables_to_cut_observables
from ..reconstruction.cutflow import (
    FILTERED_SCINTILLATOR_LOWER_MAX_MEV,
    FILTERED_SCINTILLATOR_UPPER_MAX_MEV,
    MIN_INVARIANT_MASS_MEV,
    MIN_PION_COUNT,
    MIN_SPHERICITY,
    MIN_TPC_TRACKS_TO_VERTEX,
    SCINTILLATOR_ENERGY_WINDOW_MEV,
    apply_ch10_cutflow,
)


class CutResult(Enum):
    """Result of a single cut."""
    PASSED = 1
    FAILED = 0


@dataclass
class SelectionResult:
    """Result of event selection."""
    passed: bool                    # Overall pass/fail
    n_cuts_passed: int              # Number of cuts passed
    n_cuts_total: int               # Total number of cuts
    cut_results: Dict[str, bool]    # Per-cut results
    cut_values: Dict[str, float]    # Values compared against cuts
    efficiency_weight: float        # Weight for efficiency calculation

    def __repr__(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        return f"SelectionResult({status}, {self.n_cuts_passed}/{self.n_cuts_total} cuts)"


def cut_scintillator_energy(
    ev: EventVariables,
    e_min: Optional[float] = None,
    e_max: Optional[float] = None,
) -> Tuple[bool, float]:
    """
    Cut on total scintillator energy.

    Selects events with moderate energy deposit (not too low = noise,
    not too high = cosmic or other background).

    Args:
        ev: Event variables.
        e_min: Minimum energy in MeV.
        e_max: Maximum energy in MeV.

    Returns:
        Tuple of (passed, value).
    """
    if e_min is None:
        e_min = SCINTILLATOR_ENERGY_WINDOW_MEV[0]
    if e_max is None:
        e_max = SCINTILLATOR_ENERGY_WINDOW_MEV[1]

    passed = e_min <= ev.scint_energy <= e_max
    return passed, ev.scint_energy


def cut_tpc_tracks(
    ev: EventVariables,
    min_tracks: Optional[int] = None,
) -> Tuple[bool, int]:
    """
    Cut on number of TPC tracks pointing to foil.

    Requires at least one charged track from the target.

    Args:
        ev: Event variables.
        min_tracks: Minimum number of tracks.

    Returns:
        Tuple of (passed, value).
    """
    if min_tracks is None:
        min_tracks = MIN_TPC_TRACKS_TO_VERTEX

    passed = ev.n_tracks_to_vertex >= min_tracks
    return passed, ev.n_tracks_to_vertex


def cut_pion_multiplicity(
    ev: EventVariables,
    min_pions: Optional[int] = None,
) -> Tuple[bool, int]:
    """
    Cut on number of identified pions.

    Requires at least one pion (charged or neutral).

    Args:
        ev: Event variables.
        min_pions: Minimum pion count.

    Returns:
        Tuple of (passed, value).
    """
    if min_pions is None:
        min_pions = MIN_PION_COUNT

    passed = ev.n_pions >= min_pions
    return passed, ev.n_pions


def cut_invariant_mass(
    ev: EventVariables,
    m_min: Optional[float] = None,
) -> Tuple[bool, float]:
    """
    Cut on invariant mass.

    Signal events should have W ~ 1.88 GeV (2 * nucleon mass).
    Low mass events are typically background.

    Args:
        ev: Event variables.
        m_min: Minimum invariant mass in MeV.

    Returns:
        Tuple of (passed, value).
    """
    if m_min is None:
        m_min = MIN_INVARIANT_MASS_MEV

    passed = ev.invariant_mass >= m_min
    return passed, ev.invariant_mass


def cut_sphericity(
    ev: EventVariables,
    s_min: Optional[float] = None,
) -> Tuple[bool, float]:
    """
    Cut on event sphericity.

    Signal events are isotropic (high sphericity).
    Background (e.g., cosmics) tends to be pencil-like (low sphericity).

    Args:
        ev: Event variables.
        s_min: Minimum sphericity.

    Returns:
        Tuple of (passed, value).
    """
    if s_min is None:
        s_min = MIN_SPHERICITY

    passed = ev.sphericity >= s_min
    return passed, ev.sphericity


def cut_filtered_scintillator_balance(ev: EventVariables) -> Tuple[bool, float]:
    """
    Cut on Chapter 9 out-of-time scintillator energy in upper/lower modules.

    The canonical thresholds are held in reconstruction.cutflow:
    y > 0 <= 320 MeV and y < 0 <= 930 MeV.
    """
    passed = (
        ev.filtered_scintillator_upper_mev <= FILTERED_SCINTILLATOR_UPPER_MAX_MEV
        and ev.filtered_scintillator_lower_mev <= FILTERED_SCINTILLATOR_LOWER_MAX_MEV
    )
    return passed, max(
        ev.filtered_scintillator_upper_mev,
        ev.filtered_scintillator_lower_mev,
    )


def cut_top_bottom_asymmetry(
    ev: EventVariables,
    max_asymmetry: float = 0.8,
) -> Tuple[bool, float]:
    """
    Cut on top-bottom energy asymmetry.

    Signal events are symmetric (low asymmetry).
    Cosmic rays come from above (high asymmetry).

    Args:
        ev: Event variables.
        max_asymmetry: Maximum allowed asymmetry.

    Returns:
        Tuple of (passed, value).
    """
    passed = abs(ev.top_bottom_asymmetry) <= max_asymmetry
    return passed, ev.top_bottom_asymmetry


def cut_vertex_radius(
    ev: EventVariables,
    max_r: float = 50.0,
) -> Tuple[bool, float]:
    """
    Cut on vertex radial position.

    Signal events originate from target (small r).
    Background may have vertex away from target.

    Args:
        ev: Event variables.
        max_r: Maximum vertex radius in cm.

    Returns:
        Tuple of (passed, value).
    """
    passed = ev.vertex_r <= max_r
    return passed, ev.vertex_r


def apply_selection_cuts(
    ev: EventVariables,
    cuts: Optional[List[str]] = None,
) -> SelectionResult:
    """
    Apply full event selection.

    Implements sequential cuts from thesis Table 9.1.

    Args:
        ev: Event variables.
        cuts: List of cuts to apply. If None, applies all standard cuts.

    Returns:
        SelectionResult with pass/fail and details.
    """
    if cuts is None:
        cutflow_event = event_variables_to_cut_observables(ev)
        cutflow_result = apply_ch10_cutflow(cutflow_event)
        cut_values = {
            'scintillator_energy': ev.scint_energy,
            'tpc_tracks': ev.n_tracks_to_vertex,
            'pion_count': ev.n_pions,
            'invariant_mass': ev.invariant_mass,
            'sphericity': ev.sphericity,
            'filtered_scintillator_balance': max(
                ev.filtered_scintillator_upper_mev,
                ev.filtered_scintillator_lower_mev,
            ),
            'filtered_scintillator_upper_mev': ev.filtered_scintillator_upper_mev,
            'filtered_scintillator_lower_mev': ev.filtered_scintillator_lower_mev,
        }

        return SelectionResult(
            passed=cutflow_result.passed,
            n_cuts_passed=cutflow_result.n_cuts_passed,
            n_cuts_total=cutflow_result.n_cuts_total,
            cut_results=cutflow_result.cut_results,
            cut_values=cut_values,
            efficiency_weight=1.0 if cutflow_result.passed else 0.0,
        )

    cut_functions = {
        'scintillator_energy': cut_scintillator_energy,
        'tpc_tracks': cut_tpc_tracks,
        'pion_count': cut_pion_multiplicity,
        'pion_multiplicity': cut_pion_multiplicity,
        'invariant_mass': cut_invariant_mass,
        'sphericity': cut_sphericity,
        'filtered_scintillator_balance': cut_filtered_scintillator_balance,
        'top_bottom_asymmetry': cut_top_bottom_asymmetry,
        'vertex_radius': cut_vertex_radius,
    }

    cut_results = {}
    cut_values = {}
    n_passed = 0

    for cut_name in cuts:
        if cut_name in cut_functions:
            passed, value = cut_functions[cut_name](ev)
            cut_results[cut_name] = passed
            cut_values[cut_name] = value
            if passed:
                n_passed += 1

    all_passed = all(cut_results.values())

    return SelectionResult(
        passed=all_passed,
        n_cuts_passed=n_passed,
        n_cuts_total=len(cuts),
        cut_results=cut_results,
        cut_values=cut_values,
        efficiency_weight=1.0 if all_passed else 0.0,
    )


def optimize_cuts_for_invariant_mass(
    events: List[EventVariables],
    is_signal: List[bool],
    target_mass: float = 1880.0,  # MeV (2 * nucleon mass)
    target_width: float = 100.0,  # MeV
) -> Dict[str, float]:
    """
    Optimize cut values to minimize invariant mass width while
    maintaining high signal efficiency.

    This is the key optimization the user requested:
    - Peak at ~1.88 GeV
    - Minimal distribution width

    Args:
        events: List of event variables.
        is_signal: Boolean list indicating signal events.
        target_mass: Target invariant mass peak.
        target_width: Target width (FWHM) to achieve.

    Returns:
        Dictionary of optimized cut values.
    """
    # This is a placeholder for a proper optimization
    # In practice, you would scan cut values and evaluate:
    # 1. Signal efficiency
    # 2. Background rejection
    # 3. Invariant mass resolution

    signal_events = [ev for ev, sig in zip(events, is_signal) if sig]

    if len(signal_events) == 0:
        return {}

    # For optimization, you would typically:
    # 1. Vary each cut value
    # 2. Compute signal efficiency and mass resolution
    # 3. Find optimal point on ROC curve

    # Compute current mass resolution
    masses = np.array([ev.invariant_mass for ev in signal_events])
    mean_mass = np.mean(masses)
    std_mass = np.std(masses)

    print(f"Signal invariant mass: {mean_mass:.1f} +/- {std_mass:.1f} MeV")
    print(f"Target: {target_mass:.1f} +/- {target_width:.1f} MeV")

    return {
        'scint_energy_min': SCINTILLATOR_ENERGY_WINDOW_MEV[0],
        'scint_energy_max': SCINTILLATOR_ENERGY_WINDOW_MEV[1],
        'min_tpc_tracks': MIN_TPC_TRACKS_TO_VERTEX,
        'min_pions': MIN_PION_COUNT,
        'invariant_mass_min': MIN_INVARIANT_MASS_MEV,
        'sphericity_min': MIN_SPHERICITY,
    }


def compute_selection_efficiency(
    events: List[EventVariables],
    is_signal: List[bool],
    cuts: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Compute selection efficiency for signal and background.

    Args:
        events: List of event variables.
        is_signal: Boolean list indicating signal events.
        cuts: List of cuts to apply.

    Returns:
        Dictionary with efficiency metrics.
    """
    n_signal = sum(is_signal)
    n_background = len(is_signal) - n_signal

    signal_passed = 0
    background_passed = 0

    for ev, sig in zip(events, is_signal):
        result = apply_selection_cuts(ev, cuts)
        if sig:
            if result.passed:
                signal_passed += 1
        else:
            if result.passed:
                background_passed += 1

    signal_efficiency = signal_passed / n_signal if n_signal > 0 else 0.0
    background_rejection = 1 - (background_passed / n_background) if n_background > 0 else 1.0

    return {
        'signal_efficiency': signal_efficiency,
        'background_rejection': background_rejection,
        'n_signal_passed': signal_passed,
        'n_signal_total': n_signal,
        'n_background_passed': background_passed,
        'n_background_total': n_background,
    }


if __name__ == "__main__":
    import runpy

    runpy.run_module(
        "nnbar_reconstruction.analysis.event_selection_demo",
        run_name="__main__",
    )
