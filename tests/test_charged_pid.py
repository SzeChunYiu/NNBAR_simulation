"""Regressions for thesis Ch.8 charged pion/proton t(n) PID."""

from __future__ import annotations

import pytest


def test_threshold_surface_is_digitized_electrons_per_cm_table():
    from nnbar_reconstruction.reconstruction.charged_pid import (
        CHARGED_PID_TN_THRESHOLDS_E_PER_CM,
        threshold_for_scintillator_range,
    )

    assert list(CHARGED_PID_TN_THRESHOLDS_E_PER_CM) == list(range(1, 11))
    assert all(value > 50.0 for value in CHARGED_PID_TN_THRESHOLDS_E_PER_CM.values())
    assert threshold_for_scintillator_range(1) == pytest.approx(159.9, abs=0.2)
    assert threshold_for_scintillator_range(8) == pytest.approx(61.7, abs=0.2)
    assert threshold_for_scintillator_range(10) == pytest.approx(63.2, abs=0.2)


def test_values_around_threshold_classify_pion_and_proton():
    from nnbar_reconstruction.reconstruction.charged_pid import (
        classify_pion_proton_e_per_cm,
        threshold_for_scintillator_range,
    )

    threshold = threshold_for_scintillator_range(4)

    below = classify_pion_proton_e_per_cm(threshold - 0.1, scint_range=4)
    above = classify_pion_proton_e_per_cm(threshold + 0.1, scint_range=4)

    assert below.particle_label == "pion"
    assert above.particle_label == "proton"
    assert above.threshold_e_per_cm == threshold


@pytest.mark.parametrize("bad_range", [0, 11, -1, 3.5, "4"])
def test_invalid_scintillator_range_is_explicitly_rejected(bad_range):
    from nnbar_reconstruction.reconstruction.charged_pid import (
        ChargedPIDRangeError,
        threshold_for_scintillator_range,
    )

    with pytest.raises(ChargedPIDRangeError):
        threshold_for_scintillator_range(bad_range)


def test_object_identification_wrapper_uses_electron_count_thresholds(monkeypatch):
    import nnbar_reconstruction.reconstruction.object_identification as object_id
    from nnbar_reconstruction.reconstruction.charged_pid import threshold_for_scintillator_range
    from nnbar_reconstruction.reconstruction.object_identification import (
        ParticleType,
        identify_pion_proton,
    )

    # The old path read generic MeV/cm YAML keys.  The electron-count path must
    # be locked to the Ch.8 t(n) e-/cm table instead.
    monkeypatch.setattr(
        object_id,
        "get_particle_id_params",
        lambda: {"dedx_threshold_a": 10_000.0, "dedx_threshold_b": 10_000.0},
    )

    threshold = threshold_for_scintillator_range(5)

    pion_type, _ = identify_pion_proton(threshold - 0.1, scint_range=5)
    proton_type, _ = identify_pion_proton(threshold + 0.1, scint_range=5)
    invalid_type, invalid_confidence = identify_pion_proton(threshold, scint_range=0)

    assert pion_type == ParticleType.PION_PLUS
    assert proton_type == ParticleType.PROTON
    assert invalid_type == ParticleType.UNKNOWN
    assert invalid_confidence == 0.0


def test_identify_particle_type_does_not_feed_electron_dedx_to_bethe_bloch(monkeypatch):
    import nnbar_reconstruction.reconstruction.object_identification as object_id
    from nnbar_reconstruction.reconstruction.charged_pid import threshold_for_scintillator_range
    from nnbar_reconstruction.reconstruction.object_identification import (
        ParticleType,
        identify_particle_type,
    )

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("e-/cm dE/dx must not be inverted as MeV/cm")

    monkeypatch.setattr(object_id, "momentum_from_dedx", fail_if_called)

    pid = identify_particle_type(
        dedx=threshold_for_scintillator_range(5) + 0.1,
        scint_range=5,
        total_energy=120.0,
        is_charged=True,
    )

    assert pid.particle_type == ParticleType.PROTON
    assert pid.momentum_estimate == 0.0
    assert pid.beta_gamma == 0.0


def test_legacy_mev_dedx_momentum_fallback_is_explicit(monkeypatch):
    import nnbar_reconstruction.reconstruction.object_identification as object_id
    from nnbar_reconstruction.reconstruction.object_identification import (
        identify_particle_type,
    )

    monkeypatch.setattr(object_id, "momentum_from_dedx", lambda dedx, mass: 321.0)

    pid = identify_particle_type(
        dedx=2.0,
        scint_range=5,
        total_energy=120.0,
        is_charged=True,
        dedx_units="MeV/cm",
    )

    assert pid.momentum_estimate == 321.0
    assert pid.beta_gamma > 0.0


def test_reconstruct_charged_object_does_not_invert_electron_dedx(monkeypatch):
    import numpy as np
    import pandas as pd

    import nnbar_reconstruction.reconstruction.object_identification as object_id
    from nnbar_reconstruction.reconstruction.charged_reconstruction import (
        reconstruct_charged_object,
    )
    from nnbar_reconstruction.tracking.track_fitting import Track

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("electron-count dE/dx has no MeV/cm momentum inversion")

    monkeypatch.setattr(object_id, "momentum_from_dedx", fail_if_called)

    track = Track(
        track_id=1,
        center=np.array([0.5, 0.0, 0.0]),
        direction=np.array([1.0, 0.0, 0.0]),
        head=np.array([0.0, 0.0, 0.0]),
        tail=np.array([1.0, 0.0, 0.0]),
        length=1.0,
        n_hits=2,
        rms_residual=0.0,
        linearity=1.0,
        hit_indices=np.array([0, 1]),
        total_electrons=120.0,
        total_energy_dep=0.2,
    )
    tpc_data = pd.DataFrame(
        {
            "x": [0.0, 1.0],
            "y": [0.0, 0.0],
            "z": [0.0, 0.0],
            "Layer_ID": [1, 1],
            "electrons": [60.0, 60.0],
            "eDep": [0.1, 0.1],
        }
    )

    obj = reconstruct_charged_object(
        track=track,
        vertex=np.zeros(3),
        tpc_data=tpc_data,
        scint_data=pd.DataFrame(columns=["x", "y", "z", "eDep", "Layer_ID"]),
        lg_data=pd.DataFrame(columns=["x", "y", "z", "eDep"]),
        object_id=7,
    )

    assert obj.momentum_magnitude == 0.0
