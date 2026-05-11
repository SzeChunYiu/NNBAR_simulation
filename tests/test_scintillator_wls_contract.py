from pathlib import Path

from nnbar_reconstruction.analysis.scintillator_wls_contract import (
    EvidencePackage,
    audit_current_scintillator_wls_contract,
    audit_scintillator_wls_contract,
)


def _codes(report):
    return {blocker.code for blocker in report.blockers}


def _kinds(report):
    return {surface.kind for surface in report.observed_surfaces}


def test_source_backed_radial_and_longitudinal_functions_with_dec_are_ready(tmp_path):
    source = tmp_path / "ScintillatorWLS.cc"
    source.write_text(
        "double scintillator_wls_f_r(double r_cm) { return 1.0 - 0.01 * r_cm; }\n"
        "double scintillator_wls_f_z(double z_cm) { return exp(-abs(z_cm) / 210.0); }\n"
    )

    report = audit_scintillator_wls_contract(
        EvidencePackage(
            source_surfaces=(source,),
            provenance="DEC-2026-05-11-scintillator-wls-closure",
        )
    )

    assert report.ready is True
    assert report.blockers == ()
    assert _kinds(report) >= {"wls_radial_function", "wls_longitudinal_function"}


def test_scalar_light_yield_and_attenuation_are_diagnostic_not_ready(tmp_path):
    source = tmp_path / "ScintillatorSD.cc"
    source.write_text(
        "G4int photons = (energyDeposit*11136.);\n"
        "G4double atten_scint[2] = {210*cm, 210*cm};\n"
        "scintMPT->AddProperty(\"ABSLENGTH\", energy, atten_scint, 2);\n"
    )

    report = audit_scintillator_wls_contract(EvidencePackage(source_surfaces=(source,)))

    assert report.ready is False
    assert _kinds(report) >= {"scalar_light_yield", "attenuation_length"}
    assert _codes(report) >= {
        "missing_wls_radial_function",
        "missing_wls_longitudinal_function",
        "missing_wls_provenance",
    }
    blocker_text = "\n".join(blocker.message for blocker in report.blockers)
    assert "cal_scintillator_wls_uniform_scan_v1" in blocker_text
    assert "local radial coordinate r" in blocker_text
    assert "local longitudinal coordinate z" in blocker_text
    assert "closure residual" in blocker_text


def test_missing_sources_are_reported_without_traceback(tmp_path):
    missing = tmp_path / "missing_scintillator.cc"

    report = audit_scintillator_wls_contract(EvidencePackage(source_surfaces=(missing,)))

    assert report.ready is False
    assert f"missing_surface:{missing}" in _codes(report)
    assert report.observed_surfaces == ()


def test_functions_without_dec_or_closure_artifact_still_fail_closed(tmp_path):
    source = tmp_path / "ScintillatorWLS.cc"
    source.write_text(
        "double scintillator_wls_f_r(double r_cm) { return 1.0; }\n"
        "double scintillator_wls_f_z(double z_cm) { return 1.0; }\n"
    )

    report = audit_scintillator_wls_contract(EvidencePackage(source_surfaces=(source,)))

    assert report.ready is False
    assert "missing_wls_provenance" in _codes(report)
    assert _kinds(report) >= {"wls_radial_function", "wls_longitudinal_function"}


def test_existing_repository_audit_stays_fail_closed_for_missing_wls_functions():
    report = audit_current_scintillator_wls_contract(Path("."))

    assert report.ready is False
    assert "missing_wls_radial_function" in _codes(report)
    assert "missing_wls_longitudinal_function" in _codes(report)
    assert any(
        surface.kind in {"scalar_light_yield", "attenuation_length", "wls_geometry_comment"}
        for surface in report.observed_surfaces
    )
