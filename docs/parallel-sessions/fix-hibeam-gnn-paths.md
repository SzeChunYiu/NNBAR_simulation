# Lane: fix-hibeam-gnn-paths

## Goal

Remove the machine-specific HIBEAM paper path from the GNN feature-contract
regression test while preserving the fail-closed audit behavior for current
article/preparation-script evidence.

## Writable scope

- Modify: `tests/test_hibeam_gnn_feature_contract.py`
- Modify only if required by imports/fixtures: `nnbar_reconstruction/analysis/hibeam_gnn_feature_contract.py`
- Modify only for lane status: `docs/parallel-sessions/MASTER_PLAN.md`

Forbidden:

- Do not edit the Overleaf paper, training data, preparation scripts, or any
  generated artifact.
- Do not weaken the audit into a pass-by-default result when optional local
  evidence is absent.
- Do not add new absolute `/Volumes/...` or user-home paths to tests or helpers.
- Do not promote HIBEAM paper/article numbers as final evidence.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `CODING_STANDARDS.md`
4. `docs/parallel-sessions/hibeam-gnn-feature-contract.md`
5. `nnbar_reconstruction/analysis/hibeam_gnn_feature_contract.py`
6. `tests/test_hibeam_gnn_feature_contract.py`

Before committing any path, command, or function claim, apply the verifier rules
in `docs/parallel-sessions.md`.

## Review finding to fix

Planner verification found the current test file exists and contains a hardcoded
local paper path:

```bash
rtk proxy ls tests/test_hibeam_gnn_feature_contract.py nnbar_reconstruction/analysis/hibeam_gnn_feature_contract.py
rtk proxy grep -n "/Volumes/MyDrive/nnbar/papers" tests/test_hibeam_gnn_feature_contract.py
```

The grep currently reports the path at `tests/test_hibeam_gnn_feature_contract.py:117`.

## One compact-safe iteration

1. Claim the lane by changing its MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that status-only change.
2. Add a portable way for the integration-style evidence test to locate optional
   article text, for example an environment variable such as
   `NNBAR_HIBEAM_ARTICLE_TEX` plus `pytest.skip` when the file is not supplied.
3. Keep toy tests fully deterministic and independent of local filesystem layout.
4. Preserve a regression that fails if new test/helper code contains the old
   `/Volumes/MyDrive/nnbar/papers` literal or another machine-specific fallback.
5. Keep preparation-script reads repo-relative, or skip with a clear reason if a
   required local evidence file is absent.
6. Run focused pytest, full pytest, grep for forbidden absolute paths, and file
   line-count checks.
7. Mark the MASTER_PLAN row `DONE` only after verification passes, with notes
   saying the HIBEAM article/prep evidence remains fail-closed when supplied.

## Verification command

```bash
rtk python -m pytest tests/test_hibeam_gnn_feature_contract.py -q
rtk proxy zsh -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"
rtk proxy grep -n "/Volumes/MyDrive/nnbar/papers" tests/test_hibeam_gnn_feature_contract.py
rtk proxy wc -l tests/test_hibeam_gnn_feature_contract.py nnbar_reconstruction/analysis/hibeam_gnn_feature_contract.py
```

The grep command must return no matches after the fix.

## Stop condition

Stop after the portability fix is committed, touched files remain under 500
lines, focused/full pytest pass, and MASTER_PLAN records the path-portability
regression as done without promoting unresolved HIBEAM evidence.
