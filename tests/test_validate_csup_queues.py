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
