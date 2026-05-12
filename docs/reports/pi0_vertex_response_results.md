# π⁰ vertex-radius response results

Generated: 2026-05-12 12:38 CEST by worker-1 lane swap from `codex-tasks/recon/worker-0.txt`.

## Scope

This compact iteration transformed the eight existing local vertex-scan raw samples into reconstructed response Parquets and ran the fail-closed vertex response audit on the seven fixed-radius samples. No SLURM job, C++ build, cut retuning, or simulation generation was run.

## Generated reconstructed Parquets

| Sample | Reco Parquet | Events | Reconstructed π⁰ candidates | Efficiency | truth r range [cm] | Required schema |
| --- | --- | ---: | ---: | ---: | --- | --- |
| r=0 cm | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r0mev.parquet` | 500 | 0 | 0.000000 | 0–0 | yes |
| r=5 cm | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r5mev.parquet` | 500 | 0 | 0.000000 | 5–5 | yes |
| r=10 cm | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r10mev.parquet` | 500 | 0 | 0.000000 | 10–10 | yes |
| r=15 cm | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r15mev.parquet` | 500 | 0 | 0.000000 | 15–15 | yes |
| r=20 cm | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r20mev.parquet` | 500 | 0 | 0.000000 | 20–20 | yes |
| r=25 cm | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r25mev.parquet` | 500 | 0 | 0.000000 | 25–25 | yes |
| r=30 cm | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r30mev.parquet` | 500 | 0 | 0.000000 | 30–30 | yes |
| disk r<=30 cm | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_disk_r30.parquet` | 5000 | 0 | 0.000000 | 0.614125–29.9965 | yes |

## Audit outcome

The fixed-radius audit is **not ready**: every fixed-radius sample has zero reconstructed π⁰ candidates, so mass peak, opening-angle response, and reconstructed-energy bias are unmeasured rather than validated.

| File | Blocker code | Reason |
| --- | --- | --- |
| `pi0_reco_vertex_r0mev.parquet` | `radius_bin_no_reco` | Radius 0 cm has 500 events but zero reconstructed π⁰ candidates. |
| `pi0_reco_vertex_r5mev.parquet` | `radius_bin_no_reco` | Radius 5 cm has 500 events but zero reconstructed π⁰ candidates. |
| `pi0_reco_vertex_r10mev.parquet` | `radius_bin_no_reco` | Radius 10 cm has 500 events but zero reconstructed π⁰ candidates. |
| `pi0_reco_vertex_r15mev.parquet` | `radius_bin_no_reco` | Radius 15 cm has 500 events but zero reconstructed π⁰ candidates. |
| `pi0_reco_vertex_r20mev.parquet` | `radius_bin_no_reco` | Radius 20 cm has 500 events but zero reconstructed π⁰ candidates. |
| `pi0_reco_vertex_r25mev.parquet` | `radius_bin_no_reco` | Radius 25 cm has 500 events but zero reconstructed π⁰ candidates. |
| `pi0_reco_vertex_r30mev.parquet` | `radius_bin_no_reco` | Radius 30 cm has 500 events but zero reconstructed π⁰ candidates. |

The disk-average sample also has zero reconstructed candidates across 5000 events; it is listed above as derived evidence, but it is not treated as a discrete fixed-radius audit bin because its truth radii are continuous within the 30 cm disk.

## Verification evidence

- Reco generation wrote all eight required Parquets under `build_lunarc/output/pi0_reco_response/`.
- Required audit columns checked in each output: `truth_vertex_r_cm`, `pi0_mass_mev`, `opening_angle_deg`, `reco_total_energy_mev`.
- Focused regression tests passed after the driver/audit update: `rtk python -m pytest tests/test_pi0_reco_driver.py tests/test_pi0_vertex_response_audit.py -q`.
- Full worker verification passed: `rtk proxy bash -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'` reported 253 passed / 2 skipped.
- Queue mechanical validation passed: `rtk bash scripts/validate-csup-queues.sh` scanned 27 files / 33 prompt lines with 0 failures.
- Stop condition: fail-closed evidence report only; no reconstruction cuts or constants were changed.
