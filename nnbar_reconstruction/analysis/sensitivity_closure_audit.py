"""Fail-closed sensitivity-closure audit helpers.

The Ch. 9/10 final sensitivity estimate is only thesis-ready when each numeric
ingredient is explicitly supplied by an evidence table or registry record.  This
module validates those ingredients without calculating a final sensitivity or
inventing fallback defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Iterable, Mapping

REQUIRED_SENSITIVITY_INGREDIENTS = (
    "signal_efficiency",
    "cosmic_rate",
    "beam_background_rate",
    "livetime",
    "zero_survivor_mean_upper_limit",
)

_INGREDIENT_ALIASES: dict[str, tuple[str, ...]] = {
    "signal_efficiency": (
        "signal_efficiency",
        "signal_acceptance_efficiency",
        "efficiency",
    ),
    "cosmic_rate": ("cosmic_rate", "cosmic_background_rate"),
    "beam_background_rate": ("beam_background_rate",),
    "livetime": ("livetime", "livetime_seconds", "exposure_livetime"),
    "zero_survivor_mean_upper_limit": (
        "zero_survivor_mean_upper_limit",
        "zero_survivor_poisson_limit",
    ),
}


@dataclass(frozen=True)
class SensitivityClosureBlocker:
    """One machine-readable blocker for sensitivity closure.

    Args:
        code: Stable blocker code used by tests and planner rows.
        ingredient: Canonical sensitivity ingredient responsible for the block.
        message: Deterministic human-readable fail-closed explanation.
    """

    code: str
    ingredient: str
    message: str


@dataclass(frozen=True)
class SensitivityIngredientEvidence:
    """Evidence status for one sensitivity ingredient.

    Args:
        name: Canonical ingredient name.
        present: Whether an explicit column or registry record was supplied.
        value: Numeric value after validation, or ``None`` when blocked.
        column: Supplied column/registry key that matched the ingredient.
        source: Evidence source string, prefixed by ``explicit_column`` or
            ``registry_record``.
        blocker: Fail-closed blocker for missing or invalid evidence.
    """

    name: str
    present: bool
    value: float | None
    column: str | None
    source: str
    blocker: SensitivityClosureBlocker | None = None


@dataclass(frozen=True)
class SensitivityClosureAudit:
    """Complete Ch. 9/10 sensitivity ingredient audit result.

    Args:
        ready: True only when every required ingredient is present and numeric.
        ingredients: Mapping from canonical ingredient name to evidence status.
        blockers: Explicit fail-closed blockers.
    """

    ready: bool
    ingredients: Mapping[str, SensitivityIngredientEvidence]
    blockers: tuple[SensitivityClosureBlocker, ...]


def audit_sensitivity_closure(
    columns: Mapping[str, Any] | None = None,
    *,
    registry_records: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None = None,
) -> SensitivityClosureAudit:
    """Audit evidence for the final-sensitivity calculation inputs.

    Args:
        columns: Explicit in-memory evidence columns or row values. The audit
            checks known aliases such as ``cosmic_background_rate`` and
            ``livetime_seconds`` but never supplies defaults.
        registry_records: Optional registry evidence. A mapping may use an
            ingredient/alias as the key and either a raw value or a record with
            ``value`` and ``source`` fields. An iterable may contain records with
            ``ingredient``/``name``/``column`` plus ``value``.

    Returns:
        Fail-closed audit result for signal efficiency, cosmic rate, beam
        background rate, livetime, and the zero-survivor Poisson mean limit.
    """

    column_values = dict(columns or {})
    registry_values = tuple(_registry_entries(registry_records))
    ingredients: dict[str, SensitivityIngredientEvidence] = {}
    blockers: list[SensitivityClosureBlocker] = []

    for name in REQUIRED_SENSITIVITY_INGREDIENTS:
        evidence = _ingredient_evidence(name, column_values, registry_values)
        ingredients[name] = evidence
        if evidence.blocker is not None:
            blockers.append(evidence.blocker)

    blocker_tuple = tuple(blockers)
    return SensitivityClosureAudit(
        ready=not blocker_tuple,
        ingredients=ingredients,
        blockers=blocker_tuple,
    )


def _ingredient_evidence(
    name: str,
    columns: Mapping[str, Any],
    registry_entries: tuple[tuple[str, Any, str], ...],
) -> SensitivityIngredientEvidence:
    for alias in _INGREDIENT_ALIASES[name]:
        if alias in columns:
            return _validated_evidence(
                name=name,
                column=alias,
                raw_value=columns[alias],
                source=f"explicit_column:{alias}",
            )

    aliases = set(_INGREDIENT_ALIASES[name])
    for key, raw_value, source in registry_entries:
        if key in aliases:
            return _validated_evidence(
                name=name,
                column=key,
                raw_value=raw_value,
                source=f"registry_record:{source}",
            )

    blocker = SensitivityClosureBlocker(
        code=f"missing_ingredient:{name}",
        ingredient=name,
        message=f"Missing sensitivity ingredient {name!r}; no default was invented.",
    )
    return SensitivityIngredientEvidence(
        name=name,
        present=False,
        value=None,
        column=None,
        source="missing",
        blocker=blocker,
    )


def _validated_evidence(
    *,
    name: str,
    column: str,
    raw_value: Any,
    source: str,
) -> SensitivityIngredientEvidence:
    value = _numeric_value(raw_value)
    if value is None:
        blocker = SensitivityClosureBlocker(
            code=f"nonnumeric_ingredient:{name}",
            ingredient=name,
            message=f"Sensitivity ingredient {name!r} from {source} is not numeric.",
        )
        return SensitivityIngredientEvidence(
            name=name,
            present=True,
            value=None,
            column=column,
            source=source,
            blocker=blocker,
        )

    range_blocker = _range_blocker(name, value, source)
    return SensitivityIngredientEvidence(
        name=name,
        present=True,
        value=value,
        column=column,
        source=source,
        blocker=range_blocker,
    )


def _numeric_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(number):
        return None
    return number


def _range_blocker(
    name: str,
    value: float,
    source: str,
) -> SensitivityClosureBlocker | None:
    if name == "signal_efficiency" and not 0.0 <= value <= 1.0:
        return SensitivityClosureBlocker(
            code=f"invalid_ingredient:{name}",
            ingredient=name,
            message=f"Signal efficiency from {source} must satisfy 0 <= efficiency <= 1.",
        )
    if name == "livetime" and value <= 0.0:
        return SensitivityClosureBlocker(
            code=f"invalid_ingredient:{name}",
            ingredient=name,
            message=f"Livetime from {source} must be positive.",
        )
    if name == "zero_survivor_mean_upper_limit" and value <= 0.0:
        return SensitivityClosureBlocker(
            code=f"invalid_ingredient:{name}",
            ingredient=name,
            message=f"Zero-survivor Poisson limit from {source} must be positive.",
        )
    if name in {"cosmic_rate", "beam_background_rate"} and value < 0.0:
        return SensitivityClosureBlocker(
            code=f"invalid_ingredient:{name}",
            ingredient=name,
            message=f"Rate ingredient {name!r} from {source} must be non-negative.",
        )
    return None


def _registry_entries(
    registry_records: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None,
) -> Iterable[tuple[str, Any, str]]:
    if registry_records is None:
        return ()
    if isinstance(registry_records, Mapping):
        return tuple(
            _registry_entry_from_pair(key, value)
            for key, value in registry_records.items()
        )
    return tuple(_registry_entry_from_record(record) for record in registry_records)


def _registry_entry_from_pair(key: str, value: Any) -> tuple[str, Any, str]:
    if isinstance(value, Mapping) and "value" in value:
        source = str(value.get("source") or key)
        return str(key), value["value"], source
    return str(key), value, str(key)


def _registry_entry_from_record(record: Mapping[str, Any]) -> tuple[str, Any, str]:
    key = record.get("ingredient") or record.get("name") or record.get("column")
    if key is None:
        raise ValueError("registry records must include ingredient, name, or column")
    if "value" not in record:
        raise ValueError("registry records must include a value")
    return str(key), record["value"], str(record.get("source") or key)
