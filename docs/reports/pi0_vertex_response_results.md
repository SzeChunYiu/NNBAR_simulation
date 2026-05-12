# π⁰ vertex response reconstruction results

- Generated: 2026-05-12T12:38:01 local time
- Task: `docs/parallel-sessions/pi0-reco-on-vertex-scan.md`
- Constraint evidence: no SLURM submission was run; this local Python transform only read `build_lunarc/output/studies/*` and wrote `build_lunarc/output/pi0_reco_response/*` plus this report.

## Input/output inventory

| raw sample | truth rows | lead-glass hits | scintillator hits | output | rows | candidate events | radius range cm | required columns |
|---|---:|---:|---:|---|---:|---:|---:|---|
| `pi0_vertex_scan_r0mev` | 500 | 1839719 | 255298 | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r0mev.parquet` | 500 | 0 | 0.000 | OK |
| `pi0_vertex_scan_r5mev` | 500 | 1834745 | 247504 | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r5mev.parquet` | 500 | 0 | 5.000 | OK |
| `pi0_vertex_scan_r10mev` | 500 | 1795443 | 252969 | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r10mev.parquet` | 500 | 0 | 10.000 | OK |
| `pi0_vertex_scan_r15mev` | 500 | 1834910 | 268600 | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r15mev.parquet` | 500 | 0 | 15.000 | OK |
| `pi0_vertex_scan_r20mev` | 500 | 1857803 | 255052 | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r20mev.parquet` | 500 | 0 | 20.000 | OK |
| `pi0_vertex_scan_r25mev` | 500 | 1878988 | 251671 | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r25mev.parquet` | 500 | 0 | 25.000 | OK |
| `pi0_vertex_scan_r30mev` | 500 | 1846981 | 262336 | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r30mev.parquet` | 500 | 0 | 30.000 | OK |
| `pi0_vertex_disk_r30` | 5000 | 18888787 | 2574132 | `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_disk_r30.parquet` | 5000 | 0 | 0.614–29.997 | OK |

Aggregate fixed-radius audit input: `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_scan_150mev.parquet` (3500 rows).

## Fixed-radius audit (`pi0_vertex_response_audit`)

- Ready: `True`
- Total events: 3500
- Blockers: none

| truth radius cm | events | reconstructed | efficiency | mass peak MeV | mass sigma MeV | opening angle mean deg | energy bias fraction |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 500 | 0 | 0.0000 | n/a | n/a | n/a | n/a |
| 5 | 500 | 0 | 0.0000 | n/a | n/a | n/a | n/a |
| 10 | 500 | 0 | 0.0000 | n/a | n/a | n/a | n/a |
| 15 | 500 | 0 | 0.0000 | n/a | n/a | n/a | n/a |
| 20 | 500 | 0 | 0.0000 | n/a | n/a | n/a | n/a |
| 25 | 500 | 0 | 0.0000 | n/a | n/a | n/a | n/a |
| 30 | 500 | 0 | 0.0000 | n/a | n/a | n/a | n/a |

## Disk-r30 auxiliary sample

- Rows: 5000
- Radius range: 0.614–29.997 cm
- Candidate events: 0 (efficiency 0.0000)
- Median candidate mass: n/a MeV

## Interpretation

The reconstruction/audit handoff is mechanically complete: all required raw
samples were read, all eight requested vertex-response Parquets were written,
the fixed-radius aggregate contains the seven required `truth_vertex_r_cm` bins,
and `pi0_vertex_response_audit` reports no schema/bin blockers. The physics
result is still fail-closed for promotion: the current neutral-object cuts
produce zero π⁰ candidates in every vertex-scan and disk event, so there are no
mass-peak, mass-width, opening-angle, or energy-bias curves to quote beyond the
explicit zero-efficiency table above.

## Verification run

- Output schema/row check: `PI0_VERTEX_RECO_OUTPUTS_OK` across 9
  `pi0_reco_vertex_*.parquet` files (8 requested outputs plus the fixed-radius
  aggregate).
- Focused tests:
  `rtk proxy python -m pytest tests/test_pi0_reco_driver.py tests/test_pi0_vertex_response_audit.py -q`
  → 11 passed.
- Worker full test command:
  `rtk proxy bash -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'`
  → 253 passed, 2 skipped.
- Queue validator:
  `rtk bash scripts/validate-csup-queues.sh` → 27 files scanned, 33 prompt
  lines checked, 0 failures.
- File sizes:
  `docs/parallel-sessions/pi0-reco-on-vertex-scan.md` = 61 lines;
  `docs/reports/pi0_vertex_response_results.md` = 91 lines.

## Verification to rerun

```bash
rtk proxy python - <<'PY'
from pathlib import Path
import pandas as pd
required = ['Event_ID', 'truth_vertex_x_cm', 'truth_vertex_y_cm', 'truth_vertex_z_cm', 'truth_vertex_r_cm', 'truth_ke_mev', 'truth_total_energy_mev', 'n_neutral_objects', 'n_pi0_candidates', 'pi0_mass_mev', 'opening_angle_deg', 'reco_photon_energy_mev', 'truth_photon_energy_mev', 'reco_total_energy_mev', 'reco_eff_flag']
out = Path("build_lunarc/output/pi0_reco_response")
for path in sorted(out.glob("pi0_reco_vertex_*.parquet")):
    frame = pd.read_parquet(path)
    missing = [col for col in required if col not in frame.columns]
    assert not missing, (path, missing)
    assert len(frame) > 0, path
print("PI0_VERTEX_RECO_OUTPUTS_OK")
PY
rtk proxy python -m pytest tests/test_pi0_reco_driver.py tests/test_pi0_vertex_response_audit.py -q
rtk proxy bash -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"
```
