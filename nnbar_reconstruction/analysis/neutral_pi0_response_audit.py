"""Fail-closed neutral-object and single-π⁰ response audit helpers.

Chapter 7 validates mono-energetic 50, 150, and 250 MeV π⁰ samples by
checking that reconstructed diphoton masses are centered near the true π⁰ mass
and by comparing photon-energy and opening-angle distributions.  This module
only inspects existing Parquet files; it never submits simulations, retunes
cuts, or writes production constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

import pandas as pd

PI0_SAMPLE_ENERGIES_MEV = (50, 150, 250)
THESIS_PI0_MASS_PEAK_MEV = 134.0
PI0_MASS_PEAK_TOLERANCE_MEV = 10.0
PI0_RESPONSE_REFERENCE = {
    "mass_peak": "Ch. 7: mono-energetic π⁰ invariant masses centered near 134 MeV",
    "opening_angle": "Ch. 8: truth-vs-reco photon opening-angle comparison",
    "photon_energy": "Ch. 8: truth-vs-reco photon-energy comparison",
    "sigma": "Ch. 7 Fig. pi0_mass_gun: empirical mass-resolution width per sample",
}

_MASS_COLUMNS = (
    "pi0_mass_mev",
    "reco_pi0_mass_mev",
    "invariant_mass_mev",
    "diphoton_mass_mev",
    "m_gg_mev",
)
_OPENING_ANGLE_COLUMNS = (
    "opening_angle_deg",
    "reco_opening_angle_deg",
    "photon_opening_angle_deg",
    "diphoton_opening_angle_deg",
)
_TRUTH_PHOTON_ENERGY_COLUMNS = (
    "truth_photon_energy_mev",
    "photon_energy_truth_mev",
    "true_photon_energy_mev",
)
_RECO_PHOTON_ENERGY_COLUMNS = (
    "reco_photon_energy_mev",
    "photon_energy_reco_mev",
    "reconstructed_photon_energy_mev",
)


@dataclass(frozen=True)
class Pi0ResponseBlocker:
    """Machine-readable blocker for a neutral-π⁰ response audit.

    Args:
        code: Stable blocker identifier used by tests and plan rows.
        energy_mev: Mono-energetic π⁰ sample energy for this blocker.
        reason: Human-readable fail-closed explanation with provenance context.
    """

    code: str
    energy_mev: int
    reason: str


@dataclass(frozen=True)
class AuditResult:
    """One neutral-π⁰ response audit result.

    Args:
        energy_mev: Required mono-energetic π⁰ sample energy.
        parquet_path: Existing Parquet sample inspected, if any.
        ready: True only when all required response checks are source-backed.
        n_events: Number of rows inspected from the Parquet file.
        mass_peak_mev: Median reconstructed diphoton mass, used as peak proxy.
        mass_sigma_mev: Sample standard deviation of reconstructed mass.
        opening_angle_mean_deg: Mean reconstructed photon opening angle.
        photon_energy_bias_mev: Mean ``reco - truth`` photon-energy bias.
        blockers: Structured fail-closed blockers.
    """

    energy_mev: int
    parquet_path: Path | None
    ready: bool
    n_events: int
    mass_peak_mev: float | None
    mass_sigma_mev: float | None
    opening_angle_mean_deg: float | None
    photon_energy_bias_mev: float | None
    blockers: tuple[Pi0ResponseBlocker, ...]


def discover_pi0_sample(energy_mev: int, search_root: str | Path) -> Path | None:
    """Locate an existing mono-energetic π⁰ Parquet sample without side effects.

    Args:
        energy_mev: Required kinetic energy tag, e.g. ``150``.
        search_root: Directory to search for existing ``*.parquet`` files.

    Returns:
        The first deterministic candidate whose path mentions both ``pi0`` and
        the requested energy in MeV, or ``None`` when no existing sample is
        staged locally.
    """

    root = Path(search_root)
    if not root.exists():
        return None

    candidates = [
        path
        for path in root.rglob("*.parquet")
        if not path.name.startswith("._") and _path_mentions_pi0_energy(path, energy_mev)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: ("particle_output" not in path.name.lower(), str(path)))[0]


def audit_pi0_response(parquet_path: str | Path, energy_mev: int) -> AuditResult:
    """Audit one existing mono-energetic π⁰ Parquet sample.

    Args:
        parquet_path: Existing Parquet file to inspect.
        energy_mev: Required 50, 150, or 250 MeV sample energy.

    Returns:
        Fail-closed audit result with mass peak/sigma, opening-angle summary,
        photon-energy truth-vs-reco bias, and blockers for missing or shifted
        evidence.
    """

    path = Path(parquet_path)
    if not path.exists():
        return _missing_sample_result(energy_mev)

    try:
        frame = pd.read_parquet(path)
    except Exception as exc:  # pragma: no cover - exercised only by corrupt files
        blocker = Pi0ResponseBlocker(
            code="pi0_sample_unreadable",
            energy_mev=energy_mev,
            reason=f"Could not read existing π⁰ Parquet sample {path}: {exc}",
        )
        return AuditResult(energy_mev, path, False, 0, None, None, None, None, (blocker,))

    blockers: list[Pi0ResponseBlocker] = []
    mass_peak, mass_sigma = _mass_summary(frame, energy_mev, blockers)
    opening_angle_mean = _opening_angle_summary(frame, energy_mev, blockers)
    photon_energy_bias = _photon_energy_bias(frame, energy_mev, blockers)

    return AuditResult(
        energy_mev=energy_mev,
        parquet_path=path,
        ready=not blockers,
        n_events=len(frame),
        mass_peak_mev=mass_peak,
        mass_sigma_mev=mass_sigma,
        opening_angle_mean_deg=opening_angle_mean,
        photon_energy_bias_mev=photon_energy_bias,
        blockers=tuple(blockers),
    )


def run_audit(search_root: str | Path) -> list[AuditResult]:
    """Run the fail-closed π⁰ response audit for 50, 150, and 250 MeV samples.

    Args:
        search_root: Directory containing already-generated mono-π⁰ Parquet
            outputs. Missing samples become blockers instead of exceptions.

    Returns:
        One ``AuditResult`` per required energy, in thesis order.
    """

    reports: list[AuditResult] = []
    for energy_mev in PI0_SAMPLE_ENERGIES_MEV:
        sample = discover_pi0_sample(energy_mev, search_root)
        if sample is None:
            reports.append(_missing_sample_result(energy_mev))
        else:
            reports.append(audit_pi0_response(sample, energy_mev))
    return reports


def _missing_sample_result(energy_mev: int) -> AuditResult:
    blocker = Pi0ResponseBlocker(
        code=f"pi0_{energy_mev}mev_sample_missing",
        energy_mev=energy_mev,
        reason=(
            f"No existing mono-energetic {energy_mev} MeV π⁰ Parquet sample was "
            "found; per lane spec this audit must not regenerate samples."
        ),
    )
    return AuditResult(energy_mev, None, False, 0, None, None, None, None, (blocker,))


def _path_mentions_pi0_energy(path: Path, energy_mev: int) -> bool:
    text = path.as_posix().lower().replace("π", "pi")
    if "pi0" not in text:
        return False
    pattern = rf"(?<!\d){energy_mev}(?:\.0+)?(?:\s*|[_-]*)mev(?!\d)|(?<!\d){energy_mev}(?!\d)"
    return re.search(pattern, text) is not None


def _mass_summary(
    frame: pd.DataFrame,
    energy_mev: int,
    blockers: list[Pi0ResponseBlocker],
) -> tuple[float | None, float | None]:
    mass = _numeric_column(frame, _MASS_COLUMNS)
    if mass is None or mass.empty:
        blockers.append(
            _blocker(
                "mass_peak_unverified",
                energy_mev,
                f"No numeric mass column among {_MASS_COLUMNS}; {PI0_RESPONSE_REFERENCE["mass_peak"]}.",
            )
        )
        return None, None

    peak = float(mass.median())
    sigma = float(mass.std(ddof=1)) if len(mass) > 1 else 0.0
    offset = abs(peak - THESIS_PI0_MASS_PEAK_MEV)
    if offset > PI0_MASS_PEAK_TOLERANCE_MEV:
        blockers.append(
            _blocker(
                "mass_peak_off_thesis",
                energy_mev,
                (
                    f"Mass peak offset {offset:.1f} MeV exceeds "
                    f"{PI0_MASS_PEAK_TOLERANCE_MEV:.1f} MeV tolerance: "
                    f"peak {peak:.1f} MeV vs Ch. 7 {THESIS_PI0_MASS_PEAK_MEV:.1f} MeV."
                ),
            )
        )
    return peak, sigma


def _opening_angle_summary(
    frame: pd.DataFrame,
    energy_mev: int,
    blockers: list[Pi0ResponseBlocker],
) -> float | None:
    opening_angle = _numeric_column(frame, _OPENING_ANGLE_COLUMNS)
    if opening_angle is None or opening_angle.empty:
        blockers.append(
            _blocker(
                "opening_angle_distribution_unverified",
                energy_mev,
                f"No numeric opening-angle column among {_OPENING_ANGLE_COLUMNS}; {PI0_RESPONSE_REFERENCE["opening_angle"]}.",
            )
        )
        return None
    return float(opening_angle.mean())


def _photon_energy_bias(
    frame: pd.DataFrame,
    energy_mev: int,
    blockers: list[Pi0ResponseBlocker],
) -> float | None:
    truth = _numeric_column(frame, _TRUTH_PHOTON_ENERGY_COLUMNS)
    reco = _numeric_column(frame, _RECO_PHOTON_ENERGY_COLUMNS)
    if truth is None or reco is None or truth.empty or reco.empty:
        blockers.append(
            _blocker(
                "photon_energy_bias_unverified",
                energy_mev,
                (
                    "Missing numeric truth/reco photon-energy columns; "
                    f"{PI0_RESPONSE_REFERENCE["photon_energy"]}."
                ),
            )
        )
        return None

    paired = pd.concat([truth.rename("truth"), reco.rename("reco")], axis=1).dropna()
    if paired.empty:
        blockers.append(
            _blocker(
                "photon_energy_bias_unverified",
                energy_mev,
                "Truth/reco photon-energy columns have no paired finite rows.",
            )
        )
        return None
    return float((paired["reco"] - paired["truth"]).mean())


def _numeric_column(frame: pd.DataFrame, names: Iterable[str]) -> pd.Series | None:
    for name in names:
        if name in frame.columns:
            return pd.to_numeric(frame[name], errors="coerce").dropna()
    return None


def _blocker(code: str, energy_mev: int, reason: str) -> Pi0ResponseBlocker:
    return Pi0ResponseBlocker(code=code, energy_mev=energy_mev, reason=reason)
