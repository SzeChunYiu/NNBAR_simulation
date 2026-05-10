from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from nnbar_reconstruction.ml import RFCClassifier
from nnbar_reconstruction.ml.feature_extraction import (
    RFC_FEATURE_COLUMNS,
    extract_rfc_features,
)


def _synthetic_features(n_signal: int = 100, n_background: int = 100) -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(42)
    signal = pd.DataFrame(
        rng.normal(loc=1.0, scale=0.25, size=(n_signal, len(RFC_FEATURE_COLUMNS))),
        columns=RFC_FEATURE_COLUMNS,
    )
    background = pd.DataFrame(
        rng.normal(loc=0.0, scale=0.25, size=(n_background, len(RFC_FEATURE_COLUMNS))),
        columns=RFC_FEATURE_COLUMNS,
    )
    X = pd.concat([signal, background], ignore_index=True)
    y = np.concatenate(
        [np.ones(n_signal, dtype=np.int64), np.zeros(n_background, dtype=np.int64)]
    )
    return X, y


def test_rfc_trains_on_synthetic_data():
    X, y = _synthetic_features()
    clf = RFCClassifier(n_estimators=50, max_depth=5, random_state=7)

    clf.fit(X, y)
    scores = clf.predict_proba(X)

    assert scores.shape == (len(X),)
    assert np.all((0.0 <= scores) & (scores <= 1.0))
    assert roc_auc_score(y, scores) > 0.5


def test_rfc_save_load(tmp_path):
    X, y = _synthetic_features(n_signal=50, n_background=50)
    model_path = tmp_path / "model.joblib"
    clf = RFCClassifier(n_estimators=20, max_depth=4, random_state=11).fit(X, y)

    predictions_before = clf.predict_proba(X)
    clf.save(model_path)
    loaded = RFCClassifier.load(model_path)

    assert model_path.is_file()
    np.testing.assert_allclose(predictions_before, loaded.predict_proba(X))


def test_rfc_feature_importance_plot(tmp_path):
    X, y = _synthetic_features(n_signal=50, n_background=50)
    plot_path = tmp_path / "feature_importance.png"
    clf = RFCClassifier(n_estimators=20, max_depth=4, random_state=13).fit(X, y)

    clf.feature_importance_plot(plot_path)

    assert plot_path.is_file()
    assert plot_path.stat().st_size > 0


def test_extract_rfc_features_fills_missing_columns(tmp_path):
    pd.DataFrame(
        {
            "Event_ID": [1, 1, 2],
            "edep": [10.0, 20.0, 30.0],
            "x": [1.0, 2.0, 3.0],
            "y": [1.0, -1.0, 2.0],
            "z": [0.0, 1.0, 2.0],
        }
    ).to_parquet(tmp_path / "TPC_output_0.parquet", index=False)

    features = extract_rfc_features(tmp_path, n_events=1)

    assert list(features.columns) == RFC_FEATURE_COLUMNS
    assert features.shape == (1, len(RFC_FEATURE_COLUMNS))
    assert features.loc[0, "total_energy"] == 30.0
    assert features.loc[0, "n_hits_tpc"] == 2.0
    assert features.loc[0, "leadglass_energy"] == 0.0
