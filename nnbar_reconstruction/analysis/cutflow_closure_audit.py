"""Fail-closed audit for thesis Ch. 9 Table 9.1 cutflow wiring.

The audit is intentionally read-only: it checks the canonical cutflow constants,
observable fields, provenance labels, and default event-selection order without
changing production selection behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Iterable, Mapping

from nnbar_reconstruction.analysis.event_selection import apply_selection_cuts
from nnbar_reconstruction.analysis.event_variables import EventVariables
from nnbar_reconstruction.reconstruction.cutflow import (
    CH9_CUTFLOW_ORDER,
    FILTERED_SCINTILLATOR_LOWER_MAX_MEV,
    FILTERED_SCINTILLATOR_UPPER_MAX_MEV,
    MIN_INVARIANT_MASS_MEV,
    MIN_PION_COUNT,
    MIN_SPHERICITY,
    MIN_TPC_TRACKS_TO_VERTEX,
    SCINTILLATOR_ENERGY_WINDOW_MEV,
    EventCutObservables,
)


@dataclass(frozen=True)
class CutAudit:
    """Observed status for one required Ch. 9 Table 9.1 cut."""

    name: str
    observable_names: tuple[str, ...]
    threshold: object
    relation: str
    provenance: str


@dataclass(frozen=True)
class CutflowBlocker:
    """Machine-readable reason the cutflow audit cannot certify closure."""

    code: str
    cut_name: str
    detail: str


@dataclass(frozen=True)
class CutflowClosureReport:
    """Complete fail-closed cutflow audit result."""

    ready: bool
    cuts: tuple[CutAudit, ...]
    event_selection_order: tuple[str, ...]
    blockers: tuple[CutflowBlocker, ...]


_OBSERVABLES_BY_CUT: Mapping[str, tuple[str, ...]] = {
    "scintillator_energy": ("scintillator_energy_mev",),
    "tpc_tracks": ("tpc_tracks_to_vertex",),
    "pion_count": ("pion_count",),
    "invariant_mass": ("invariant_mass_mev",),
    "sphericity": ("sphericity",),
    "filtered_scintillator_balance": (
        "filtered_scintillator_upper_mev",
        "filtered_scintillator_lower_mev",
    ),
}

_RELATION_BY_CUT: Mapping[str, str] = {
    "scintillator_energy": "inclusive window: min <= scintillator_energy_mev <= max",
    "tpc_tracks": "minimum: tpc_tracks_to_vertex >= MIN_TPC_TRACKS_TO_VERTEX",
    "pion_count": "minimum: pion_count >= MIN_PION_COUNT",
    "invariant_mass": "minimum: invariant_mass_mev >= MIN_INVARIANT_MASS_MEV",
    "sphericity": "minimum: sphericity >= MIN_SPHERICITY",
    "filtered_scintillator_balance": (
        "upper/lower maxima: filtered_scintillator_upper_mev <= upper and "
        "filtered_scintillator_lower_mev <= lower"
    ),
}


_SCORE_SOURCE = "Ch. 9 Table 9.1 via nnbar_reconstruction.reconstruction.cutflow"


def current_cutflow_thresholds() -> dict[str, object]:
    """Return current canonical threshold values without duplicating numbers."""

    return {
        "scintillator_energy": SCINTILLATOR_ENERGY_WINDOW_MEV,
        "tpc_tracks": MIN_TPC_TRACKS_TO_VERTEX,
        "pion_count": MIN_PION_COUNT,
        "invariant_mass": MIN_INVARIANT_MASS_MEV,
        "sphericity": MIN_SPHERICITY,
        "filtered_scintillator_balance": (
            FILTERED_SCINTILLATOR_UPPER_MAX_MEV,
            FILTERED_SCINTILLATOR_LOWER_MAX_MEV,
        ),
    }


def default_cutflow_provenance() -> dict[str, str]:
    """Return provenance tags tying each threshold to the thesis table."""

    return {
        "scintillator_energy": f"{_SCORE_SOURCE}.SCINTILLATOR_ENERGY_WINDOW_MEV",
        "tpc_tracks": f"{_SCORE_SOURCE}.MIN_TPC_TRACKS_TO_VERTEX",
        "pion_count": f"{_SCORE_SOURCE}.MIN_PION_COUNT",
        "invariant_mass": f"{_SCORE_SOURCE}.MIN_INVARIANT_MASS_MEV",
        "sphericity": f"{_SCORE_SOURCE}.MIN_SPHERICITY",
        "filtered_scintillator_balance": (
            f"{_SCORE_SOURCE}.FILTERED_SCINTILLATOR_UPPER_MAX_MEV/"
            "FILTERED_SCINTILLATOR_LOWER_MAX_MEV"
        ),
    }


def current_event_selection_order() -> tuple[str, ...]:
    """Run a synthetic passing event through the default selection path."""

    scint_min, scint_max = SCINTILLATOR_ENERGY_WINDOW_MEV
    event = EventVariables(
        invariant_mass=max(MIN_INVARIANT_MASS_MEV, 1880.0),
        sphericity=max(MIN_SPHERICITY, 0.5),
        total_energy=1900.0,
        scint_energy=(scint_min + scint_max) / 2.0,
        lg_energy=1200.0,
        longitudinal_energy=0.0,
        transverse_energy=0.0,
        top_bottom_asymmetry=1.0,
        forward_backward_asymmetry=0.0,
        n_charged=2,
        n_neutral=1,
        n_pions=MIN_PION_COUNT,
        n_protons=0,
        vertex_r=999.0,
        n_tracks_to_vertex=MIN_TPC_TRACKS_TO_VERTEX,
        filtered_scintillator_upper_mev=0.0,
        filtered_scintillator_lower_mev=0.0,
    )
    return tuple(apply_selection_cuts(event).cut_results)


def audit_cutflow_closure(
    *,
    order: Iterable[str] | None = None,
    event_selection_order: Iterable[str] | None = None,
    observable_names: Iterable[str] | None = None,
    thresholds: Mapping[str, object] | None = None,
    provenance: Mapping[str, str] | None = None,
) -> CutflowClosureReport:
    """Audit Table 9.1 cutflow closure with explicit fail-closed blockers.

    Args:
        order: Observed canonical cutflow order. Defaults to ``CH9_CUTFLOW_ORDER``.
        event_selection_order: Observed default ``apply_selection_cuts`` order.
        observable_names: Available fields on the cutflow observable carrier.
        thresholds: Observed threshold mapping, keyed by cut name.
        provenance: Provenance labels, keyed by cut name.

    Returns:
        A report that is ready only when order, observables, thresholds, default
        selection wiring, and provenance all match the Ch. 9 Table 9.1 contract.
    """

    expected_order = tuple(CH9_CUTFLOW_ORDER)
    observed_order = tuple(order) if order is not None else expected_order
    observed_selection_order = (
        tuple(event_selection_order)
        if event_selection_order is not None
        else current_event_selection_order()
    )
    observed_observables = (
        set(observable_names)
        if observable_names is not None
        else set(EventCutObservables.__dataclass_fields__)
    )
    observed_thresholds = dict(thresholds) if thresholds is not None else current_cutflow_thresholds()
    observed_provenance = (
        dict(provenance) if provenance is not None else default_cutflow_provenance()
    )
    expected_thresholds = current_cutflow_thresholds()

    cuts = tuple(
        CutAudit(
            name=name,
            observable_names=_OBSERVABLES_BY_CUT[name],
            threshold=observed_thresholds.get(name),
            relation=_RELATION_BY_CUT[name],
            provenance=observed_provenance.get(name, ""),
        )
        for name in expected_order
    )

    blockers: list[CutflowBlocker] = []
    if observed_order != expected_order:
        blockers.append(
            CutflowBlocker(
                code="wrong_order",
                cut_name="cutflow",
                detail=f"expected {expected_order}, observed {observed_order}",
            )
        )
    if observed_selection_order != expected_order:
        blockers.append(
            CutflowBlocker(
                code="wrong_event_selection_order",
                cut_name="event_selection",
                detail=(
                    f"apply_selection_cuts default order must be {expected_order}, "
                    f"observed {observed_selection_order}"
                ),
            )
        )

    for cut in cuts:
        for observable in cut.observable_names:
            if observable not in observed_observables:
                blockers.append(
                    CutflowBlocker(
                        code="missing_observable",
                        cut_name=cut.name,
                        detail=f"missing EventCutObservables field {observable}",
                    )
                )

        if cut.name not in observed_thresholds:
            blockers.append(
                CutflowBlocker(
                    code="missing_threshold",
                    cut_name=cut.name,
                    detail="required threshold is absent from the observed mapping",
                )
            )
        elif not _is_numeric_threshold(cut.threshold):
            blockers.append(
                CutflowBlocker(
                    code="nonnumeric_threshold",
                    cut_name=cut.name,
                    detail=f"threshold must be numeric, observed {cut.threshold!r}",
                )
            )
        elif cut.threshold != expected_thresholds[cut.name]:
            blockers.append(
                CutflowBlocker(
                    code="threshold_mismatch",
                    cut_name=cut.name,
                    detail=(
                        f"expected {expected_thresholds[cut.name]!r}, "
                        f"observed {cut.threshold!r}"
                    ),
                )
            )

        if not cut.provenance or "Ch. 9 Table 9.1" not in cut.provenance:
            blockers.append(
                CutflowBlocker(
                    code="missing_provenance",
                    cut_name=cut.name,
                    detail="threshold lacks a Ch. 9 Table 9.1 provenance tag",
                )
            )

    return CutflowClosureReport(
        ready=not blockers,
        cuts=cuts,
        event_selection_order=observed_selection_order,
        blockers=tuple(blockers),
    )


def _is_numeric_threshold(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, Real):
        return True
    if isinstance(value, tuple):
        return bool(value) and all(_is_numeric_threshold(item) for item in value)
    return False
