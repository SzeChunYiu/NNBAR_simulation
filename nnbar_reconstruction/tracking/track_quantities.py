"""Derived track quantities for TPC reconstruction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Tuple

import numpy as np
import pandas as pd

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .track_fitting import Track


_COORD_COLUMNS = ("x", "y", "z")


def compute_track_dedx(
    track: "Track",
    hits: pd.DataFrame,
    truncation: float = 0.6,
) -> Tuple[float, np.ndarray]:
    """
    Compute the lower-truncated TPC dE/dx observable for a track.

    Thesis convention (Chapter 7): for each valid TPC layer, divide the
    ionization-electron count by that layer's track path length, then average
    the lower ``truncation`` fraction.  Values are therefore in e-/cm whenever
    an ``electrons`` column is present.

    Legacy fallback: if no ``electrons`` column is available, use ``eDep`` over
    the same layer path length.  That fallback preserves the old MeV/cm
    behavior explicitly for old samples that do not store ionization counts.

    Args:
        track: Track object with hit indices into ``hits``.
        hits: DataFrame with TPC hit data.
        truncation: Fraction of lowest layer values to use (0.6 = lower 60%).

    Returns:
        Tuple of (truncated mean dE/dx, per-layer dE/dx array).  The per-layer
        array contains one value per valid TPC layer in ascending ``Layer_ID``
        order when layer ids are available.
    """
    track_hits = hits.iloc[track.hit_indices]
    use_electrons = "electrons" in track_hits.columns
    source_column = "electrons" if use_electrons else "eDep"

    if source_column not in track_hits.columns:
        return 0.0, np.array([])

    if "Layer_ID" not in track_hits.columns:
        if track.length <= 0:
            return 0.0, np.array([])
        total = _numeric_sum(track_hits[source_column])
        if total <= 0 and use_electrons:
            total = float(getattr(track, "total_electrons", 0.0))
        elif total <= 0:
            total = float(getattr(track, "total_energy_dep", 0.0))
        return total / track.length, np.array([])

    layer_dedx = []
    for _, layer_hits in track_hits.groupby("Layer_ID", sort=True):
        path_length = _layer_path_length_cm(layer_hits)
        if path_length <= 0:
            continue

        source_total = _numeric_sum(layer_hits[source_column])
        layer_dedx.append(source_total / path_length)

    if not layer_dedx:
        return 0.0, np.array([])

    layer_values = np.asarray(layer_dedx, dtype=float)
    n_keep = max(1, int(len(layer_values) * truncation))
    truncated_mean = float(np.mean(np.sort(layer_values)[:n_keep]))
    return truncated_mean, layer_values


def _numeric_sum(series: pd.Series) -> float:
    """Return a numeric sum with non-numeric values treated as absent."""
    return float(pd.to_numeric(series, errors="coerce").fillna(0.0).sum())


def _layer_path_length_cm(layer_hits: pd.DataFrame) -> float:
    """Estimate the path length through one TPC layer in centimeters."""
    if all(column in layer_hits.columns for column in _COORD_COLUMNS):
        points = layer_hits.loc[:, _COORD_COLUMNS].to_numpy(dtype=float)
        if len(points) >= 2:
            path_length = float(np.linalg.norm(points[-1] - points[0]))
            if np.isfinite(path_length) and path_length > 0:
                return path_length

    # Single-hit layers or missing coordinates keep the previous documented
    # approximation: one centimeter of path length through the layer.
    return 1.0


def compute_track_features(
    track: "Track",
    hits: pd.DataFrame,
) -> Dict[str, float]:
    """
    Compute features for ML-based track classification.

    These features are used for signal-vs-Compton classification and vertex
    prediction input.
    """
    track_hits = hits.iloc[track.hit_indices]
    points = track_hits[["x", "y", "z"]].values

    dx = points[:, 0].max() - points[:, 0].min()
    dy = points[:, 1].max() - points[:, 1].min()
    dz = points[:, 2].max() - points[:, 2].min()

    centered = points - track.center
    cov = np.cov(centered.T)
    eigenvalues = np.sort(np.linalg.eigvalsh(cov))[::-1]
    w1, w2, w3 = eigenvalues[0], eigenvalues[1], eigenvalues[2]
    w_sum = w1 + w2 + w3 + 1e-10

    elongation1 = (w1 - w2) / (w1 + 1e-10)
    elongation2 = (w2 - w3) / (w1 + 1e-10)
    sphericity = w3 / (w1 + 1e-10)
    dominant_mode = w1 / w_sum

    volume = (dx + 1) * (dy + 1) * (dz + 1)
    density = np.log(len(points) / volume + 1e-10)

    time_std = 0.0
    if "t" in track_hits:
        time_std = track_hits["t"].std()

    r_center = np.sqrt(track.center[0] ** 2 + track.center[1] ** 2)
    x_over_x0 = 0.01 / 0.0889
    beta_p = 300.0
    highland_theta0 = (
        (13.6 / beta_p)
        * np.sqrt(x_over_x0)
        * (1 + 0.038 * np.log(x_over_x0))
    )

    return {
        "dx": dx,
        "dy": dy,
        "dz": dz,
        "elongation1": elongation1,
        "elongation2": elongation2,
        "sphericity": sphericity,
        "dominant_mode": dominant_mode,
        "density": density,
        "time_std": time_std,
        "x_over_X0": x_over_x0,
        "highland_theta0": highland_theta0,
        "r_surface": r_center,
        "length": track.length,
        "rms_residual": track.rms_residual,
        "linearity": track.linearity,
        "n_hits": track.n_hits,
        "dir_x": track.direction[0],
        "dir_y": track.direction[1],
        "dir_z": track.direction[2],
    }


def tracks_to_dataframe(tracks: list["Track"]) -> pd.DataFrame:
    """Convert a list of tracks to a DataFrame."""
    if not tracks:
        return pd.DataFrame()
    return pd.DataFrame([track.to_dict() for track in tracks])
