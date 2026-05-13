import math

import pandas as pd

from nnbar_reconstruction.analysis.cry_kinematics_audit import (
    ENERGY_BINS_GEV,
    NONZERO_BINS,
    audit_bin,
    run_audit,
)
from nnbar_reconstruction.data_pipeline.cosmic_weights import get_weight


def _uniform_ke_values(n: int, ebin: int) -> list[float]:
    lo_gev, hi_gev = ENERGY_BINS_GEV[ebin]
    lo = lo_gev * 1000.0
    hi = (hi_gev if hi_gev is not None else lo_gev + 10.0) * 1000.0
    edges = [lo + (hi - lo) * i / 10 for i in range(11)]
    values: list[float] = []
    base, extra = divmod(n, 10)
    for i in range(10):
        count = base + (1 if i < extra else 0)
        values.extend([(edges[i] + edges[i + 1]) / 2.0] * count)
    return values


def _cos2_zenith_angles(n: int) -> list[float]:
    edges = [i / 5 for i in range(6)]
    counts = [round(n * (edges[i + 1] ** 3 - edges[i] ** 3)) for i in range(5)]
    counts[-1] += n - sum(counts)
    angles: list[float] = []
    for i, count in enumerate(counts):
        mu = (edges[i] + edges[i + 1]) / 2.0
        angles.extend([math.acos(-mu)] * count)
    return angles


def _write_particle_parquet(path, *, ebin: int = 1, particle_idx: int = 0, n: int = 1500):
    angles = _cos2_zenith_angles(n)
    frame = pd.DataFrame(
        {
            "Event_ID": range(n),
            "KE": _uniform_ke_values(n, ebin),
            "angle": angles,
            "u": [0.0] * n,
            "v": [0.0] * n,
            "w": [math.cos(angle) for angle in angles],
            "weight": [get_weight(ebin, particle_idx)] * n,
        }
    )
    frame.to_parquet(path, index=False)
    return path


def test_run_audit_reports_every_nonzero_bin_missing_without_raising(tmp_path):
    results = run_audit(tmp_path)

    assert len(results) == len(NONZERO_BINS) == 27
    assert all(not result.ready for result in results)
    assert all(result.blockers.parquet_missing for result in results)


def test_audit_bin_accepts_synthetic_uniform_energy_and_cos2_zenith(tmp_path):
    parquet_path = _write_particle_parquet(tmp_path / "Particle_output_0.parquet")

    result = audit_bin("mu-", 1, parquet_path)

    assert result.ready
    assert result.observed_events == 1500
    assert result.expected_3yr_count == 1.90e11
    assert result.blocker_codes == ()


def test_audit_bin_marks_underfilled_samples_as_blocked(tmp_path):
    parquet_path = _write_particle_parquet(tmp_path / "Particle_output_0.parquet", n=50)

    result = audit_bin("mu-", 1, parquet_path)

    assert not result.ready
    assert "bin_underfilled" in result.blocker_codes
    assert not result.blockers.parquet_missing
