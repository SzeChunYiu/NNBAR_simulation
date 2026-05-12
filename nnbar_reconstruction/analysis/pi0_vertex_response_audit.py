"""Fail-closed π⁰ vertex-radius response audit helpers.

The parametric π⁰ study scans truth vertex radius at fixed 150 MeV and asks
for response curves versus ``truth_vertex_r_cm``.  This module inspects already
reconstructed ``pi0_reco_{E}mev.parquet`` files only; it never submits SLURM,
regenerates samples, or promotes new production constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

import pandas as pd

STUDY1_ENERGIES_MEV = (150,)
STUDY1_RADII_CM = (0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0)
_RADIUS_COLUMN = "truth_vertex_r_cm"
_RECO_FLAG_COLUMN = "reco_eff_flag"
_N_PI0_COLUMN = "n_pi0_candidates"
_MASS_COLUMN = "pi0_mass_mev"
_OPENING_ANGLE_COLUMN = "opening_angle_deg"
_RECO_TOTAL_ENERGY_COLUMN = "reco_total_energy_mev"
_TRUTH_TOTAL_ENERGY_COLUMN = "truth_total_energy_mev"
_RADIUS_KEY_DIGITS = 6


@dataclass(frozen=True)
class Pi0VertexBlocker:
    """Machine-readable blocker for the vertex-radius π⁰ response audit.

    Args:
        code: Stable blocker identifier used by tests and plan rows.
        energy_mev: Mono-energetic π⁰ sample energy under audit.
        reason: Human-readable fail-closed explanation.
    """

    code: str
    energy_mev: int
    reason: str


@dataclass(frozen=True)
class RadiusResponseBin:
    """Response summary for one truth vertex-radius bin.

    Args:
        radius_cm: Truth vertex radius in centimeters.
        n_events: Events in this radius bin.
        n_reconstructed: Events with a reconstructed π⁰ candidate.
        efficiency: ``n_reconstructed / n_events``.
        mass_peak_mev: Median reconstructed invariant mass for reconstructed
            candidates, if available.
        mass_sigma_mev: Sample standard deviation of reconstructed mass.
        opening_angle_mean_deg: Mean reconstructed opening angle.
        energy_bias_fraction: Mean ``(E_reco - E_truth) / E_truth``.
    """

    radius_cm: float
    n_events: int
    n_reconstructed: int
    efficiency: float
    mass_peak_mev: float | None
    mass_sigma_mev: float | None
    opening_angle_mean_deg: float | None
    energy_bias_fraction: float | None


@dataclass(frozen=True)
class VertexResponseAudit:
    """Audit result for one reconstructed mono-π⁰ vertex-radius sample.

    Args:
        energy_mev: Mono-energetic π⁰ sample energy.
        parquet_path: Reconstructed Parquet inspected, if present.
        ready: True only when no fail-closed blockers fired.
        total_events: Number of rows loaded from the Parquet file.
        radius_bins: Per-radius response summaries.
        blockers: Structured blockers for missing samples/schema/radius bins.
    """

    energy_mev: int
    parquet_path: Path | None
    ready: bool
    total_events: int
    radius_bins: tuple[RadiusResponseBin, ...]
    blockers: tuple[Pi0VertexBlocker, ...]

    def summary_records(self) -> tuple[dict[str, float | int | None], ...]:
        """Return a table-like radius summary suitable for JSON/CSV writers."""
        return tuple(
            {
                "truth_vertex_r_cm": radius_bin.radius_cm,
                "n_events": radius_bin.n_events,
                "n_reconstructed": radius_bin.n_reconstructed,
                "efficiency": radius_bin.efficiency,
                "mass_peak_mev": radius_bin.mass_peak_mev,
                "mass_sigma_mev": radius_bin.mass_sigma_mev,
                "opening_angle_mean_deg": radius_bin.opening_angle_mean_deg,
                "energy_bias_fraction": radius_bin.energy_bias_fraction,
            }
            for radius_bin in self.radius_bins
        )


def discover_pi0_reco_sample(energy_mev: int, search_root: str | Path) -> Path | None:
    """Locate an existing ``pi0_reco_{E}mev.parquet`` file without side effects.

    Args:
        energy_mev: Required reconstructed π⁰ energy tag, e.g. ``150``.
        search_root: Directory to search for already staged ``*.parquet`` files.

    Returns:
        The deterministic best matching reconstructed sample path, preferring
        ``pi0_reco_response/pi0_reco_{E}mev.parquet`` over other reco-tagged
        files. Raw ``Particle_output`` samples are intentionally ignored because
        this audit requires reconstructed response columns.
    """
    root = Path(search_root)
    if not root.exists():
        return None

    candidates = [
        path
        for path in root.rglob("*.parquet")
        if not path.name.startswith("._") and _path_mentions_pi0_reco_energy(path, energy_mev)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: (_candidate_rank(path, energy_mev), str(path)))[0]


def run_vertex_response_audit(
    search_root: str | Path,
    energies_mev: Iterable[int] = STUDY1_ENERGIES_MEV,
    expected_radii_cm: Iterable[float] = STUDY1_RADII_CM,
) -> list[VertexResponseAudit]:
    """Audit every requested reconstructed mono-π⁰ vertex-response sample.

    Missing samples become blockers instead of exceptions, preserving the lane
    rule that this audit must not launch simulations or generate data.
    """
    reports: list[VertexResponseAudit] = []
    for energy_mev in energies_mev:
        sample = discover_pi0_reco_sample(int(energy_mev), search_root)
        if sample is None:
            reports.append(_missing_sample_result(int(energy_mev)))
        else:
            reports.append(audit_pi0_vertex_response(sample, int(energy_mev), tuple(expected_radii_cm)))
    return reports


def audit_pi0_vertex_response(
    parquet_path: str | Path,
    energy_mev: int,
    expected_radii_cm: Iterable[float] = STUDY1_RADII_CM,
) -> VertexResponseAudit:
    """Summarize reconstructed π⁰ response versus truth vertex radius.

    Args:
        parquet_path: Existing ``pi0_reco_{E}mev.parquet`` file.
        energy_mev: Mono-energetic π⁰ energy represented by the file.
        expected_radii_cm: Radius bins required by the scan spec.  Missing bins
            produce blockers but already present bins are still summarized.
    """
    path = Path(parquet_path)
    if not path.exists():
        return _missing_sample_result(energy_mev)

    try:
        frame = pd.read_parquet(path)
    except Exception as exc:  # pragma: no cover - engine-specific exception text
        return VertexResponseAudit(
            energy_mev,
            path,
            False,
            0,
            (),
            (Pi0VertexBlocker("pi0_vertex_sample_unreadable", energy_mev, f"Could not read {path}: {exc}"),),
        )

    blockers: list[Pi0VertexBlocker] = []
    _check_required_columns(frame, energy_mev, blockers)
    if _has_blocker(blockers, "truth_vertex_r_missing") or _has_blocker(blockers, "reco_efficiency_flag_missing"):
        return VertexResponseAudit(energy_mev, path, False, len(frame), (), tuple(blockers))

    radii = pd.to_numeric(frame[_RADIUS_COLUMN], errors="coerce")
    reco_mask = _reco_mask(frame)
    assert reco_mask is not None  # for type checkers; guarded above
    work = frame.assign(__radius_key=radii.map(_radius_key), __reco=reco_mask).dropna(subset=["__radius_key"])

    radius_bins = tuple(_summarize_radius_group(float(radius), group, energy_mev, blockers) for radius, group in work.groupby("__radius_key", sort=True))
    _check_expected_radii(radius_bins, expected_radii_cm, energy_mev, blockers)

    return VertexResponseAudit(
        energy_mev=energy_mev,
        parquet_path=path,
        ready=not blockers,
        total_events=len(frame),
        radius_bins=radius_bins,
        blockers=tuple(blockers),
    )


def _missing_sample_result(energy_mev: int) -> VertexResponseAudit:
    blocker = Pi0VertexBlocker(
        code=f"pi0_vertex_{energy_mev}mev_sample_missing",
        energy_mev=energy_mev,
        reason=(
            f"No existing reconstructed pi0_reco_{energy_mev}mev.parquet sample was found; "
            "per lane spec this audit must not regenerate samples or submit SLURM."
        ),
    )
    return VertexResponseAudit(energy_mev, None, False, 0, (), (blocker,))


def _check_required_columns(frame: pd.DataFrame, energy_mev: int, blockers: list[Pi0VertexBlocker]) -> None:
    if _RADIUS_COLUMN not in frame.columns:
        blockers.append(_blocker("truth_vertex_r_missing", energy_mev, f"Missing required `{_RADIUS_COLUMN}` grouping column."))
    if _reco_mask(frame) is None:
        blockers.append(
            _blocker(
                "reco_efficiency_flag_missing",
                energy_mev,
                f"Missing `{_RECO_FLAG_COLUMN}` or `{_N_PI0_COLUMN}` column needed for efficiency.",
            )
        )
    for column, code in (
        (_MASS_COLUMN, "mass_column_missing"),
        (_OPENING_ANGLE_COLUMN, "opening_angle_column_missing"),
        (_RECO_TOTAL_ENERGY_COLUMN, "reco_total_energy_missing"),
        (_TRUTH_TOTAL_ENERGY_COLUMN, "truth_total_energy_missing"),
    ):
        if column not in frame.columns:
            blockers.append(_blocker(code, energy_mev, f"Missing `{column}` from Study 1 output schema."))


def _summarize_radius_group(
    radius_cm: float,
    group: pd.DataFrame,
    energy_mev: int,
    blockers: list[Pi0VertexBlocker],
) -> RadiusResponseBin:
    reconstructed = group["__reco"].astype(bool)
    n_events = int(len(group))
    n_reconstructed = int(reconstructed.sum())
    reco_group = group.loc[reconstructed]
    mass_peak, mass_sigma = _mass_summary(radius_cm, reco_group, energy_mev, blockers)
    return RadiusResponseBin(
        radius_cm=radius_cm,
        n_events=n_events,
        n_reconstructed=n_reconstructed,
        efficiency=(n_reconstructed / n_events) if n_events else 0.0,
        mass_peak_mev=mass_peak,
        mass_sigma_mev=mass_sigma,
        opening_angle_mean_deg=_mean_column(reco_group, _OPENING_ANGLE_COLUMN),
        energy_bias_fraction=_energy_bias(reco_group),
    )


def _mass_summary(
    radius_cm: float,
    reco_group: pd.DataFrame,
    energy_mev: int,
    blockers: list[Pi0VertexBlocker],
) -> tuple[float | None, float | None]:
    if _MASS_COLUMN not in reco_group.columns or reco_group.empty:
        return None, None
    masses = pd.to_numeric(reco_group[_MASS_COLUMN], errors="coerce").dropna()
    if masses.empty:
        blockers.append(
            _blocker("mass_bin_empty", energy_mev, f"Radius {radius_cm:g} cm has reconstructed candidates but no finite mass.")
        )
        return None, None
    sigma = float(masses.std(ddof=1)) if len(masses) > 1 else 0.0
    return float(masses.median()), sigma


def _mean_column(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns or frame.empty:
        return None
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.mean())


def _energy_bias(frame: pd.DataFrame) -> float | None:
    if frame.empty or _RECO_TOTAL_ENERGY_COLUMN not in frame.columns or _TRUTH_TOTAL_ENERGY_COLUMN not in frame.columns:
        return None
    paired = pd.concat(
        [
            pd.to_numeric(frame[_RECO_TOTAL_ENERGY_COLUMN], errors="coerce").rename("reco"),
            pd.to_numeric(frame[_TRUTH_TOTAL_ENERGY_COLUMN], errors="coerce").rename("truth"),
        ],
        axis=1,
    ).dropna()
    paired = paired[paired["truth"] != 0.0]
    if paired.empty:
        return None
    return float(((paired["reco"] - paired["truth"]) / paired["truth"]).mean())


def _check_expected_radii(
    radius_bins: tuple[RadiusResponseBin, ...],
    expected_radii_cm: Iterable[float],
    energy_mev: int,
    blockers: list[Pi0VertexBlocker],
) -> None:
    observed = {_radius_key(radius_bin.radius_cm) for radius_bin in radius_bins}
    missing = [float(radius) for radius in expected_radii_cm if _radius_key(float(radius)) not in observed]
    if missing:
        blockers.append(
            _blocker(
                "radius_bin_missing",
                energy_mev,
                f"Missing required Study 1 truth_vertex_r_cm bins: {', '.join(f'{radius:g}' for radius in missing)} cm.",
            )
        )


def _reco_mask(frame: pd.DataFrame) -> pd.Series | None:
    if _RECO_FLAG_COLUMN in frame.columns:
        values = frame[_RECO_FLAG_COLUMN]
        if values.dtype == bool:
            return values.fillna(False)
        return pd.to_numeric(values, errors="coerce").fillna(0).astype(float) > 0.0
    if _N_PI0_COLUMN in frame.columns:
        return pd.to_numeric(frame[_N_PI0_COLUMN], errors="coerce").fillna(0).astype(float) > 0.0
    return None


def _path_mentions_pi0_reco_energy(path: Path, energy_mev: int) -> bool:
    text = path.as_posix().lower().replace("π", "pi")
    if "pi0" not in text or "reco" not in text:
        return False
    return re.search(rf"(?<!\d){energy_mev}(?:\.0+)?\s*[_-]?\s*mev(?!\d)|pi0_reco_{energy_mev}(?!\d)", text) is not None


def _candidate_rank(path: Path, energy_mev: int) -> int:
    name = path.name.lower()
    parent = path.parent.as_posix().lower()
    if name == f"pi0_reco_{energy_mev}mev.parquet" and "pi0_reco_response" in parent:
        return 0
    if name == f"pi0_reco_{energy_mev}mev.parquet":
        return 1
    if "pi0_reco_response" in parent:
        return 2
    return 3


def _radius_key(radius_cm: float) -> float:
    return round(float(radius_cm), _RADIUS_KEY_DIGITS)


def _has_blocker(blockers: Iterable[Pi0VertexBlocker], code: str) -> bool:
    return any(blocker.code == code for blocker in blockers)


def _blocker(code: str, energy_mev: int, reason: str) -> Pi0VertexBlocker:
    return Pi0VertexBlocker(code=code, energy_mev=energy_mev, reason=reason)
