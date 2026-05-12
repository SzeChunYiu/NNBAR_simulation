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
