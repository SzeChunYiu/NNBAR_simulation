# OpenMC remote CE validation gate preservation — 2026-05-17

Factory item: `mcaccel-openmc-adapter` RUNNING acceptance gap / TEAM_PLAN A1 evidence hygiene.
Blocker queue checked: `codex-tasks/blockers.txt`, `codex-tasks/g4gpu/blockers.txt`, `codex-tasks/meta/blockers.txt`, `codex-tasks/recon/blockers.txt`, `codex-tasks/review/blockers.txt`, and `codex-tasks/sim/blockers.txt` contain no un-commented `/goal` blocker lines claimable by worker-0.

## Role and lease

- Role type: specialist-contractor (`worker-0`, C++/GPU/LUNARC worker).
- Manager / escalation: VALIDATOR via `docs/parallel-sessions/TEAM_PLAN.md`.
- Decision rights: preserve LUNARC adapter evidence inside the already-running `mcaccel-openmc-adapter` lane; no promotion, speedup, parity, or paper-table claims.
- Branch/worktree: LUNARC `/projects/hep/fs10/shared/nnbar/billy/geant4-gpu-openmc-adapter`, branch `lane/mcaccel-openmc-adapter`.
- Writable lease used: `adapters/openmc/validation/ce_data_smoke_20260512.md` in the isolated adapter checkout, plus this coordination report.

## Change

The LUNARC adapter checkout had one untracked validation document:
`adapters/openmc/validation/ce_data_smoke_20260512.md`. Its previous contents had shell-expanded placeholders, leaving the OpenMC binary, cross-section XML, run directory, output files, and `RUNNING` disposition blank.

This iteration rewrote that document with concrete evidence from `docs/reports/openmc_ce_data_staging_20260512.md` and committed it in the adapter checkout:

```text
d271966 docs(openmc): preserve CE smoke validation gate
```

## Verification evidence

Remote checks run after the rewrite and before the commit:

```text
test -x /projects/hep/fs10/shared/nnbar/billy/openmc/build-lunarc/bin/openmc
test -f /projects/hep/fs10/shared/nnbar/billy/openmc-data/nndc_hdf5/cross_sections.xml
test -d /projects/hep/fs10/shared/nnbar/billy/openmc-ce-data-verify-worker0-20260512T135823+0200
python3 scripts/verify_openmc_adapter_scaffold.py
# OPENMC_ADAPTER_SCAFFOLD_OK
test $(wc -l < adapters/openmc/validation/ce_data_smoke_20260512.md) -le 500
git diff --check -- adapters/openmc/validation/ce_data_smoke_20260512.md
```

Post-commit status:

```text
## lane/mcaccel-openmc-adapter
```

## Disposition

Keep `mcaccel-openmc-adapter` RUNNING/OPEN. The committed CE document is reduced-smoke evidence only. It does not implement Iteration-3 QMC/RNG, create canonical OpenMC `results.parquet`/`manifest.json`, approve multi-temperature CE coverage, validate Geant4/OpenMC cross-code RNG behavior, or authorize any speedup/parity claim.
