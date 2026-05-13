from pathlib import Path

from nnbar_reconstruction.analysis.scintillator_wls_contract import (
    SCALAR_RESPONSE,
    WLS_FUNCTION,
    audit_current_scintillator_wls_contract,
    audit_scintillator_wls_contract,
    scan_text_for_wls_evidence,
)


def test_text_scanner_distinguishes_wls_functions_from_scalar_response():
    radial = scan_text_for_wls_evidence(
        "f(r) = A exp(-r/B) + C; source DEC-2026-05-11-WLS", "radial.cc"
    )
    longitudinal = scan_text_for_wls_evidence(
        "auto f_z = D * exp(-z / E); closure artifact output/wls/summary.json",
        "longitudinal.cc",
    )
    scalar = scan_text_for_wls_evidence(
        "light_yield: 11136\nattenuation_length: 200.0", "nnbar_geometry.yaml"
    )

    assert radial.radial_function.kind == WLS_FUNCTION
    assert radial.radial_function.present is True
    assert radial.longitudinal_function.present is False
    assert radial.provenance_present is True
    assert longitudinal.longitudinal_function.kind == WLS_FUNCTION
    assert longitudinal.longitudinal_function.present is True
    assert longitudinal.provenance_present is True
    assert scalar.scalar_response.kind == SCALAR_RESPONSE
    assert scalar.scalar_response.present is True
    assert scalar.radial_function.present is False
    assert scalar.longitudinal_function.present is False


def test_complete_source_backed_wls_functions_with_provenance_are_ready(tmp_path):
    source = tmp_path / "NNBAR_Detector" / "src" / "Sensitive_Detector"
    source.mkdir(parents=True)
    (source / "ScintillatorWLS.cc").write_text(
        """
        // DEC-2026-05-11-WLS source-backed closure
        double radial = A * std::exp(-r / B) + C; // f(r)
        double longitudinal = D * std::exp(-z / E); // f(z)
        // closure artifact: output/calibration/scintillator_wls/summary.json
        """
    )

    report = audit_scintillator_wls_contract(tmp_path)

    assert report.ready is True
    assert report.radial_function.present is True
    assert report.longitudinal_function.present is True
    assert report.radial_function.source_backed is True
    assert report.longitudinal_function.source_backed is True
    assert report.radial_function.provenance_present is True
    assert report.longitudinal_function.provenance_present is True
    assert report.blockers == ()


def test_scalar_only_current_style_config_fails_closed_with_specific_blockers(tmp_path):
    config_dir = tmp_path / "nnbar_reconstruction" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "nnbar_geometry.yaml").write_text(
        """
        scintillator:
          light_yield: 11136
          attenuation_length: 200.0
        """
    )

    report = audit_scintillator_wls_contract(tmp_path)

    assert report.ready is False
    assert report.scalar_response.present is True
    assert report.radial_function.present is False
    assert report.longitudinal_function.present is False
    blocker_text = "\n".join(blocker.message for blocker in report.blockers)
    assert "cal_scintillator_wls_muon200_v1" in blocker_text
    assert "n_SiPM / n_scint versus radial distance r" in blocker_text
    assert "fit residual and pull width for f(r)" in blocker_text
    assert "n_SiPM / n_WLS versus longitudinal distance z" in blocker_text
    assert "fit residual and pull width for f(z)" in blocker_text


def test_missing_optional_cpp_surface_is_diagnostic_not_exception(tmp_path):
    report = audit_scintillator_wls_contract(tmp_path)

    assert report.ready is False
    assert any(surface.status == "missing" for surface in report.surfaces)
    assert any("NNBAR_Detector" in surface.path for surface in report.surfaces)
    assert {blocker.code for blocker in report.blockers} >= {
        "missing_radial_wls_function",
        "missing_longitudinal_wls_function",
    }


def test_current_repository_audit_is_fail_closed_until_wls_closure_exists():
    report = audit_current_scintillator_wls_contract(Path("."))

    assert report.ready is False
    assert report.scalar_response.present is True
    assert report.radial_function.present is False
    assert report.longitudinal_function.present is False
    assert any("cal_scintillator_wls_muon200_v1" in b.message for b in report.blockers)
