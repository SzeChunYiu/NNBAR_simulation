from __future__ import annotations

import pandas as pd


def test_muon_bin0_weight():
    from nnbar_reconstruction.data_pipeline.cosmic_weights import get_weight

    w = get_weight(ebin=0, particle_idx=0)

    assert w > 0
    expected = (1.69e11 / 1e6) * (1.69e11 / 1.814e12)
    assert abs(w - expected) / expected < 0.01


def test_zero_N_returns_zero():
    from nnbar_reconstruction.data_pipeline.cosmic_weights import get_weight

    w = get_weight(ebin=4, particle_idx=2)

    assert w == 0.0


def test_all_weights_positive_for_nonzero_N():
    from nnbar_reconstruction.data_pipeline.cosmic_weights import N_IJ, get_weight

    for (ebin, pidx), N in N_IJ.items():
        if N > 0:
            assert get_weight(ebin, pidx) > 0


def test_combine_cosmic_background_multiplies_existing_event_weight(tmp_path):
    from nnbar_reconstruction.data_pipeline.cosmic_weights import get_weight
    from scripts.combine_cosmic_background import combine_cosmic_background

    cosmic_root = tmp_path / "cosmic"
    run_dir = cosmic_root / "cosmic_mu-_bin0"
    run_dir.mkdir(parents=True)
    pd.DataFrame(
        {"Event_ID": [1, 2], "weight": [2.0, 3.0], "edep": [10.0, 20.0]}
    ).to_parquet(run_dir / "TPC_output_0.parquet", index=False)

    output_path = tmp_path / "combined.parquet"

    combined, summary = combine_cosmic_background(cosmic_root, output_path, "TPC")

    expected = get_weight(0, 0)
    assert output_path.is_file()
    assert summary["n_events_by_particle"] == {"mu-": 2}
    assert summary["total_rows"] == 2
    assert combined["cosmic_particle"].tolist() == ["mu-", "mu-"]
    assert combined["cosmic_ebin"].tolist() == [0, 0]
    assert combined["cosmic_weight"].tolist() == [expected, expected]
    assert combined["weight"].tolist() == [2.0 * expected, 3.0 * expected]
