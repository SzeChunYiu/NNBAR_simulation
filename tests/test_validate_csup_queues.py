"""Regression tests for codex-supervisor queue validation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate-csup-queues.sh"


def test_queue_file_failures_affect_exit_status(tmp_path: Path) -> None:
    """Invalid follow-up queue lines must make the validator reject startup."""
    scripts_dir = tmp_path / "scripts"
    queue_dir = tmp_path / "codex-tasks" / "demo"
    scripts_dir.mkdir()
    queue_dir.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts_dir / SCRIPT.name)

    (tmp_path / "codex-prompts-demo.txt").write_text(
        "/goal You are PANE 0, lane DEMO. Read docs/parallel-sessions/demo.md.\n",
        encoding="utf-8",
    )
    (queue_dir / "bad.txt").write_text(
        "not-a-goal docs/parallel-sessions/demo.md\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(scripts_dir / SCRIPT.name)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "FAIL codex-tasks/demo/bad.txt:1" in result.stdout
    assert "failures: 1" in result.stdout


def test_unterminated_final_queue_line_is_validated(tmp_path: Path) -> None:
    """The final queue entry must be checked even without a trailing newline."""
    scripts_dir = tmp_path / "scripts"
    queue_dir = tmp_path / "codex-tasks" / "demo"
    scripts_dir.mkdir()
    queue_dir.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts_dir / SCRIPT.name)

    (tmp_path / "codex-prompts-demo.txt").write_text(
        "/goal You are PANE 0, lane DEMO. Read docs/parallel-sessions/demo.md.\n",
        encoding="utf-8",
    )
    (queue_dir / "bad.txt").write_text(
        "not-a-goal docs/parallel-sessions/demo.md",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(scripts_dir / SCRIPT.name)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "FAIL codex-tasks/demo/bad.txt:1" in result.stdout
    assert "failures: 1" in result.stdout


def test_appledouble_resource_forks_are_ignored(tmp_path: Path) -> None:
    """macOS ``._*.txt`` sidecars must not be treated as queue files."""
    scripts_dir = tmp_path / "scripts"
    queue_dir = tmp_path / "codex-tasks" / "demo"
    scripts_dir.mkdir()
    queue_dir.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts_dir / SCRIPT.name)

    (tmp_path / "codex-prompts-demo.txt").write_text(
        "/goal You are PANE 0, lane DEMO. Read docs/parallel-sessions/demo.md.\n",
        encoding="utf-8",
    )
    (queue_dir / "worker.txt").write_text(
        "/goal You are PANE 1, lane WORKER. Read docs/parallel-sessions/demo.md.\n",
        encoding="utf-8",
    )
    (queue_dir / "._worker.txt").write_text(
        "not-a-goal docs/parallel-sessions/demo.md\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(scripts_dir / SCRIPT.name)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "files scanned: 2" in result.stdout
    assert "failures: 0" in result.stdout


def test_whitespace_only_queue_lines_are_ignored(tmp_path: Path) -> None:
    """Blank queue lines may contain tabs from manual editor cleanup."""
    scripts_dir = tmp_path / "scripts"
    queue_dir = tmp_path / "codex-tasks" / "demo"
    scripts_dir.mkdir()
    queue_dir.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts_dir / SCRIPT.name)

    (tmp_path / "codex-prompts-demo.txt").write_text(
        "/goal You are PANE 0, lane DEMO. Read docs/parallel-sessions/demo.md.\n",
        encoding="utf-8",
    )
    (queue_dir / "worker.txt").write_text(
        "\t  \t\n"
        "/goal You are PANE 1, lane WORKER. Read docs/parallel-sessions/demo.md.\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(scripts_dir / SCRIPT.name)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "prompt lines checked: 2" in result.stdout
    assert "failures: 0" in result.stdout


def test_over_word_limit_prompt_lines_are_rejected(tmp_path: Path) -> None:
    """Queue lint must mirror the supervisor's compact /goal word cap."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    shutil.copy2(SCRIPT, scripts_dir / SCRIPT.name)

    long_prompt = " ".join(
        [
            "/goal",
            "Read",
            "docs/parallel-sessions/demo.md",
            *[f"word{i}" for i in range(48)],
        ]
    )
    (tmp_path / "codex-prompts-demo.txt").write_text(
        f"{long_prompt}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(scripts_dir / SCRIPT.name)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "codex-prompts-demo.txt:1" in result.stdout
    assert "word cap is 50" in result.stdout


def test_unknown_flag_is_rejected_before_validation(tmp_path: Path) -> None:
    """Typos in validator flags must not look like a clean queue scan."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    shutil.copy2(SCRIPT, scripts_dir / SCRIPT.name)

    result = subprocess.run(
        ["bash", str(scripts_dir / SCRIPT.name), "--bogus"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "unknown arg: --bogus" in result.stdout
    assert "OK: every prompt line passes" not in result.stdout


def test_meta_debugger_queue_rejects_validator_prompt(tmp_path: Path) -> None:
    """The project-wide DEBUGGER queue must not receive VALIDATOR work."""
    scripts_dir = tmp_path / "scripts"
    queue_dir = tmp_path / "codex-tasks" / "meta"
    scripts_dir.mkdir()
    queue_dir.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts_dir / SCRIPT.name)

    (tmp_path / "codex-prompts-meta.txt").write_text(
        "/goal You are PANE 0, lane DEBUGGER. Read docs/parallel-sessions/debugger.md.\n"
        "/goal You are PANE 1, lane VALIDATOR. Read docs/parallel-sessions/validator-planner.md.\n",
        encoding="utf-8",
    )
    (queue_dir / "worker-0.txt").write_text(
        "/goal You are VALIDATOR-PLANNER. Read docs/parallel-sessions/validator-planner.md.\n",
        encoding="utf-8",
    )
    (queue_dir / "worker-1.txt").write_text(
        "/goal You are PANE 1, lane VALIDATOR. Read docs/parallel-sessions/validator-planner.md.\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(scripts_dir / SCRIPT.name)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "codex-tasks/meta/worker-0.txt:1" in result.stdout
    assert "meta worker-0 is DEBUGGER-only" in result.stdout
    assert "failures: 1" in result.stdout
