"""Random Forest Classifier wrapper for NNBAR event selection."""

from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve

from .feature_extraction import RFC_FEATURE_COLUMNS

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


class RFCClassifier:
    """Random Forest Classifier for signal-vs-cosmic event discrimination."""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42,
    ) -> None:
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
        )
        self.feature_names_: list[str] = list(RFC_FEATURE_COLUMNS)

    def fit(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        sample_weight: np.ndarray | None = None,
    ) -> "RFCClassifier":
        """Fit the random forest and return ``self`` for chaining."""
        X_prepared = self._prepare_fit_features(X)
        self.model.fit(X_prepared, np.asarray(y), sample_weight=sample_weight)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return the fitted model's signal probability P(signal)."""
        X_prepared = self._prepare_predict_features(X)
        probabilities = self.model.predict_proba(X_prepared)
        classes = list(self.model.classes_)
        if 1 in classes:
            return probabilities[:, classes.index(1)]
        return np.zeros(len(X_prepared), dtype=float)

    def save(self, path: Path) -> None:
        """Persist this classifier with joblib."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: Path) -> "RFCClassifier":
        """Load a classifier persisted by :meth:`save`."""
        loaded = joblib.load(Path(path))
        if not isinstance(loaded, cls):
            raise TypeError(f"Expected RFCClassifier in {path}, got {type(loaded)!r}")
        return loaded

    def feature_importance_plot(self, path: Path) -> None:
        """Save a PNG bar chart of feature importances."""
        self._require_fitted()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        importances = np.asarray(self.model.feature_importances_)
        order = np.argsort(importances)
        names = np.asarray(self.feature_names_)[order]

        fig, ax = plt.subplots(figsize=(8, max(4, 0.35 * len(names))))
        ax.barh(names, importances[order], color="#4477aa")
        ax.set_xlabel("Feature importance")
        ax.set_title("RFC feature importance")
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)

    def roc_curve_plot(
        self,
        X_test: pd.DataFrame,
        y_test: np.ndarray,
        path: Path,
        weights_test: np.ndarray | None = None,
    ) -> float:
        """Save a ROC curve PNG and return the weighted ROC AUC."""
        self._require_fitted()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        scores = self.predict_proba(X_test)
        fpr, tpr, _ = roc_curve(y_test, scores, sample_weight=weights_test)
        roc_auc = roc_auc_score(y_test, scores, sample_weight=weights_test)
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(fpr, tpr, label=f"AUC = {roc_auc:.3f}", color="#228833")
        ax.plot([0, 1], [0, 1], linestyle="--", color="#999999", label="Random")
        ax.set_xlabel("False positive rate")
        ax.set_ylabel("Signal efficiency")
        ax.set_title("RFC ROC curve")
        ax.legend(loc="lower right")
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return float(roc_auc)

    def _prepare_fit_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Validate and order training features."""
        frame = self._as_frame(X)
        self.feature_names_ = list(frame.columns)
        return frame.astype(float)

    def _prepare_predict_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Validate and order prediction features."""
        frame = self._as_frame(X)
        missing = [column for column in self.feature_names_ if column not in frame.columns]
        if missing:
            raise ValueError(f"Missing RFC feature columns: {missing}")
        return frame[self.feature_names_].astype(float)

    def _as_frame(self, X: pd.DataFrame) -> pd.DataFrame:
        """Convert inputs to a numeric DataFrame."""
        if isinstance(X, pd.DataFrame):
            return X.copy()
        return pd.DataFrame(X, columns=self.feature_names_)

    def _require_fitted(self) -> None:
        """Raise if the underlying sklearn model has not been fitted."""
        if not hasattr(self.model, "classes_"):
            raise RuntimeError("RFCClassifier must be fitted before plotting or predicting")
