from pathlib import Path

import pytest

from nnbar_reconstruction.analysis.geometry_constants import (
    THESIS_DETECTOR_CONSTANTS,
    audit_geometry_constants,
    load_and_audit_geometry_constants,
    normalize_value,
)


def report_by_name(report):
    return {item.name: item for item in report.items}


def test_normalize_value_converts_lengths_to_cm():
    assert normalize_value(6.4, "m") == pytest.approx(640.0)
    assert normalize_value(2.0, "mm") == pytest.approx(0.2)
    assert normalize_value((8.0, 25.0), "cm") == pytest.approx((8.0, 25.0))


def test_audit_geometry_constants_reports_toy_mismatch():
    toy_config = {
        "scintillator": {"n_layers": 9},
        "calorimeter": {"module_size": 8.0, "module_length": 25.0},
    }

    report = audit_geometry_constants(toy_config)
    items = report_by_name(report)

    assert items["scintillator_layer_count"].status == "mismatch"
    assert items["scintillator_layer_count"].expected == 10
    assert items["scintillator_layer_count"].actual == 9
    assert items["lead_glass_block_width_cm"].status == "match"
    assert items["lead_glass_block_length_cm"].status == "match"
    assert items["tpc_type1_width_cm"].status == "missing"


def test_load_and_audit_geometry_constants_reads_yaml(tmp_path):
    config_path = tmp_path / "geometry.yaml"
    config_path.write_text(
        "tpc:\n"
        "  type1:\n"
        "    width: 85.0\n"
        "  w_value: 23.6\n"
        "shield:\n"
        "  half_x: 320.0\n"
    )

    report = load_and_audit_geometry_constants(config_path)
    items = report_by_name(report)

    assert items["tpc_type1_width_cm"].status == "match"
    assert items["tpc_w_value_ev"].status == "mismatch"
    assert items["cosmic_veto_half_x_cm"].status == "match"


def test_current_config_audit_is_deterministic_and_exposes_known_drift():
    report = load_and_audit_geometry_constants()
    names = [item.name for item in report.items]
    items = report_by_name(report)

    assert names == [constant.name for constant in THESIS_DETECTOR_CONSTANTS]
    assert items["scintillator_layer_count"].status == "match"
    assert items["tpc_w_value_ev"].status == "mismatch"
    assert items["lead_glass_block_width_cm"].status == "mismatch"
    assert items["lead_glass_block_length_cm"].status == "mismatch"
    assert items["cosmic_veto_half_y_cm"].status == "mismatch"
    assert items["passive_shield_thickness_cm"].status == "missing"
    assert report.counts["mismatch"] > 0
    assert report.counts["missing"] > 0


def test_manifest_source_paths_are_existing_thesis_extracts():
    for constant in THESIS_DETECTOR_CONSTANTS:
        assert Path(constant.source_path).exists(), constant.name
        assert "thesis_extracted" in constant.source_path
