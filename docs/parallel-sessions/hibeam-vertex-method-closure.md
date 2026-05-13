# Lane: hibeam-vertex-method-closure

## Goal

Make the HIBEAM vertex method-comparison and metric-table closure requirements
machine-checkable for Least-squares, Trackless, GraphNeT, and Clustering+GNN
results. This lane should audit evidence completeness first; it must not create
new physics results.

## Writable scope

- Create: `nnbar_reconstruction/analysis/hibeam_vertex_method_closure.py`
- Create: `tests/test_hibeam_vertex_method_closure.py`
- Modify only for lane status: `docs/parallel-sessions/MASTER_PLAN.md`

Forbidden:

- Do not train networks, rerun reconstruction studies, edit the Overleaf paper,
  submit SLURM jobs, or run simulations.
- Do not fill blank paper tables or promote numbers without verified local
  artifacts, dataset versions, split definitions, and uncertainty definitions.
- Do not conflate oracle validation labels with deployable reconstruction
  performance.
- Do not cite unverified line numbers, non-existent files, or unsupported
  `python -m nnbar_reconstruction.*` commands.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `CODING_STANDARDS.md`
4. `/Volumes/MyDrive/nnbar/papers/overleaf-696757e2/main.tex`
5. `docs/rebuild_plans/03_dataset_registry.md`
6. `docs/rebuild_plans/30_subsystem_vertex.md`
7. `docs/rebuild_plans/57_mva_method_protocol.md`
8. `docs/thesis_reproduction_ledger.md`
9. `acts_tracking/INTEGRATION_GUIDE.md`

Before committing any file, function, path, or command claim, apply the verifier
rules in `docs/parallel-sessions.md`.

## One compact-safe iteration

1. Claim the lane by changing its MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that status-only change.
2. Add a small data model for each method/Compton-level result: method name,
   dataset id, truth source, split id, metric definitions, artifact path,
   deployable/oracle status, and blocker messages.
3. Encode the required method set exactly as `least_squares`, `trackless`,
   `graphnet`, and `clustering_gnn`, and the required Compton levels as
   `0, 1, 2, 4, 8`.
4. Encode required metrics: `dx`, `dy`, `d_tot`, radial uncertainty or
   `sigma_r`, efficiency `epsilon`, outlier definition, and signal-track or
   signal-hit association efficiency.
5. Provide pure audit helpers that accept a manifest/table-like structure and
   fail closed for missing methods, missing Compton levels, blank/placeholder
   metrics, missing uncertainties, unpinned datasets, or oracle-only labels.
6. Add toy tests for complete evidence, missing GraphNeT results, missing 4/8
   Compton levels, missing uncertainty/error columns, and oracle-only labels.
7. Add one deterministic integration-style test against the current article text
   that confirms the existing HIBEAM method tables still expose blockers instead
   of being treated as final thesis-ready evidence.
8. Mark the MASTER_PLAN row `DONE` only after focused/full pytest and file-cap
   checks pass, with notes summarizing which methods/levels remain blocked.

## Verification command

```bash
rtk python -m pytest tests/test_hibeam_vertex_method_closure.py -q
rtk proxy zsh -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"
rtk proxy wc -l nnbar_reconstruction/analysis/hibeam_vertex_method_closure.py tests/test_hibeam_vertex_method_closure.py
```

## Stop condition

Stop after the method-closure audit module/tests are committed, touched files
remain under 500 lines, and MASTER_PLAN records that HIBEAM vertex comparison
claims remain blocked until every method/Compton-level metric has verified
artifact, dataset, split, uncertainty, and deployable/oracle evidence.
