"""Regression tests for the codex-supervisor corruption watchdog."""

from __future__ import annotations

import os
import re
import subprocess
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "csup-corruption-watchdog.sh"
CSUP_CONFIG = REPO_ROOT / ".codex-supervisor.toml"


def _watchdog_prompt_map() -> dict[str, str]:
    text = SCRIPT.read_text(encoding="utf-8")
    return dict(
        re.findall(r'"([A-Za-z0-9_.-]+)=([A-Za-z0-9_.-]+\.txt)"', text)
    )


def test_watchdog_covers_every_lunarc_prompt_session() -> None:
    """Every active LUNARC prompt session should be scanned for /goal corruption."""
    config = tomllib.loads(CSUP_CONFIG.read_text(encoding="utf-8"))
    expected = {
        host_config["session"]: host_config["prompts"]
        for host_name, host_config in config["hosts"].items()
        if host_name.endswith("-lunarc")
    }

    assert expected.items() <= _watchdog_prompt_map().items()


def test_watchdog_once_handles_empty_holder_job_with_fake_ssh(tmp_path: Path) -> None:
    """The watchdog should initialize and exit cleanly when no holder job exists."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_ssh.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--once"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0
    assert "no RUNNING nnbar-csup holder; skipping" in result.stdout


def test_watchdog_once_scans_holder_job_with_fake_ssh(tmp_path: Path) -> None:
    """The watchdog should run its scan loop under macOS /bin/bash 3.2."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        "case \"$*\" in\n"
        "  *squeue*) echo 12345 ;;\n"
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--once"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0
    assert "mapfile: command not found" not in result.stderr


def test_watchdog_once_skips_unavailable_tmux_session(tmp_path: Path) -> None:
    """A missing remote tmux/srun target should not kill the whole watchdog pass."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        "case \"$*\" in\n"
        "  *squeue*) echo 12345; exit 0 ;;\n"
        "  *) echo 'srun: error: task exited' >&2; exit 1 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--once"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0


def test_watchdog_reinjects_pane_zero_prompt(tmp_path: Path) -> None:
    """tmux pane 0 should map to the first /goal prompt line, not index -1."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ssh_log = tmp_path / "ssh.log"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        "case \"$*\" in\n"
        "  *squeue*) echo 12345 ;;\n"
        "  *list-panes*) echo 0 ;;\n"
        "  *capture-pane*) echo '/model goal You are PANE' ;;\n"
        "  *) printf '%s\\n' \"$*\" >> \"$SSH_LOG\" ;;\n"
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["SSH_LOG"] = str(ssh_log)

    result = subprocess.run(
        ["bash", str(SCRIPT), "--once"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0
    assert "no prompt at index -1" not in result.stdout
    assert "PANE 0" in ssh_log.read_text(encoding="utf-8")


def test_watchdog_detects_invalid_request_error_regex(tmp_path: Path) -> None:
    """Regex-style corruption patterns should match real invalid_request errors."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ssh_log = tmp_path / "ssh.log"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        "case \"$*\" in\n"
        "  *squeue*) echo 12345 ;;\n"
        "  *list-panes*) echo 0 ;;\n"
        "  *capture-pane*) echo 'invalid_request_error: bad model command' ;;\n"
        "  *) printf '%s\\n' \"$*\" >> \"$SSH_LOG\" ;;\n"
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["SSH_LOG"] = str(ssh_log)

    result = subprocess.run(
        ["bash", str(SCRIPT), "--once"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0
    assert "PANE 0" in ssh_log.read_text(encoding="utf-8")
