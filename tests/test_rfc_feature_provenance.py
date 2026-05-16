from __future__ import annotations

from nnbar_reconstruction.analysis.rfc_feature_provenance import (
    audit_rfc_feature_provenance,
)
from nnbar_reconstruction.ml.feature_extraction import RFC_FEATURE_COLUMNS


def _by_name(audit):
    return {entry.name: entry for entry in audit.features}


def test_audit_reports_every_rfc_feature_column():
    audit = audit_rfc_feature_provenance()

    assert [entry.name for entry in audit.features] == RFC_FEATURE_COLUMNS


def test_event_variable_features_resolve_to_canonical_sources():
    feature = _by_name(audit_rfc_feature_provenance())

    for name in ["total_energy", "sphericity", "invariant_mass"]:
        assert feature[name].status == "canonical_event_variable"
        assert feature[name].canonical_column == name
        assert feature[name].blocker is None

    assert feature["scintillator_energy"].canonical_column == "scint_energy"
    assert feature["leadglass_energy"].canonical_column == "lg_energy"


def test_hit_level_fallbacks_are_explicit_provenance_blockers():
    feature = _by_name(audit_rfc_feature_provenance())

    for name in ["vertex_x", "vertex_y", "vertex_z", "n_hits_tpc", "leading_track_dedx"]:
        assert feature[name].status == "hit_level_fallback"
        assert feature[name].blocker == f"missing_provenance:{name}"
        assert "extract_rfc_features" in feature[name].source


def test_cosmic_weight_is_available_from_get_weight_or_supplied_column():
    by_column = audit_rfc_feature_provenance(weight_column="event_weight")
    by_lookup = audit_rfc_feature_provenance(cosmic_energy_bin=0, particle_idx=0)

    assert by_column.cosmic_weight.status == "supplied_weight_column"
    assert by_column.cosmic_weight.source == "event_weight"
    assert by_column.cosmic_weight.blocker is None

    assert by_lookup.cosmic_weight.status == "get_weight"
    assert by_lookup.cosmic_weight.value is not None
    assert by_lookup.cosmic_weight.value > 0.0
    assert by_lookup.cosmic_weight.blocker is None


def test_missing_cosmic_weight_evidence_is_a_blocker():
    audit = audit_rfc_feature_provenance()

    assert audit.cosmic_weight.status == "missing_weight_evidence"
    assert audit.cosmic_weight.blocker == "missing_cosmic_weight_evidence"


def test_invalid_feature_column_contracts_fail_closed_without_type_errors():
    for bad_columns in ["total_energy", b"total_energy", 7, ("total_energy", 7)]:
        audit = audit_rfc_feature_provenance(feature_columns=bad_columns)

        assert len(audit.features) == 1
        feature = audit.features[0]
        assert feature.name == "<invalid_feature_columns>"
        assert feature.status == "invalid_feature_column_contract"
        assert feature.blocker == "invalid_feature_column_contract"
        assert "sequence of column-name strings" in feature.detail
