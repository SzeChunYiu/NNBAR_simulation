"""Pure-Python final-sensitivity accounting primitives.

This module intentionally stops at deterministic accounting inputs: weighted
yields, statistical ``sum_w2`` variance, generated/surviving acceptance, and the
zero-observed-event Poisson mean limit for an explicit confidence level.  It
does not encode a final NNBAR sensitivity number because the exact weighted
signal and cosmic samples must be verified before such a claim is made.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log, sqrt
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class WeightedYield:
    """Weighted event-yield summary.

    Attributes:
        n_events: Number of accepted records included in the sum.
        sum_w: Sum of event weights, the expected weighted yield.
        sum_w2: Sum of squared event weights, the Poisson statistical variance
            estimate for independently weighted events.
    """

    n_events: int
    sum_w: float
    sum_w2: float

    @property
    def statistical_variance(self) -> float:
        """Return the standard independent-weight ``sum_w2`` variance."""

        return self.sum_w2

    @property
    def statistical_uncertainty(self) -> float:
        """Return ``sqrt(sum_w2)`` for independently weighted events."""

        return sqrt(self.sum_w2)

    def to_dict(self) -> dict[str, float | int]:
        """Serialize the yield summary for deterministic reports."""

        return {
            "n_events": self.n_events,
            "sum_w": self.sum_w,
            "sum_w2": self.sum_w2,
            "statistical_variance": self.statistical_variance,
            "statistical_uncertainty": self.statistical_uncertainty,
        }


@dataclass(frozen=True)
class AcceptanceSummary:
    """Generated/surviving-count acceptance summary."""

    generated_count: int
    surviving_count: int

    @property
    def rejected_count(self) -> int:
        """Return generated events that did not survive the selection."""

        return self.generated_count - self.surviving_count

    @property
    def efficiency(self) -> float:
        """Return ``surviving_count / generated_count``, or zero if empty."""

        if self.generated_count == 0:
            return 0.0
        return self.surviving_count / self.generated_count

    @property
    def binomial_variance(self) -> float:
        """Return the simple binomial variance on the acceptance estimate."""

        if self.generated_count == 0:
            return 0.0
        p = self.efficiency
        return p * (1.0 - p) / self.generated_count

    @property
    def binomial_uncertainty(self) -> float:
        """Return ``sqrt(p(1-p)/N)`` for the acceptance estimate."""

        return sqrt(self.binomial_variance)

    def to_dict(self) -> dict[str, float | int]:
        """Serialize the acceptance summary for deterministic reports."""

        return {
            "generated_count": self.generated_count,
            "surviving_count": self.surviving_count,
            "rejected_count": self.rejected_count,
            "efficiency": self.efficiency,
            "binomial_variance": self.binomial_variance,
            "binomial_uncertainty": self.binomial_uncertainty,
        }


@dataclass(frozen=True)
class SensitivityAccountingReport:
    """Bundle accounting inputs while preserving exact-sample blockers."""

    signal_yield: WeightedYield
    background_yield: WeightedYield
    signal_acceptance: AcceptanceSummary
    confidence_level: float
    zero_survivor_mean_upper_limit: float
    blockers: tuple[str, ...]

    @property
    def ready_for_final_sensitivity(self) -> bool:
        """Return whether no blockers prevent final numeric sensitivity claims."""

        return len(self.blockers) == 0

    def require_final_sensitivity_ready(self) -> None:
        """Raise if report inputs are still blocked by missing verification."""

        if self.blockers:
            blocker_text = "; ".join(self.blockers)
            raise RuntimeError(f"Final numeric sensitivity is blocked: {blocker_text}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report with an explicit ready/blocked status."""

        return {
            "status": "ready" if self.ready_for_final_sensitivity else "blocked",
            "signal_yield": self.signal_yield.to_dict(),
            "background_yield": self.background_yield.to_dict(),
            "signal_acceptance": self.signal_acceptance.to_dict(),
            "confidence_level": self.confidence_level,
            "zero_survivor_mean_upper_limit": self.zero_survivor_mean_upper_limit,
            "blockers": list(self.blockers),
        }


def compute_weighted_yield(
    records_or_weights: Iterable[Any],
    *,
    weight_key: str | None = None,
) -> WeightedYield:
    """Compute weighted yield and ``sum_w2`` variance.

    Args:
        records_or_weights: Iterable of numeric weights, or records containing
            a numeric weight when ``weight_key`` is provided.
        weight_key: Optional mapping key or object attribute name that supplies
            each record weight.

    Raises:
        ValueError: If a weight is negative or non-finite.
        KeyError: If ``weight_key`` is requested but absent from a mapping.
        AttributeError: If ``weight_key`` is requested but absent from an object.
    """

    n_events = 0
    sum_w = 0.0
    sum_w2 = 0.0

    for record in records_or_weights:
        weight = _extract_weight(record, weight_key)
        if not isfinite(weight):
            raise ValueError(f"weight must be finite, got {weight!r}")
        if weight < 0.0:
            raise ValueError(f"negative weight is not allowed: {weight!r}")
        n_events += 1
        sum_w += weight
        sum_w2 += weight * weight

    return WeightedYield(n_events=n_events, sum_w=sum_w, sum_w2=sum_w2)


def compute_acceptance(generated_count: int, surviving_count: int) -> AcceptanceSummary:
    """Compute acceptance from generated and surviving event counts.

    Raises:
        ValueError: If counts are non-integral, negative, or surviving events
            exceed generated events.
    """

    generated_count = _coerce_event_count("generated_count", generated_count)
    surviving_count = _coerce_event_count("surviving_count", surviving_count)

    if generated_count < 0 or surviving_count < 0:
        raise ValueError("generated_count and surviving_count must be non-negative")
    if surviving_count > generated_count:
        raise ValueError("surviving_count cannot exceed generated_count")
    return AcceptanceSummary(
        generated_count=generated_count,
        surviving_count=surviving_count,
    )


def zero_survivor_poisson_mean_limit(confidence_level: float) -> float:
    """Return the upper limit on the Poisson mean for zero observed events.

    The confidence level is explicit by design: for zero observed events and no
    subtraction encoded here, ``P(0; mu) = exp(-mu) = 1 - CL``, hence
    ``mu = -ln(1 - CL)``.
    """

    if not isfinite(confidence_level) or not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be finite and satisfy 0 < CL < 1")
    return -log(1.0 - confidence_level)


def build_sensitivity_accounting_report(
    *,
    signal_weights: Iterable[Any],
    background_weights: Iterable[Any],
    generated_signal_count: int,
    surviving_signal_count: int,
    confidence_level: float,
    blockers: Iterable[str],
    signal_weight_key: str | None = None,
    background_weight_key: str | None = None,
) -> SensitivityAccountingReport:
    """Build a report of final-sensitivity accounting inputs.

    ``blockers`` has no default so callers must explicitly state whether exact
    signal/cosmic samples are verified (empty blockers) or absent (non-empty
    blocker text).
    """

    blocker_tuple = tuple(str(blocker) for blocker in blockers if str(blocker))
    return SensitivityAccountingReport(
        signal_yield=compute_weighted_yield(signal_weights, weight_key=signal_weight_key),
        background_yield=compute_weighted_yield(
            background_weights,
            weight_key=background_weight_key,
        ),
        signal_acceptance=compute_acceptance(
            generated_count=generated_signal_count,
            surviving_count=surviving_signal_count,
        ),
        confidence_level=confidence_level,
        zero_survivor_mean_upper_limit=zero_survivor_poisson_mean_limit(confidence_level),
        blockers=blocker_tuple,
    )


def _extract_weight(record: Any, weight_key: str | None) -> float:
    if weight_key is None:
        return float(record)
    if isinstance(record, Mapping):
        return float(record[weight_key])
    return float(getattr(record, weight_key))


def _coerce_event_count(name: str, value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer count")
    try:
        integer_value = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be an integer count") from exc
    if value != integer_value:
        raise ValueError(f"{name} must be an integer count")
    return integer_value
