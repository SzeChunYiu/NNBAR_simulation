from __future__ import annotations

import math

from nnbar_reconstruction.analysis.sensitivity_closure_audit import (
    REQUIRED_SENSITIVITY_INGREDIENTS,
    audit_sensitivity_closure,
)


def _blocker_codes(report):
    return {blocker.code for blocker in report.blockers}


def test_all_missing_inputs_fail_closed_for_each_sensitivity_ingredient():
    report = audit_sensitivity_closure({})

    assert report.ready is False
    assert _blocker_codes(report) == {
        f"missing_ingredient:{name}" for name in REQUIRED_SENSITIVITY_INGREDIENTS
    }
    assert set(report.ingredients) == set(REQUIRED_SENSITIVITY_INGREDIENTS)
    assert all(not ingredient.present for ingredient in report.ingredients.values())


def test_complete_synthetic_explicit_columns_are_ready():
    report = audit_sensitivity_closure(
        {
            "signal_efficiency": 0.42,
            "cosmic_background_rate": 1.2e-4,
            "beam_background_rate": 2.5e-6,
            "livetime_seconds": 3.16e7,
            "zero_survivor_mean_upper_limit": -math.log(0.10),
        }
    )

    assert report.ready is True
    assert report.blockers == ()
    assert report.ingredients["signal_efficiency"].value == 0.42
    assert report.ingredients["cosmic_rate"].source == "explicit_column:cosmic_background_rate"
    assert report.ingredients["livetime"].column == "livetime_seconds"
    assert report.ingredients["zero_survivor_mean_upper_limit"].present is True


def test_registry_records_can_supply_sensitivity_ingredients():
    report = audit_sensitivity_closure(
        columns={"signal_efficiency": 0.12, "livetime": 100.0},
        registry_records={
            "cosmic_rate": {"value": 4.0e-5, "source": "ledger:cosmic_cry_essLund_v1"},
            "beam_background_rate": {"value": 3.0e-6, "source": "ledger:beam_bg_v1"},
            "zero_survivor_poisson_limit": {
                "value": 2.30258509299,
                "source": "sensitivity.py:zero_survivor_poisson_mean_limit(0.90)",
            },
        },
    )

    assert report.ready is True
    assert report.blockers == ()
    assert report.ingredients["cosmic_rate"].source == "registry_record:ledger:cosmic_cry_essLund_v1"
    assert report.ingredients["zero_survivor_mean_upper_limit"].column == "zero_survivor_poisson_limit"


def test_partial_nonnumeric_input_is_blocked_without_defaulting_missing_fields():
    report = audit_sensitivity_closure(
        {
            "signal_efficiency": "not-a-number",
            "cosmic_rate": 1.0,
        }
    )

    assert report.ready is False
    codes = _blocker_codes(report)
    assert "nonnumeric_ingredient:signal_efficiency" in codes
    assert "missing_ingredient:beam_background_rate" in codes
    assert "missing_ingredient:livetime" in codes
    assert "missing_ingredient:zero_survivor_mean_upper_limit" in codes
    assert "missing_ingredient:cosmic_rate" not in codes
    assert report.ingredients["signal_efficiency"].present is True
    assert report.ingredients["signal_efficiency"].value is None
