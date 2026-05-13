"""Fail-closed audit helpers for charged cone and deflection evidence.

The thesis Ch. 7 charged-object cone and beampipe multiple-scattering
statements are treated as evidence requirements, not as production retuning
permission.  Missing scan artifacts or provenance produce explicit blockers.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from pathlib import Path
import re
from typing import Mapping

from nnbar_reconstruction.utils.config import load_config

CANONICAL_CHARGED_CONE_ANGLE_DEG = 25.0
ALLOWED_CONE_SCAN_RANGE_DEG = (5.0, 85.0)
REQUIRED_CONE_SCAN_ANGLES_DEG = (5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 85.0)

CURRENT_REPO_CONE_SCAN_ARTIFACT = Path("output/ledger/LIC-CH07-NUM-15.csv")
CURRENT_REPO_BEAMPIPE_DEFLECTION_ARTIFACT = Path("output/ledger/LIC-CH07-FIG-10.csv")

_TOLERANCE_DEG = 1e-9
_CONE_SOURCE_PATTERN = re.compile(
    r"cone_angle\s*(?:=|:|,)\s*25(?:\.0+)?", re.IGNORECASE
)


@dataclass(frozen=True)
class EvidenceRequirement:
    """One required thesis-evidence artifact.

    Args:
        key: Field name on ``EvidencePackage``.
        blocker_code: Stable blocker identifier when the artifact is absent.
        sample: Required sample or sample family.
        observable: Observable the artifact must contain.
        figure_of_merit: Figure of merit required before promotion.
        thesis_source: Human-readable thesis/ledger source label.
    """

    key: str
    blocker_code: str
    sample: str
    observable: str
    figure_of_merit: str
    thesis_source: str


@dataclass(frozen=True)
class EvidenceBlocker:
    """Fail-closed blocker for missing charged-cone evidence.

    Args:
        code: Stable blocker identifier.
        sample: Needed sample or evidence package.
        observable: Needed observable.
        figure_of_merit: Needed figure of merit or provenance criterion.
        message: Deterministic summary suitable for reports.
    """

    code: str
    sample: str
    observable: str
    figure_of_merit: str
    message: str


@dataclass(frozen=True)
class EvidencePackage:
    """Paths/provenance supplied for charged-cone-deflection closure.

    Args:
        cone_scan_artifact: Artifact for the Ch. 7 single-track cone scan.
        beampipe_deflection_artifact: Artifact for pion beampipe scattering.
        provenance: DEC, ledger, or report identifier binding the artifacts to
            their samples, commands, hashes, and interpretation.
    """

    cone_scan_artifact: str | Path | None = None
    beampipe_deflection_artifact: str | Path | None = None
    provenance: str | None = None


@dataclass(frozen=True)
class ObjectIdentificationConeAudit:
    """Audit result for current cone-angle text/config evidence.

    Args:
        source_path: Source text inspected for a literal 25-degree cone angle.
        config_path: Config file inspected, if available.
        source_contains_canonical_cone_angle: Whether source text contains a
            literal ``cone_angle`` value matching 25 degrees.
        config_cone_angle_deg: Configured ``reconstruction.cone_angle`` value.
        config_contains_canonical_cone_angle: Whether the config value is 25.
        cone_angle_present: Whether either inspected surface contains 25 deg.
        message: Deterministic human-readable summary.
    """

    source_path: Path
    config_path: Path | None
    source_contains_canonical_cone_angle: bool
    config_cone_angle_deg: float | None
    config_contains_canonical_cone_angle: bool
    cone_angle_present: bool
    message: str


@dataclass(frozen=True)
class ChargedConeDeflectionAudit:
    """Combined charged cone and beampipe-deflection audit result.

    Args:
        canonical_cone_angle_deg: Thesis Ch. 7 adopted cone angle.
        allowed_scan_range_deg: Required fixed-energy scan coverage range.
        required_scan_angles_deg: Required fixed-energy scan points.
        ready: Whether all required evidence artifacts and provenance exist.
        blockers: Structured fail-closed blockers.
        object_identification: Optional current source/config cone audit.
    """

    canonical_cone_angle_deg: float
    allowed_scan_range_deg: tuple[float, float]
    required_scan_angles_deg: tuple[float, ...]
    ready: bool
    blockers: tuple[EvidenceBlocker, ...]
    object_identification: ObjectIdentificationConeAudit | None = None


CONE_SCAN_REQUIREMENT = EvidenceRequirement(
    key="cone_scan_artifact",
    blocker_code="missing_cone_scan_artifact",
    sample="cal_singleelectron_v1",
    observable="single-track energy collection efficiency vs cone angle",
    figure_of_merit="energy collection efficiency versus cone angle",
    thesis_source="Ch. 7 Single Track Energy Collection Efficiency; LIC-CH07-NUM-13..15",
)

BEAMPIPE_DEFLECTION_REQUIREMENT = EvidenceRequirement(
    key="beampipe_deflection_artifact",
    blocker_code="missing_beampipe_deflection_artifact",
    sample="cal_singlepionplus_v1",
    observable="deflection angle versus pion kinetic energy",
    figure_of_merit="energy-binned deflection-angle distribution",
    thesis_source="Ch. 7 Momentum Direction; LIC-CH07-NUM-16..17 and LIC-CH07-FIG-10",
)

PROVENANCE_REQUIREMENT = EvidenceRequirement(
    key="provenance",
    blocker_code="missing_provenance",
    sample="charged-cone-deflection evidence package",
    observable="DEC/provenance record for cone scan and beampipe deflection artifacts",
    figure_of_merit="reproducible command, sample, hash, and interpretation chain",
    thesis_source="docs/parallel-sessions/charged-cone-deflection.md",
)

EVIDENCE_REQUIREMENTS = (
    CONE_SCAN_REQUIREMENT,
    BEAMPIPE_DEFLECTION_REQUIREMENT,
    PROVENANCE_REQUIREMENT,
)


def audit_charged_cone_deflection(
    package: EvidencePackage | None = None,
    *,
    root: str | Path = ".",
    object_identification: ObjectIdentificationConeAudit | None = None,
) -> ChargedConeDeflectionAudit:
    """Audit supplied evidence for charged cone and deflection closure.

    Args:
        package: Evidence paths/provenance to audit. Missing fields fail closed.
        root: Root directory for relative artifact paths.
        object_identification: Optional source/config cone audit to attach.

    Returns:
        Combined audit report. ``ready`` is true only when every required
        artifact exists and a provenance record is supplied.
    """
    evidence = package or EvidencePackage()
    root_path = Path(root)
    blockers = tuple(_missing_blockers(evidence, root_path))
    return ChargedConeDeflectionAudit(
        canonical_cone_angle_deg=CANONICAL_CHARGED_CONE_ANGLE_DEG,
        allowed_scan_range_deg=ALLOWED_CONE_SCAN_RANGE_DEG,
        required_scan_angles_deg=REQUIRED_CONE_SCAN_ANGLES_DEG,
        ready=not blockers,
        blockers=blockers,
        object_identification=object_identification,
    )


def audit_current_charged_cone_deflection(
    root: str | Path = ".",
) -> ChargedConeDeflectionAudit:
    """Audit the current checkout for charged-cone closure artifacts.

    Args:
        root: Repository root used for expected relative artifact paths.

    Returns:
        Current-checkout audit. The default expected artifacts are the row-
        specific Ch. 7 ledger outputs; absent files and absent provenance block
        promotion rather than inventing values.
    """
    root_path = Path(root)
    object_audit = audit_object_identification_cone_angle(
        source_path=root_path / "nnbar_reconstruction/reconstruction/object_identification.py",
        config_path=root_path / "nnbar_reconstruction/config/nnbar_geometry.yaml",
    )
    return audit_charged_cone_deflection(
        EvidencePackage(
            cone_scan_artifact=CURRENT_REPO_CONE_SCAN_ARTIFACT,
            beampipe_deflection_artifact=CURRENT_REPO_BEAMPIPE_DEFLECTION_ARTIFACT,
            provenance=None,
        ),
        root=root_path,
        object_identification=object_audit,
    )


def audit_object_identification_cone_angle(
    source_path: str | Path = "nnbar_reconstruction/reconstruction/object_identification.py",
    config_path: str | Path | None = None,
) -> ObjectIdentificationConeAudit:
    """Inspect object-identification source and config for the 25-degree cone.

    Args:
        source_path: Object-identification source text to inspect.
        config_path: Optional YAML config path. When omitted, package-relative
            default discovery is used.

    Returns:
        Audit report stating whether a canonical ``cone_angle`` value is present
        in the inspected source text or reconstruction config.
    """
    source = Path(source_path)
    source_text = source.read_text() if source.exists() else ""
    source_has_angle = bool(_CONE_SOURCE_PATTERN.search(source_text))

    loaded_config_path: Path | None
    if config_path is None:
        loaded_config_path = None
    else:
        loaded_config_path = Path(config_path)
    config_cone_angle = _load_config_cone_angle(config_path)
    config_has_angle = _is_canonical_angle(config_cone_angle)
    present = source_has_angle or config_has_angle

    if config_has_angle and source_has_angle:
        message = "source text and config both expose cone_angle=25.0"
    elif config_has_angle:
        message = "config exposes reconstruction.cone_angle=25.0; object-identification text does not"
    elif source_has_angle:
        message = "object-identification text exposes cone_angle=25.0; config does not"
    else:
        message = "canonical cone_angle=25.0 is absent from inspected source/config"

    return ObjectIdentificationConeAudit(
        source_path=source,
        config_path=loaded_config_path,
        source_contains_canonical_cone_angle=source_has_angle,
        config_cone_angle_deg=config_cone_angle,
        config_contains_canonical_cone_angle=config_has_angle,
        cone_angle_present=present,
        message=message,
    )


def _missing_blockers(
    evidence: EvidencePackage, root: Path
) -> tuple[EvidenceBlocker, ...]:
    blockers: list[EvidenceBlocker] = []
    if not _artifact_exists(evidence.cone_scan_artifact, root):
        blockers.append(_blocker_for(CONE_SCAN_REQUIREMENT))
    if not _artifact_exists(evidence.beampipe_deflection_artifact, root):
        blockers.append(_blocker_for(BEAMPIPE_DEFLECTION_REQUIREMENT))
    if not _provenance_present(evidence.provenance):
        blockers.append(_blocker_for(PROVENANCE_REQUIREMENT))
    return tuple(blockers)


def _artifact_exists(value: str | Path | None, root: Path) -> bool:
    if value is None:
        return False
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.exists()


def _provenance_present(value: str | None) -> bool:
    return bool(value and value.strip())


def _blocker_for(requirement: EvidenceRequirement) -> EvidenceBlocker:
    message = (
        f"missing {requirement.key}: need sample {requirement.sample}; "
        f"observable {requirement.observable}; figure of merit "
        f"{requirement.figure_of_merit}; source {requirement.thesis_source}"
    )
    return EvidenceBlocker(
        code=requirement.blocker_code,
        sample=requirement.sample,
        observable=requirement.observable,
        figure_of_merit=requirement.figure_of_merit,
        message=message,
    )


def _load_config_cone_angle(config_path: str | Path | None) -> float | None:
    try:
        config = load_config(config_path, force_reload=True)
    except (FileNotFoundError, ImportError):
        return None
    raw_value = _get_path(config, ("reconstruction", "cone_angle"))
    if raw_value is None:
        return None
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def _get_path(config: Mapping[str, object], path: tuple[str, ...]) -> object | None:
    current: object = config
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current


def _is_canonical_angle(value: float | None) -> bool:
    if value is None:
        return False
    return isclose(value, CANONICAL_CHARGED_CONE_ANGLE_DEG, rel_tol=0.0, abs_tol=_TOLERANCE_DEG)
