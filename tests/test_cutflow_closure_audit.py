from __future__ import annotations

from nnbar_reconstruction.analysis.cutflow_closure_audit import (
    audit_cutflow_closure,
    current_cutflow_thresholds,
    default_cutflow_provenance,
)
from nnbar_reconstruction.reconstruction.cutflow import (
    CH9_CUTFLOW_ORDER,
    SCINTILLATOR_ENERGY_WINDOW_MEV,
)


def _codes(report):
    return {blocker.code for blocker in report.blockers}


def test_complete_production_cutflow_is_ready_and_provenance_tagged():
    report = audit_cutflow_closure()

    assert report.ready is True
    assert report.blockers == ()
    assert tuple(cut.name for cut in report.cuts) == CH9_CUTFLOW_ORDER
    assert report.event_selection_order == CH9_CUTFLOW_ORDER

    by_name = {cut.name: cut for cut in report.cuts}
    assert by_name["scintillator_energy"].threshold == SCINTILLATOR_ENERGY_WINDOW_MEV
    assert by_name["scintillator_energy"].observable_names == (
        "scintillator_energy_mev",
    )
    assert by_name["filtered_scintillator_balance"].observable_names == (
        "filtered_scintillator_upper_mev",
        "filtered_scintillator_lower_mev",
    )
    assert all(cut.provenance.startswith("Ch. 9 Table 9.1") for cut in report.cuts)


def test_wrong_cut_order_fails_closed():
    wrong_order = (
        "tpc_tracks",
        "scintillator_energy",
        "pion_count",
        "invariant_mass",
        "sphericity",
        "filtered_scintillator_balance",
    )

    report = audit_cutflow_closure(order=wrong_order)

    assert report.ready is False
    assert "wrong_order" in _codes(report)
    assert report.blockers[0].cut_name == "cutflow"
    assert "scintillator_energy" in report.blockers[0].detail


def test_missing_observable_fails_closed():
    observable_names = {
        "scintillator_energy_mev",
        "tpc_tracks_to_vertex",
        "pion_count",
        "invariant_mass_mev",
        # missing sphericity
        "filtered_scintillator_upper_mev",
        "filtered_scintillator_lower_mev",
    }

    report = audit_cutflow_closure(observable_names=observable_names)

    assert report.ready is False
    assert "missing_observable" in _codes(report)
    assert any(blocker.cut_name == "sphericity" for blocker in report.blockers)


def test_nonnumeric_threshold_fails_closed():
    thresholds = current_cutflow_thresholds()
    thresholds["invariant_mass"] = "500 MeV"

    report = audit_cutflow_closure(thresholds=thresholds)

    assert report.ready is False
    assert "nonnumeric_threshold" in _codes(report)
    assert any(blocker.cut_name == "invariant_mass" for blocker in report.blockers)


def test_missing_provenance_fails_closed():
    provenance = default_cutflow_provenance()
    del provenance["pion_count"]

    report = audit_cutflow_closure(provenance=provenance)

    assert report.ready is False
    assert "missing_provenance" in _codes(report)
    assert any(blocker.cut_name == "pion_count" for blocker in report.blockers)
