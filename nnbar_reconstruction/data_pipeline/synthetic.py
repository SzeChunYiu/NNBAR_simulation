"""Synthetic reconstruction inputs for pipeline tests.

The helpers in this module intentionally mirror the minimal TPC parquet schema
used by the reconstruction pipeline so tests can run without a local signal
data copy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


TPC_COLUMNS = [
    "Event_ID",
    "x",
    "y",
    "z",
    "time",
    "edep",
    "particle_id",
    "track_id",
]


def make_empty_tpc_hits() -> pd.DataFrame:
    """Return an empty TPC hit table with the expected parquet dtypes."""
    return pd.DataFrame(
        {
            "Event_ID": pd.Series(dtype="int64"),
            "x": pd.Series(dtype="float64"),
            "y": pd.Series(dtype="float64"),
            "z": pd.Series(dtype="float64"),
            "time": pd.Series(dtype="float64"),
            "edep": pd.Series(dtype="float64"),
            "particle_id": pd.Series(dtype="int64"),
            "track_id": pd.Series(dtype="int64"),
        },
        columns=TPC_COLUMNS,
    )


def make_synthetic_tpc_hits(n_events: int, hits_per_event: int = 20) -> pd.DataFrame:
    """Generate random TPC hits for pipeline testing."""
    if n_events < 0:
        raise ValueError("n_events must be non-negative")
    if hits_per_event < 0:
        raise ValueError("hits_per_event must be non-negative")
    if n_events == 0 or hits_per_event == 0:
        return make_empty_tpc_hits()

    rng = np.random.default_rng(20260511)
    rows: list[pd.DataFrame] = []
    for event_id in range(n_events):
        parameter = np.linspace(-1.0, 1.0, hits_per_event)
        radius = 500.0 + 3.0 * event_id
        phase = 0.2 * event_id
        noise = rng.normal(0.0, 0.4, size=(hits_per_event, 3))

        x = radius + 25.0 * parameter + noise[:, 0]
        y = 30.0 * np.sin(parameter + phase) + noise[:, 1]
        z = 120.0 * parameter + 2.0 * event_id + noise[:, 2]
        rows.append(
            pd.DataFrame(
                {
                    "Event_ID": np.full(hits_per_event, event_id, dtype=np.int64),
                    "x": x.astype(np.float64),
                    "y": y.astype(np.float64),
                    "z": z.astype(np.float64),
                    "time": (50.0 + event_id + np.arange(hits_per_event) * 0.5).astype(
                        np.float64
                    ),
                    "edep": rng.uniform(0.05, 1.0, size=hits_per_event).astype(
                        np.float64
                    ),
                    "particle_id": np.full(hits_per_event, 2112, dtype=np.int64),
                    "track_id": np.full(hits_per_event, event_id, dtype=np.int64),
                },
                columns=TPC_COLUMNS,
            )
        )

    return pd.concat(rows, ignore_index=True)
