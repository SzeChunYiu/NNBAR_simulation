"""Fail-closed audit helpers for the thesis reproduction ledger.

The helpers in this module parse the ledger table without mutating it and make
command/sample blockers explicit before any row is promoted as executable.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import shlex
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

COMMAND_PLACEHOLDER = "command_placeholder"
PYTHON_CLI_COMMAND = "python_cli_command"
MACRO_OR_SCRIPT_COMMAND = "macro_or_script_command"
UNSUPPORTED_COMMAND = "unsupported_command"
READY_FOR_REPRODUCTION = "ready_for_future_reproduction"
SAMPLE_PATH_MISSING = "sample_path_missing"
SAMPLE_PATH_NOT_CHECKED = "sample_path_not_checked"


@dataclass(frozen=True)
class LedgerRow:
    """Minimal row extracted from ``docs/thesis_reproduction_ledger.md``.

    Args:
        row_id: Stable ledger row identifier.
        sample: Reproduction sample or dataset-id cell.
        command: Reproducing command cell with inline markdown code stripped.
        status: Current ledger status cell.
        notes: Free-text ledger notes cell.
    """

    row_id: str
    sample: str
    command: str
    status: str
    notes: str


@dataclass(frozen=True)
class LedgerAudit:
    """Fail-closed audit result for one ledger row.

    Args:
        row_id: Stable ledger row identifier.
        command_kind: Command classification or ``READY_FOR_REPRODUCTION``.
        ready: Whether command and sample checks are complete enough to run.
        blockers: Deterministic blocker identifiers for this row.
        sample_path: Checked relative sample path, if a mapping was supplied.
    """

    row_id: str
    command_kind: str
    ready: bool
    blockers: tuple[str, ...]
    sample_path: str | None = None


@dataclass(frozen=True)
class LedgerAuditSummary:
    """Aggregate blocker counts for a ledger audit.

    Args:
        total_rows: Number of audited rows.
        ready_rows: Number of rows with no blockers.
        blocked_rows: Number of rows with one or more blockers.
        blocker_counts: Mapping from blocker identifier to row count.
    """

    total_rows: int
    ready_rows: int
    blocked_rows: int
    blocker_counts: Mapping[str, int]


def parse_ledger_rows(markdown: str) -> tuple[LedgerRow, ...]:
    """Parse thesis-ledger markdown rows into audit records.

    Args:
        markdown: Complete or partial markdown text containing the ledger table.

    Returns:
        Tuple of parsed ``LedgerRow`` records from the table whose header has
        ``id``, ``sample``, ``reproducing.command``, ``status``, and ``notes``.
    """

    rows: list[LedgerRow] = []
    columns: dict[str, int] | None = None
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = [_clean_cell(cell) for cell in _split_markdown_row(line)]
        if _is_separator_row(cells):
            continue
        normalized = [_normalize_header(cell) for cell in cells]
        if "reproducing.command" in normalized and "id" in normalized:
            columns = {name: normalized.index(name) for name in normalized}
            continue
        if columns is None:
            continue
        required = ("id", "sample", "reproducing.command", "status", "notes")
        if not all(name in columns and columns[name] < len(cells) for name in required):
            continue
        rows.append(
            LedgerRow(
                row_id=cells[columns["id"]],
                sample=cells[columns["sample"]],
                command=_strip_inline_code(cells[columns["reproducing.command"]]),
                status=cells[columns["status"]],
                notes=cells[columns["notes"]],
            )
        )
    return tuple(rows)


def audit_row(
    row: LedgerRow,
    *,
    root: str | Path = ".",
    sample_paths: Mapping[str, str | Path] | None = None,
    verified_cli_subcommands: Iterable[str] = (),
) -> LedgerAudit:
    """Classify one ledger row and surface fail-closed blockers.

    Args:
        row: Parsed ledger row.
        root: Root directory used for relative file and sample checks.
        sample_paths: Optional mapping from ledger sample id to a relative path.
        verified_cli_subcommands: CLI subcommands whose help surface has already
            been verified by the caller.

    Returns:
        ``LedgerAudit`` with blockers for placeholders, unverified CLI commands,
        missing command files, unknown command shapes, and unchecked/missing
        sample paths.
    """

    root_path = Path(root)
    verified_cli = frozenset(verified_cli_subcommands)
    blockers: list[str] = []
    command_kind = _classify_command(row.command, blockers, root_path, verified_cli)
    sample_path = _audit_sample_path(row.sample, sample_paths, root_path, blockers)
    ready = not blockers
    if ready:
        command_kind = READY_FOR_REPRODUCTION
    return LedgerAudit(
        row_id=row.row_id,
        command_kind=command_kind,
        ready=ready,
        blockers=tuple(dict.fromkeys(blockers)),
        sample_path=sample_path,
    )


def audit_ledger_rows(
    rows: Sequence[LedgerRow],
    *,
    root: str | Path = ".",
    sample_paths: Mapping[str, str | Path] | None = None,
    verified_cli_subcommands: Iterable[str] = (),
) -> tuple[LedgerAudit, ...]:
    """Audit multiple ledger rows with identical verification context.

    Args:
        rows: Parsed ledger rows.
        root: Root directory used for relative file and sample checks.
        sample_paths: Optional mapping from ledger sample id to a relative path.
        verified_cli_subcommands: CLI subcommands already verified by the caller.

    Returns:
        Tuple of per-row audit results in input order.
    """

    return tuple(
        audit_row(
            row,
            root=root,
            sample_paths=sample_paths,
            verified_cli_subcommands=verified_cli_subcommands,
        )
        for row in rows
    )


def summarize_audits(audits: Sequence[LedgerAudit]) -> LedgerAuditSummary:
    """Summarize row readiness and blocker identifiers.

    Args:
        audits: Per-row audit results.

    Returns:
        Aggregate counts suitable for MASTER_PLAN notes.
    """

    blocker_counts: Counter[str] = Counter()
    ready_rows = 0
    for audit in audits:
        if audit.ready:
            ready_rows += 1
        blocker_counts.update(audit.blockers)
    total_rows = len(audits)
    counts = MappingProxyType(dict(sorted(blocker_counts.items())))
    return LedgerAuditSummary(
        total_rows=total_rows,
        ready_rows=ready_rows,
        blocked_rows=total_rows - ready_rows,
        blocker_counts=counts,
    )


def _classify_command(
    command: str,
    blockers: list[str],
    root: Path,
    verified_cli: frozenset[str],
) -> str:
    if _is_placeholder_command(command):
        blockers.append(COMMAND_PLACEHOLDER)
        return COMMAND_PLACEHOLDER
    cli_subcommand = _python_cli_subcommand(command)
    if cli_subcommand is not None:
        if cli_subcommand not in verified_cli:
            blockers.append(f"python_cli_unverified:{cli_subcommand}")
        return PYTHON_CLI_COMMAND
    command_paths = _command_file_paths(command)
    if command_paths:
        for relative_path in command_paths:
            if not (root / relative_path).exists():
                blockers.append(f"command_file_missing:{relative_path}")
        return MACRO_OR_SCRIPT_COMMAND
    blockers.append(UNSUPPORTED_COMMAND)
    return UNSUPPORTED_COMMAND


def _audit_sample_path(
    sample: str,
    sample_paths: Mapping[str, str | Path] | None,
    root: Path,
    blockers: list[str],
) -> str | None:
    if not sample_paths or sample not in sample_paths:
        blockers.append(SAMPLE_PATH_NOT_CHECKED)
        return None
    relative_path = Path(sample_paths[sample])
    if relative_path.is_absolute():
        checked_path = relative_path
        rendered = str(relative_path)
    else:
        checked_path = root / relative_path
        rendered = relative_path.as_posix()
    if not checked_path.exists():
        blockers.append(SAMPLE_PATH_MISSING)
    return rendered


def _split_markdown_row(line: str) -> list[str]:
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    for char in line.strip().strip("|"):
        if char == "`":
            in_code = not in_code
        if char == "|" and not in_code:
            cells.append("".join(current))
            current = []
        else:
            current.append(char)
    cells.append("".join(current))
    return cells


def _is_separator_row(cells: Sequence[str]) -> bool:
    return bool(cells) and all(set(cell.strip()) <= {"-", ":"} for cell in cells)


def _clean_cell(cell: str) -> str:
    return " ".join(cell.strip().split())


def _normalize_header(cell: str) -> str:
    return _strip_inline_code(cell).strip().lower()


def _strip_inline_code(cell: str) -> str:
    stripped = cell.strip()
    if len(stripped) >= 2 and stripped.startswith("`") and stripped.endswith("`"):
        return stripped[1:-1].strip()
    return stripped


def _is_placeholder_command(command: str) -> bool:
    normalized = command.strip().upper()
    return not normalized or normalized.startswith("TODO") or "TODO(" in normalized


def _python_cli_subcommand(command: str) -> str | None:
    tokens = _shell_tokens(command)
    for index, token in enumerate(tokens[:-1]):
        if token != "-m":
            continue
        module = tokens[index + 1]
        if not module.startswith("nnbar_reconstruction"):
            continue
        if module == "nnbar_reconstruction.cli":
            return _next_non_control_token(tokens[index + 2 :]) or "<missing>"
        return module.removeprefix("nnbar_reconstruction.")
    return None


def _next_non_control_token(tokens: Sequence[str]) -> str | None:
    for token in tokens:
        if token in {"&&", ";"}:
            return None
        if token.startswith("-"):
            continue
        return token
    return None


def _command_file_paths(command: str) -> tuple[str, ...]:
    paths: list[str] = []
    for token in _shell_tokens(command):
        if token in {"&&", ";"}:
            continue
        if token.startswith("./"):
            paths.append(token[2:])
        elif token.endswith((".mac", ".sh")):
            paths.append(token.removeprefix("./"))
    return tuple(dict.fromkeys(paths))


def _shell_tokens(command: str) -> tuple[str, ...]:
    try:
        return tuple(shlex.split(command))
    except ValueError:
        return ()
