from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nnbar_reconstruction.analysis.neutral_pi0_response_audit import discover_pi0_sample


def _write_pi0_raw_sample(root: Path, energy_mev: int) -> Path:
    sample_dir = root / f"pi0_mono_{energy_mev}mev"
    sample_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Event_ID": [1], "KE": [float(energy_mev)]}).to_parquet(
        sample_dir / "Particle_output_0.parquet", index=False
    )

    # Two photon-like lead-glass clusters from the origin.  Each cluster sums
    # to 67.5 MeV, so a back-to-back pair gives an invariant mass near 135 MeV.
    offsets = np.linspace(-1.0, 1.0, 10)
    energies = [20.0] + [47.5 / 9.0] * 9
    rows = []
    for sign in (1.0, -1.0):
        for dx, edep in zip(offsets, energies):
            rows.append(
                {
                    "Event_ID": 1,
                    "x": sign * (280.0 + dx),
                    "y": 0.5 * dx,
                    "z": 0.25 * dx,
                    "eDep": edep,
                }
            )
    pd.DataFrame(rows).to_parquet(sample_dir / "LeadGlass_output_0.parquet", index=False)
    pd.DataFrame(columns=["Event_ID", "x", "y", "z", "eDep"]).to_parquet(
        sample_dir / "Scintillator_output_0.parquet", index=False
    )
    return sample_dir


def _write_vertex_raw_sample(root: Path, sample_name: str, vertex: tuple[float, float, float] = (3.0, 4.0, 0.0)) -> Path:
    sample_dir = root / sample_name
    sample_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "Event_ID": [1],
            "KE": [150.0],
            "x": [vertex[0]],
            "y": [vertex[1]],
            "z": [vertex[2]],
        }
    ).to_parquet(sample_dir / "Particle_output_0.parquet", index=False)

    offsets = np.linspace(-1.0, 1.0, 10)
    energies = [20.0] + [47.5 / 9.0] * 9
    rows = []
    for sign in (1.0, -1.0):
        for dx, edep in zip(offsets, energies):
            rows.append(
                {
                    "Event_ID": 1,
                    "x": vertex[0] + sign * (280.0 + dx),
                    "y": vertex[1] + 0.5 * dx,
                    "z": vertex[2] + 0.25 * dx,
                    "eDep": edep,
                }
            )
    pd.DataFrame(rows).to_parquet(sample_dir / "LeadGlass_output_0.parquet", index=False)
    pd.DataFrame(columns=["Event_ID", "x", "y", "z", "eDep"]).to_parquet(
        sample_dir / "Scintillator_output_0.parquet", index=False
    )
    return sample_dir


def test_smoke_two_cluster_event_writes_reconstructed_pi0_columns(tmp_path):
    from nnbar_reconstruction.analysis.pi0_reco_driver import run_pi0_reco

    _write_pi0_raw_sample(tmp_path, 150)

    written = run_pi0_reco(tmp_path, tmp_path / "pi0_reco_response", energies_mev=(150,))

    assert written == [tmp_path / "pi0_reco_response" / "pi0_reco_150mev.parquet"]
    frame = pd.read_parquet(written[0])
    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["Event_ID"] == 1
    assert row["n_neutral_objects"] == 2
    assert row["n_pi0_candidates"] == 1
    assert not pd.isna(row["pi0_mass_mev"])
    assert row["opening_angle_deg"] > 30.0
    assert row["reco_photon_energy_mev"] > 0.0
    assert row["truth_photon_energy_mev"] == (150.0 + 134.9766) / 2.0


def test_vertex_scan_reco_writes_truth_radius_and_audit_columns(tmp_path):
    from nnbar_reconstruction.analysis.pi0_reco_driver import run_pi0_vertex_scan_reco

    studies_root = tmp_path / "studies"
    _write_vertex_raw_sample(studies_root, "pi0_vertex_scan_r5mev")

    written = run_pi0_vertex_scan_reco(
        studies_root,
        tmp_path / "pi0_reco_response",
        samples=(("pi0_vertex_scan_r5mev", "pi0_reco_vertex_r5mev.parquet"),),
    )

    assert written == [tmp_path / "pi0_reco_response" / "pi0_reco_vertex_r5mev.parquet"]
    frame = pd.read_parquet(written[0])
    row = frame.iloc[0]
    assert row["Event_ID"] == 1
    assert row["truth_vertex_x_cm"] == pytest.approx(3.0)
    assert row["truth_vertex_y_cm"] == pytest.approx(4.0)
    assert row["truth_vertex_z_cm"] == pytest.approx(0.0)
    assert row["truth_vertex_r_cm"] == pytest.approx(5.0)
    assert {"reco_total_energy_mev", "reco_eff_flag"} <= set(frame.columns)


def test_missing_energy_emits_no_crash(tmp_path):
    from nnbar_reconstruction.analysis.pi0_reco_driver import run_pi0_reco

    with pytest.warns(RuntimeWarning) as emitted:
        written = run_pi0_reco(tmp_path, tmp_path / "pi0_reco_response")

    assert written == []
    assert len(emitted) == 3


def test_discover_prefers_reco_file_over_raw_particle_output(tmp_path):
    raw = tmp_path / "pi0_mono_50mev" / "Particle_output_0.parquet"
    raw.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Event_ID": [1], "KE": [50.0]}).to_parquet(raw, index=False)
    reco = tmp_path / "pi0_reco_response" / "pi0_reco_50mev.parquet"
    reco.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Event_ID": [1], "pi0_mass_mev": [135.0]}).to_parquet(reco, index=False)

    assert discover_pi0_sample(50, tmp_path) == reco
