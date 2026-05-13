from pathlib import Path

from nnbar_reconstruction.analysis.thesis_ledger_closure import (
    COMMAND_PLACEHOLDER,
    MACRO_OR_SCRIPT_COMMAND,
    PYTHON_CLI_COMMAND,
    READY_FOR_REPRODUCTION,
    SAMPLE_PATH_MISSING,
    SAMPLE_PATH_NOT_CHECKED,
    UNSUPPORTED_COMMAND,
    audit_ledger_rows,
    audit_row,
    parse_ledger_rows,
    summarize_audits,
)


def _one_row(command, sample="toy_sample", status="blocked-no-sample", notes="n/a"):
    text = f"""
| id | source | thesis_value | sample | reproducing.command | status | leaf | decision_log | notes |
|---|---|---|---|---|---|---|---|---|
| ROW-1 | source text | figure | {sample} | `{command}` | {status} | P.1 |  | {notes} |
"""
    return parse_ledger_rows(text)[0]


def test_parse_ledger_rows_extracts_audit_columns():
    rows = parse_ledger_rows(
        """
| id | source | thesis_value | sample | reproducing.command | status | leaf | decision_log | notes |
|---|---|---|---|---|---|---|---|---|
| LIC-1 | src | value | sig_foil_v3 | `python3 -m nnbar_reconstruction.cli summarize sample` | blocked-no-sample | V.1 | DEC-1 | absent sample |
"""
    )

    assert len(rows) == 1
    assert rows[0].row_id == "LIC-1"
    assert rows[0].sample == "sig_foil_v3"
    assert rows[0].command == "python3 -m nnbar_reconstruction.cli summarize sample"
    assert rows[0].status == "blocked-no-sample"
    assert rows[0].notes == "absent sample"


def test_todo_command_is_fail_closed_placeholder_blocker():
    row = _one_row("TODO(L2/L3): replace missing geometry-audit CLI")

    audit = audit_row(row)

    assert audit.command_kind == COMMAND_PLACEHOLDER
    assert audit.ready is False
    assert COMMAND_PLACEHOLDER in audit.blockers


def test_unsupported_python_cli_command_needs_verification():
    row = _one_row("python3 -m nnbar_reconstruction.cli geometry-audit toy_sample")

    audit = audit_row(row, verified_cli_subcommands={"summarize"})

    assert audit.command_kind == PYTHON_CLI_COMMAND
    assert audit.ready is False
    assert "python_cli_unverified:geometry-audit" in audit.blockers


def test_macro_or_script_command_requires_existing_file():
    row = _one_row("./nnbar-detector-simulation -m macro/missing.mac", sample="toy_sample")

    audit = audit_row(row, root=Path("."), sample_paths={"toy_sample": "."})

    assert audit.command_kind == MACRO_OR_SCRIPT_COMMAND
    assert audit.ready is False
    assert "command_file_missing:nnbar-detector-simulation" in audit.blockers
    assert "command_file_missing:macro/missing.mac" in audit.blockers


def test_missing_sample_blocks_verified_command():
    row = _one_row("python3 -m nnbar_reconstruction.cli summarize toy_sample")

    audit = audit_row(row, verified_cli_subcommands={"summarize"})

    assert audit.command_kind == PYTHON_CLI_COMMAND
    assert audit.ready is False
    assert SAMPLE_PATH_NOT_CHECKED in audit.blockers


def test_verified_local_toy_sample_and_cli_are_ready(tmp_path):
    sample_dir = tmp_path / "sample"
    sample_dir.mkdir()
    row = _one_row("python3 -m nnbar_reconstruction.cli summarize toy_sample")

    audit = audit_row(
        row,
        root=tmp_path,
        sample_paths={"toy_sample": "sample"},
        verified_cli_subcommands={"summarize"},
    )

    assert audit.ready is True
    assert audit.command_kind == READY_FOR_REPRODUCTION
    assert audit.blockers == ()


def test_absent_mapped_sample_path_is_reported_as_missing(tmp_path):
    row = _one_row("python3 -m nnbar_reconstruction.cli summarize toy_sample")

    audit = audit_row(
        row,
        root=tmp_path,
        sample_paths={"toy_sample": "missing-sample"},
        verified_cli_subcommands={"summarize"},
    )

    assert audit.ready is False
    assert SAMPLE_PATH_MISSING in audit.blockers


def test_current_thesis_ledger_still_has_fail_closed_blockers():
    rows = parse_ledger_rows(Path("docs/thesis_reproduction_ledger.md").read_text())
    audits = audit_ledger_rows(rows, verified_cli_subcommands={"summarize", "validate-reco"})
    summary = summarize_audits(audits)

    assert len(rows) >= 100
    assert summary.total_rows == len(rows)
    assert summary.ready_rows == 0
    assert summary.blocked_rows == len(rows)
    assert summary.blocker_counts[SAMPLE_PATH_NOT_CHECKED] > 0
    assert summary.blocker_counts[COMMAND_PLACEHOLDER] > 0
