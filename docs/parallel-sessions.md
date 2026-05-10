# Parallel codex sessions — coordination protocol

This repo is currently being worked on by **4 parallel codex sessions**
running in tmux panes via `codex-supervisor` (session name
`nnbar-rebuild`). **Each lane is file-disjoint** by design; merges into
`main` cannot conflict.

**Read this file at the start of every iteration** — assume the
protocol may have evolved since you last looked.

## Lanes

| Pane | Lane | Branch | Worktree | Repo | Target file(s) |
| ---- | ---- | ------ | -------- | ---- | -------------- |
| 0 | L0 | `lane/L0-sim-walkthrough` | `/Volumes/MyDrive/nnbar/nnbar/simulation-L0` | simulation (this) | `docs/rebuild_plans/07_simulation_atomic_walkthrough.md` |
| 1 | L1 | `lane/L1-reco-walkthrough` | `/Volumes/MyDrive/nnbar/nnbar/simulation-L1` | simulation (this) | `docs/rebuild_plans/08_reconstruction_atomic_walkthrough.md` |
| 2 | L2 | `lane/L2-io-macros` | `/Volumes/MyDrive/nnbar/nnbar/simulation-L2` | simulation (this) | `docs/rebuild_plans/09_io_schema_data_dictionary.md`, `docs/rebuild_plans/10_macro_and_sample_inventory.md` |
| 3 | L3 | `lane/L3-foundations-code` | `/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3` | **NNBAR_Detector** (separate) | new files under `nnbar_reconstruction/{audit,registry,statistics}/` and `tests/` |

L0/L1/L2 work in the orchestration repo (this repo, simulation/). L3
works in the NNBAR_Detector repo (sibling worktree). The plan-set lives
in the orchestration repo and is read-only for L3.

Per-lane spec files:

- `docs/parallel-sessions/L0.md`
- `docs/parallel-sessions/L1.md`
- `docs/parallel-sessions/L2.md`
- `docs/parallel-sessions/L3.md`

## Rules every session follows

1. **Re-read this file at the start of every iteration.**
2. **Stay in your worktree.** Each pane has a designated worktree path
   (table above). Do not edit files outside your worktree, and do not
   touch files outside your declared writable targets.
3. **500-line file cap** per `CODING_STANDARDS.md` §1. When a file
   approaches 450 lines, split before adding. Test files included.
4. **One unit per iteration.** A "unit" is one builder, one SD, one
   reconstruction module, one parquet column-table, one macro cluster,
   or one code module + tests. Do not bundle.
5. **Commit on your branch.** Format:
   ```
   <type>(<scope>): <subject under 72 chars>

   <optional body>

   Plan: <plan IDs touched>
   Lane: L<n>
   ```
   `<type>` ∈ {feat, fix, refactor, docs, test, build, ci, chore}.
6. **L0/L1/L2: merge after every commit** by running
   `bash /Volumes/MyDrive/nnbar/nnbar/simulation/scripts/codex-supervisor/merge.sh lane/L<n>-<topic>`.
   The script holds a directory lock so concurrent calls serialise.
7. **L3: do NOT auto-merge.** L3 commits stay on
   `lane/L3-foundations-code` for human review. NNBAR_Detector master
   is dirty with the user's in-flight rebuild work and L3 must not
   collide with it.
8. **Decision-log entries** (`docs/governance/DECISION_LOG.md`,
   plan 05) for any methodology change: changing a numerical
   threshold, adding/removing an MVA feature, replacing an algorithm
   at any leaf, pinning a dependency version. The DEC entry is
   committed *with* the code change.

## Iteration cycle (template)

For lanes L0, L1, L2:

1. Re-read `docs/parallel-sessions.md` and your lane spec.
2. Read every plan section your task references.
3. Pick one unit per the lane spec.
4. Make the change in your worktree.
5. Verify file size ≤ 500 lines.
6. `git add <files>` and `git commit -m "<message per §5>"`.
7. `bash /Volumes/MyDrive/nnbar/nnbar/simulation/scripts/codex-supervisor/merge.sh lane/L<n>-<topic>`.
8. Continue until stop condition (lane spec) or rate-limited.

For lane L3: same cycle, but step 7 is replaced by `pytest tests/ -x
--tb=short` and the commit is left on the branch (no merge).

## Git contention

Sessions run inside their own git worktrees, but `simulation/main` is
shared by L0/L1/L2 merges. The `merge.sh` mkdir-lock serialises
concurrent merges. If `merge.sh` reports "could not acquire lock",
wait and retry — do NOT remove the lock directory unless it's been
stuck for > 120 seconds.

If `git push` ever appears in a script, ignore it for now — there is
no remote configured for the orchestration repo.

## A+ examiner gate (mandatory before declaring "Goal achieved")

The user is grading this rebuild at A+ standard. An examiner pass on
2026-05-10 caught the following classes of failure that **must not
re-appear**:

1. **Hallucinated line refs.** Plans 25–31 cited functions in
   `nnbar_reconstruction/reconstruction.py` at line ranges that were
   either off by 50–150 lines, pointed past EOF, or named functions
   (`_leadglass_shower_sources`, `build_photon_row`) that don't exist.
2. **Hallucinated files.** Lane spec referenced
   `nnbar_reconstruction/{pi0_study.py,charged_study.py}` at ~2 kLOC
   each — these never existed in any branch.
3. **Hallucinated CLI commands.** Plan 42 §2.1 prescribed
   `python -m nnbar_reconstruction.cli response-matrix …` with flags
   (`--all-runs`, `--table`, `--bootstrap`) that don't exist.

Before any commit, every claim of the form
`<file>:<line>` / `<file>:<L>-<M>` / `python -m nnbar_reconstruction.<x>`
/ `<function_name>` / "the existing file `<path>`" must satisfy:

- **Citation verifier.** Run, from the worktree root that contains the
  cited file:
  ```
  grep -n "^(def|class|void|TString|using|inline|template) <name>" <file>
  ```
  The match line number must fall **inside** the cited range. If you
  cite a single line, the match must be on that line. If the function
  is C++ (`reconstructor.cc` etc.), use the same grep with the C++
  signature.
- **CLI verifier.** Run
  `python -m nnbar_reconstruction.<subcommand> --help` from the L3
  worktree. If it errors, the command does not exist — either remove
  the cite or stop and ask L3 to implement it. **Never invent CLI
  surface in a plan.**
- **File-existence verifier.** Run `ls <path>` (or `git show <ref>:<path>`)
  before claiming a file exists at a particular size. Quote the
  `wc -l` output, not a guess.
- **Bibtex verifier.** When citing a paper in plans 12–15, grep
  `/Users/billy/Desktop/projects/overleaf-hibeam-thesis/ref.bib` for
  the cite key. No key, no cite.

If a verifier fails, **fix the citation** before committing. If you
cannot fix it (e.g. the function genuinely doesn't exist), remove the
claim and replace it with a TODO that names the lane responsible for
filling the gap.

Files in scope for citation auditing live under
`docs/rebuild_plans/`, `docs/parallel-sessions/`, and any
`*.md` written in this iteration.

## When to stop and ask

Only stop and surface a question when:

- A change forces edits to another lane's writable targets.
- The 500-line rule cannot be satisfied without a non-obvious split.
- A plan section needs clarification that isn't in the existing plan
  set or `CODING_STANDARDS.md`.
- A test fails for a reason that suggests the lane spec or
  `CODING_STANDARDS.md` is wrong.
- External credentials or access are required and unavailable.
- The remaining work would risk destructive behavior or data loss.

Otherwise: keep iterating.

## Read-only files (every lane)

- `CODING_STANDARDS.md`
- `docs/parallel-sessions.md` (this file)
- `docs/rebuild_plans/00_README.md` and 01–06 (foundations)
- Other lanes' `docs/parallel-sessions/L*.md`
- Other lanes' writable targets

## Required reading (every lane, every iteration)

- `docs/parallel-sessions.md` (this file)
- Your `docs/parallel-sessions/L<n>.md`
- Plan sections your task references (the relevant
  `docs/rebuild_plans/*.md`)
- `CODING_STANDARDS.md` (only on first iteration; sessions remember)
