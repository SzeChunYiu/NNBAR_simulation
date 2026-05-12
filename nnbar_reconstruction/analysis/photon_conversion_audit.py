"""Fail-closed Ch. 5 photon-conversion fraction audit helpers.

The thesis reports 100 MeV mono-photon conversion fractions of 4.1% in
silicon, 23.1% in the beampipe, 5.0% in the TPC, 18.2% in scintillator,
and 49.6% in lead glass.  This module only inspects existing parquet
artifacts; it never launches simulations, submits SLURM jobs, or retunes
geometry constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd

THESIS_CH5_CONVERSION_FRACTIONS = {
    "silicon": 0.041,
    "beampipe": 0.231,
    "tpc": 0.050,
    "scintillator": 0.182,
    "leadglass": 0.496,
}
THESIS_CH5_CONVERSION_SOURCE = (
    "Ch. 5 100 MeV photon conversion map: silicon 4.1%, beampipe 23.1%, "
    "TPC 5.0%, scintillator 18.2%, lead glass 49.6%."
)
DEFAULT_ABSOLUTE_TOLERANCE = 0.01
_DIRECT_VOLUME_COLUMNS = (
    "first_interaction_subdetector",
    "first_interaction_volume",
    "conversion_subdetector",
    "conversion_volume",
    "subdetector",
    "detector",
    "volume",
    "volume_name",
    "Volume",
    "VolumeName",
)
_EVENT_COLUMNS = ("event_id", "Event_ID", "event", "eventID")
_ORDER_COLUMNS = ("step_id", "Step_ID", "step", "time", "Time")
_INTERACTION_VOLUME_COLUMNS = ("Current_Vol", "current_vol", "current_volume", "CurrentVolume")
_INTERACTION_PROCESS_COLUMNS = ("Proc", "proc", "process", "Process")
_INTERACTION_PARTICLE_COLUMNS = ("Name", "name", "particle", "Particle", "particle_name")
_INTERACTION_TIME_COLUMNS = ("t", "time", "Time")


@dataclass(frozen=True)
class PhotonConversionBlocker:
    """One machine-readable blocker for the photon-conversion audit.

    Args:
        code: Stable blocker code used in tests and plan rows.
        reason: Human-readable fail-closed explanation.
    """

    code: str
    reason: str


@dataclass(frozen=True)
class PhotonConversionAuditResult:
    """Complete photon-conversion audit result.

    Args:
        ready: True when a sample exists and all fractions are within tolerance.
        sample_path: Existing parquet artifact inspected by the audit, if any.
        total_photons: Number of first-interaction photon rows counted.
        fractions: Canonical detector-volume fractions observed in the sample.
        expected_fractions: Pinned Ch. 5 reference fractions.
        tolerance: Absolute fraction tolerance used for the comparison.
        blockers: Explicit fail-closed blockers.
    """

    ready: bool
    sample_path: Path | None
    total_photons: int
    fractions: dict[str, float]
    expected_fractions: dict[str, float]
    tolerance: float
    blockers: tuple[PhotonConversionBlocker, ...]


def discover_photon_sample(search_root: str | Path) -> Path | None:
    """Locate an existing 100 MeV mono-photon parquet artifact.

    Args:
        search_root: Directory to search recursively.

    Returns:
        The first deterministic parquet path whose path text identifies a
        photon sample and 100 MeV energy, or ``None`` when no such existing
        artifact is present.
    """

    root = Path(search_root)
    if not root.exists():
        return None

    candidates = sorted(
        path
        for path in root.rglob("*.parquet")
        if not path.name.startswith("._") and _looks_like_100mev_photon(path)
    )
    interaction_candidates = [
        path
        for path in candidates
        if path.name == "Interaction_output_0.parquet" and _looks_like_100mev_photon(path.parent)
    ]
    if interaction_candidates:
        return interaction_candidates[0]
    return candidates[0] if candidates else None


def audit_conversion_fractions(
    parquet_path: str | Path,
    *,
    tolerance: float = DEFAULT_ABSOLUTE_TOLERANCE,
) -> PhotonConversionAuditResult:
    """Audit one existing photon parquet against the Ch. 5 conversion map.

    Args:
        parquet_path: Existing parquet file with first-interaction detector
            labels or per-event interaction rows.
        tolerance: Absolute per-volume fraction tolerance.

    Returns:
        Fail-closed audit result with a single
        ``conversion_fractions_unverified`` blocker when the observed fractions
        cannot be computed or do not match the thesis reference.
    """

    sample_path = Path(parquet_path)
    frame = pd.read_parquet(sample_path)
    labels, column_error = _first_interaction_labels(frame)
    total = len(labels)
    fractions = _fractions(labels)
    blockers: list[PhotonConversionBlocker] = []

    if column_error is not None:
        blockers.append(PhotonConversionBlocker("conversion_fractions_unverified", column_error))
    elif total == 0:
        blockers.append(
            PhotonConversionBlocker(
                "conversion_fractions_unverified",
                "No first-interaction photon rows were available for the Ch. 5 conversion audit.",
            )
        )
    else:
        mismatches = _mismatches(fractions, THESIS_CH5_CONVERSION_FRACTIONS, tolerance)
        if mismatches:
            blockers.append(
                PhotonConversionBlocker(
                    "conversion_fractions_unverified",
                    _mismatch_reason(mismatches, total, tolerance),
                )
            )

    return PhotonConversionAuditResult(
        ready=not blockers,
        sample_path=sample_path,
        total_photons=total,
        fractions=fractions,
        expected_fractions=dict(THESIS_CH5_CONVERSION_FRACTIONS),
        tolerance=tolerance,
        blockers=tuple(blockers),
    )


def run_audit(search_root: str | Path) -> PhotonConversionAuditResult:
    """Run the current-checkout photon conversion audit without side effects.

    Args:
        search_root: Directory tree that may already contain a 100 MeV
            mono-photon parquet artifact.

    Returns:
        A fail-closed audit result. Missing samples produce a ``sample_missing``
        blocker instead of raising or launching new simulation work.
    """

    sample_path = discover_photon_sample(search_root)
    if sample_path is None:
        return PhotonConversionAuditResult(
            ready=False,
            sample_path=None,
            total_photons=0,
            fractions={volume: 0.0 for volume in THESIS_CH5_CONVERSION_FRACTIONS},
            expected_fractions=dict(THESIS_CH5_CONVERSION_FRACTIONS),
            tolerance=DEFAULT_ABSOLUTE_TOLERANCE,
            blockers=(
                PhotonConversionBlocker(
                    "sample_missing",
                    "No existing 100 MeV mono-photon parquet sample was found; not regenerating.",
                ),
            ),
        )
    return audit_conversion_fractions(sample_path)


def _looks_like_100mev_photon(path: Path) -> bool:
    """Return whether a path name looks like the desired photon sample."""

    text = str(path).lower().replace("_", "").replace("-", "")
    return "photon" in text and ("100mev" in text or "100gev" not in text and "100" in text)


def _first_interaction_labels(frame: pd.DataFrame) -> tuple[list[str], str | None]:
    """Extract one canonical first-interaction label per photon event."""

    volume_column = _first_present(frame.columns, _DIRECT_VOLUME_COLUMNS)
    if volume_column is None:
        return _interaction_conversion_labels(frame)

    reduced = frame
    event_column = _first_present(frame.columns, _EVENT_COLUMNS)
    if event_column is not None:
        order_column = _first_present(frame.columns, _ORDER_COLUMNS)
        if order_column is not None:
            reduced = frame.sort_values([event_column, order_column])
        reduced = reduced.drop_duplicates(subset=[event_column], keep="first")

    labels = [_canonical_volume(value) for value in reduced[volume_column].dropna()]
    return labels, None


def _interaction_conversion_labels(frame: pd.DataFrame) -> tuple[list[str], str | None]:
    """Extract conversion labels from Geant4 ``Interaction_output`` rows."""

    event_column = _first_present(frame.columns, _EVENT_COLUMNS)
    process_column = _first_present(frame.columns, _INTERACTION_PROCESS_COLUMNS)
    particle_column = _first_present(frame.columns, _INTERACTION_PARTICLE_COLUMNS)
    volume_column = _first_present(frame.columns, _INTERACTION_VOLUME_COLUMNS)
    time_column = _first_present(frame.columns, _INTERACTION_TIME_COLUMNS)
    required = {
        "event": event_column,
        "process": process_column,
        "particle": particle_column,
        "volume": volume_column,
        "time": time_column,
    }
    missing = [name for name, column in required.items() if column is None]
    if missing:
        return [], "No first-interaction subdetector/volume column was found in the photon parquet."

    conv_rows = frame[
        frame[process_column].astype(str).str.strip().str.casefold().eq("conv")
        & frame[particle_column].astype(str).str.strip().isin({"e+", "e-"})
    ]
    if conv_rows.empty:
        return [], None

    first_rows = (
        conv_rows.sort_values([event_column, time_column])
        .drop_duplicates(subset=[event_column], keep="first")
    )
    labels = [_canonical_volume(value) for value in first_rows[volume_column].dropna()]
    return labels, None


def _first_present(columns: Sequence[str], candidates: Sequence[str]) -> str | None:
    """Return the first candidate column name present in ``columns``."""

    available = set(columns)
    for candidate in candidates:
        if candidate in available:
            return candidate
    return None


def _canonical_volume(value: object) -> str:
    """Map a raw detector/volume label to a canonical thesis volume key."""

    text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    compact = text.replace("_", "")
    if "leadglass" in compact or compact in {"lg", "lead"}:
        return "leadglass"
    if "scint" in compact:
        return "scintillator"
    if "beampipe" in compact or "beampipe" in text or "beam_pipe" in text:
        return "beampipe"
    if compact in {"si", "silicon"} or "silicon" in compact:
        return "silicon"
    if "tpc" in compact or "timeprojectionchamber" in compact:
        return "tpc"
    return compact


def _fractions(labels: Sequence[str]) -> dict[str, float]:
    """Compute canonical detector fractions from labels."""

    total = len(labels)
    if total == 0:
        return {volume: 0.0 for volume in THESIS_CH5_CONVERSION_FRACTIONS}

    return {
        volume: round(sum(label == volume for label in labels) / total, 6)
        for volume in THESIS_CH5_CONVERSION_FRACTIONS
    }


def _mismatches(
    actual: Mapping[str, float],
    expected: Mapping[str, float],
    tolerance: float,
) -> dict[str, tuple[float, float, float]]:
    """Return per-volume mismatches as actual/expected/delta triples."""

    mismatched: dict[str, tuple[float, float, float]] = {}
    for volume, expected_fraction in expected.items():
        actual_fraction = actual.get(volume, 0.0)
        delta = actual_fraction - expected_fraction
        if abs(delta) > tolerance:
            mismatched[volume] = (actual_fraction, expected_fraction, delta)
    return mismatched


def _mismatch_reason(
    mismatches: Mapping[str, tuple[float, float, float]],
    total: int,
    tolerance: float,
) -> str:
    """Build a compact mismatch reason for the plan row and tests."""

    details = "; ".join(
        f"{volume}: actual={actual:.3f}, expected={expected:.3f}, delta={delta:+.3f}"
        for volume, (actual, expected, delta) in mismatches.items()
    )
    return (
        f"Ch. 5 photon conversion fractions differ for {details} "
        f"with n={total} photons and tolerance={tolerance:.3f}."
    )
