import numpy as np
import pandas as pd

from nnbar_reconstruction.reconstruction.event_preselection import (
    find_event_time,
    rolling_time_window_trigger,
)
from nnbar_reconstruction.utils import config as config_module


def setup_function():
    config_module._config_cache = None
    config_module._config_path = None


def teardown_function():
    config_module._config_cache = None
    config_module._config_path = None


def _empty_hits():
    return pd.DataFrame({"t": [], "eDep": []})


def test_one_tpc_track_with_many_hits_does_not_trigger():
    tpc_hits = pd.DataFrame(
        {
            "t": [100.0, 105.0, 110.0, 115.0],
            "track_id": [42, 42, 42, 42],
        }
    )

    result = rolling_time_window_trigger(tpc_hits, _empty_hits(), _empty_hits())

    assert result["triggered"] is False
    assert result["n_trigger_windows"] == 0


def test_two_distinct_tpc_tracks_in_same_window_trigger():
    tpc_hits = pd.DataFrame(
        {
            "t": [100.0, 105.0, 110.0, 115.0],
            "track_id": [10, 10, 11, 11],
        }
    )

    result = rolling_time_window_trigger(tpc_hits, _empty_hits(), _empty_hits())

    assert result["triggered"] is True
    assert result["n_trigger_windows"] > 0


def test_tpc_only_trigger_selects_window_containing_tracks():
    tpc_hits = pd.DataFrame(
        {
            "t": [100.0, 105.0, 110.0, 115.0],
            "track_id": [10, 10, 11, 11],
        }
    )

    result = rolling_time_window_trigger(tpc_hits, _empty_hits(), _empty_hits())

    assert result["triggered"] is True
    assert result["tpc_mask"].sum() == 4


def test_track_id_capitalization_is_supported():
    tpc_hits = pd.DataFrame(
        {
            "t": [100.0, 105.0, 110.0, 115.0],
            "Track_ID": [10, 10, 11, 11],
        }
    )

    result = rolling_time_window_trigger(tpc_hits, _empty_hits(), _empty_hits())

    assert result["triggered"] is True


def test_negative_tpc_track_ids_do_not_count_as_tracks():
    tpc_times = np.array([100.0, 105.0, 110.0, 115.0])
    track_ids = np.array([-1, -1, 42, 42])

    _, _, n_triggers = find_event_time(
        tpc_times,
        np.array([]),
        np.array([]),
        min_tpc_tracks=2,
        tpc_track_ids=track_ids,
    )

    assert n_triggers == 0


def test_calorimeter_threshold_triggers_with_fewer_than_two_tpc_tracks():
    tpc_hits = pd.DataFrame({"t": [100.0], "track_id": [42]})
    scint_hits = pd.DataFrame({"t": [100.0], "eDep": [100.0]})

    result = rolling_time_window_trigger(tpc_hits, scint_hits, _empty_hits())

    assert result["triggered"] is True
    assert result["total_energy"] == 100.0


def test_calorimeter_energy_below_threshold_does_not_trigger_alone():
    tpc_hits = pd.DataFrame({"t": [100.0], "track_id": [42]})
    scint_hits = pd.DataFrame({"t": [100.0], "eDep": [99.999]})

    result = rolling_time_window_trigger(tpc_hits, scint_hits, _empty_hits())

    assert result["triggered"] is False


def test_default_tpc_trigger_requires_more_than_one_legacy_hit():
    _, _, n_triggers = find_event_time(
        np.array([100.0]),
        np.array([]),
        np.array([]),
    )

    assert n_triggers == 0


def test_legacy_times_only_path_counts_hits_explicitly():
    _, _, n_triggers = find_event_time(
        np.array([100.0, 105.0]),
        np.array([]),
        np.array([]),
        min_tpc_tracks=2,
    )

    assert n_triggers > 0
