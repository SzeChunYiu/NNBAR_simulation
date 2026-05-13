# Lane: config-portability

## Goal

Make the reconstruction configuration loader portable after the Ch.9 cutflow
integration added `nnbar_reconstruction/utils/config.py`. The loader must find
the package/repo config without machine-specific absolute paths.

## Scope

Pane 1 / Python infrastructure only.

Writable files:
- `nnbar_reconstruction/utils/config.py`
- focused config tests under `tests/`
- `docs/parallel-sessions/MASTER_PLAN.md` only for final status

Do not change physics constants, detector dimensions, C++, CUDA, SLURM, or
LUNARC jobs in this lane. Physics-value mismatches belong to separate thesis
alignment tasks already listed in `MASTER_PLAN.md`.

## Required reading

- `docs/parallel-sessions/MASTER_PLAN.md`
- `docs/parallel-sessions/planner.md` review checklist
- `nnbar_reconstruction/utils/config.py`
- `nnbar_reconstruction/config/nnbar_geometry.yaml`

## Required changes

1. Remove hardcoded local fallbacks such as `/home/billy/nnbar/...` from
   `get_default_config_path()`.
2. Keep repo/package-relative discovery working for the committed
   `nnbar_reconstruction/config/nnbar_geometry.yaml`.
3. If an override mechanism is useful, make it explicit (for example an
   environment variable) and document/test it.
4. Add focused pytest coverage for:
   - default config discovery from this checkout,
   - explicit config path loading,
   - missing explicit path raising `FileNotFoundError`,
   - no machine-specific absolute paths in the default candidate list.

## Verification

Run:

```bash
python -m pytest tests/test_config.py tests/test_ch9_cutflow_integration.py -q
python -m pytest tests/ -x -q
```

## Stop condition

Stop when hardcoded local config fallback paths are gone, focused/full tests pass,
`MASTER_PLAN.md` marks this lane `DONE`, and changes are committed.

Handoff format:

```text
DONE: config-portability
Files changed: ...
Verification: ...
Notes/blockers: ...
```
