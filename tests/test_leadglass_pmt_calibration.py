from pathlib import Path

import pytest

from nnbar_reconstruction.analysis.leadglass_pmt_calibration import (
    THESIS_LEADGLASS_REFLECTIVITY_PERCENT,
    THESIS_PMT_ENERGY_CALIBRATION,
    audit_current_leadglass_pmt_calibration,
    audit_leadglass_pmt_calibration,
    pmt_count_to_gamma_energy_mev,
)


def test_thesis_pmt_energy_formula_requires_positive_n_pmt():
    assert THESIS_PMT_ENERGY_CALIBRATION.slope_mev_per_pmt == pytest.approx(0.46)
    assert THESIS_PMT_ENERGY_CALIBRATION.intercept_mev == pytest.approx(8.02)
    assert THESIS_PMT_ENERGY_CALIBRATION.valid_when == "N_PMT > 0"
    assert pmt_count_to_gamma_energy_mev(100) == pytest.approx(54.02)

    with pytest.raises(ValueError, match="N_PMT"):
        pmt_count_to_gamma_energy_mev(0)


def test_generic_photons_per_mev_evidence_is_non_thesis(tmp_path):
    python_surface = tmp_path / "leadglass_calibration.py"
    python_surface.write_text(
        "nominal_cerenkov_yield: float = 200.0  # photons/MeV\n"
    )

    report = audit_leadglass_pmt_calibration(
        python_surfaces=(python_surface,),
        cpp_reflectivity_surfaces=(),
    )

    assert report.ready is False
    assert report.observed_surfaces[0].status == "non_thesis"
    assert report.observed_surfaces[0].observed_value == pytest.approx(200.0)
    assert report.observed_surfaces[0].unit == "photons_per_mev"
    assert "E_gamma = 0.46 N_PMT + 8.02" in report.observed_surfaces[0].message
    assert "non_thesis_photons_per_mev" in {blocker.code for blocker in report.blockers}


def test_cpp_reflectivity_95_percent_is_mismatch_not_accepted(tmp_path):
    cpp_surface = tmp_path / "LeadGlass_geometry.cc"
    cpp_surface.write_text(
        "G4double reflectivity_coating[] = { 0.95, 0.95 };"
        "  // 95% reflective sides\n"
    )

    report = audit_leadglass_pmt_calibration(
        python_surfaces=(),
        cpp_reflectivity_surfaces=(cpp_surface,),
    )

    assert THESIS_LEADGLASS_REFLECTIVITY_PERCENT == pytest.approx(90.0)
    assert report.ready is False
    assert report.observed_surfaces[0].status == "mismatch"
    assert report.observed_surfaces[0].observed_value == pytest.approx(95.0)
    assert report.observed_surfaces[0].expected_value == pytest.approx(90.0)
    assert "reflectivity_mismatch" in {blocker.code for blocker in report.blockers}


def test_missing_surfaces_return_blockers_instead_of_tracebacks(tmp_path):
    missing_python = tmp_path / "missing_leadglass_calibration.py"
    missing_cpp = tmp_path / "missing_LeadGlass_geometry.cc"

    report = audit_leadglass_pmt_calibration(
        python_surfaces=(missing_python,),
        cpp_reflectivity_surfaces=(missing_cpp,),
    )

    codes = {blocker.code for blocker in report.blockers}
    assert f"missing_surface:{missing_python}" in codes
    assert f"missing_surface:{missing_cpp}" in codes
    assert report.ready is False


def test_current_repository_audit_is_fail_closed_for_unpromoted_surfaces():
    report = audit_current_leadglass_pmt_calibration(Path("."))

    assert pmt_count_to_gamma_energy_mev(100) == pytest.approx(54.02)
    assert report.ready is False
    assert report.blockers
    assert all(
        blocker.code.startswith("missing_surface:")
        or blocker.code
        in {
            "missing_python_photons_per_mev",
            "non_thesis_photons_per_mev",
            "missing_cpp_reflectivity",
            "reflectivity_mismatch",
        }
        for blocker in report.blockers
    )
