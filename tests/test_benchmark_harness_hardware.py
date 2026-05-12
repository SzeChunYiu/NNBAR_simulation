import subprocess

from benchmarks.harness.hardware import collect_fingerprint, fingerprint_from_sources, hardware_evidence_text


CPUINFO = """\
processor   : 0
vendor_id   : GenuineIntel
model name  : Intel(R) Xeon(R) Gold 6338 CPU @ 2.00GHz

processor   : 1
vendor_id   : GenuineIntel
model name  : Intel(R) Xeon(R) Gold 6338 CPU @ 2.00GHz
"""


NVIDIA_SMI = """\
NVIDIA A40, 535.161.08, 46068 MiB
NVIDIA A40, 535.161.08, 46068 MiB
"""


def test_fingerprint_from_mocked_cpu_gpu_and_slurm_sources():
    fingerprint = fingerprint_from_sources(
        "H3",
        cpuinfo_text=CPUINFO,
        nvidia_smi_csv=NVIDIA_SMI,
        env={
            "SLURM_JOB_ID": "3047999",
            "SLURM_JOB_PARTITION": "gpua40",
            "SLURM_JOB_NODELIST": "cg14",
            "SLURM_CPUS_PER_TASK": "8",
            "SLURM_GPUS": "2",
        },
    )

    assert fingerprint.hw_id == "H3"
    assert fingerprint.cpu_model == "Intel(R) Xeon(R) Gold 6338 CPU @ 2.00GHz"
    assert fingerprint.logical_cpus == 2
    assert [gpu.name for gpu in fingerprint.gpus] == ["NVIDIA A40", "NVIDIA A40"]
    assert fingerprint.gpus[0].driver_version == "535.161.08"
    assert fingerprint.gpus[0].memory_mib == 46068
    assert fingerprint.slurm["SLURM_JOB_ID"] == "3047999"
    assert fingerprint.slurm["SLURM_JOB_PARTITION"] == "gpua40"

    evidence = hardware_evidence_text(fingerprint)
    assert "hw_id: H3" in evidence
    assert "logical_cpus: 2" in evidence
    assert "gpu[0]: NVIDIA A40, driver=535.161.08, memory_mib=46068" in evidence
    assert "SLURM_JOB_NODELIST=cg14" in evidence


def test_collect_fingerprint_reads_cpuinfo_and_injected_nvidia_smi(tmp_path):
    cpuinfo = tmp_path / "cpuinfo"
    cpuinfo.write_text(CPUINFO)
    calls = []

    def fake_run(cmd, *, text=True, capture_output=True, check=False):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=NVIDIA_SMI, stderr="")

    fingerprint = collect_fingerprint(
        "H3",
        cpuinfo_path=cpuinfo,
        env={"SLURM_JOB_ID": "3048000"},
        nvidia_smi_cmd=("mock-nvidia-smi", "--csv"),
        runner=fake_run,
    )

    assert calls == [["mock-nvidia-smi", "--csv"]]
    assert fingerprint.logical_cpus == 2
    assert len(fingerprint.gpus) == 2
    assert fingerprint.slurm["SLURM_JOB_ID"] == "3048000"
