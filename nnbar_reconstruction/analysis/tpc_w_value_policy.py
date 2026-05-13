"""TPC W-value production/reference policy audit helpers.

The current reconstruction samples store TPC ionisation using the production
23.6 eV conversion. Reference W-values are exposed only as deterministic
electron-count scale factors so callers can audit or reweight without mutating
existing simulation output.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from pathlib import Path
from typing import Mapping

from nnbar_reconstruction.utils.config import load_config


@dataclass(frozen=True)
class TPCWValuePolicy:
    """One named TPC ionisation W-value policy point.

    Args:
        policy_key: Stable identifier for the policy point.
        w_value_ev: W-value in eV per electron-ion pair.
        role: How this value may be used in the rebuild.
        source: Evidence binding the value to rebuild plans.
    """

    policy_key: str
    w_value_ev: float
    role: str
    source: str


@dataclass(frozen=True)
class TPCWValueAuditReport:
    """Audit result comparing a config W-value with the policy table.

    Args:
        config_w_value_ev: W-value loaded from the geometry config, or ``None``
            when the key is absent.
        production_match: Whether the config matches the 23.6 eV production
            conversion used by current samples.
        reference_match: Whether the config matches either reference point.
        matched_policy_key: Matching policy key, or ``None`` if unmatched.
        message: Deterministic human-readable summary.
    """

    config_w_value_ev: float | None
    production_match: bool
    reference_match: bool
    matched_policy_key: str | None
    message: str


# Plan 17 §3 / plan 45 row N1: current samples and TPCSD output use 23.6 eV.
PRODUCTION_W_VALUE = TPCWValuePolicy(
    policy_key="production",
    w_value_ev=23.6,
    role="default conversion for current electron-count samples",
    source="docs/rebuild_plans/17_field_calibration.md §3; docs/rebuild_plans/45_systematics_taxonomy.md row N1",
)

# Plan 17 §3 / plan 45 row N1: Ar/CO2 reference spread for reweighting only.
LOWER_REFERENCE_W_VALUE = TPCWValuePolicy(
    policy_key="lower_reference",
    w_value_ev=26.0,
    role="lower reference closure/reweighting point",
    source="docs/rebuild_plans/17_field_calibration.md §3; docs/rebuild_plans/45_systematics_taxonomy.md row N1",
)
UPPER_REFERENCE_W_VALUE = TPCWValuePolicy(
    policy_key="upper_reference",
    w_value_ev=27.4,
    role="upper reference systematic-envelope endpoint",
    source="docs/rebuild_plans/17_field_calibration.md §3; docs/rebuild_plans/45_systematics_taxonomy.md row N1",
)

REFERENCE_W_VALUES: tuple[TPCWValuePolicy, ...] = (
    LOWER_REFERENCE_W_VALUE,
    UPPER_REFERENCE_W_VALUE,
)
TPC_W_VALUE_POLICIES: tuple[TPCWValuePolicy, ...] = (
    PRODUCTION_W_VALUE,
    *REFERENCE_W_VALUES,
)

_TOLERANCE_EV = 1e-9
_MISSING = object()


def electron_count_scale_factor(reference_w_value: TPCWValuePolicy | float) -> float:
    """Return the electron-count reweighting factor for a reference W-value.

    Args:
        reference_w_value: Policy point or raw W-value in eV for the target
            reference conversion.

    Returns:
        ``production_w_value / reference_w_value`` for fixed energy deposit,
        matching plan 17 §3.

    Raises:
        ValueError: If ``reference_w_value`` is not positive.
    """
    w_value_ev = _coerce_w_value_ev(reference_w_value)
    if w_value_ev <= 0.0:
        raise ValueError("reference_w_value must be positive")
    return PRODUCTION_W_VALUE.w_value_ev / w_value_ev


def audit_tpc_w_value_policy(config_path: str | Path | None = None) -> TPCWValueAuditReport:
    """Load the geometry config and audit its TPC production W-value.

    Args:
        config_path: Optional YAML config path. When omitted, the existing
            package config loader discovers ``nnbar_geometry.yaml``.

    Returns:
        Report showing whether ``tpc.w_value`` matches production or reference
        policy values.
    """
    config = load_config(config_path, force_reload=True)
    return _audit_tpc_w_value_config(config)


def _audit_tpc_w_value_config(config: Mapping[str, object]) -> TPCWValueAuditReport:
    """Audit a parsed geometry config mapping against the policy table.

    Args:
        config: Parsed ``nnbar_geometry.yaml``-style mapping.

    Returns:
        Report showing whether ``tpc.w_value`` matches production or reference
        policy values.
    """
    raw_w_value = _get_path(config, ("tpc", "w_value"))
    if raw_w_value is _MISSING:
        return TPCWValueAuditReport(
            config_w_value_ev=None,
            production_match=False,
            reference_match=False,
            matched_policy_key=None,
            message="tpc.w_value is missing; expected production 23.6 eV",
        )

    config_w_value_ev = float(raw_w_value)
    matched = _matching_policy(config_w_value_ev)
    production_match = matched == PRODUCTION_W_VALUE
    reference_match = matched in REFERENCE_W_VALUES
    matched_key = matched.policy_key if matched else None
    if matched_key is None:
        message = f"tpc.w_value={config_w_value_ev:g} eV does not match a known policy point"
    elif production_match:
        message = "tpc.w_value matches the 23.6 eV production policy"
    else:
        message = f"tpc.w_value matches reference policy {matched_key}, not production"

    return TPCWValueAuditReport(
        config_w_value_ev=config_w_value_ev,
        production_match=production_match,
        reference_match=reference_match,
        matched_policy_key=matched_key,
        message=message,
    )


def _coerce_w_value_ev(reference_w_value: TPCWValuePolicy | float) -> float:
    if isinstance(reference_w_value, TPCWValuePolicy):
        return reference_w_value.w_value_ev
    return float(reference_w_value)


def _matching_policy(w_value_ev: float) -> TPCWValuePolicy | None:
    for policy in TPC_W_VALUE_POLICIES:
        if isclose(w_value_ev, policy.w_value_ev, rel_tol=0.0, abs_tol=_TOLERANCE_EV):
            return policy
    return None


def _get_path(config: Mapping[str, object], path: tuple[str, ...]) -> object:
    current: object = config
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return _MISSING
        current = current[key]
    return current
