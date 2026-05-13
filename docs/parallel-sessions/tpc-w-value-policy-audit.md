# Lane: tpc-w-value-policy-audit

## Goal

Make the TPC ionization W-value policy explicit and testable in Python without
changing simulation output. The current samples/config use a 23.6 eV production
conversion, while thesis/reference material discusses 26.0--27.4 eV alternatives;
this lane should expose that policy and the reference-scale factors as data.

## Writable scope

- Create: `nnbar_reconstruction/analysis/tpc_w_value_policy.py`
- Create: `tests/test_tpc_w_value_policy.py`
- Modify only for status updates: `docs/parallel-sessions/MASTER_PLAN.md`

Forbidden:

- Do not edit `nnbar_reconstruction/calibration/tpc_calibration.py`; it is over
  the 500-line cap and needs a separate split before feature edits.
- Do not edit C++ source (`NNBAR_Detector/**`) in this Python lane.
- Do not change the production W-value from 23.6 eV unless a separate DEC and
  simulation/data migration task are created.

## Required reading

- `docs/parallel-sessions.md`
- `docs/parallel-sessions/MASTER_PLAN.md`
- `CODING_STANDARDS.md`
- `docs/rebuild_plans/17_field_calibration.md` §3
- `docs/rebuild_plans/45_systematics_taxonomy.md` row N1
- `docs/parallel-sessions/tpc-dedx-electrons.md`

## One-iteration cycle

1. Claim the lane by changing the MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that one-line change.
2. Verify the existing file-cap constraint before touching anything:
   ```bash
   rtk proxy wc -l nnbar_reconstruction/calibration/tpc_calibration.py
   ```
   If it is still over 500 lines, keep it read-only.
3. Create `nnbar_reconstruction/analysis/tpc_w_value_policy.py` with:
   - dataclasses or named tuples for production, lower-reference, and
     upper-reference W-values;
   - constants: production 23.6 eV, lower reference 26.0 eV, upper reference
     27.4 eV, all sourced to plan 17/45 comments;
   - a pure function returning electron-count scale factors
     `production_w_value / reference_w_value`;
   - an audit function that loads `nnbar_geometry.yaml` with the existing config
     loader and reports whether the config production value matches 23.6 eV;
   - no absolute local paths.
4. Add `tests/test_tpc_w_value_policy.py` covering:
   - production value stays 23.6 eV;
   - 26.0 and 27.4 eV scale factors are below one and numerically correct;
   - the default config reports a production match;
   - a toy config with 27.4 eV reports a production mismatch but a reference
     match.
5. Verification:
   ```bash
   rtk python -m pytest tests/test_tpc_w_value_policy.py -q
   rtk proxy zsh -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"
   rtk proxy wc -l nnbar_reconstruction/analysis/tpc_w_value_policy.py      tests/test_tpc_w_value_policy.py
   ```
6. Mark the MASTER_PLAN row `DONE` only after focused/full pytest and file-cap
   checks pass.

## Stop condition

Stop after the policy module/tests are committed and the MASTER_PLAN row is
`DONE`, or after recording a concrete blocker if the current config loader cannot
be used without violating the file-cap/read-only constraints.
