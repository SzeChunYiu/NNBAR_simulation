"""Audit thesis detector constants against the Python geometry config.

The manifest is intentionally small and evidence-bound: every constant below is
copied from the checked Chapter 4/5 thesis extracts named in ``source_path``.
C++ geometry remains read-only for this audit unit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from nnbar_reconstruction.utils.config import load_config

CHAPTER4_SOURCE = (
    "/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/"
    "4_HIBEAM_NNBAR_detector_setup.tex"
)
CHAPTER5_SOURCE = (
    "/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/"
    "5_Detector_simulation.tex"
)


@dataclass(frozen=True)
class ThesisConstant:
    """A thesis detector constant and its Python config location.

    Args:
        name: Stable audit identifier.
        config_path: Nested keys in ``nnbar_geometry.yaml``.
        thesis_value: Value verified from the thesis extract.
        thesis_unit: Unit for ``thesis_value``.
        config_unit: Unit used by the current Python config value.
        source_path: Thesis extract file that contains the value.
        source_note: Short provenance note without line-number claims.
        tolerance: Absolute comparison tolerance after unit normalization.
    """

    name: str
    config_path: tuple[str, ...]
    thesis_value: float | int
    thesis_unit: str
    config_unit: str
    source_path: str
    source_note: str
    tolerance: float = 1e-6

    @property
    def expected(self) -> float | int:
        """Return the thesis value in the config comparison unit."""
        return normalize_value(self.thesis_value, self.thesis_unit)


@dataclass(frozen=True)
class GeometryAuditItem:
    """One normalized comparison result for a detector constant.

    Args:
        name: Stable audit identifier.
        status: ``match``, ``mismatch``, or ``missing``.
        expected: Thesis value after normalization.
        actual: Config value after normalization, or ``None`` when missing.
        unit: Unit shared by ``expected`` and ``actual``.
        config_path: Dot-separated config key path.
        source_path: Thesis extract path that supplied the expected value.
        source_note: Human-readable provenance note.
        message: Deterministic summary for reports and tests.
    """

    name: str
    status: str
    expected: float | int
    actual: float | int | None
    unit: str
    config_path: str
    source_path: str
    source_note: str
    message: str


@dataclass(frozen=True)
class GeometryAuditReport:
    """Collection of detector-constant audit items.

    Args:
        items: Ordered audit results following ``THESIS_DETECTOR_CONSTANTS``.
    """

    items: tuple[GeometryAuditItem, ...]

    @property
    def counts(self) -> dict[str, int]:
        """Return result counts for each audit status."""
        return {
            status: sum(item.status == status for item in self.items)
            for status in ("match", "mismatch", "missing")
        }


_MANIFEST_ROWS = (
    ("tpc_type1_width_cm", ("tpc", "type1", "width"), 0.85, "m", "cm", CHAPTER4_SOURCE, "Ch.4: Type-I TPC is 0.85 m x 1.87 m x 2 m."),
    ("tpc_type1_height_cm", ("tpc", "type1", "height"), 1.87, "m", "cm", CHAPTER4_SOURCE, "Ch.4: Type-I TPC is 0.85 m x 1.87 m x 2 m."),
    ("tpc_type2_width_cm", ("tpc", "type2", "width"), 2.04, "m", "cm", CHAPTER4_SOURCE, "Ch.4: Type-II TPC is 2.04 m x 0.85 m x 2 m."),
    ("tpc_type2_height_cm", ("tpc", "type2", "height"), 0.85, "m", "cm", CHAPTER4_SOURCE, "Ch.4: Type-II TPC is 2.04 m x 0.85 m x 2 m."),
    ("tpc_w_value_ev", ("tpc", "w_value"), 27.4, "eV", "eV", CHAPTER5_SOURCE, "Ch.5: Ar/CO2 composite W value is 27.4 eV."),
    ("tpc_container_wall_cm", ("tpc", "container_wall_thickness"), 2.0, "mm", "cm", CHAPTER4_SOURCE, "Ch.4: TPC aluminium container thickness is 2 mm."),
    ("tpc_cell_width_cm", ("tpc", "cell_width"), 1.0, "cm", "cm", CHAPTER5_SOURCE, "Ch.5: TPC readout cells are 1 cm x 1 cm x 2 m."),
    ("tpc_cell_height_cm", ("tpc", "cell_height"), 1.0, "cm", "cm", CHAPTER5_SOURCE, "Ch.5: TPC readout cells are 1 cm x 1 cm x 2 m."),
    ("tpc_cell_length_cm", ("tpc", "cell_length"), 2.0, "m", "cm", CHAPTER5_SOURCE, "Ch.5: TPC readout cells are 1 cm x 1 cm x 2 m."),
    ("scintillator_layer_count", ("scintillator", "n_layers"), 10, "count", "count", CHAPTER4_SOURCE, "Ch.4: a scintillator module contains 10 layers."),
    ("scintillator_staves_per_layer", ("scintillator", "n_staves_per_layer"), 4, "count", "count", CHAPTER4_SOURCE, "Ch.4: each scintillator layer has four staves."),
    ("scintillator_stave_width_cm", ("scintillator", "stave_width"), 10.0, "cm", "cm", CHAPTER4_SOURCE, "Ch.4: stave dimensions are 10 cm x 3 cm x 40 cm."),
    ("scintillator_stave_thickness_cm", ("scintillator", "stave_thickness"), 3.0, "cm", "cm", CHAPTER4_SOURCE, "Ch.4: stave dimensions are 10 cm x 3 cm x 40 cm."),
    ("scintillator_stave_length_cm", ("scintillator", "stave_length"), 40.0, "cm", "cm", CHAPTER4_SOURCE, "Ch.4: stave dimensions are 10 cm x 3 cm x 40 cm."),
    ("scintillator_tpc_gap_cm", ("scintillator", "gap_above_tpc"), 5.0, "cm", "cm", CHAPTER4_SOURCE, "Ch.4: scintillator modules sit 5 cm above TPC modules."),
    ("scintillator_layer_spacing_cm", ("scintillator", "layer_spacing"), 5.0, "cm", "cm", CHAPTER4_SOURCE, "Ch.4: scintillator modules are spaced 5 cm apart."),
    ("lead_glass_block_width_cm", ("calorimeter", "module_size"), 8.0, "cm", "cm", CHAPTER4_SOURCE, "Ch.4: SF-5 lead-glass blocks are 8 cm x 8 cm x 25 cm."),
    ("lead_glass_block_height_cm", ("calorimeter", "module_size"), 8.0, "cm", "cm", CHAPTER4_SOURCE, "Ch.4: SF-5 lead-glass blocks are 8 cm x 8 cm x 25 cm."),
    ("lead_glass_block_length_cm", ("calorimeter", "module_length"), 25.0, "cm", "cm", CHAPTER4_SOURCE, "Ch.4: SF-5 lead-glass blocks are 8 cm x 8 cm x 25 cm."),
    ("lead_glass_reflectivity_percent", ("calorimeter", "reflectivity"), 90.0, "percent", "percent", CHAPTER5_SOURCE, "Ch.5: lead-glass reflective optical surface assumes 90 percent."),
    ("cosmic_veto_half_x_cm", ("shield", "half_x"), 3.2, "m", "cm", CHAPTER4_SOURCE, "Ch.4: cosmic-veto envelope is 6.4 m x 6.4 m x 7.2 m."),
    ("cosmic_veto_half_y_cm", ("shield", "half_y"), 3.2, "m", "cm", CHAPTER4_SOURCE, "Ch.4: cosmic-veto envelope is 6.4 m x 6.4 m x 7.2 m."),
    ("cosmic_veto_half_z_cm", ("shield", "half_z"), 3.6, "m", "cm", CHAPTER4_SOURCE, "Ch.4: cosmic-veto envelope is 6.4 m x 6.4 m x 7.2 m."),
    ("passive_shield_thickness_cm", ("shield", "passive_concrete_thickness"), 2.0, "m", "cm", CHAPTER4_SOURCE, "Ch.4: passive concrete shielding is 2 m thick."),
)

THESIS_DETECTOR_CONSTANTS: tuple[ThesisConstant, ...] = tuple(
    ThesisConstant(*row) for row in _MANIFEST_ROWS
)

_LENGTH_FACTORS_TO_CM = {
    "cm": 1.0,
    "m": 100.0,
    "mm": 0.1,
}
_IDENTITY_UNITS = {"count", "eV", "percent"}
_MISSING = object()


def normalize_value(value: Any, unit: str) -> Any:
    """Normalize a scalar or sequence value according to ``unit``.

    Args:
        value: Numeric scalar or sequence of numeric values.
        unit: ``cm``, ``m``, ``mm``, ``count``, ``eV``, or ``percent``.

    Returns:
        Numeric value with lengths converted to centimetres; dimensionless
        units are returned unchanged.

    Raises:
        ValueError: If the unit is not supported.
    """
    if unit in _LENGTH_FACTORS_TO_CM:
        factor = _LENGTH_FACTORS_TO_CM[unit]
    elif unit in _IDENTITY_UNITS:
        factor = 1.0
    else:
        raise ValueError(f"Unsupported geometry-constant unit: {unit}")

    if _is_sequence(value):
        return tuple(float(entry) * factor for entry in value)
    if isinstance(value, int) and factor == 1.0:
        return value
    return float(value) * factor


def audit_geometry_constants(
    config: Mapping[str, Any],
    manifest: Sequence[ThesisConstant] = THESIS_DETECTOR_CONSTANTS,
) -> GeometryAuditReport:
    """Compare thesis detector constants with a loaded config mapping.

    Args:
        config: Parsed ``nnbar_geometry.yaml``-style mapping.
        manifest: Constants to audit, in deterministic report order.

    Returns:
        Ordered report containing ``match``, ``mismatch``, or ``missing`` for
        each manifest entry.
    """
    items = tuple(_audit_one(config, constant) for constant in manifest)
    return GeometryAuditReport(items=items)


def load_and_audit_geometry_constants(
    config_path: str | Path | None = None,
    manifest: Sequence[ThesisConstant] = THESIS_DETECTOR_CONSTANTS,
) -> GeometryAuditReport:
    """Load a YAML geometry config and audit it against the thesis manifest.

    Args:
        config_path: Optional path to a geometry YAML file. When omitted, the
            package default config is loaded.
        manifest: Constants to audit, in deterministic report order.

    Returns:
        Ordered geometry audit report.
    """
    config = load_config(config_path, force_reload=True)
    return audit_geometry_constants(config, manifest=manifest)


def _audit_one(config: Mapping[str, Any], constant: ThesisConstant) -> GeometryAuditItem:
    raw_actual = _get_path(config, constant.config_path)
    expected = constant.expected
    config_path = ".".join(constant.config_path)

    if raw_actual is _MISSING:
        return GeometryAuditItem(
            name=constant.name,
            status="missing",
            expected=expected,
            actual=None,
            unit=constant.config_unit,
            config_path=config_path,
            source_path=constant.source_path,
            source_note=constant.source_note,
            message=f"{config_path} is missing; thesis expects {expected:g} {constant.config_unit}",
        )

    actual = normalize_value(raw_actual, constant.config_unit)
    status = "match" if _values_close(expected, actual, constant.tolerance) else "mismatch"
    message = (
        f"{config_path}: expected {expected:g} {constant.config_unit}, "
        f"found {actual:g} {constant.config_unit}"
    )
    return GeometryAuditItem(
        name=constant.name,
        status=status,
        expected=expected,
        actual=actual,
        unit=constant.config_unit,
        config_path=config_path,
        source_path=constant.source_path,
        source_note=constant.source_note,
        message=message,
    )


def _get_path(config: Mapping[str, Any], path: Sequence[str]) -> Any:
    current: Any = config
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return _MISSING
        current = current[key]
    return current


def _values_close(expected: Any, actual: Any, tolerance: float) -> bool:
    if _is_sequence(expected) or _is_sequence(actual):
        if not (_is_sequence(expected) and _is_sequence(actual)):
            return False
        if len(expected) != len(actual):
            return False
        return all(abs(float(lhs) - float(rhs)) <= tolerance for lhs, rhs in zip(expected, actual))
    return abs(float(expected) - float(actual)) <= tolerance


def _is_sequence(value: Any) -> bool:
    return isinstance(value, (tuple, list)) and not isinstance(value, (str, bytes))
