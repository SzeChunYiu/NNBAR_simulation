"""Fail-closed Ch. 6 annihilation-signal kinematics audit helpers.

The thesis-level signal validation requires the 50k-event annihilation sample
and source-backed evidence for foil vertex radial distribution, photon/pion/
proton kinetic-energy peaks, and opening-angle distributions.  This module
only inspects caller-supplied evidence or small parquet metadata; it never runs
simulations, submits jobs, shells out, or fits new peak values.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from nnbar_reconstruction.data_pipeline.load_simulation_data import load_dataset

THESIS_SIGNAL_EVENT_COUNT = 50_000
CURRENT_SIGNAL_SAMPLE_PATH = Path("output/sig_foil_v3/Particle_output_0.parquet")
REQUIRED_EVIDENCE_KEYS = (
    "sample_path",
    "n_events",
    "foil_radial_distribution",
    "photon_ke_peak",
    "pion_plus_ke_peak",
    "pion_minus_ke_peak",
    "proton_ke_peak",
    "opening_angle_distribution",
)
KINETIC_ENERGY_PEAK_KEYS = (
    "photon_ke_peak",
    "pion_plus_ke_peak",
    "pion_minus_ke_peak",
    "proton_ke_peak",
)
DEFAULT_CH6_REFERENCES = {
    key: f"Ch. 6 annihilation-signal kinematics evidence: {key}"
    for key in REQUIRED_EVIDENCE_KEYS
}


@dataclass(frozen=True)
class SignalKinematicsBlocker:
    """One machine-readable blocker for signal-sample kinematics closure.

    Args:
        code: Stable blocker code used by tests and plan rows.
        evidence_key: Required evidence key responsible for the blocker.
        thesis_reference: Ch. 6 source string expected to justify the evidence.
        message: Human-readable fail-closed explanation.
    """

    code: str
    evidence_key: str
    thesis_reference: str
    message: str


@dataclass(frozen=True)
class EvidenceKeyStatus:
    """Presence and verification status for one required evidence key.

    Args:
        key: Evidence key from ``REQUIRED_EVIDENCE_KEYS``.
        present: Whether the caller supplied the evidence and any referenced
            file exists where applicable.
        verified: Whether the evidence is source-backed and satisfies the Ch. 6
            thesis-validation requirement.
        thesis_reference: Ch. 6 source binding for this evidence item.
        source: Compact provenance or artifact description.
    """

    key: str
    present: bool
    verified: bool
    thesis_reference: str
    source: str


@dataclass(frozen=True)
class SignalKinematicsAudit:
    """Complete signal-sample kinematics audit result.

    Args:
        ready: True only when every required evidence key is verified and the
            sample has at least ``THESIS_SIGNAL_EVENT_COUNT`` events.
        n_events: Verified or inspected event count, if available.
        required_events: Thesis-level event-count requirement.
        sample_path: Supplied sample path, if any.
        evidence_status: Per-key status records.
        blockers: Explicit fail-closed blockers.
    """

    ready: bool
    n_events: int | None
    required_events: int
    sample_path: Path | None
    evidence_status: dict[str, EvidenceKeyStatus]
    blockers: tuple[SignalKinematicsBlocker, ...]


def audit_signal_kinematics(
    evidence: Mapping[str, Any] | None = None,
    *,
    root: str | Path = ".",
    required_events: int = THESIS_SIGNAL_EVENT_COUNT,
) -> SignalKinematicsAudit:
    """Audit one annihilation-signal sample evidence package.

    Args:
        evidence: Mapping with required keys such as ``sample_path``,
            ``n_events``, kinematic-evidence rows, and a ``thesis_reference``
            mapping. Kinematic rows are verified only when they carry
            ``verified: True`` or are explicitly ``True``.
        root: Root used to resolve relative sample paths.
        required_events: Minimum event count for thesis-level validation.

    Returns:
        Fail-closed audit result. Missing samples, sub-50k statistics, missing
        KE peaks, and missing vertex/opening-angle evidence are blockers rather
        than silent passes.
    """

    raw = dict(evidence or {})
    root_path = Path(root)
    sample_path = _sample_path(raw.get("sample_path"), root_path)
    sample_exists = sample_path is not None and sample_path.exists()
    n_events = _event_count(raw.get("n_events"), sample_path if sample_exists else None)
    references = _reference_mapping(raw.get("thesis_reference"))

    statuses = {
        "sample_path": EvidenceKeyStatus(
            key="sample_path",
            present=sample_exists,
            verified=sample_exists,
            thesis_reference=_reference_for("sample_path", raw, references),
            source=str(sample_path) if sample_path is not None else "missing",
        ),
        "n_events": EvidenceKeyStatus(
            key="n_events",
            present=n_events is not None,
            verified=n_events is not None and n_events >= required_events,
            thesis_reference=_reference_for("n_events", raw, references),
            source="missing" if n_events is None else str(n_events),
        ),
    }

    for key in REQUIRED_EVIDENCE_KEYS:
        if key in statuses:
            continue
        value = raw.get(key)
        present = value is not None
        verified = _verified(value)
        statuses[key] = EvidenceKeyStatus(
            key=key,
            present=present,
            verified=verified,
            thesis_reference=_reference_for(key, raw, references),
            source=_source(value),
        )

    blockers = _blockers(statuses, n_events, required_events)
    return SignalKinematicsAudit(
        ready=not blockers,
        n_events=n_events,
        required_events=required_events,
        sample_path=sample_path,
        evidence_status=statuses,
        blockers=tuple(blockers),
    )


def audit_current_signal_kinematics(root: str | Path = ".") -> SignalKinematicsAudit:
    """Audit the current checkout for local thesis-level signal evidence.

    Args:
        root: Repository root used to resolve the expected local signal sample.

    Returns:
        Fail-closed current-checkout audit. The expected 50k ``sig_foil_v3``
        sample is not staged locally, so this should remain blocked until the
        simulation team supplies a provenance-pinned sample and Ch. 6 evidence.
    """

    return audit_signal_kinematics(
        {
            "sample_path": CURRENT_SIGNAL_SAMPLE_PATH,
            "thesis_reference": DEFAULT_CH6_REFERENCES,
        },
        root=root,
    )


def _blockers(
    statuses: Mapping[str, EvidenceKeyStatus],
    n_events: int | None,
    required_events: int,
) -> list[SignalKinematicsBlocker]:
    """Build deterministic fail-closed blockers from evidence statuses."""

    blockers: list[SignalKinematicsBlocker] = []
    if not statuses["sample_path"].verified:
        blockers.append(
            _blocker(
                "sample_missing",
                "sample_path",
                statuses,
                "No local, existing annihilation-signal sample path was supplied.",
            )
        )

    if n_events is None or n_events < required_events:
        blockers.append(
            _blocker(
                "under_statistics",
                "n_events",
                statuses,
                f"Verified events {n_events or 0} are below the Ch. 6 50k requirement.",
            )
        )

    if any(not statuses[key].verified for key in KINETIC_ENERGY_PEAK_KEYS):
        blockers.append(
            _blocker(
                "KE_peak_not_verified",
                "photon_ke_peak",
                statuses,
                "Photon, pion, and proton KE peaks must be source-backed by Ch. 6 evidence.",
            )
        )

    if not statuses["foil_radial_distribution"].verified:
        blockers.append(
            _blocker(
                "vertex_distribution_unverified",
                "foil_radial_distribution",
                statuses,
                "Foil vertex radial distribution evidence is absent or unverified.",
            )
        )

    if not statuses["opening_angle_distribution"].verified:
        blockers.append(
            _blocker(
                "opening_angle_distribution_unverified",
                "opening_angle_distribution",
                statuses,
                "Opening-angle bias/distribution evidence is absent or unverified.",
            )
        )

    for key, status in statuses.items():
        if not status.thesis_reference:
            blockers.append(
                SignalKinematicsBlocker(
                    code=f"missing_thesis_reference:{key}",
                    evidence_key=key,
                    thesis_reference="",
                    message=f"Required evidence key {key} lacks a Ch. 6 thesis reference.",
                )
            )

    return blockers


def _blocker(
    code: str,
    key: str,
    statuses: Mapping[str, EvidenceKeyStatus],
    message: str,
) -> SignalKinematicsBlocker:
    """Create one blocker bound to an evidence key's thesis reference."""

    return SignalKinematicsBlocker(
        code=code,
        evidence_key=key,
        thesis_reference=statuses[key].thesis_reference,
        message=message,
    )


def _sample_path(value: Any, root: Path) -> Path | None:
    """Resolve a caller-supplied sample path against ``root`` if relative."""

    if value in (None, ""):
        return None
    path = Path(value)
    return path if path.is_absolute() else root / path


def _event_count(value: Any, sample_path: Path | None) -> int | None:
    """Return explicit or parquet-inspected event count without fitting data."""

    if value not in (None, ""):
        return int(value)
    if sample_path is None:
        return None
    if sample_path.is_dir():
        dataset = load_dataset(sample_path)
        for frame in dataset.values():
            count = _event_count_from_frame(frame)
            if count is not None:
                return count
        return None
    if sample_path.suffix == ".parquet" and sample_path.is_file():
        return _event_count_from_frame(pd.read_parquet(sample_path))
    return None


def _event_count_from_frame(frame: pd.DataFrame) -> int | None:
    """Count distinct events in one parquet-like table."""

    if frame.empty:
        return 0
    for column in ("Event_ID", "event_id", "event"):
        if column in frame:
            return int(frame[column].nunique())
    return int(len(frame))


def _verified(value: Any) -> bool:
    """Return whether a raw evidence row explicitly verifies its claim."""

    if isinstance(value, Mapping):
        return bool(value.get("verified"))
    return value is True


def _source(value: Any) -> str:
    """Return compact source text for a raw evidence row."""

    if isinstance(value, Mapping):
        artifact = value.get("artifact") or value.get("source") or value.get("path")
        return "missing" if artifact in (None, "") else str(artifact)
    if value in (None, ""):
        return "missing"
    return str(value)


def _reference_mapping(value: Any) -> Mapping[str, str]:
    """Normalise top-level thesis-reference evidence."""

    if isinstance(value, Mapping):
        return {str(key): str(ref) for key, ref in value.items() if ref}
    if value:
        return {key: str(value) for key in REQUIRED_EVIDENCE_KEYS}
    return {}


def _reference_for(key: str, raw: Mapping[str, Any], references: Mapping[str, str]) -> str:
    """Return the Ch. 6 thesis reference for one evidence key."""

    value = raw.get(key)
    if isinstance(value, Mapping) and value.get("thesis_reference"):
        return str(value["thesis_reference"])
    return references.get(key, "")
