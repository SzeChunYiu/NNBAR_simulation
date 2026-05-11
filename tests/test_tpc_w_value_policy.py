import pytest

from nnbar_reconstruction.analysis.tpc_w_value_policy import (
    LOWER_REFERENCE_W_VALUE,
    PRODUCTION_W_VALUE,
    UPPER_REFERENCE_W_VALUE,
    audit_tpc_w_value_policy,
    electron_count_scale_factor,
)


def test_production_w_value_stays_at_current_sample_constant():
    assert PRODUCTION_W_VALUE.w_value_ev == pytest.approx(23.6)
    assert PRODUCTION_W_VALUE.policy_key == "production"


def test_reference_w_value_scale_factors_are_below_one_and_numerically_correct():
    lower_scale = electron_count_scale_factor(LOWER_REFERENCE_W_VALUE)
    upper_scale = electron_count_scale_factor(UPPER_REFERENCE_W_VALUE)

    assert lower_scale < 1.0
    assert upper_scale < 1.0
    assert lower_scale == pytest.approx(23.6 / 26.0)
    assert upper_scale == pytest.approx(23.6 / 27.4)


def test_default_config_reports_production_w_value_match():
    report = audit_tpc_w_value_policy()

    assert report.config_w_value_ev == pytest.approx(23.6)
    assert report.production_match is True
    assert report.reference_match is False
    assert report.matched_policy_key == "production"


def test_toy_reference_config_reports_mismatch_to_production_but_reference_match(tmp_path):
    config_path = tmp_path / "toy_geometry.yaml"
    config_path.write_text("tpc:\n  w_value: 27.4\n")

    report = audit_tpc_w_value_policy(config_path)

    assert report.config_w_value_ev == pytest.approx(27.4)
    assert report.production_match is False
    assert report.reference_match is True
    assert report.matched_policy_key == "upper_reference"
