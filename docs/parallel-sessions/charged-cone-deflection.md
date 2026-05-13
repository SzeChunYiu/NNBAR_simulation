# Lane: charged-cone-deflection

## Goal

Validate the thesis Ch. 7 charged-object 25 degree hit-collection cone and the
beampipe multiple-scattering deflection evidence without promoting unsupported
numbers. This is a fail-closed audit/closure task: if the scan artifacts or
thesis inputs are absent, emit explicit blockers instead of inventing values.

## Files

- Create: `nnbar_reconstruction/analysis/charged_cone_deflection.py`
- Test: `tests/test_charged_cone_deflection.py`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only
- Read-only references:
  - `nnbar_reconstruction/reconstruction/object_identification.py`
  - `docs/rebuild_plans/24_reconstruction_question_tree/24_3_charged.md`
  - `docs/rebuild_plans/29_subsystem_charged_pid.md`

Do not edit C++ or run simulations/SLURM jobs.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, and `CODING_STANDARDS.md`.
2. Check touched file sizes before editing; split instead of pushing any file
over 500 lines.
3. Write a failing test with toy audit inputs proving:
   - canonical charged cone angle is 25 degrees;
   - allowed scan range covers 5--85 degrees;
   - missing scan artifact, missing beampipe-deflection artifact, or missing
     DEC/provenance creates blockers;
   - a toy complete evidence package is marked ready.
4. Implement minimal immutable records/helpers in
   `charged_cone_deflection.py`; keep it independent of unavailable data.
5. Add a helper that inspects the current object-identification text/config and
   reports whether `cone_angle=25.0` is present; do not change production
   defaults in this task.
6. If real thesis scan artifacts are not present in the repo, leave blockers
   naming the needed sample, observable, and figure of merit.
7. Update `MASTER_PLAN.md` with DONE only after verification; otherwise keep a
   precise blocker note.

## Verification

Run:

```bash
rtk python -m pytest tests/test_charged_cone_deflection.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/charged_cone_deflection.py tests/test_charged_cone_deflection.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused tests pass; full test command exits 0; every touched file is
<= 500 lines.

## Stop condition

Stop after one compact unit: the fail-closed audit helper/tests are committed
and `MASTER_PLAN.md` records DONE or a concrete blocker. Do not run closure
simulations in this iteration.
