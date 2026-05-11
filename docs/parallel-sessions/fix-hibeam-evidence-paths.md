# Lane: fix-hibeam-evidence-paths

## Goal

Remove the machine-specific HIBEAM paper path from the evidence-archive
regression test while preserving the fail-closed audit behavior for optional
local paper/governance evidence.

## Writable scope

- Modify: `tests/test_hibeam_evidence_archive.py`
- Modify only if required by imports/fixtures:
  `nnbar_reconstruction/analysis/hibeam_evidence_archive.py`
- Modify only for lane status: `docs/parallel-sessions/MASTER_PLAN.md`

Forbidden:

- Do not edit the Overleaf paper, train models, submit SLURM jobs, regenerate
  datasets, or promote HIBEAM numbers.
- Do not weaken missing evidence into a pass-by-default result.
- Do not add new absolute `/Volumes/...`, `/Users/...`, or user-home fallbacks
  in tests or helpers.
- Do not create fake registry, DEC, ledger, validation-report, archive, or
  commit-pin evidence.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `CODING_STANDARDS.md`
4. `docs/parallel-sessions/hibeam-evidence-archive.md`
5. `nnbar_reconstruction/analysis/hibeam_evidence_archive.py`
6. `tests/test_hibeam_evidence_archive.py`

Before committing any path, command, or function claim, apply the verifier rules
in `docs/parallel-sessions.md`.

## Review finding to fix

Planner verification found the current test file exists and contains a hardcoded
local paper path:

```bash
rtk proxy grep -n "/Volumes/MyDrive/nnbar/papers" tests/test_hibeam_evidence_archive.py
```

The grep currently reports the path in the optional local-paper integration
test. That makes the test machine-specific and repeats the path-portability
problem already fixed for the HIBEAM GNN feature-contract tests.

## One compact-safe iteration

1. Claim the lane by changing its MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that status-only change.
2. Replace the hardcoded paper path with a portable optional input such as
   `NNBAR_HIBEAM_ARTICLE_TEX`, using `pytest.skip` when it is not supplied or
   does not point to a file.
3. Keep deterministic toy tests independent of local filesystem layout.
4. Preserve an integration-style evidence test that surfaces blockers when
   optional article text is supplied.
5. Add or update a regression that fails if the test/helper source contains
   `/Volumes/MyDrive/nnbar/papers`, `/Users/`, or `/home/billy`.
6. Run focused pytest, full pytest, forbidden-path grep, and file-cap checks.
7. Mark the MASTER_PLAN row `DONE` only after verification passes, with notes
   saying HIBEAM evidence remains fail-closed when optional paper text is
   supplied.

## Verification command

```bash
rtk python -m pytest tests/test_hibeam_evidence_archive.py -q
rtk proxy zsh -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"
rtk proxy grep -n "/Volumes/MyDrive/nnbar/papers\|/Users/\|/home/billy" tests/test_hibeam_evidence_archive.py
rtk proxy wc -l tests/test_hibeam_evidence_archive.py nnbar_reconstruction/analysis/hibeam_evidence_archive.py
```

The grep command must return no matches after the fix.

## Stop condition

Stop after the portability fix is committed, touched files remain under 500
lines, focused/full pytest pass, and MASTER_PLAN records the test-path
portability regression as done without promoting unresolved HIBEAM evidence.
