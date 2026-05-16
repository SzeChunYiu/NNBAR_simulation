from __future__ import annotations

from nnbar_reconstruction.analysis.cosmic_background_rate_audit import (
    EXPECTED_COSMIC_BINS,
    audit_cosmic_background_rate,
)


def _complete_bin_records(overrides=None):
    overrides = overrides or {}
    records = []
    for particle, ebin in EXPECTED_COSMIC_BINS:
        record = {
            "particle": particle,
            "ebin": ebin,
            "output_rows": 12,
            "output_bytes": 4096,
        }
        record.update(overrides.get((particle, ebin), {}))
        records.append(record)
    return records


def _valid_rate_summary():
    return {
        "total_weighted_events": 42.5,
        "livetime_seconds": 3.0 * 365.25 * 24.0 * 3600.0,
        "cosmic_rate_hz": 4.49e-7,
    }


def test_all_expected_bins_and_numeric_rate_evidence_are_ready():
    audit = audit_cosmic_background_rate(
        _complete_bin_records(),
        rate_summary=_valid_rate_summary(),
    )

    assert audit.ready
    assert audit.expected_bin_count == 27
    assert len(audit.bin_evidence) == 27
    assert audit.blockers == ()
    assert audit.rate_evidence["weighted_sum"].value == 42.5
    assert audit.rate_evidence["livetime_seconds"].value > 0.0
    assert audit.rate_evidence["output_rate"].value == 4.49e-7


def test_missing_expected_bin_is_reported_as_fail_closed_blocker():
    records = [
        record
        for record in _complete_bin_records()
        if not (record["particle"] == "proton" and record["ebin"] == 5)
    ]

    audit = audit_cosmic_background_rate(records, rate_summary=_valid_rate_summary())

    assert not audit.ready
    assert "missing_bin:proton:5" in {blocker.code for blocker in audit.blockers}
    assert audit.bin_evidence[("proton", 5)].status == "missing"


def test_fractional_energy_bin_does_not_satisfy_expected_bin():
    records = _complete_bin_records(
        {
            ("proton", 5): {
                "ebin": 5.7,
            }
        }
    )

    audit = audit_cosmic_background_rate(records, rate_summary=_valid_rate_summary())

    assert not audit.ready
    assert "missing_bin:proton:5" in {blocker.code for blocker in audit.blockers}


def test_invalid_normalization_livetime_and_rate_fields_block_readiness():
    audit = audit_cosmic_background_rate(
        _complete_bin_records(),
        rate_summary={
            "weighted_sum": "not-a-number",
            "livetime_seconds": 0.0,
            "output_rate_hz": None,
        },
    )

    assert not audit.ready
    codes = {blocker.code for blocker in audit.blockers}
    assert "nonnumeric_rate_field:weighted_sum" in codes
    assert "invalid_rate_field:livetime_seconds" in codes
    assert "nonnumeric_rate_field:output_rate" in codes


def test_gamma_bin4_root_stub_blocks_until_merge_artifact_exists():
    gamma_stub = {
        ("gamma", 4): {
            "output_rows": 0,
            "output_bytes": 4,
            "documented_blocker": "root stub exists while shard outputs contain rows",
        }
    }

    blocked = audit_cosmic_background_rate(
        _complete_bin_records(gamma_stub),
        rate_summary=_valid_rate_summary(),
    )
    merged = audit_cosmic_background_rate(
        _complete_bin_records(
            {
                ("gamma", 4): {
                    "output_rows": 0,
                    "output_bytes": 4,
                    "merge_artifact": "build_lunarc/output/cosmic_gamma_bin4/merged.parquet",
                }
            }
        ),
        rate_summary=_valid_rate_summary(),
    )

    assert not blocked.ready
    assert "gamma_bin4_unmerged_shards" in {b.code for b in blocked.blockers}
    assert merged.ready
    assert merged.bin_evidence[("gamma", 4)].status == "merged_artifact"
