"""CMake build helpers for benchmark harness reference and optimized builds."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Callable, Sequence


Runner = Callable[..., subprocess.CompletedProcess[str]]


class BuildError(RuntimeError):
    """Raised when a benchmark build is unusable."""


def build_vanilla(
    geant4_prefix: str | Path,
    workload: str,
    output_dir: str | Path,
    *,
    source_dir: str | Path = ".",
    log_dir: str | Path = "benchmarks/build_logs",
    opt_id: str = "vanilla",
    hw_id: str = "local",
    cmake_flags: str | Sequence[str] = (),
    binary_name: str | None = None,
    target: str | None = None,
    runner: Runner = subprocess.run,
) -> Path:
    """Configure and build the vanilla Geant4 benchmark tree.

    The returned path is the CMake build directory. A `BuildError` is raised if
    any command fails, the combined log contains `Error`, or the expected binary
    is missing.
    """

    build_path = Path(output_dir) / opt_id / workload
    commands = [
        _cmake_configure_command(geant4_prefix, source_dir, build_path, cmake_flags),
        _cmake_build_command(build_path, target or binary_name or workload),
    ]
    _run_commands(commands, log_dir=log_dir, opt_id=opt_id, hw_id=hw_id, runner=runner)
    _assert_usable_build(build_path, binary_name or workload, log_dir, opt_id, hw_id)
    return build_path


def build_optimized(
    geant4_prefix: str | Path,
    opt_branch: str,
    cmake_flags: str | Sequence[str],
    workload: str,
    output_dir: str | Path,
    *,
    source_dir: str | Path = ".",
    log_dir: str | Path = "benchmarks/build_logs",
    opt_id: str | None = None,
    hw_id: str = "local",
    binary_name: str | None = None,
    target: str | None = None,
    runner: Runner = subprocess.run,
) -> Path:
    """Checkout, configure, and build an optimized benchmark branch."""

    resolved_opt_id = opt_id or _safe_branch_id(opt_branch)
    build_path = Path(output_dir) / resolved_opt_id / workload
    commands = [
        ["git", "-C", str(Path(source_dir)), "checkout", opt_branch],
        _cmake_configure_command(geant4_prefix, source_dir, build_path, cmake_flags),
        _cmake_build_command(build_path, target or binary_name or workload),
    ]
    _run_commands(
        commands,
        log_dir=log_dir,
        opt_id=resolved_opt_id,
        hw_id=hw_id,
        runner=runner,
    )
    _assert_usable_build(
        build_path,
        binary_name or workload,
        log_dir,
        resolved_opt_id,
        hw_id,
    )
    return build_path


def _cmake_configure_command(
    geant4_prefix: str | Path,
    source_dir: str | Path,
    build_path: Path,
    cmake_flags: str | Sequence[str],
) -> list[str]:
    return [
        "cmake",
        "-S",
        str(Path(source_dir)),
        "-B",
        str(build_path),
        f"-DCMAKE_PREFIX_PATH={Path(geant4_prefix)}",
        *_split_flags(cmake_flags),
    ]


def _cmake_build_command(build_path: Path, target: str) -> list[str]:
    return ["cmake", "--build", str(build_path), "--target", target, "-j", "8"]


def _split_flags(cmake_flags: str | Sequence[str]) -> list[str]:
    if isinstance(cmake_flags, str):
        return shlex.split(cmake_flags)
    return [str(flag) for flag in cmake_flags]


def _run_commands(
    commands: Sequence[Sequence[str]],
    *,
    log_dir: str | Path,
    opt_id: str,
    hw_id: str,
    runner: Runner,
) -> None:
    log_path = _log_path(log_dir, opt_id, hw_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    for command in commands:
        command_text = " ".join(shlex.quote(str(part)) for part in command)
        chunks.append(f"$ {command_text}\n")
        result = runner(
            [str(part) for part in command],
            text=True,
            capture_output=True,
            check=False,
        )
        chunks.append(result.stdout or "")
        chunks.append(result.stderr or "")
        if result.returncode != 0:
            log_path.write_text("".join(chunks))
            raise BuildError(f"build command failed with exit {result.returncode}: {command_text}")
    log_path.write_text("".join(chunks))


def _assert_usable_build(
    build_path: Path,
    binary_name: str,
    log_dir: str | Path,
    opt_id: str,
    hw_id: str,
) -> None:
    log_text = _log_path(log_dir, opt_id, hw_id).read_text()
    if "Error" in log_text:
        raise BuildError("build log contains `Error`; refusing to use this build")
    if not _binary_exists(build_path, binary_name):
        raise BuildError(f"expected binary is absent after build: {binary_name}")


def _binary_exists(build_path: Path, binary_name: str) -> bool:
    return any(
        candidate.exists()
        for candidate in (build_path / binary_name, build_path / "bin" / binary_name)
    )


def _log_path(log_dir: str | Path, opt_id: str, hw_id: str) -> Path:
    return Path(log_dir) / f"{opt_id}_{hw_id}.txt"


def _safe_branch_id(branch: str) -> str:
    return branch.replace("/", "_").replace(" ", "_")
