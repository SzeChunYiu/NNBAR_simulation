"""Train the NNBAR Random Forest Classifier."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve
from sklearn.model_selection import train_test_split

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nnbar_reconstruction.ml import RFCClassifier
from nnbar_reconstruction.ml.feature_extraction import (
    RFC_FEATURE_COLUMNS,
    extract_rfc_features,
)


def train_rfc(
    signal_dir: Path,
    cosmic_dir: Path,
    output_dir: Path,
    n_events: int = 10000,
) -> dict[str, float]:
    """Train the RFC and write model/diagnostic artifacts."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    X_signal, y_signal, w_signal = _load_sample(signal_dir, 1, n_events)
    X_cosmic, y_cosmic, w_cosmic = _load_sample(cosmic_dir, 0, n_events)
    X = pd.concat([X_signal, X_cosmic], ignore_index=True)
    y = np.concatenate([y_signal, y_cosmic])
    weights = np.concatenate([w_signal, w_cosmic])

    X_train, X_test, y_train, y_test, weights_train, weights_test = train_test_split(
        X,
        y,
        weights,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    classifier = RFCClassifier(n_estimators=100, max_depth=10, random_state=42)
    classifier.fit(X_train, y_train, sample_weight=weights_train)
    classifier.save(output_dir / "model.joblib")
    classifier.feature_importance_plot(output_dir / "feature_importance.png")
    auc_value = classifier.roc_curve_plot(
        X_test,
        y_test,
        output_dir / "roc_curve.png",
        weights_test=weights_test,
    )

    scores = classifier.predict_proba(X_test)
    signal_efficiency = _signal_efficiency_at_background_rejection(
        y_test,
        scores,
        background_rejection=0.5,
        weights=weights_test,
    )
    print(f"AUC: {auc_value:.6f}")
    print(
        "Signal efficiency at 50% background rejection: "
        f"{signal_efficiency:.6f}"
    )
    return {"auc": float(auc_value), "signal_efficiency_at_50_bkg_rejection": signal_efficiency}


def _load_sample(data_dir: Path, label: int, n_events: int) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Load one labelled sample, falling back to deterministic synthetic features."""
    features = extract_rfc_features(Path(data_dir), n_events=n_events)
    if features.empty:
        features = _make_synthetic_features(label, _synthetic_count(n_events))
    labels = np.full(len(features), label, dtype=np.int64)
    weights = np.ones(len(features), dtype=float)
    if label == 0:
        weights = _load_cosmic_weights(Path(data_dir), len(features))
    return features[RFC_FEATURE_COLUMNS], labels, weights


def _load_cosmic_weights(data_dir: Path, n_rows: int) -> np.ndarray:
    """Read optional cosmic event weights from parquet files."""
    if not Path(data_dir).is_dir():
        return np.ones(n_rows, dtype=float)
    weights: list[float] = []
    for path in sorted(Path(data_dir).glob("*.parquet")):
        frame = pd.read_parquet(path, columns=None)
        if "weight" not in frame:
            continue
        if "Event_ID" in frame:
            values = frame.groupby("Event_ID")["weight"].first().to_numpy(dtype=float)
        else:
            values = frame["weight"].to_numpy(dtype=float)
        weights.extend(values.tolist())
    if not weights:
        return np.ones(n_rows, dtype=float)
    padded = np.ones(n_rows, dtype=float)
    values = np.asarray(weights[:n_rows], dtype=float)
    padded[: len(values)] = values
    return padded


def _make_synthetic_features(label: int, n_events: int) -> pd.DataFrame:
    """Create deterministic fallback features when parquet inputs are unavailable."""
    rng = np.random.default_rng(20260511 + label)
    center = 1.0 if label == 1 else 0.0
    frame = pd.DataFrame(
        rng.normal(center, 0.3, size=(n_events, len(RFC_FEATURE_COLUMNS))),
        columns=RFC_FEATURE_COLUMNS,
    )
    non_negative = [
        "total_energy",
        "scintillator_energy",
        "leadglass_energy",
        "n_charged_tracks",
        "n_pi0",
        "invariant_mass",
        "n_hits_tpc",
        "leading_track_dedx",
    ]
    frame[non_negative] = frame[non_negative].abs()
    frame["sphericity"] = frame["sphericity"].clip(0.0, 1.0)
    frame["energy_asymmetry"] = frame["energy_asymmetry"].clip(-1.0, 1.0)
    return frame.astype(float)


def _synthetic_count(n_events: int) -> int:
    """Return fallback sample size while respecting positive --n-events values."""
    if n_events < 0:
        return 200
    return max(2, n_events)


def _signal_efficiency_at_background_rejection(
    y_true: np.ndarray,
    scores: np.ndarray,
    background_rejection: float,
    weights: np.ndarray | None = None,
) -> float:
    """Return max signal efficiency where background rejection target is met."""
    fpr, tpr, _ = roc_curve(y_true, scores, sample_weight=weights)
    allowed = fpr <= (1.0 - background_rejection)
    if not np.any(allowed):
        return 0.0
    return float(np.max(tpr[allowed]))


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signal-dir", type=Path, default=Path("data/signal_test"))
    parser.add_argument("--cosmic-dir", type=Path, default=Path("data/cosmic_test"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/rfc"))
    parser.add_argument("--n-events", type=int, default=10000)
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = _parse_args()
    train_rfc(
        signal_dir=args.signal_dir,
        cosmic_dir=args.cosmic_dir,
        output_dir=args.output_dir,
        n_events=args.n_events,
    )


if __name__ == "__main__":
    main()
