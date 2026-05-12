from __future__ import annotations

from pathlib import Path

from scripts.verify_beam_background_occupancy import validate


APPENDIX_TEXT = """
Config. 1 no coating
Config. 2 B4C coating
Config. 3 6LiF coating
Config. 4 Cd absorber
default B4C: 2.6e11 photons/s
no coating: 3.0e11 photons/s
6LiF: 7.6e8 photons/s
Cd absorber: 9.9e11 photons/s
detector interaction intensities per 50 ns
25 microseconds drift frame
0.071 ms pulse separation
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _minimal_tree(root: Path) -> None:
    _write(root / "thesis/12_Appendix_1.tex", APPENDIX_TEXT)
    _write(
        root / "NNBAR_Detector/src/detector/beampipe_geometry.cc",
        """
        auto coating = SelectAbsorberMaterial(config.absorber);
        if (config.absorber == "B4C") use_B4C();
        if (config.absorber == "6LiF") use_6LiF();
        if (config.absorber == "Cd") use_Cd();
        """,
    )
    _write(
        root / "NNBAR_Detector/src/core/PhysicsList.cc",
        "RegisterPhysics(new G4HadronPhysicsFTFP_BERT_HP());",
    )
    _write(root / "NNBAR_Detector/slurm/beam_background.sbatch", "sbatch")
    _write(
        root / "data/registry/beam_neutron_hibeam_test_v1/manifest.txt",
        """
        command: sbatch beam_background.sbatch
        output: output/beam_background.parquet
        normalization: 14 pulses, 0.071 ms spacing
        physics_list: FTFP_BERT_HP
        """,
    )


def test_missing_inputs_fail_closed(tmp_path: Path) -> None:
    report = validate(tmp_path, appendix_path=tmp_path / "missing_appendix.tex")

    assert not report.ok
    blocker_names = {item.name for item in report.blockers}
    assert "appendix_a_source" in blocker_names
    assert "beampipe_geometry_source" in blocker_names
    assert "beam_neutron_registry" in blocker_names


def test_validator_passes_when_required_surfaces_exist(tmp_path: Path) -> None:
    _minimal_tree(tmp_path)

    report = validate(tmp_path, appendix_path=tmp_path / "thesis/12_Appendix_1.tex")

    assert report.ok
    assert report.blockers == []


def test_hardcoded_b4c_and_non_hp_emit_specific_blockers(tmp_path: Path) -> None:
    _minimal_tree(tmp_path)
    _write(
        tmp_path / "NNBAR_Detector/src/detector/beampipe_geometry.cc",
        """
        auto B4CMaterial = G4Material::GetMaterial("B4C");
        new G4LogicalVolume(solid, B4CMaterial, "beam_pipe_coating");
        """,
    )
    _write(
        tmp_path / "NNBAR_Detector/src/core/PhysicsList.cc",
        """
        #include "G4HadronPhysicsFTFP_BERT_HP.hh"
        RegisterPhysics(new G4HadronPhysicsFTFP_BERT());
        """,
    )

    report = validate(tmp_path, appendix_path=tmp_path / "thesis/12_Appendix_1.tex")

    blocker_names = {item.name for item in report.blockers}
    assert "absorber_selector" in blocker_names
    assert "hp_physics_registration" in blocker_names
