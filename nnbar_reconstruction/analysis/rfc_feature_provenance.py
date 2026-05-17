"""RFC feature provenance audit helpers.

The Random Forest Classifier must train on feature columns with explicit Ch. 9
or cosmic-weight provenance.  This module reports which current
``RFC_FEATURE_COLUMNS`` are backed by canonical ``EventVariables.to_dict()``
outputs and which remain fail-closed blockers before model retraining.
"""

from __future__ import annotations

from dataclasses import dataclass

from nnbar_reconstruction.analysis.event_variables import EventVariables
from nnbar_reconstruction.data_pipeline.cosmic_weights import get_weight
from nnbar_reconstruction.ml.feature_extraction import RFC_FEATURE_COLUMNS


@dataclass(frozen=True)
class FeatureProvenance:
    """Per-feature provenance status for one RFC input column."""

    name: str
    status: str
    source: str
    canonical_column: str | None = None
    blocker: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class CosmicWeightProvenance:
    """Cosmic background sample-weight provenance status."""

    status: str
    source: str | None = None
    value: float | None = None
    blocker: str | None = None


@dataclass(frozen=True)
class RFCFeatureProvenanceAudit:
    """Complete provenance audit for RFC features plus cosmic weights."""

    features: tuple[FeatureProvenance, ...]
    cosmic_weight: CosmicWeightProvenance

    @property
    def blockers(self) -> tuple[str, ...]:
        """Return every explicit fail-closed blocker emitted by the audit."""
        feature_blockers = tuple(
            feature.blocker for feature in self.features if feature.blocker is not None
        )
        if self.cosmic_weight.blocker is None:
            return feature_blockers
        return feature_blockers + (self.cosmic_weight.blocker,)


_CANONICAL_ALIASES = {
    "scintillator_energy": "scint_energy",
    "leadglass_energy": "lg_energy",
}
_HIT_LEVEL_FALLBACKS = {
    "energy_asymmetry": "extract_rfc_features:_energy_asymmetry detector-y split",
    "n_charged_tracks": "extract_rfc_features:TPC track_id nunique",
    "n_hits_tpc": "extract_rfc_features:TPC hit count",
    "leading_track_dedx": "extract_rfc_features:per-track deposited-energy sum",
    "vertex_x": "extract_rfc_features:TPC hit-position mean x",
    "vertex_y": "extract_rfc_features:TPC hit-position mean y",
    "vertex_z": "extract_rfc_features:TPC hit-position mean z",
}


_PUBLIC_EVENT_VARIABLE_DEFAULTS = {
    "invariant_mass": 0.0,
    "sphericity": 0.0,
    "total_energy": 0.0,
    "scint_energy": 0.0,
    "lg_energy": 0.0,
    "longitudinal_energy": 0.0,
    "transverse_energy": 0.0,
    "top_bottom_asymmetry": 0.0,
    "forward_backward_asymmetry": 0.0,
    "n_charged": 0,
    "n_neutral": 0,
    "n_pions": 0,
    "n_protons": 0,
    "vertex_r": 0.0,
    "n_tracks_to_vertex": 0,
}
_INVALID_FEATURE_COLUMNS_NAME = "<invalid_feature_columns>"
_INVALID_FEATURE_COLUMNS_BLOCKER = "invalid_feature_column_contract"
_INVALID_FEATURE_COLUMNS_DETAIL = (
    "feature_columns must be a sequence of column-name strings; strings must "
    "be exact, non-blank, and unique. Scalar strings, bytes, non-iterable "
    "values, empty sequences, blank names, whitespace-padded names, and "
    "duplicate feature names are rejected to avoid character-wise, vacuous, "
    "typo-prone, or ambiguous audits."
)


def audit_rfc_feature_provenance(
    feature_columns: tuple[str, ...] | list[str] | object | None = None,
    *,
    weight_column: object | None = None,
    cosmic_energy_bin: int | None = None,
    particle_idx: int | None = None,
) -> RFCFeatureProvenanceAudit:
    """Audit RFC feature columns and cosmic-weight evidence.

    Args:
        feature_columns: RFC columns to audit. Defaults to ``RFC_FEATURE_COLUMNS``.
        weight_column: Existing event/sample-weight column supplied by the caller.
        cosmic_energy_bin: Cosmic energy bin for ``get_weight`` lookup.
        particle_idx: Cosmic particle index for ``get_weight`` lookup.

    Returns:
        Audit result containing one status row per feature and one cosmic-weight
        evidence row. Missing evidence is represented as explicit blockers.
    """
    columns = _normalize_feature_columns(feature_columns)
    event_variable_columns = _event_variable_columns()
    if columns is None:
        features = (
            FeatureProvenance(
                name=_INVALID_FEATURE_COLUMNS_NAME,
                status=_INVALID_FEATURE_COLUMNS_BLOCKER,
                source="audit_rfc_feature_provenance(feature_columns=...)",
                blocker=_INVALID_FEATURE_COLUMNS_BLOCKER,
                detail=_INVALID_FEATURE_COLUMNS_DETAIL,
            ),
        )
    else:
        features = tuple(
            _feature_provenance(column, event_variable_columns) for column in columns
        )
    return RFCFeatureProvenanceAudit(
        features=features,
        cosmic_weight=_cosmic_weight_provenance(
            weight_column=weight_column,
            cosmic_energy_bin=cosmic_energy_bin,
            particle_idx=particle_idx,
        ),
    )


def _normalize_feature_columns(feature_columns: object | None) -> tuple[str, ...] | None:
    if feature_columns is None:
        return tuple(RFC_FEATURE_COLUMNS)
    if isinstance(feature_columns, (str, bytes, bytearray)):
        return None
    try:
        columns = tuple(feature_columns)  # type: ignore[arg-type]
    except TypeError:
        return None
    if not columns:
        return None
    if not all(
        isinstance(column, str) and column.strip() and column == column.strip()
        for column in columns
    ):
        return None
    if len(set(columns)) != len(columns):
        return None
    return columns


def _feature_provenance(
    column: str,
    event_variable_columns: set[str],
) -> FeatureProvenance:
    if column in event_variable_columns:
        return FeatureProvenance(
            name=column,
            status="canonical_event_variable",
            source="EventVariables.to_dict()",
            canonical_column=column,
        )

    canonical_column = _CANONICAL_ALIASES.get(column)
    if canonical_column in event_variable_columns:
        return FeatureProvenance(
            name=column,
            status="canonical_event_variable",
            source="EventVariables.to_dict() alias",
            canonical_column=canonical_column,
            detail=f"RFC column maps to canonical event variable {canonical_column!r}.",
        )

    if column in _HIT_LEVEL_FALLBACKS:
        return FeatureProvenance(
            name=column,
            status="hit_level_fallback",
            source=_HIT_LEVEL_FALLBACKS[column],
            blocker=f"missing_provenance:{column}",
            detail="Current extractor derives this from detector hits, not a canonical Ch. 9 event-variable row.",
        )

    return FeatureProvenance(
        name=column,
        status="missing_provenance",
        source="no canonical EventVariables.to_dict() source or documented hit fallback",
        blocker=f"missing_provenance:{column}",
    )


def _cosmic_weight_provenance(
    *,
    weight_column: object | None,
    cosmic_energy_bin: int | None,
    particle_idx: int | None,
) -> CosmicWeightProvenance:
    if (
        isinstance(weight_column, str)
        and weight_column.strip()
        and weight_column == weight_column.strip()
    ):
        return CosmicWeightProvenance(
            status="supplied_weight_column",
            source=weight_column,
        )

    if cosmic_energy_bin is not None and particle_idx is not None:
        if not (_is_exact_int(cosmic_energy_bin) and _is_exact_int(particle_idx)):
            return CosmicWeightProvenance(
                status="missing_weight_evidence",
                blocker="missing_cosmic_weight_evidence",
            )
        value = get_weight(cosmic_energy_bin, particle_idx)
        if value > 0.0:
            return CosmicWeightProvenance(
                status="get_weight",
                source=f"get_weight({cosmic_energy_bin}, {particle_idx})",
                value=value,
            )
        return CosmicWeightProvenance(
            status="missing_weight_evidence",
            source=f"get_weight({cosmic_energy_bin}, {particle_idx})",
            value=value,
            blocker="missing_cosmic_weight_evidence",
        )

    return CosmicWeightProvenance(
        status="missing_weight_evidence",
        blocker="missing_cosmic_weight_evidence",
    )


def _is_exact_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _event_variable_columns() -> set[str]:
    sample = EventVariables(**_PUBLIC_EVENT_VARIABLE_DEFAULTS)
    return set(sample.to_dict())
