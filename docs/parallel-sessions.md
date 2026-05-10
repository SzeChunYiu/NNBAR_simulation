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

## Atomic scientific derivation (Wave 6 — academic-grade understanding)

The user's standard goes beyond "decompose + cite the current
implementation" to "every reconstruction decision must follow from
physics first principles, every numerical parameter must be either
derived or empirically optimised in a closure study, and every code
function must reflect the derivation".

### Per-leaf required content (plans 24, 25–37 + new physics plans)

For every leaf identifier (V.1–V.5, C.1–C.6, P.1–P.7, E.1–E.9,
S.1–S.6) the owning subsystem plan must contain a **Physics
derivation** subsection covering:

1. **What is physically measured**: the ground-truth quantity the
   leaf estimates (e.g. "primary annihilation vertex coordinate",
   "specific ionisation per unit length", "charged-particle range
   in the scintillator stack"). State the truth-side definition
   without reference to the reconstruction.
2. **Estimator rationale**: why the chosen algorithm is the
   optimal-or-near-optimal estimator under the available Class A
   inputs. Cite the textbook or review paper that establishes this
   (e.g. Bethe-Bloch + Landau distribution + truncation theory for
   dE/dx; covariance-weighted vertex fit for V.4; isolation cone
   theory for photon ID).
3. **Statistical character**: bias, variance, robustness against
   outliers / pile-up / detector imperfections. State which of
   these dominate the leaf's uncertainty budget.
4. **Citation**: at least one textbook chapter or review paper
   reference, resolved via `\cite{key}` against
   `overleaf-hibeam-thesis/ref.bib`.

Plus a **Logic gaps** subsection enumerating *every numerical
parameter in the algorithm*: angular cuts, distance windows, bin
widths, isolation radii, fit ranges, window thresholds, weighting
constants. For each parameter: either

- a citation / first-principles derivation in one sentence, or
- a `OPEN:` marker plus a proposed closure study (which sample, which
  observable, what figure of merit) to fix the value empirically.

Plus a **Closure test for the derivation** subsection: one numbered
procedure that empirically validates the estimator behaves as the
derivation predicts (typical pattern: run on a Class A truth-clean
sample, compute the estimator + its theoretical uncertainty, assert
the residual distribution matches the derived bias and width within
the closure tolerance).

### Per-function code requirement (L3)

Every reconstruction function in `nnbar_reconstruction/<subsystem>.py`
gets a docstring section:

```python
def estimator(...):
    """One-line summary.

    Physics derivation:
        See `docs/rebuild_plans/<plan>.md` §<N> for the first-
        principles derivation. The estimator implemented here is
        <X> on Class A inputs <Y>; expected bias ≈ <Z>, variance
        ≈ <W>.

    Numerical parameters:
        - <param>: <value>, source: DEC-YYYY-MM-DD-N or
          `<plan>.md` §<N> closure study.
        - ...
    """
```

A function whose docstring lacks the Physics derivation block fails
review. A function whose Numerical parameters list contains an
`OPEN:` marker with no resolution date fails review.

### Verification (Wave 6 stop conditions per lane)

A lane finishes Wave 6 when:
1. Every leaf in its writable plans has the three required
   subsections (Physics derivation, Logic gaps, Closure test for
   derivation).
2. Every numerical parameter is either cited / derived or carries
   an `OPEN:` marker with a named closure study and a target
   resolution date.
3. Every cite resolves via `scripts/verify_citations.py` and
   `ref.bib` lookup.
4. (L3 only) Every per-leaf code function has the required
   docstring section.

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
