# Lane: pi0-reco-audit-run

## Goal

Run the newly implemented π⁰ reconstruction driver on the already-staged
mono-π⁰ raw samples, then run the neutral-object/π⁰ response audit and update
`docs/parallel-sessions/MASTER_PLAN.md` with the real outcome.

This is a data/evidence closure lane only. Do not change reconstruction
algorithms, cuts, C++, macros, SLURM scripts, or detector constants.

## Required reading

- `docs/parallel-sessions.md`
- `docs/parallel-sessions/MASTER_PLAN.md`
- `docs/parallel-sessions/pi0-reco-driver.md`
- `docs/parallel-sessions/neutral-object-pi0-mass-response.md`
- `CODING_STANDARDS.md`

## Writable scope

- `docs/parallel-sessions/MASTER_PLAN.md` (status/evidence rows only)
- Optional handoff note under `docs/reports/` if the audit output is too long
  for the MASTER_PLAN row

Generated Parquet files under `build_lunarc/output/pi0_reco_response/` are local
derived evidence outputs. Do not commit generated Parquet data unless a later
operator explicitly asks for data versioning.

## Read-only inputs

- `build_lunarc/output/pi0_mono_50mev/`
- `build_lunarc/output/pi0_mono_150mev/`
- `build_lunarc/output/pi0_mono_250mev/`
- `nnbar_reconstruction/analysis/pi0_reco_driver.py`
- `nnbar_reconstruction/analysis/neutral_pi0_response_audit.py`
- `tests/test_pi0_reco_driver.py`

## One-iteration steps

1. Re-run the focused driver test to confirm the committed driver still works.
2. Verify the three raw sample directories and their `Particle_output_0.parquet`,
   `LeadGlass_output_0.parquet`, and `Scintillator_output_0.parquet` files exist.
3. Run the driver on existing local raw samples only:
   ```bash
   rtk proxy python - <<'PY'
   from nnbar_reconstruction.analysis.pi0_reco_driver import run_pi0_reco
   print(run_pi0_reco('build_lunarc/output', 'build_lunarc/output/pi0_reco_response'))
   PY
   ```
4. Verify exactly three `pi0_reco_{50,150,250}mev.parquet` outputs were written
   and each has the required audit columns and expected row count from the raw
   sample count.
5. Run the neutral-object/π⁰ audit on `build_lunarc/output`.
6. Update the MASTER_PLAN row `Neutral-object and single-π⁰ response validation`:
   - `DONE` only if all three audit results are ready and source-backed.
   - `BLOCKED` with exact blocker codes and file evidence if any energy fails.
7. Commit only the MASTER_PLAN/status report changes. Do not commit generated
   Parquet outputs.

## Verification commands

```bash
rtk python -m pytest tests/test_pi0_reco_driver.py -q
rtk proxy python - <<'PY'
from pathlib import Path
import pandas as pd
required = {'pi0_mass_mev', 'opening_angle_deg', 'reco_photon_energy_mev', 'truth_photon_energy_mev'}
for energy in (50, 150, 250):
    raw = Path(f'build_lunarc/output/pi0_mono_{energy}mev/Particle_output_0.parquet')
    reco = Path(f'build_lunarc/output/pi0_reco_response/pi0_reco_{energy}mev.parquet')
    raw_rows = len(pd.read_parquet(raw))
    frame = pd.read_parquet(reco)
    missing = required - set(frame.columns)
    if missing or len(frame) != raw_rows:
        raise SystemExit(f'{energy} MeV invalid: rows {len(frame)}/{raw_rows}, missing {sorted(missing)}')
print('PI0_RECO_OUTPUTS_OK')
PY
rtk proxy python - <<'PY'
from nnbar_reconstruction.analysis.neutral_pi0_response_audit import run_audit
for result in run_audit('build_lunarc/output'):
    print(result)
PY
rtk proxy bash -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
```

## Stop condition

Stop after one evidence pass and MASTER_PLAN update. If the audit fails, do not
retune thresholds or edit production code in this lane; record exact blockers and
queue a follow-up spec if needed.
