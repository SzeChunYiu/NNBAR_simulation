# Lane assignments — first parallel wave

Each lane is a single tmux pane running one codex CLI session. Lanes
are **file-disjoint** by design: no two lanes write the same file,
and merges into `main` cannot conflict.

## L0 — Simulation walkthrough deepening

- **Branch:** `lane/L0-sim-walkthrough`
- **Worktree:** `/Volumes/MyDrive/nnbar/nnbar/simulation-L0`
- **Sole writable target:** `docs/rebuild_plans/07_simulation_atomic_walkthrough.md`
- **Goal:** populate stub sections §5.4 (per-detector-builder detail)
  and §6.2 (per-SD detail) by reading the actual source under
  `NNBAR_Detector/src/detector/*.cc` and `NNBAR_Detector/src/sensitive/*.cc`.
- **Stop condition:** every active builder and SD has its
  sub-section with line-number citations.
- **Owner per plan 06:** Sim Production WG.

## L1 — Reconstruction walkthrough deepening

- **Branch:** `lane/L1-reco-walkthrough`
- **Worktree:** `/Volumes/MyDrive/nnbar/nnbar/simulation-L1`
- **Sole writable target:** `docs/rebuild_plans/08_reconstruction_atomic_walkthrough.md`
- **Goal:** populate §3.3 (vertex), §3.4 (charged), §3.5 (photon/π⁰),
  §6 (validation), §7–§9 (study modules) by reading
  `NNBAR_Detector/nnbar_reconstruction/*.py` end-to-end.
- **Stop condition:** every public function has a § entry with file
  path, line numbers, inputs, outputs, decision rule, truth-column
  use.
- **Owner per plan 06:** Reproducibility WG.

## L2 — IO data dictionary + macro inventory

- **Branch:** `lane/L2-io-macros`
- **Worktree:** `/Volumes/MyDrive/nnbar/nnbar/simulation-L2`
- **Sole writable targets:**
  - `docs/rebuild_plans/09_io_schema_data_dictionary.md`
  - `docs/rebuild_plans/10_macro_and_sample_inventory.md`
- **Goal (09):** for every parquet output file, fill §5–§14 column
  tables to the depth currently shown in §8 (TPC). Every column gets
  name, dtype, units, semantics, Class A/B/C, rule citation,
  producer, consumer.
- **Goal (10):** every `.mac` under `NNBAR_Detector/macro/` and
  `NNBAR_Detector/macros/` gets a definitive status:
  `active | legacy | retired`. Document each macro's commands,
  output files, and sample target.
- **Stop condition:** zero columns remain unclassified; zero macros
  lack a status.
- **Owner per plan 06:** Reproducibility WG.

## L3 — Foundations code (audit, registry, statistics)

- **Repo:** `NNBAR_Detector` (separate from the orchestration repo) —
  remote `github.com/SzeChunYiu/NNBAR_Detector`.
- **Branch:** `lane/L3-foundations-code` (off `master` HEAD, clean
  baseline).
- **Worktree:** `/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3`
- **Sole writable area:** new files only. Forbidden: editing existing
  reconstruction code.
  - `nnbar_reconstruction/audit/` (NEW package)
  - `nnbar_reconstruction/registry/` (NEW package)
  - `nnbar_reconstruction/statistics/` (NEW package)
  - `nnbar_reconstruction/_realism.py` (decorators per plan 01 §5)
  - `tests/test_realism_audit.py`
  - `tests/test_registry_integrity.py`
  - `tests/test_statistics.py`
- **Merging:** L3 does NOT auto-merge to master. Master's working tree
  contains in-progress rebuild work the user is doing in parallel.
  L3 commits stay on its branch and are reviewed manually before
  the user integrates them.
- **Goal:**
  1. Plan 01 §4 realism audit: AST walker that flags Class B reads
     in functions lacking the permissive decorators.
  2. Plan 03 registry: schema, freeze workflow, hash sealing,
     integrity test.
  3. Plan 04 statistics: bootstrap, jackknife, Wilson, Feldman-
     Cousins (n_obs=0 case), calibration propagation.
- **Stop condition:** all three modules pass their pytest suite;
  every public function has a unit test exercising the worked
  examples named in the plan (§ references in the test docstring).
- **Owner per plan 06:** Software Quality.
- **Constraint:** every new file ≤ 500 lines (CODING_STANDARDS.md §1).
  When approaching the limit, split.

## Conflict-avoidance contract

1. Each lane writes only to its declared targets above.
2. Each lane reads any file freely; reads do not produce conflicts.
3. Each lane commits to its branch only.
4. Each lane runs `merge.sh` after every iteration to integrate to
   `main`. The script's mkdir-lock serialises calls.

## When a lane finishes early

If a lane reaches its stop condition before the others, it picks up
overflow from this list (in priority order):

1. Deepen plan 11 (build environment) — list every CMake target,
   every external dependency hash.
2. Deepen plan 12 (physics list audit) — enumerate every constructor,
   verify against `PhysicsList.cc`.
3. Populate plan 51 (reviewer-question registry) seeds from the
   licentiate text (if available) or supervisor meeting notes.
4. Implement a tiny plan 53 CI workflow file (just the realism audit
   + 500-line check) under `.github/workflows/` if the user wants a
   CI surface.

## What is OUT of scope for this wave

- Sample regeneration (plans 20–23) — needs supervisor sign-off and
  cluster scheduling per plan 52.
- Plan 16+ (geometry/alignment) work — depends on the realism
  contract code (L3) landing first.
- MVA training (plan 57) — explicit in plan 57 §1.1: no MVA before
  baseline reproduces.
