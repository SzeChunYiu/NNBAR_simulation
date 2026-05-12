"""Fail-closed CRY cosmic-bin kinematics and rate audit helpers.

The CRY integration lane records the thesis Table 6.1 three-year cosmic counts
and Eq. 6.1 event weights.  This module inspects existing Particle parquet
outputs only; it never submits jobs, regenerates samples, or changes simulation
configuration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from nnbar_reconstruction.data_pipeline.cosmic_weights import N_IJ, PARTICLES, get_weight

ENERGY_BINS_GEV: tuple[tuple[float, float | None], ...] = (
    (0.0, 0.5),
    (0.5, 1.0),
    (1.0, 5.0),
    (5.0, 10.0),
    (10.0, 50.0),
    (50.0, None),
)
NONZERO_BINS: tuple[tuple[str, int], ...] = tuple(
    (particle, ebin)
    for ebin in range(len(ENERGY_BINS_GEV))
    for pidx, particle in enumerate(PARTICLES)
    if N_IJ.get((ebin, pidx), 0.0) > 0.0
)
MIN_EVENTS_FOR_SHAPE = 1000
ENERGY_SPECTRAL_INDEX = 0.0
KE_REDUCED_CHI2_MAX = 3.0
ZENITH_REDUCED_CHI2_MAX = 5.0
WEIGHT_RELATIVE_TOLERANCE = 1.0e-6


@dataclass(frozen=True)
class CryKinematicsAudit:
    """Structured fail-closed blocker fields for one CRY cosmic bin.

    Args:
        ch6_3yr_count_unverified: Rate or Eq. 6.1 weight blockers.
        zenith_distribution_unverified: Zenith-shape blockers.
        ke_distribution_unverified: Kinetic-energy-shape blockers.
        parquet_missing: Missing or unreadable parquet blockers.
        bin_underfilled: Statistics blockers for bins below 1000 events.
    """

    ch6_3yr_count_unverified: tuple[str, ...] = ()
    zenith_distribution_unverified: tuple[str, ...] = ()
    ke_distribution_unverified: tuple[str, ...] = ()
    parquet_missing: tuple[str, ...] = ()
    bin_underfilled: tuple[str, ...] = ()

    @property
    def codes(self) -> tuple[str, ...]:
        """Return stable blocker codes with at least one reason."""
        codes: list[str] = []
        for code in (
            "ch6_3yr_count_unverified",
            "zenith_distribution_unverified",
            "ke_distribution_unverified",
            "parquet_missing",
            "bin_underfilled",
        ):
            if getattr(self, code):
                codes.append(code)
        return tuple(codes)


@dataclass(frozen=True)
class AuditResult:
    """Audit result for one `(particle, energy_bin)` CRY parquet output.

    Args:
        particle: CRY particle label.
        ebin_idx: Thesis Table 6.1 energy-bin index.
        parquet_path: Particle parquet path inspected or expected.
        observed_events: Number of rows/events loaded from parquet, if any.
        expected_3yr_count: Thesis Table 6.1 three-year count, if citeable.
        expected_weight: Eq. 6.1 weight for this bin, if citeable.
        ke_reduced_chi2: Reduced chi-square for KE shape, if tested.
        zenith_reduced_chi2: Reduced chi-square for cos² zenith shape.
        blockers: Structured fail-closed blockers.
    """

    particle: str
    ebin_idx: int
    parquet_path: Path
    observed_events: int | None
    expected_3yr_count: float | None
    expected_weight: float | None
    ke_reduced_chi2: float | None
    zenith_reduced_chi2: float | None
    blockers: CryKinematicsAudit

    @property
    def ready(self) -> bool:
        """Return True only when no fail-closed blocker fired."""
        return not self.blockers.codes

    @property
    def blocker_codes(self) -> tuple[str, ...]:
        """Return stable blocker codes for this result."""
        return self.blockers.codes


def audit_bin(particle: str, ebin_idx: int, parquet_path: str | Path) -> AuditResult:
    """Audit one CRY cosmic-bin Particle parquet file.

    Args:
        particle: CRY particle label such as ``"mu-"`` or ``"gamma"``.
        ebin_idx: Energy-bin index from thesis Table 6.1.
        parquet_path: Existing ``Particle_output_*.parquet`` path.

    Returns:
        Fail-closed audit result. Missing/unreadable parquet, underfilled bins,
        KE-shape mismatches, zenith-shape mismatches, and unverified Eq. 6.1
        weights are blockers rather than exceptions.
    """
    path = Path(parquet_path)
    pidx = _particle_index(particle)
    expected_count = N_IJ.get((ebin_idx, pidx)) if pidx is not None else None
    expected_weight = get_weight(ebin_idx, pidx) if pidx is not None else None
    blockers = _empty_blockers()

    if pidx is None or expected_count is None or expected_count <= 0.0:
        blockers["ch6_3yr_count_unverified"].append(
            f"no nonzero Table 6.1 N_ij for particle={particle!r}, ebin={ebin_idx}"
        )

    if not path.exists():
        blockers["parquet_missing"].append(f"missing parquet: {path}")
        return _result(particle, ebin_idx, path, None, expected_count, expected_weight, None, None, blockers)

    try:
        frame = pd.read_parquet(path)
    except Exception as exc:  # pragma: no cover - exact engine exception varies
        blockers["parquet_missing"].append(f"unreadable parquet {path}: {exc}")
        return _result(particle, ebin_idx, path, None, expected_count, expected_weight, None, None, blockers)

    observed_events = int(len(frame))
    if observed_events < MIN_EVENTS_FOR_SHAPE:
        blockers["bin_underfilled"].append(
            f"{observed_events} events < {MIN_EVENTS_FOR_SHAPE} minimum for shape checks"
        )

    _check_weight(frame, expected_weight, blockers)
    ke_chi2 = _check_ke_distribution(frame, ebin_idx, blockers)
    zenith_chi2 = _check_zenith_distribution(frame, blockers)

    return _result(
        particle,
        ebin_idx,
        path,
        observed_events,
        expected_count,
        expected_weight,
        ke_chi2,
        zenith_chi2,
        blockers,
    )


def run_audit(output_dir: str | Path) -> list[AuditResult]:
    """Audit all 27 nonzero CRY cosmic bins under an output directory.

    Args:
        output_dir: Directory containing ``cosmic_<particle>_<bin>`` subdirs.

    Returns:
        One result per nonzero thesis Table 6.1 bin. Missing bins return
        ``parquet_missing`` blockers and do not stop the sweep.
    """
    root = Path(output_dir)
    return [audit_bin(particle, ebin, _parquet_path(root, particle, ebin)) for particle, ebin in NONZERO_BINS]


def _empty_blockers() -> dict[str, list[str]]:
    return {
        "ch6_3yr_count_unverified": [],
        "zenith_distribution_unverified": [],
        "ke_distribution_unverified": [],
        "parquet_missing": [],
        "bin_underfilled": [],
    }


def _result(
    particle: str,
    ebin_idx: int,
    parquet_path: Path,
    observed_events: int | None,
    expected_count: float | None,
    expected_weight: float | None,
    ke_chi2: float | None,
    zenith_chi2: float | None,
    blockers: dict[str, list[str]],
) -> AuditResult:
    return AuditResult(
        particle=particle,
        ebin_idx=ebin_idx,
        parquet_path=parquet_path,
        observed_events=observed_events,
        expected_3yr_count=expected_count,
        expected_weight=expected_weight,
        ke_reduced_chi2=ke_chi2,
        zenith_reduced_chi2=zenith_chi2,
        blockers=CryKinematicsAudit(**{key: tuple(value) for key, value in blockers.items()}),
    )


def _particle_index(particle: str) -> int | None:
    aliases = {"mu": 0, "mu-": 0, "mu+": 0}
    aliases.update({name: idx for idx, name in enumerate(PARTICLES)})
    return aliases.get(particle)


def _parquet_path(root: Path, particle: str, ebin: int) -> Path:
    candidates = (
        root / f"cosmic_{particle}_{ebin}",
        root / f"cosmic_{particle}_bin{ebin}",
        root / f"cosmic_{particle.replace("-", "minus")}_{ebin}",
    )
    for directory in candidates:
        exact = directory / "Particle_output_0.parquet"
        if exact.exists():
            return exact
        matches = sorted(directory.glob("Particle_output_*.parquet")) if directory.exists() else []
        if matches:
            return matches[0]
    return candidates[0] / "Particle_output_0.parquet"


def _check_weight(
    frame: pd.DataFrame,
    expected_weight: float | None,
    blockers: dict[str, list[str]],
) -> None:
    if expected_weight is None:
        return
    if "weight" not in frame:
        blockers["ch6_3yr_count_unverified"].append("missing Eq. 6.1 weight column")
        return
    weights = pd.to_numeric(frame["weight"], errors="coerce").dropna()
    if weights.empty:
        blockers["ch6_3yr_count_unverified"].append("weight column has no finite values")
        return
    observed = float(weights.median())
    scale = max(abs(expected_weight), 1.0)
    if abs(observed - expected_weight) / scale > WEIGHT_RELATIVE_TOLERANCE:
        blockers["ch6_3yr_count_unverified"].append(
            f"median weight {observed:.6g} != Eq. 6.1 expected {expected_weight:.6g}"
        )


def _check_ke_distribution(
    frame: pd.DataFrame,
    ebin_idx: int,
    blockers: dict[str, list[str]],
) -> float | None:
    if "KE" not in frame:
        blockers["ke_distribution_unverified"].append("missing KE column")
        return None
    values = pd.to_numeric(frame["KE"], errors="coerce").dropna()
    if values.empty:
        blockers["ke_distribution_unverified"].append("KE column has no finite values")
        return None

    lo_gev, hi_gev = ENERGY_BINS_GEV[ebin_idx]
    lo_mev = lo_gev * 1000.0
    hi_mev = hi_gev * 1000.0 if hi_gev is not None else float(values.max())
    if hi_mev <= lo_mev:
        blockers["ke_distribution_unverified"].append("open-ended KE bin has no finite span")
        return None

    in_range = values[(values >= lo_mev) & (values <= hi_mev)]
    out_fraction = 1.0 - len(in_range) / len(values)
    if out_fraction > 0.02:
        blockers["ke_distribution_unverified"].append(
            f"{out_fraction:.1%} of KE values outside bin {lo_mev:g}-{hi_mev:g} MeV"
        )
        return None

    chi2 = _reduced_chi2(in_range, _edges(lo_mev, hi_mev, 10), ENERGY_SPECTRAL_INDEX)
    if chi2 is None or chi2 > KE_REDUCED_CHI2_MAX:
        blockers["ke_distribution_unverified"].append(
            "KE histogram incompatible with configured E^0 sampling"
            if chi2 is None
            else f"KE reduced chi2 {chi2:.3g} > {KE_REDUCED_CHI2_MAX:g}"
        )
    return chi2


def _check_zenith_distribution(
    frame: pd.DataFrame,
    blockers: dict[str, list[str]],
) -> float | None:
    mu = _zenith_cosine_abs(frame)
    if mu is None or mu.empty:
        blockers["zenith_distribution_unverified"].append("missing angle or direction columns")
        return None
    mu = mu[(mu >= 0.0) & (mu <= 1.0)]
    if mu.empty:
        blockers["zenith_distribution_unverified"].append("zenith cosine has no values in [0, 1]")
        return None

    chi2 = _reduced_chi2(mu, _edges(0.0, 1.0, 5), spectral_index=-2.0)
    if chi2 is None or chi2 > ZENITH_REDUCED_CHI2_MAX:
        blockers["zenith_distribution_unverified"].append(
            "zenith histogram incompatible with cos^2(theta)"
            if chi2 is None
            else f"zenith reduced chi2 {chi2:.3g} > {ZENITH_REDUCED_CHI2_MAX:g}"
        )
    return chi2


def _zenith_cosine_abs(frame: pd.DataFrame) -> pd.Series | None:
    if "angle" in frame:
        angles = pd.to_numeric(frame["angle"], errors="coerce").dropna()
        return angles.map(lambda angle: abs(math.cos(float(angle))))
    if {"u", "v", "w"}.issubset(frame.columns):
        u = pd.to_numeric(frame["u"], errors="coerce")
        v = pd.to_numeric(frame["v"], errors="coerce")
        w = pd.to_numeric(frame["w"], errors="coerce")
        norm = (u * u + v * v + w * w).map(math.sqrt)
        return (w.abs() / norm).dropna()
    return None


def _edges(lo: float, hi: float, n_bins: int) -> list[float]:
    step = (hi - lo) / n_bins
    return [lo + step * i for i in range(n_bins + 1)]


def _reduced_chi2(values: Iterable[float], edges: list[float], spectral_index: float) -> float | None:
    observed = [0] * (len(edges) - 1)
    total = 0
    for value in values:
        x = float(value)
        if x < edges[0] or x > edges[-1]:
            continue
        idx = min(len(observed) - 1, max(0, int((x - edges[0]) / (edges[-1] - edges[0]) * len(observed))))
        observed[idx] += 1
        total += 1
    if total == 0:
        return None

    probs = _power_law_probabilities(edges, spectral_index)
    chi2 = 0.0
    dof = 0
    for obs, prob in zip(observed, probs, strict=True):
        exp = total * prob
        if exp <= 0.0:
            continue
        chi2 += (obs - exp) ** 2 / exp
        dof += 1
    return chi2 / max(dof - 1, 1)


def _power_law_probabilities(edges: list[float], spectral_index: float) -> list[float]:
    if spectral_index == -2.0:
        weights = [max(edges[i + 1], 0.0) ** 3 - max(edges[i], 0.0) ** 3 for i in range(len(edges) - 1)]
    elif abs(spectral_index - 1.0) < 1.0e-12:
        weights = [math.log(edges[i + 1] / max(edges[i], 1.0e-12)) for i in range(len(edges) - 1)]
    else:
        power = 1.0 - spectral_index
        weights = [edges[i + 1] ** power - edges[i] ** power for i in range(len(edges) - 1)]
    total = sum(weights)
    return [weight / total for weight in weights]
