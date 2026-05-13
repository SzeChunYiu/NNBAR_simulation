# Lane: hibeam-evidence-archive

## Goal

Make the HIBEAM reconstruction evidence package fail-closed before any thesis,
paper, or defence number is promoted. This compact-safe iteration should create
a machine-checkable audit for dataset-version pins, registry IDs, decision-log
links, validation reports, ledger rows, and archive/commit evidence; it must not
train models or invent final HIBEAM metrics.

## Writable scope

- Create: `nnbar_reconstruction/analysis/hibeam_evidence_archive.py`
- Create: `tests/test_hibeam_evidence_archive.py`
- Optional create: `docs/reports/hibeam_evidence_archive.md`
- Modify only for lane status: `docs/parallel-sessions/MASTER_PLAN.md`

Forbidden:

- Do not edit the Overleaf paper, run training, submit SLURM jobs, or regenerate
  datasets.
- Do not promote `\todonumber`, `\obs{...}`, placeholder tables, or unpinned
  local paths as final evidence.
- Do not cite unverified line numbers, unsupported CLIs, or non-existent files.
- Do not create a fake archive; unresolved evidence must be returned as blockers.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `CODING_STANDARDS.md`
4. `docs/rebuild_plans/03_dataset_registry.md`
5. `docs/governance/DECISION_LOG.md`
6. `docs/thesis_reproduction_ledger.md`
7. `docs/rebuild_plans/56_glossary.md`
8. `/Volumes/MyDrive/nnbar/papers/overleaf-696757e2/main.tex`
9. `docs/parallel-sessions/hibeam-gnn-feature-contract.md`
10. `docs/parallel-sessions/hibeam-vertex-method-closure.md`

Before committing any path, command, or metric claim, apply the verifier rules in
`docs/parallel-sessions.md`. Prefer evidence IDs and grep output over line-number
claims.

## One compact-safe iteration

1. Claim the lane by changing its MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that status-only change.
2. Verify evidence inputs exist with `rtk proxy ls` before citing them.
3. Add a small pure-Python audit model for evidence items: claim id, required
   dataset registry id, decision-log id, validation report path, ledger row id,
   archive member, pinned commit/tag/hash, status, and blocker text.
4. Encode fail-closed checks that reject missing registry IDs, missing DEC links,
   absent validation reports, placeholder paper tokens, unpinned paths, and
   archive members without stable digests.
5. Add helper functions that can audit supplied text/manifests without reading
   machine-specific absolute paths by default.
6. Add toy tests covering a complete pinned evidence package, missing dataset
   registry/DEC links, placeholder HIBEAM paper tokens, and stale/unhashed
   archive members.
7. Add one deterministic integration-style test against current local HIBEAM
   paper and/or governance text that surfaces blockers rather than accepting the
   package as final.
8. If useful, write `docs/reports/hibeam_evidence_archive.md` summarizing blocker
   counts and the next smallest archive-pinning task.
9. Mark the MASTER_PLAN row `DONE` only after focused/full pytest and file-cap
   checks pass, with notes saying whether HIBEAM results remain blocked.

## Verification command

```bash
rtk python -m pytest tests/test_hibeam_evidence_archive.py -q
rtk proxy zsh -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"
rtk proxy wc -l nnbar_reconstruction/analysis/hibeam_evidence_archive.py tests/test_hibeam_evidence_archive.py docs/reports/hibeam_evidence_archive.md
```

## Stop condition

Stop after the audit module/tests and any report are committed, touched files are
under 500 lines, and MASTER_PLAN records the remaining dataset, decision-log,
validation-report, ledger, archive, or commit-pin blockers.
