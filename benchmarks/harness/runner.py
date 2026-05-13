"""SLURM sbatch rendering and submission for benchmark harness jobs."""

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class RunRequest:
    """Inputs required to render one benchmark measurement sbatch script."""

    opt_id: str
    workload: str
    physics_list: str
    hw_id: str
    seeds: Sequence[int]
    vanilla_binary: Path
    optimized_binary: Path
    repo_root: Path = Path(".")
    account: str = "lu2026-2-51"
    partition: str = "lu48"
    time_limit: str = "02:00:00"
    modules: Sequence[str] = field(default_factory=lambda: ("GCC/13.2.0", "CUDA/12.8.0"))
    n_events: int | None = None


def render_sbatch(request: RunRequest) -> str:
    """Return a SLURM script that runs vanilla then optimized per seed."""

    _validate_request(request)
    raw_dir = Path("benchmarks/raw") / request.opt_id / request.workload
    lines = [
        "#!/bin/bash",
        f"#SBATCH --job-name=bench-{_slug(request.opt_id)}-{_slug(request.workload)}",
        f"#SBATCH --account={request.account}",
        f"#SBATCH --partition={request.partition}",
        f"#SBATCH --time={request.time_limit}",
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks=1",
        "#SBATCH --cpus-per-task=1",
        "",
        "set -euo pipefail",
        f"module load {' '.join(request.modules)}",
        f"cd {_q(request.repo_root)}",
        f"mkdir -p {_q(raw_dir)}",
        "",
    ]
    for seed in request.seeds:
        lines.extend(_run_lines(request, raw_dir, int(seed)))
    lines.extend(
        [
            _collect_command(request),
            "",
        ]
    )
    return "\n".join(lines)


def write_sbatch(request: RunRequest, script_path: str | Path) -> Path:
    """Write an sbatch script and mark it executable."""

    path = Path(script_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_sbatch(request))
    path.chmod(path.stat().st_mode | 0o111)
    return path


def submit_sbatch(
    script_path: str | Path,
    *,
    submit: bool,
    runner: Runner = subprocess.run,
) -> str:
    """Submit an sbatch script, or return it unchanged when `submit` is false."""

    path = Path(script_path)
    if not submit:
        return path.read_text()
    result = runner(
        ["sbatch", str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or f"sbatch failed with exit {result.returncode}")
    return result.stdout


def _validate_request(request: RunRequest) -> None:
    if not request.seeds:
        raise ValueError("at least one seed is required")
    if any(int(seed) < 0 for seed in request.seeds):
        raise ValueError("seeds must be non-negative integers")
    if not request.opt_id or not request.workload or not request.physics_list or not request.hw_id:
        raise ValueError("opt_id, workload, physics_list, and hw_id are required")


def _run_lines(request: RunRequest, raw_dir: Path, seed: int) -> list[str]:
    event_args = [] if request.n_events is None else ["--n-events", str(request.n_events)]
    common = ["--seed", str(seed), "--physics-list", request.physics_list, *event_args]
    vanilla_out = raw_dir / f"seed_{seed}_vanilla.txt"
    optimized_out = raw_dir / f"seed_{seed}_optimized.txt"
    return [
        f"{_q(request.vanilla_binary)} {_join(common)} > {_q(vanilla_out)}",
        f"{_q(request.optimized_binary)} {_join(common)} > {_q(optimized_out)}",
    ]


def _collect_command(request: RunRequest) -> str:
    seeds = ",".join(str(int(seed)) for seed in request.seeds)
    parts = [
        "python",
        "-m",
        "benchmarks.harness.run",
        "--collect",
        "--opt-id",
        request.opt_id,
        "--workload",
        request.workload,
        "--physics-list",
        request.physics_list,
        "--hw",
        request.hw_id,
        "--seeds",
        seeds,
    ]
    return _join(parts)


def _join(parts: Sequence[object]) -> str:
    return " ".join(_q(part) for part in parts)


def _q(value: object) -> str:
    return shlex.quote(os.fspath(value))


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in value)
