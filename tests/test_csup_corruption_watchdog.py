"""Regression tests for the codex-supervisor corruption watchdog."""

from __future__ import annotations

import base64
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


def _decoded_reinject_prompts(ssh_log: str) -> list[str]:
    payloads = re.findall(
        r"printf '\\''%s'\\'' '\\''([A-Za-z0-9+/=]+)'\\'' \| base64 -d",
        ssh_log,
    )
    return [
        base64.b64decode(payload).decode("utf-8")
        for payload in payloads
    ]


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


def test_watchdog_checks_lunarc_control_socket_before_remote_scan(
    tmp_path: Path,
) -> None:
    """The watchdog should guard operational ssh lunarc calls with socket check."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ssh_log = tmp_path / "ssh.log"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$SSH_LOG\"\n"
        "case \"$*\" in\n"
        "  '-O check lunarc') exit 0 ;;\n"
        "  *squeue*) exit 0 ;;\n"
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
    assert ssh_log.read_text(encoding="utf-8").splitlines()[0] == "-O check lunarc"


def test_watchdog_reuses_lunarc_control_socket_within_one_sweep(
    tmp_path: Path,
) -> None:
    """A single watchdog sweep should not re-check the socket before every ssh."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ssh_log = tmp_path / "ssh.log"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$SSH_LOG\"\n"
        "case \"$*\" in\n"
        "  '-O check lunarc') exit 0 ;;\n"
        "  *squeue*) echo 12345; exit 0 ;;\n"
        "  *list-panes*) echo 0; exit 0 ;;\n"
        "  *capture-pane*) echo 'pane clean'; exit 0 ;;\n"
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

    socket_checks = [
        line
        for line in ssh_log.read_text(encoding="utf-8").splitlines()
        if line == "-O check lunarc"
    ]

    assert result.returncode == 0
    assert socket_checks == ["-O check lunarc"]


def test_watchdog_checks_corruption_patterns_once_per_pane(tmp_path: Path) -> None:
    """A clean pane should require one regex scan, not one grep per pattern."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    grep_log = tmp_path / "grep.log"

    fake_scripts = {
        "ssh": (
            "#!/usr/bin/env bash\n"
            "case \"$*\" in\n"
            "  '-O check lunarc') exit 0 ;;\n"
            "  *squeue*) echo 12345; exit 0 ;;\n"
            "  *list-panes*) echo 0; exit 0 ;;\n"
            "  *capture-pane*) echo 'pane clean'; exit 0 ;;\n"
            "esac\n"
            "exit 0\n"
        ),
        "grep": (
            "#!/usr/bin/env bash\n"
            "if [[ \"$1\" == '-Eq' ]]; then printf '%s\\n' \"$2\" >> \"$GREP_LOG\"; fi\n"
            "exec /usr/bin/grep \"$@\"\n"
        ),
    }
    for name, content in fake_scripts.items():
        path = fake_bin / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    env = os.environ.copy()
    env.update({"PATH": f"{fake_bin}{os.pathsep}{env['PATH']}", "GREP_LOG": str(grep_log)})

    result = subprocess.run(
        ["bash", str(SCRIPT), "--once"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    pattern_checks = grep_log.read_text(encoding="utf-8").splitlines()
    assert result.returncode == 0
    assert len(pattern_checks) == len(_watchdog_prompt_map())


def test_watchdog_once_scans_holder_job_with_fake_ssh(tmp_path: Path) -> None:
    """The watchdog should run its scan loop under macOS /bin/bash 3.2."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        "case \"$*\" in\n"
        "  *squeue*) echo 12345 ;;\n"
        "  *list-panes*) echo 'flatpak: libmount mismatch' >&2 ;;\n"
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
    assert "flatpak:" not in result.stderr


def test_watchdog_once_skips_unavailable_tmux_session(tmp_path: Path) -> None:
    """A missing remote tmux/srun target should not kill the whole watchdog pass."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        "case \"$*\" in\n"
        "  '-O check lunarc') exit 0 ;;\n"
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
    decoded_prompts = _decoded_reinject_prompts(ssh_log.read_text(encoding="utf-8"))
    assert any("PANE 0" in prompt for prompt in decoded_prompts)


def test_watchdog_reinjects_prompt_without_literal_shell_payload(
    tmp_path: Path,
) -> None:
    """Prompt text should not be interpolated directly into the remote shell."""
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

    canonical_prompt = next(
        line for line in (REPO_ROOT / "codex-prompts-recon.txt").read_text().splitlines()
        if line.startswith("/goal")
    )
    reinject_commands = ssh_log.read_text(encoding="utf-8")

    assert result.returncode == 0
    assert canonical_prompt not in reinject_commands
    assert canonical_prompt in _decoded_reinject_prompts(reinject_commands)


def test_watchdog_maps_one_based_tmux_panes_by_position(tmp_path: Path) -> None:
    """LUNARC tmux panes are one-based, but pane 1 is still prompt line 0."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ssh_log = tmp_path / "ssh.log"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        "case \"$*\" in\n"
        "  *squeue*) echo 12345 ;;\n"
        "  *list-panes*) echo 1 ;;\n"
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

    reinject_commands = ssh_log.read_text(encoding="utf-8")
    decoded_prompts = _decoded_reinject_prompts(reinject_commands)
    assert result.returncode == 0
    assert any("PANE 0, lane planner-recon" in prompt for prompt in decoded_prompts)
    assert not any(
        "PANE 1, lane event-variable-electron-pair-count" in prompt
        for prompt in decoded_prompts
    )


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
    decoded_prompts = _decoded_reinject_prompts(ssh_log.read_text(encoding="utf-8"))
    assert any("PANE 0" in prompt for prompt in decoded_prompts)


def test_watchdog_detects_documented_truncated_goal_command(tmp_path: Path) -> None:
    """The documented '/g<non-letter>' corruption signal should trigger recovery."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ssh_log = tmp_path / "ssh.log"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        "case \"$*\" in\n"
        "  *squeue*) echo 12345 ;;\n"
        "  *list-panes*) echo 0 ;;\n"
        "  *capture-pane*) echo '/g ' ;;\n"
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
    decoded_prompts = _decoded_reinject_prompts(ssh_log.read_text(encoding="utf-8"))
    assert any("PANE 0" in prompt for prompt in decoded_prompts)
