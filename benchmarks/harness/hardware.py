"""Hardware fingerprinting helpers for benchmark-harness evidence.

The functions in this module are deliberately local-safe: tests can inject
mocked ``/proc/cpuinfo`` text, ``nvidia-smi`` CSV text, and SLURM environment
variables without touching the host.  Production collection uses those same
parsers against the live LUNARC job environment.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence


NVIDIA_SMI_QUERY = (
    "nvidia-smi",
    "--query-gpu=name,driver_version,memory.total",
    "--format=csv,noheader,nounits",
)
SLURM_KEYS = (
    "SLURM_JOB_ID",
    "SLURM_JOB_NAME",
    "SLURM_JOB_PARTITION",
    "SLURM_JOB_NODELIST",
    "SLURM_CPUS_PER_TASK",
    "SLURM_NTASKS",
    "SLURM_GPUS",
    "SLURM_JOB_GPUS",
    "SLURM_MEM_PER_NODE",
)
Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class GpuFingerprint:
    """One GPU row parsed from ``nvidia-smi`` CSV output."""

    name: str
    driver_version: str
    memory_mib: int | None


@dataclass(frozen=True)
class HardwareFingerprint:
    """Benchmark hardware evidence for one harness hardware ID."""

    hw_id: str
    cpu_model: str
    logical_cpus: int
    gpus: tuple[GpuFingerprint, ...]
    slurm: dict[str, str]
    nvidia_smi_available: bool

    def to_record(self) -> dict[str, object]:
        """Return a JSON-serialisable record for future Parquet integration."""

        return {
            "hw_id": self.hw_id,
            "cpu_model": self.cpu_model,
            "logical_cpus": self.logical_cpus,
            "gpus": [
                {
                    "name": gpu.name,
                    "driver_version": gpu.driver_version,
                    "memory_mib": gpu.memory_mib,
                }
                for gpu in self.gpus
            ],
            "slurm": dict(self.slurm),
            "nvidia_smi_available": self.nvidia_smi_available,
        }


def collect_fingerprint(
    hw_id: str,
    *,
    cpuinfo_path: str | Path = "/proc/cpuinfo",
    env: Mapping[str, str] | None = None,
    nvidia_smi_cmd: Sequence[str] = NVIDIA_SMI_QUERY,
    runner: Runner = subprocess.run,
) -> HardwareFingerprint:
    """Collect a hardware fingerprint from local CPU/GPU/SLURM sources."""

    cpuinfo_text = Path(cpuinfo_path).read_text(errors="replace")
    nvidia_smi_csv = _run_nvidia_smi(nvidia_smi_cmd, runner=runner)
    return fingerprint_from_sources(
        hw_id,
        cpuinfo_text=cpuinfo_text,
        nvidia_smi_csv=nvidia_smi_csv,
        env=os.environ if env is None else env,
    )


def fingerprint_from_sources(
    hw_id: str,
    *,
    cpuinfo_text: str,
    nvidia_smi_csv: str | None,
    env: Mapping[str, str],
) -> HardwareFingerprint:
    """Build a fingerprint from injected source text and environment values."""

    if not hw_id:
        raise ValueError("hw_id must be non-empty")
    cpu_model, logical_cpus = _parse_cpuinfo(cpuinfo_text)
    gpus = tuple(_parse_nvidia_smi_csv(nvidia_smi_csv or ""))
    return HardwareFingerprint(
        hw_id=hw_id,
        cpu_model=cpu_model,
        logical_cpus=logical_cpus,
        gpus=gpus,
        slurm=_slurm_env(env),
        nvidia_smi_available=nvidia_smi_csv is not None,
    )


def hardware_evidence_text(fingerprint: HardwareFingerprint) -> str:
    """Render a stable text artifact for ``benchmarks/hardware_evidence/``."""

    lines = [
        f"hw_id: {fingerprint.hw_id}",
        f"cpu_model: {fingerprint.cpu_model}",
        f"logical_cpus: {fingerprint.logical_cpus}",
        f"nvidia_smi_available: {fingerprint.nvidia_smi_available}",
    ]
    if fingerprint.gpus:
        for index, gpu in enumerate(fingerprint.gpus):
            memory = "unknown" if gpu.memory_mib is None else str(gpu.memory_mib)
            lines.append(
                f"gpu[{index}]: {gpu.name}, driver={gpu.driver_version}, memory_mib={memory}"
            )
    else:
        lines.append("gpu: none")
    if fingerprint.slurm:
        lines.append("slurm:")
        lines.extend(f"  {key}={value}" for key, value in sorted(fingerprint.slurm.items()))
    else:
        lines.append("slurm: none")
    return "\n".join(lines) + "\n"


def write_hardware_evidence(fingerprint: HardwareFingerprint, path: str | Path) -> Path:
    """Write a hardware evidence artifact and return its path."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(hardware_evidence_text(fingerprint))
    return output


def _parse_cpuinfo(cpuinfo_text: str) -> tuple[str, int]:
    model = "unknown"
    logical_cpus = 0
    for line in cpuinfo_text.splitlines():
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if key == "processor":
            logical_cpus += 1
        elif key in {"model name", "Hardware", "Processor"} and model == "unknown":
            model = value
    if logical_cpus == 0:
        logical_cpus = os.cpu_count() or 1
    return model, logical_cpus


def _parse_nvidia_smi_csv(text: str) -> list[GpuFingerprint]:
    gpus: list[GpuFingerprint] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        name = parts[0] if parts else "unknown"
        driver = parts[1] if len(parts) > 1 else "unknown"
        memory = _parse_memory_mib(parts[2]) if len(parts) > 2 else None
        gpus.append(GpuFingerprint(name=name, driver_version=driver, memory_mib=memory))
    return gpus


def _parse_memory_mib(value: str) -> int | None:
    token = value.strip().split()[0] if value.strip() else ""
    try:
        return int(token)
    except ValueError:
        return None


def _slurm_env(env: Mapping[str, str]) -> dict[str, str]:
    return {key: str(env[key]) for key in SLURM_KEYS if env.get(key)}


def _run_nvidia_smi(command: Sequence[str], *, runner: Runner = subprocess.run) -> str | None:
    try:
        result = runner(
            list(command),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout
