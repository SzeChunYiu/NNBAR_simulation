"""Fail-closed pion multiplicity closure audit helpers.

The Ch. 9 Table 9.1 pion-count gate is only thesis-ready when the
``sig_foil_v3`` signal sample supplies truth and reconstructed charged,
neutral, and total pion multiplicities together with a provenance-pinned
truth-vs-reconstruction heatmap or confusion matrix.  This module makes those
requirements explicit without changing production cut constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from nnbar_reconstruction.analysis.event_variables import (
    EventVariables,
    event_variables_to_cut_observables,
)
from nnbar_reconstruction.reconstruction.cutflow import (
    CH9_CUTFLOW_ORDER,
    MIN_PION_COUNT,
)

SIGNAL_SAMPLE_ID = "sig_foil_v3"
PION_TRUTH_RECO_OBSERVABLE = "charged/neutral/total pion multiplicity truth-vs-reco"
PION_CLOSURE_FIGURE_OF_MERIT = "confusion matrix or heatmap residuals"
CURRENT_SIG_FOIL_V3_HEATMAP_ARTIFACT = Path(
    "output/ledger/sig_foil_v3_pion_multiplicity_truth_reco_heatmap.csv"
)

REQUIRED_TRUTH_COLUMNS = {
    "charged": "charged_pion_count_truth",
    "neutral": "neutral_pion_count_truth",
    "total": "total_pion_count_truth",
}
REQUIRED_RECO_COLUMNS = {
    "charged": "charged_pion_count_reco",
    "neutral": "neutral_pion_count_reco",
    "total": "total_pion_count_reco",
}


@dataclass(frozen=True)
class PionMultiplicityBlocker:
    """One fail-closed blocker for pion multiplicity closure.

    Args:
        code: Stable machine-readable blocker code.
        sample: Required sample or evidence package.
        observable: Required observable that must be supplied.
        figure_of_merit: Required closure figure of merit.
        message: Deterministic human-readable summary.
    """

    code: str
    sample: str
    observable: str
    figure_of_merit: str
    message: str


@dataclass(frozen=True)
class PionMultiplicityEvidence:
    """Optional artifact/provenance package for pion multiplicity closure.

    Args:
        heatmap_artifact: Path to the truth-vs-reco heatmap or confusion matrix
            artifact for the ``sig_foil_v3`` signal sample.
        provenance: DEC, ledger, or report identifier binding the artifact to
            sample ID, command, input hashes, observable, and interpretation.
    """

    heatmap_artifact: str | Path | None = None
    provenance: str | None = None


@dataclass(frozen=True)
class MultiplicityColumnStatus:
    """Presence and source status for one pion multiplicity count column.

    Args:
        kind: ``truth`` or ``reco`` count family.
        multiplicity: ``charged``, ``neutral``, or ``total`` pion count.
        column: Required column name.
        present: Whether the supplied DataFrame contains the column.
        status: Source status used by reports/tests.
        source: Human-readable provenance expectation for the column.
        blocker: Missing-column blocker, if any.
    """

    kind: str
    multiplicity: str
    column: str
    present: bool
    status: str
    source: str
    blocker: PionMultiplicityBlocker | None = None


@dataclass(frozen=True)
class Table91PionGateAudit:
    """Provenance status for the Ch. 9 Table 9.1 pion-count cut.

    Args:
        min_pion_count: Current canonical ``MIN_PION_COUNT`` constant.
        cut_name: Cutflow observable name checked by Table 9.1.
        event_variable_source: EventVariables field feeding the cut observable.
        source: Human-readable source chain for the gate.
        ready: Whether the current code still implements the documented gate.
        blocker: Fail-closed blocker if the gate is no longer documented.
    """

    min_pion_count: int
    cut_name: str
    event_variable_source: str
    source: str
    ready: bool
    blocker: PionMultiplicityBlocker | None = None


@dataclass(frozen=True)
class PionMultiplicityClosureAudit:
    """Complete pion multiplicity closure audit result.

    Args:
        ready: True only when columns, artifact, provenance, and Table 9.1 gate
            provenance are all present.
        column_statuses: Truth/reconstruction count-column status rows.
        table91_gate: Current gate provenance status.
        evidence: Artifact/provenance package inspected by the audit.
        blockers: Explicit fail-closed blockers.
    """

    ready: bool
    column_statuses: tuple[MultiplicityColumnStatus, ...]
    table91_gate: Table91PionGateAudit
    evidence: PionMultiplicityEvidence
    blockers: tuple[PionMultiplicityBlocker, ...]


def audit_pion_multiplicity_closure(
    truth_counts: pd.DataFrame,
    reco_counts: pd.DataFrame,
    evidence: PionMultiplicityEvidence | None = None,
    *,
    root: str | Path = ".",
) -> PionMultiplicityClosureAudit:
    """Audit in-memory pion multiplicity counts and closure evidence.

    Args:
        truth_counts: DataFrame expected to contain charged, neutral, and total
            truth-side pion multiplicity columns for ``sig_foil_v3``.
        reco_counts: DataFrame expected to contain charged, neutral, and total
            reconstructed pion multiplicity columns for the same events.
        evidence: Optional artifact/provenance package for the truth-vs-reco
            closure heatmap or confusion matrix.
        root: Repository or artifact root used to resolve relative paths.

    Returns:
        Immutable audit result. ``ready`` is false unless every required count
        column, the closure artifact, provenance, and Table 9.1 gate evidence
        are present.
    """
    evidence_package = evidence or PionMultiplicityEvidence()
    column_statuses = _column_statuses(truth_counts, reco_counts)
    table91_gate = audit_table91_min_pion_gate()

    blockers = tuple(
        status.blocker for status in column_statuses if status.blocker is not None
    )
    blockers += _evidence_blockers(evidence_package, Path(root))
    if table91_gate.blocker is not None:
        blockers += (table91_gate.blocker,)

    return PionMultiplicityClosureAudit(
        ready=not blockers,
        column_statuses=column_statuses,
        table91_gate=table91_gate,
        evidence=evidence_package,
        blockers=blockers,
    )


def audit_current_pion_multiplicity_closure(
    root: str | Path = ".",
) -> PionMultiplicityClosureAudit:
    """Audit the current checkout for pion multiplicity closure evidence.

    Args:
        root: Repository root used to resolve the expected current artifact path.

    Returns:
        Current-checkout audit. Empty DataFrames intentionally represent the
        absence of a pinned ``sig_foil_v3`` closure table in this repo and keep
        the closure blocked until real artifacts are supplied.
    """
    return audit_pion_multiplicity_closure(
        pd.DataFrame(),
        pd.DataFrame(),
        PionMultiplicityEvidence(
            heatmap_artifact=CURRENT_SIG_FOIL_V3_HEATMAP_ARTIFACT,
            provenance=None,
        ),
        root=root,
    )


def audit_table91_min_pion_gate() -> Table91PionGateAudit:
    """Audit the documented Ch. 9 Table 9.1 pion-count gate.

    Returns:
        Gate provenance record tying ``MIN_PION_COUNT == 1`` to
        ``EventVariables.n_pions`` via ``event_variables_to_cut_observables``.
    """
    probe = EventVariables(
        invariant_mass=0.0,
        sphericity=0.0,
        total_energy=0.0,
        scint_energy=0.0,
        lg_energy=0.0,
        longitudinal_energy=0.0,
        transverse_energy=0.0,
        top_bottom_asymmetry=0.0,
        forward_backward_asymmetry=0.0,
        n_charged=0,
        n_neutral=0,
        n_pions=7,
        n_protons=0,
        vertex_r=0.0,
        n_tracks_to_vertex=0,
    )
    cut_observables = event_variables_to_cut_observables(probe)
    mapped_from_event_variables = cut_observables.pion_count == probe.n_pions
    gate_in_order = "pion_count" in CH9_CUTFLOW_ORDER
    ready = MIN_PION_COUNT == 1 and gate_in_order and mapped_from_event_variables

    blocker = None
    if not ready:
        blocker = _blocker(
            "invalid_table91_min_pion_gate",
            SIGNAL_SAMPLE_ID,
            PION_TRUTH_RECO_OBSERVABLE,
            PION_CLOSURE_FIGURE_OF_MERIT,
            "Ch. 9 Table 9.1 pion gate must remain MIN_PION_COUNT == 1 "
            "and map EventVariables.n_pions into cutflow pion_count.",
        )

    return Table91PionGateAudit(
        min_pion_count=MIN_PION_COUNT,
        cut_name="pion_count",
        event_variable_source="EventVariables.n_pions",
        source="Ch. 9 Table 9.1: EventVariables.n_pions -> EventCutObservables.pion_count -> MIN_PION_COUNT",
        ready=ready,
        blocker=blocker,
    )


def _column_statuses(
    truth_counts: pd.DataFrame,
    reco_counts: pd.DataFrame,
) -> tuple[MultiplicityColumnStatus, ...]:
    return tuple(
        _status_for_column("truth", multiplicity, column, truth_counts)
        for multiplicity, column in REQUIRED_TRUTH_COLUMNS.items()
    ) + tuple(
        _status_for_column("reco", multiplicity, column, reco_counts)
        for multiplicity, column in REQUIRED_RECO_COLUMNS.items()
    )


def _status_for_column(
    kind: str,
    multiplicity: str,
    column: str,
    frame: pd.DataFrame,
) -> MultiplicityColumnStatus:
    present = column in frame.columns
    if kind == "truth":
        present_status = "source_backed_truth"
        missing_status = "missing_truth_column"
        source = f"{SIGNAL_SAMPLE_ID} truth-side pion multiplicity column"
    else:
        present_status = "source_backed_reconstruction"
        missing_status = "missing_reco_column"
        source = f"{SIGNAL_SAMPLE_ID} reconstructed pion multiplicity column"

    blocker = None
    if not present:
        blocker = _blocker(
            f"{missing_status}:{multiplicity}",
            SIGNAL_SAMPLE_ID,
            f"{multiplicity} pion multiplicity {kind} count",
            PION_CLOSURE_FIGURE_OF_MERIT,
            f"Missing {column!r} for sample={SIGNAL_SAMPLE_ID}; observable="
            f"{PION_TRUTH_RECO_OBSERVABLE}; figure_of_merit="
            f"{PION_CLOSURE_FIGURE_OF_MERIT}.",
        )

    return MultiplicityColumnStatus(
        kind=kind,
        multiplicity=multiplicity,
        column=column,
        present=present,
        status=present_status if present else missing_status,
        source=source,
        blocker=blocker,
    )


def _evidence_blockers(
    evidence: PionMultiplicityEvidence,
    root: Path,
) -> tuple[PionMultiplicityBlocker, ...]:
    blockers: list[PionMultiplicityBlocker] = []
    if evidence.heatmap_artifact is None or not _path_exists(evidence.heatmap_artifact, root):
        blockers.append(
            _blocker(
                "missing_heatmap_artifact",
                SIGNAL_SAMPLE_ID,
                PION_TRUTH_RECO_OBSERVABLE,
                PION_CLOSURE_FIGURE_OF_MERIT,
                f"Missing {SIGNAL_SAMPLE_ID} charged/neutral/total pion multiplicity truth-vs-reco heatmap artifact; "
                f"figure_of_merit={PION_CLOSURE_FIGURE_OF_MERIT}.",
            )
        )

    if not evidence.provenance:
        blockers.append(
            _blocker(
                "missing_provenance",
                SIGNAL_SAMPLE_ID,
                PION_TRUTH_RECO_OBSERVABLE,
                PION_CLOSURE_FIGURE_OF_MERIT,
                f"Missing provenance for sample={SIGNAL_SAMPLE_ID}; observable="
                f"{PION_TRUTH_RECO_OBSERVABLE}; figure_of_merit="
                f"{PION_CLOSURE_FIGURE_OF_MERIT}.",
            )
        )
    return tuple(blockers)


def _path_exists(path: str | Path, root: Path) -> bool:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.exists()


def _blocker(
    code: str,
    sample: str,
    observable: str,
    figure_of_merit: str,
    message: str,
) -> PionMultiplicityBlocker:
    return PionMultiplicityBlocker(
        code=code,
        sample=sample,
        observable=observable,
        figure_of_merit=figure_of_merit,
        message=message,
    )
