import os
import subprocess
from pathlib import Path

import pytest


def test_build_vanilla_writes_log_and_rejects_absent_binary(tmp_path):
    from benchmarks.harness.builder import BuildError, build_vanilla

    calls: list[list[str]] = []

    def fake_run(cmd, *, cwd=None, text=True, capture_output=True, check=False):
        calls.append([str(part) for part in cmd])
        if cmd[:2] == ["cmake", "--build"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="built\n", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="configured\n", stderr="")

    with pytest.raises(BuildError, match="binary is absent"):
        build_vanilla(
            geant4_prefix=tmp_path / "geant4",
            workload="TestEm0",
            output_dir=tmp_path / "builds",
            source_dir=tmp_path / "src",
            log_dir=tmp_path / "logs",
            runner=fake_run,
        )

    log_text = (tmp_path / "logs" / "vanilla_local.txt").read_text()
    assert "configured" in log_text
    assert "built" in log_text
    assert calls[0][:3] == ["cmake", "-S", str(tmp_path / "src")]
    assert calls[1][:3] == ["cmake", "--build", str(tmp_path / "builds" / "vanilla" / "TestEm0")]


def test_build_optimized_uses_branch_flags_and_returns_existing_binary(tmp_path):
    from benchmarks.harness.builder import build_optimized

    calls: list[list[str]] = []

    def fake_run(cmd, *, cwd=None, text=True, capture_output=True, check=False):
        calls.append([str(part) for part in cmd])
        if cmd[:2] == ["cmake", "--build"]:
            bin_dir = tmp_path / "builds" / "BD-geant4-032" / "W1" / "bin"
            bin_dir.mkdir(parents=True)
            (bin_dir / "benchmark_driver").write_text("#!/bin/sh\n")
        return subprocess.CompletedProcess(cmd, 0, stdout="ok\n", stderr="")

    build_path = build_optimized(
        geant4_prefix=tmp_path / "geant4",
        opt_branch="lane/bd-geant4-032",
        cmake_flags="-DG4GPU_BD032=ON -DCMAKE_BUILD_TYPE=Release",
        workload="W1",
        output_dir=tmp_path / "builds",
        source_dir=tmp_path / "src",
        log_dir=tmp_path / "logs",
        opt_id="BD-geant4-032",
        binary_name="benchmark_driver",
        runner=fake_run,
    )

    assert build_path == tmp_path / "builds" / "BD-geant4-032" / "W1"
    assert calls[0] == ["git", "-C", str(tmp_path / "src"), "checkout", "lane/bd-geant4-032"]
    configure = calls[1]
    assert "-DG4GPU_BD032=ON" in configure
    assert "-DCMAKE_BUILD_TYPE=Release" in configure
    assert (tmp_path / "logs" / "BD-geant4-032_local.txt").exists()


def test_build_fails_when_combined_log_contains_error(tmp_path):
    from benchmarks.harness.builder import BuildError, build_vanilla

    def fake_run(cmd, *, cwd=None, text=True, capture_output=True, check=False):
        if cmd[:2] == ["cmake", "--build"]:
            bin_dir = tmp_path / "builds" / "vanilla" / "W1" / "bin"
            bin_dir.mkdir(parents=True)
            (bin_dir / "W1").write_text("#!/bin/sh\n")
            return subprocess.CompletedProcess(cmd, 0, stdout="Error: stale object\n", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="configured\n", stderr="")

    with pytest.raises(BuildError, match="build log contains"):
        build_vanilla(
            geant4_prefix=tmp_path / "geant4",
            workload="W1",
            output_dir=tmp_path / "builds",
            source_dir=tmp_path / "src",
            log_dir=tmp_path / "logs",
            runner=fake_run,
        )


def test_runner_writes_lunarc_sbatch_that_bash_accepts(tmp_path):
    from benchmarks.harness.runner import RunRequest, write_sbatch

    request = RunRequest(
        opt_id="BD-geant4-032",
        workload="W1",
        physics_list="PL1",
        hw_id="H3",
        seeds=[11, 22],
        vanilla_binary=Path("/build/vanilla/bin/W1"),
        optimized_binary=Path("/build/opt/bin/W1"),
        repo_root=tmp_path,
    )

    script_path = write_sbatch(request, tmp_path / "bench.sbatch")

    result = subprocess.run(["bash", "-n", str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    text = script_path.read_text()
    assert "#SBATCH --account=lu2026-2-51" in text
    assert "module load GCC/13.2.0 CUDA/12.8.0" in text
    assert "benchmarks/raw/BD-geant4-032/W1/seed_11_vanilla.txt" in text
    assert "benchmarks/raw/BD-geant4-032/W1/seed_22_optimized.txt" in text
    assert "python -m benchmarks.harness.run --collect" in text
    assert "--physics-list PL1" in text


def test_submit_sbatch_dry_run_returns_script_without_calling_sbatch(tmp_path):
    from benchmarks.harness.runner import RunRequest, submit_sbatch, write_sbatch

    request = RunRequest(
        opt_id="dry",
        workload="W2",
        physics_list="PL2",
        hw_id="H3",
        seeds=[1],
        vanilla_binary=Path("/build/vanilla/bin/W2"),
        optimized_binary=Path("/build/opt/bin/W2"),
        repo_root=tmp_path,
    )
    script_path = write_sbatch(request, tmp_path / "dry.sbatch")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("dry run must not invoke sbatch")

    script_text = submit_sbatch(script_path, submit=False, runner=fail_if_called)

    assert script_text.startswith("#!/bin/bash")
    assert os.fspath(script_path) not in script_text
