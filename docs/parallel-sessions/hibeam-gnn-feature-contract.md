# Lane: hibeam-gnn-feature-contract

## Goal

Make the HIBEAM TrackGNN/VertexGNN feature, dataset, and result contract
machine-checkable before any thesis or paper numbers are promoted. This lane
should produce an audit surface first; it must not train models or invent final
metrics.

## Writable scope

- Create: `nnbar_reconstruction/analysis/hibeam_gnn_feature_contract.py`
- Create: `tests/test_hibeam_gnn_feature_contract.py`
- Modify only for lane status: `docs/parallel-sessions/MASTER_PLAN.md`

Forbidden:

- Do not train models, regenerate datasets, edit the Overleaf paper, submit
  SLURM jobs, or run simulations.
- Do not treat truth-particle parquet columns as deployable reconstruction
  features; classify such inputs as validation/oracle evidence only.
- Do not hard-code final TrackGNN/VertexGNN performance numbers unless a local
  artifact and dataset/split evidence are verified in this worktree.
- Do not cite unverified line numbers, non-existent files, or unsupported
  `python -m nnbar_reconstruction.*` commands.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `CODING_STANDARDS.md`
4. `/Volumes/MyDrive/nnbar/papers/overleaf-696757e2/main.tex`
5. `docs/rebuild_plans/03_dataset_registry.md`
6. `docs/rebuild_plans/57_mva_method_protocol.md`
7. `docs/thesis_reproduction_ledger.md`
8. `nnbar_reconstruction/training/prepare_training_data.py`
9. `nnbar_reconstruction/training/prepare_psignal_from_gun.py`
10. `NNBAR_Detector/nnbar_reconstruction/validation.py`

Before committing any file, function, path, or command claim, apply the verifier
rules in `docs/parallel-sessions.md`.

## One compact-safe iteration

1. Claim the lane by changing its MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that status-only change.
2. Add a small data model for HIBEAM GNN contract items: feature name, source
   category, deployable/oracle status, required artifact, and blocker message.
3. Encode the paper-facing requirements as data: geometry-only feature schema,
   TrackGNN/VertexGNN distinction, Compton levels `0, 1, 2, 4, 8`, train/
   validation/test split evidence, `sigma_r`, efficiency `epsilon`, uncertainty,
   and deployable/oracle labels.
4. Audit current preparation scripts conservatively: mark truth ancestry,
   particle labels, and particle-parquet-derived labels as oracle-only unless a
   deployable reconstruction source is verified.
5. Provide pure helper functions that classify a supplied feature schema and
   result manifest without reading absolute local paths.
6. Add toy tests for:
   - a deployable geometry-only schema with all required result metadata;
   - truth-particle columns downgraded to oracle-only evidence;
   - missing Compton levels or train/test split evidence reported as blockers;
   - unresolved paper TODO/placeholder metrics reported as blockers.
7. Add one deterministic integration-style test against the current local
   article and/or prep-script text that asserts blockers are surfaced, not
   silently accepted as final HIBEAM results.
8. Mark the MASTER_PLAN row `DONE` only after focused/full pytest and file-cap
   checks pass, with notes summarizing blocker counts and remaining artifacts.

## Verification command

```bash
rtk python -m pytest tests/test_hibeam_gnn_feature_contract.py -q
rtk proxy zsh -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"
rtk proxy wc -l nnbar_reconstruction/analysis/hibeam_gnn_feature_contract.py tests/test_hibeam_gnn_feature_contract.py
```

## Stop condition

Stop after the contract audit module/tests are committed, touched files remain
under 500 lines, and MASTER_PLAN records whether HIBEAM GNN thesis/paper claims
are still blocked by feature schema, dataset, split, or metric evidence gaps.
