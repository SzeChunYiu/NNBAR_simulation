from __future__ import annotations

import pandas as pd
import pytest


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


def test_combine_cosmic_background_counts_reused_event_ids_per_run(tmp_path):
    """Event IDs restart in each cosmic run/bin and must not be de-duplicated globally."""
    from nnbar_reconstruction.data_pipeline.cosmic_weights import get_weight
    from scripts.combine_cosmic_background import combine_cosmic_background

    cosmic_root = tmp_path / "cosmic"
    for run_name, edep in (("cosmic_mu-_bin0", 10.0), ("cosmic_mu-_bin1", 20.0)):
        run_dir = cosmic_root / run_name
        run_dir.mkdir(parents=True)
        pd.DataFrame({"Event_ID": [42], "edep": [edep]}).to_parquet(
            run_dir / "TPC_output_0.parquet",
            index=False,
        )

    _, summary = combine_cosmic_background(
        cosmic_root,
        tmp_path / "combined.parquet",
        "TPC",
    )

    assert summary["n_events_by_particle"] == {"mu-": 2}
    assert summary["weighted_events_by_particle"]["mu-"] == pytest.approx(
        get_weight(0, 0) + get_weight(1, 0)
    )


def test_combine_cosmic_background_counts_reused_event_ids_per_shard(tmp_path):
    """Event IDs can restart in separate parquet shards from the same run."""
    from nnbar_reconstruction.data_pipeline.cosmic_weights import get_weight
    from scripts.combine_cosmic_background import combine_cosmic_background

    cosmic_root = tmp_path / "cosmic"
    run_dir = cosmic_root / "cosmic_gamma_bin4"
    run_dir.mkdir(parents=True)
    for shard, edep in enumerate((10.0, 20.0)):
        pd.DataFrame({"Event_ID": [0], "edep": [edep]}).to_parquet(
            run_dir / f"TPC_output_{shard}.parquet",
            index=False,
        )

    combined, summary = combine_cosmic_background(
        cosmic_root,
        tmp_path / "combined.parquet",
        "TPC",
    )

    expected = get_weight(4, 1)
    assert summary["n_events_by_particle"] == {"gamma": 2}
    assert summary["weighted_events_by_particle"]["gamma"] == pytest.approx(2 * expected)
    assert set(combined["cosmic_source_file"]) == {
        "TPC_output_0.parquet",
        "TPC_output_1.parquet",
    }
