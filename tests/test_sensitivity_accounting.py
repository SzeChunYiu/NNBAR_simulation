from __future__ import annotations

import inspect
import math

import pytest

from nnbar_reconstruction.analysis.sensitivity import (
    build_sensitivity_accounting_report,
    compute_acceptance,
    compute_weighted_yield,
    zero_survivor_poisson_mean_limit,
)


def test_weighted_yield_sums_weights_and_sum_w2_variance():
    summary = compute_weighted_yield([2.0, 3.0, 5.0])

    assert summary.n_events == 3
    assert summary.sum_w == pytest.approx(10.0)
    assert summary.sum_w2 == pytest.approx(38.0)
    assert summary.statistical_variance == pytest.approx(38.0)
    assert summary.statistical_uncertainty == pytest.approx(math.sqrt(38.0))


def test_weighted_yield_accepts_weight_records():
    summary = compute_weighted_yield(
        [{"weight": 0.5}, {"weight": 1.25}],
        weight_key="weight",
    )

    assert summary.n_events == 2
    assert summary.sum_w == pytest.approx(1.75)
    assert summary.sum_w2 == pytest.approx(0.5**2 + 1.25**2)


def test_weighted_yield_empty_inputs_are_zero():
    summary = compute_weighted_yield([])

    assert summary.n_events == 0
    assert summary.sum_w == 0.0
    assert summary.sum_w2 == 0.0
    assert summary.statistical_uncertainty == 0.0


def test_weighted_yield_rejects_negative_weights():
    with pytest.raises(ValueError, match="negative weight"):
        compute_weighted_yield([1.0, -0.1])


def test_acceptance_from_generated_and_surviving_counts():
    acceptance = compute_acceptance(generated_count=10, surviving_count=3)

    assert acceptance.generated_count == 10
    assert acceptance.surviving_count == 3
    assert acceptance.rejected_count == 7
    assert acceptance.efficiency == pytest.approx(0.3)
    assert acceptance.binomial_variance == pytest.approx(0.3 * 0.7 / 10)


def test_acceptance_edge_cases_reject_impossible_counts():
    empty = compute_acceptance(generated_count=0, surviving_count=0)
    assert empty.efficiency == 0.0
    assert empty.binomial_variance == 0.0

    with pytest.raises(ValueError, match="surviving_count cannot exceed generated_count"):
        compute_acceptance(generated_count=2, surviving_count=3)

    with pytest.raises(ValueError, match="non-negative"):
        compute_acceptance(generated_count=-1, surviving_count=0)


def test_acceptance_rejects_non_integral_counts_before_coercion():
    with pytest.raises(ValueError, match="integer"):
        compute_acceptance(generated_count=1.5, surviving_count=1)

    with pytest.raises(ValueError, match="integer"):
        compute_acceptance(generated_count=1, surviving_count=0.5)


def test_zero_survivor_limit_uses_explicit_confidence_level():
    assert zero_survivor_poisson_mean_limit(0.90) == pytest.approx(-math.log(0.10))
    assert zero_survivor_poisson_mean_limit(0.95) == pytest.approx(-math.log(0.05))

    signature = inspect.signature(zero_survivor_poisson_mean_limit)
    assert signature.parameters["confidence_level"].default is inspect._empty

    for invalid_cl in (0.0, 1.0, -0.1, 1.1):
        with pytest.raises(ValueError, match="confidence_level"):
            zero_survivor_poisson_mean_limit(invalid_cl)


def test_report_helper_carries_sample_blockers_and_refuses_final_claims():
    report = build_sensitivity_accounting_report(
        signal_weights=[1.0, 1.0],
        background_weights=[],
        generated_signal_count=50,
        surviving_signal_count=2,
        confidence_level=0.90,
        blockers=("exact sig_foil_v3/cosmic_cry_essLund_v1 samples are absent",),
    )

    assert report.signal_yield.sum_w == pytest.approx(2.0)
    assert report.background_yield.sum_w == 0.0
    assert report.signal_acceptance.efficiency == pytest.approx(0.04)
    assert report.zero_survivor_mean_upper_limit == pytest.approx(-math.log(0.10))
    assert report.blockers == ("exact sig_foil_v3/cosmic_cry_essLund_v1 samples are absent",)
    assert not report.ready_for_final_sensitivity

    as_dict = report.to_dict()
    assert as_dict["status"] == "blocked"
    assert "sig_foil_v3" in as_dict["blockers"][0]

    with pytest.raises(RuntimeError, match="Final numeric sensitivity is blocked"):
        report.require_final_sensitivity_ready()


def test_report_builder_requires_explicit_blocker_argument():
    signature = inspect.signature(build_sensitivity_accounting_report)

    assert signature.parameters["blockers"].default is inspect._empty
