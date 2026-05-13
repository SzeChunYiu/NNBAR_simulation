from pathlib import Path

from nnbar_reconstruction.analysis.tpc_response_boundary import (
    ADVANCED_NON_THESIS,
    MISSING_OR_UNVERIFIED,
    THESIS_FIRST_ORDER,
    THESIS_FIRST_ORDER_REQUIRED_COLUMNS,
    classify_tpc_response_config,
    classify_tpc_schema,
    thesis_first_order_contract,
)


def test_thesis_electron_count_schema_is_accepted():
    report = classify_tpc_schema(THESIS_FIRST_ORDER_REQUIRED_COLUMNS)

    assert report.accepted is True
    assert report.category == THESIS_FIRST_ORDER
    assert report.missing_columns == ()
    assert "electrons" in report.required_columns
    assert report.surface.contract["electron_count_model"] == "poisson_from_energy_loss"
    assert report.surface.contract["cell_dimensions_cm"] == (1.0, 1.0, 200.0)


def test_missing_electrons_column_is_downgraded():
    schema_without_electrons = [
        column for column in THESIS_FIRST_ORDER_REQUIRED_COLUMNS if column != "electrons"
    ]

    report = classify_tpc_schema(schema_without_electrons)

    assert report.accepted is False
    assert report.category == MISSING_OR_UNVERIFIED
    assert report.missing_columns == ("electrons",)
    assert "missing required TPC response columns" in report.message


def test_advanced_drift_gain_and_diffusion_flags_are_non_thesis():
    report = classify_tpc_response_config(
        {
            "tpc": {
                "drift_model": "field_map",
                "gas_gain_model": "polya",
                "diffusion_model": "magboltz",
            }
        }
    )

    assert report.category == ADVANCED_NON_THESIS
    assert report.advanced_flags == (
        "tpc.diffusion_model",
        "tpc.drift_model",
        "tpc.gas_gain_model",
    )
    assert "not thesis-authoritative" in report.message


def test_config_audit_does_not_require_absolute_paths():
    report = classify_tpc_response_config(
        {"tpc": {"field_map_path": "/does/not/need/to/exist.map"}}
    )

    assert report.absolute_paths_required is False
    assert report.advanced_flags == ()
    assert report.category == THESIS_FIRST_ORDER


def test_contract_required_columns_are_documented_in_current_tpc_schema_doc():
    schema_doc = Path("docs/rebuild_plans/09_io_schema_data_dictionary/09_tpc.md")
    text = schema_doc.read_text()
    documented = {column for column in THESIS_FIRST_ORDER_REQUIRED_COLUMNS if f"`{column}`" in text}

    assert documented == set(THESIS_FIRST_ORDER_REQUIRED_COLUMNS)
    report = classify_tpc_schema(documented)
    assert report.accepted is True


def test_thesis_contract_records_first_order_evidence_sources():
    contract = thesis_first_order_contract()

    assert contract.category == THESIS_FIRST_ORDER
    assert contract.contract["electron_count_model"] == "poisson_from_energy_loss"
    assert "advanced drift/gain/diffusion" in contract.boundary_note
    assert all(not source.startswith("/") for source in contract.evidence_sources)
