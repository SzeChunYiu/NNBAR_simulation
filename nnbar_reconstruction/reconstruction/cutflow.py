"""Canonical event cutflow constants from the thesis event-selection chapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# Thesis Ch.10 preliminary event-selection table, in sequential order.
CH10_CUTFLOW_ORDER = (
    "scintillator_energy",
    "tpc_tracks",
    "pion_count",
    "invariant_mass",
    "sphericity",
    "filtered_scintillator_balance",
)

SCINTILLATOR_ENERGY_WINDOW_MEV = (20.0, 2000.0)
MIN_TPC_TRACKS_TO_VERTEX = 1
MIN_PION_COUNT = 1
MIN_INVARIANT_MASS_MEV = 500.0
MIN_SPHERICITY = 0.2
FILTERED_SCINTILLATOR_UPPER_MAX_MEV = 320.0
FILTERED_SCINTILLATOR_LOWER_MAX_MEV = 930.0


@dataclass(frozen=True)
class EventCutObservables:
    """Minimal observables required by the Ch.10 cutflow table."""

    scintillator_energy_mev: float
    tpc_tracks_to_vertex: int
    pion_count: int
    invariant_mass_mev: float
    sphericity: float
    filtered_scintillator_upper_mev: float
    filtered_scintillator_lower_mev: float


@dataclass(frozen=True)
class CutflowResult:
    """Result of applying the Ch.10 event-selection cuts."""

    passed: bool
    cut_results: dict[str, bool]
    first_failed_cut: str | None
    n_cuts_passed: int
    n_cuts_total: int


def apply_ch10_cutflow(event: EventCutObservables) -> CutflowResult:
    """Apply thesis Ch.10 cuts in table order."""

    scint_min, scint_max = SCINTILLATOR_ENERGY_WINDOW_MEV
    checks = (
        ("scintillator_energy", scint_min <= event.scintillator_energy_mev <= scint_max),
        ("tpc_tracks", event.tpc_tracks_to_vertex >= MIN_TPC_TRACKS_TO_VERTEX),
        ("pion_count", event.pion_count >= MIN_PION_COUNT),
        ("invariant_mass", event.invariant_mass_mev >= MIN_INVARIANT_MASS_MEV),
        ("sphericity", event.sphericity >= MIN_SPHERICITY),
        (
            "filtered_scintillator_balance",
            event.filtered_scintillator_upper_mev <= FILTERED_SCINTILLATOR_UPPER_MAX_MEV
            and event.filtered_scintillator_lower_mev <= FILTERED_SCINTILLATOR_LOWER_MAX_MEV,
        ),
    )

    cut_results = {name: passed for name, passed in checks}
    first_failed = next((name for name, passed in checks if not passed), None)
    n_passed = sum(cut_results.values())

    return CutflowResult(
        passed=first_failed is None,
        cut_results=cut_results,
        first_failed_cut=first_failed,
        n_cuts_passed=n_passed,
        n_cuts_total=len(CH10_CUTFLOW_ORDER),
    )


def compute_signal_efficiency(events: Iterable[EventCutObservables]) -> float:
    """Fraction of signal-like events that pass all Ch.10 cuts."""

    event_list = list(events)
    if not event_list:
        return 0.0
    return sum(apply_ch10_cutflow(event).passed for event in event_list) / len(event_list)


def compute_background_rejection(events: Iterable[EventCutObservables]) -> float:
    """Fraction of background-like events rejected by at least one Ch.10 cut."""

    event_list = list(events)
    if not event_list:
        return 0.0
    return 1.0 - compute_signal_efficiency(event_list)
