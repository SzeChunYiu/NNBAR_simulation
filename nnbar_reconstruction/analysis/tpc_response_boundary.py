"""TPC response-boundary audit helpers.

This module makes the permitted TPC response surface explicit: thesis-backed
reconstruction may use first-order ionisation-electron counts per TPC segment,
while drift, gain, diffusion, Garfield, and GPU digitisation paths remain
non-authoritative unless a future source-backed audit promotes them.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping

THESIS_FIRST_ORDER = "thesis_first_order"
PRODUCTION_SCHEMA = "production_schema"
ADVANCED_NON_THESIS = "advanced_non_thesis"
MISSING_OR_UNVERIFIED = "missing_or_unverified"

RESPONSE_CATEGORIES = (
    THESIS_FIRST_ORDER,
    PRODUCTION_SCHEMA,
    ADVANCED_NON_THESIS,
    MISSING_OR_UNVERIFIED,
)

THESIS_FIRST_ORDER_REQUIRED_COLUMNS = (
    "Event_ID",
    "Track_ID",
    "Module_ID",
    "Layer_ID",
    "x",
    "y",
    "z",
    "trackl",
    "eDep",
    "electrons",
)

ADVANCED_CONFIG_KEYS = frozenset(
    {
        "diffusion_model",
        "drift_model",
        "electron_drift_model",
        "garfield_enabled",
        "gas_gain_model",
        "gain_model",
        "gpu_drift_enabled",
        "pad_response_model",
    }
)


@dataclass(frozen=True)
class TPCResponseSurface:
    """Machine-readable description of one TPC response surface.

    Args:
        name: Stable surface identifier.
        category: One of ``RESPONSE_CATEGORIES``.
        contract: Small value dictionary describing the response contract.
        evidence_sources: Relative docs/plans/thesis labels supporting it.
        evidence_by_item: Per-contract-item evidence labels.
        boundary_note: Human-readable authority boundary.
    """

    name: str
    category: str
    contract: Mapping[str, object]
    evidence_sources: tuple[str, ...]
    evidence_by_item: Mapping[str, str]
    boundary_note: str


@dataclass(frozen=True)
class TPCSchemaAuditReport:
    """Result of classifying a TPC parquet-like schema.

    Args:
        category: Evidence category assigned to the schema.
        accepted: Whether the schema satisfies the first-order thesis contract.
        required_columns: Columns required by the first-order contract.
        missing_columns: Required columns absent from the audited schema.
        surface: Response surface used for the classification.
        message: Deterministic summary suitable for ledger notes.
    """

    category: str
    accepted: bool
    required_columns: tuple[str, ...]
    missing_columns: tuple[str, ...]
    surface: TPCResponseSurface
    message: str


@dataclass(frozen=True)
class TPCConfigAuditReport:
    """Result of classifying TPC response options in a config mapping.

    Args:
        category: Evidence category assigned to the config.
        advanced_flags: Advanced response keys present with enabled values.
        absolute_paths_required: Always false; this audit never reads paths.
        message: Deterministic summary suitable for ledger notes.
    """

    category: str
    advanced_flags: tuple[str, ...]
    absolute_paths_required: bool
    message: str


def _frozen_mapping(values: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(values))


THESIS_FIRST_ORDER_SURFACE = TPCResponseSurface(
    name="tpc_first_order_electron_count",
    category=THESIS_FIRST_ORDER,
    contract=_frozen_mapping(
        {
            "electron_count_model": "poisson_from_energy_loss",
            "cell_dimensions_cm": (1.0, 1.0, 200.0),
            "required_columns": THESIS_FIRST_ORDER_REQUIRED_COLUMNS,
            "dedx_observable": "electrons_per_track_length_cm",
            "advanced_digitisation": "out_of_scope",
        }
    ),
    evidence_sources=(
        "thesis_extracted/5_Detector_simulation.tex Time Projection Chamber",
        "thesis_extracted/7_Reconstruction.tex TPC dE/dx calculation",
        "docs/rebuild_plans/09_io_schema_data_dictionary/09_tpc.md",
        "docs/rebuild_plans/17_field_calibration.md §3",
    ),
    evidence_by_item=MappingProxyType(
        {
            "poisson_ionisation_electrons": "thesis Ch.5 TPC simulation",
            "segment_cell_dimensions": "thesis Ch.5 TPC simulation",
            "required_parquet_columns": "plan 09 split TPC schema",
            "dedx_from_electrons_per_length": "thesis Ch.7 TPC dE/dx calculation",
        }
    ),
    boundary_note=(
        "Thesis-authoritative surface is first-order electron count per segment; "
        "advanced drift/gain/diffusion digitisation is outside this authority."
    ),
)

PRODUCTION_SCHEMA_SURFACE = TPCResponseSurface(
    name="current_tpc_parquet_schema",
    category=PRODUCTION_SCHEMA,
    contract=_frozen_mapping(
        {
            "file_pattern": "TPC_output_<run>.parquet",
            "position_units": "cm",
            "electron_count_column": "electrons",
        }
    ),
    evidence_sources=("docs/rebuild_plans/09_io_schema_data_dictionary/09_tpc.md",),
    evidence_by_item=MappingProxyType(
        {"schema_columns": "plan 09 split TPC schema"}
    ),
    boundary_note="Production schema records the current parquet surface only.",
)

ADVANCED_NON_THESIS_SURFACE = TPCResponseSurface(
    name="advanced_tpc_digitisation_flags",
    category=ADVANCED_NON_THESIS,
    contract=_frozen_mapping(
        {
            "advanced_flags": tuple(sorted(ADVANCED_CONFIG_KEYS)),
            "authority": "not thesis-authoritative in this audit",
        }
    ),
    evidence_sources=(
        "docs/rebuild_plans/17_field_calibration.md §3-§4",
        "docs/parallel-sessions/tpc-response-boundary-audit.md",
    ),
    evidence_by_item=MappingProxyType(
        {"advanced_boundary": "lane spec and plan 17 limitations"}
    ),
    boundary_note=(
        "Drift, gain, diffusion, pad response, Garfield, and GPU response "
        "flags are treated as non-thesis evidence unless separately audited."
    ),
)

MISSING_OR_UNVERIFIED_SURFACE = TPCResponseSurface(
    name="missing_or_unverified_tpc_response",
    category=MISSING_OR_UNVERIFIED,
    contract=_frozen_mapping(
        {"authority": "missing required columns or unverified advanced source"}
    ),
    evidence_sources=("docs/parallel-sessions/tpc-response-boundary-audit.md",),
    evidence_by_item=MappingProxyType(
        {"failure_mode": "lane spec fail-closed boundary"}
    ),
    boundary_note="Do not make thesis reconstruction claims from this surface.",
)

TPC_RESPONSE_SURFACES = MappingProxyType(
    {
        THESIS_FIRST_ORDER_SURFACE.name: THESIS_FIRST_ORDER_SURFACE,
        PRODUCTION_SCHEMA_SURFACE.name: PRODUCTION_SCHEMA_SURFACE,
        ADVANCED_NON_THESIS_SURFACE.name: ADVANCED_NON_THESIS_SURFACE,
        MISSING_OR_UNVERIFIED_SURFACE.name: MISSING_OR_UNVERIFIED_SURFACE,
    }
)


def thesis_first_order_contract() -> TPCResponseSurface:
    """Return the thesis-authoritative first-order TPC response contract.

    Returns:
        Immutable response-surface record for Poisson ionisation-electron
        counts per segmented TPC cell.
    """
    return THESIS_FIRST_ORDER_SURFACE


def classify_tpc_schema(columns: Iterable[str] | Mapping[str, object]) -> TPCSchemaAuditReport:
    """Classify a TPC parquet-like schema against the first-order contract.

    Args:
        columns: Iterable of column names, or a mapping whose keys are the
            available column names.

    Returns:
        Schema audit report. Missing first-order columns fail closed as
        ``missing_or_unverified``.
    """
    available = set(columns.keys() if isinstance(columns, Mapping) else columns)
    missing = tuple(
        column for column in THESIS_FIRST_ORDER_REQUIRED_COLUMNS if column not in available
    )
    if missing:
        return TPCSchemaAuditReport(
            category=MISSING_OR_UNVERIFIED,
            accepted=False,
            required_columns=THESIS_FIRST_ORDER_REQUIRED_COLUMNS,
            missing_columns=missing,
            surface=MISSING_OR_UNVERIFIED_SURFACE,
            message="missing required TPC response columns: " + ", ".join(missing),
        )

    return TPCSchemaAuditReport(
        category=THESIS_FIRST_ORDER,
        accepted=True,
        required_columns=THESIS_FIRST_ORDER_REQUIRED_COLUMNS,
        missing_columns=(),
        surface=THESIS_FIRST_ORDER_SURFACE,
        message="schema satisfies the thesis first-order TPC electron-count contract",
    )


def classify_tpc_response_config(config: Mapping[str, object]) -> TPCConfigAuditReport:
    """Classify TPC response options in a config mapping without path I/O.

    Args:
        config: Parsed config dictionary. Absolute path values are treated as
            inert strings; the audit never checks whether they exist.

    Returns:
        Config audit report. Enabled advanced response keys are marked
        ``advanced_non_thesis``.
    """
    advanced_flags = tuple(
        sorted(
            path
            for path, value in _flatten_mapping(config)
            if _is_enabled_advanced_key(path, value)
        )
    )
    if advanced_flags:
        return TPCConfigAuditReport(
            category=ADVANCED_NON_THESIS,
            advanced_flags=advanced_flags,
            absolute_paths_required=False,
            message=(
                "advanced TPC response flags are present but not thesis-authoritative: "
                + ", ".join(advanced_flags)
            ),
        )

    return TPCConfigAuditReport(
        category=THESIS_FIRST_ORDER,
        advanced_flags=(),
        absolute_paths_required=False,
        message="no enabled advanced TPC response flags; path values were not read",
    )


def _flatten_mapping(
    mapping: Mapping[str, object], prefix: tuple[str, ...] = ()
) -> tuple[tuple[str, object], ...]:
    rows: list[tuple[str, object]] = []
    for key, value in mapping.items():
        path = (*prefix, str(key))
        if isinstance(value, Mapping):
            rows.extend(_flatten_mapping(value, path))
        else:
            rows.append((".".join(path), value))
    return tuple(rows)


def _is_enabled_advanced_key(path: str, value: object) -> bool:
    leaf = path.rsplit(".", 1)[-1]
    if leaf not in ADVANCED_CONFIG_KEYS:
        return False
    if value is False or value is None:
        return False
    if isinstance(value, str) and value.strip().lower() in {"", "none", "off", "false"}:
        return False
    return True
