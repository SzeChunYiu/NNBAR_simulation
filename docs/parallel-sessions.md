# Parallel codex sessions — coordination protocol

This repo is currently run by the LUNARC `codex-supervisor` layout described in
`docs/parallel-sessions/MASTER_PLAN.md`: **five tmux sessions / 22 panes**
(`recon`, `sim`, `g4gpu`, `review`, and `meta`) launched from the
`codex-prompts-*.txt` files at the repo root. The older local
`nnbar-gpu-batch` six-pane layout and Wave-6 `L0`--`L3` plan lanes are kept
below only as historical context for plan-audit work; they are not the active
supervisor topology.

**Read this file at the start of every iteration** — assume the protocol may
have evolved since you last looked.

## Active LUNARC sessions

All active panes work from the LUNARC checkout
`/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/` unless a lane spec
explicitly names an external repo (for example the isolated `geant4-gpu` or
`geant4-fork` trees). The local checkout mirrors coordination docs and prompt
files. Queue files are one-line FIFO `/goal` prompts under
`codex-tasks/<session>/`; the legacy local `codex-tasks/worker-{0..4}.txt`
files are migrated/inert and must not receive new active work.

| Session | Panes | Prompt file | Queue dir | Ownership summary |
| ------- | ----- | ----------- | --------- | ----------------- |
| `nnbar-recon-lunarc` | 7 | `codex-prompts-recon.txt` | `codex-tasks/recon/` | Python reconstruction/audit lanes; pane 0 is `planner-recon`. |
| `nnbar-sim-lunarc` | 7 | `codex-prompts-sim.txt` | `codex-tasks/sim/` | C++/SLURM/cosmic recovery and simulation evidence lanes; pane 0 is `planner-sim`. |
| `nnbar-g4gpu-lunarc` | 4 | `codex-prompts-g4gpu.txt` | `codex-tasks/g4gpu/` | Isolated G4GPU implementation/research lanes. |
| `nnbar-review-lunarc` | 2 | `codex-prompts-review.txt` | `codex-tasks/review/` | Geant4/OpenMC/source-review lanes. |
| `nnbar-meta-lunarc` | 2 | `codex-prompts-meta.txt` | `codex-tasks/meta/` | Cross-cutting DEBUGGER and VALIDATOR-PLANNER only. |

Per-pane lane names, specs, and writable scopes are in the prompt files and in
the lane-specific markdown referenced by those prompts. `MASTER_PLAN.md` is the
authoritative status table when it differs from this summary.

## Active iteration rules

1. **Re-read this file and your lane spec at the start of every iteration.**
2. **Stay inside your declared writable scope.** Do not edit another worker's
   task files unless your spec explicitly says to update shared coordination
   docs such as `MASTER_PLAN.md`.
3. **Use RTK for repo commands.** The repo `AGENTS.md` imports
   `/Users/billy/.codex/RTK.md`; prefix shell commands with `rtk`, or use
   `rtk proxy ...` for raw/compound commands.
4. **500-line file cap** per `CODING_STANDARDS.md` §1. When a file approaches
   450 lines, split before adding. Test files included.
5. **One compact unit per iteration.** A unit is the single task or subtask in
   your lane spec; do not bundle unrelated fixes.
6. **Commit only your own paths.** Other panes may leave dirty files in the
   shared worktree. Stage explicit paths and never clean, reset, or overwrite
   unrelated work.
7. **Status commits.** Queue-driven workers mark `NEXT` → `RUNNING`, commit the
   claim, implement and verify, then mark `RUNNING` → `DONE` in
   `MASTER_PLAN.md` and commit the completion. Queue pops should be committed
   with the claim when the queue file is tracked.
8. **G4GPU isolation is mandatory.** Worker-3/4 output must remain separated
   from NNBAR thesis-production code and data; see
   `docs/policies/g4gpu-isolation.md`.
9. **Decision-log entries** (`docs/governance/DECISION_LOG.md`, plan 05) are
   required for methodology changes: changing a numerical threshold,
   adding/removing an MVA feature, replacing an algorithm at any leaf, or
   pinning a dependency version.

## Active iteration cycle (template)

For non-planner workers in `recon`, `sim`, `g4gpu`, and `review` sessions:

1. Re-read `docs/parallel-sessions.md` and your lane-specific markdown spec.
2. Check your session queue file first (`codex-tasks/<session>/worker-N.txt`)
   if your spec defines one; otherwise inspect `MASTER_PLAN.md` for a matching
   unassigned `NEXT` task.
3. Claim exactly one task (`NEXT` → `RUNNING`) and commit the claim.
4. Read the task spec and every plan/source section it references.
5. Make the scoped change, respecting lane isolation and file caps.
6. Run the verification command named by the task spec.
7. Commit the implementation, update `MASTER_PLAN.md` to `DONE`, commit the
   completion, then stop.

For planner panes: review new commits, maintain queue depth across the active
LUNARC queue dirs, write compact lane specs, update `MASTER_PLAN.md`, then stop.

## Never idle — always find work

When your queue file is empty AND `MASTER_PLAN.md` shows no `NEXT` task in your
lane, do NOT sit GOAL_DONE. The supervisor defaults
`CODEX_SUPERVISOR_CONTINUOUS_LANES=*` and re-sends your `/goal`. Pick up new
work in this priority order:

1. **Pop from another lane's queue** (`codex-tasks/<other-session>/worker-N.txt`)
   if the lane is closest to your scope and `## Files you must NOT touch` does
   not block you. Mention the lane swap in your commit message.
2. **Plan-audit / methodology check** — open `MASTER_PLAN.md`, find a `DONE`
   item from the last 24h whose verification artifact is missing or thin, and
   add the missing artifact (decision-log entry, regenerated readiness report,
   missing test). Per-lane specs may also list `## Open questions for operator`
   you can answer with a one-paragraph note.
3. **Gap scan** — walk your lane's writable scope for files near the 500-line
   cap, missing tests, or duplicated logic; pick the smallest improvement and
   commit one bounded change.
4. **G4GPU + isolation panes**: if your scope is fully sealed off, drop down
   into research/notebooks under `docs/research/` and produce one new
   bounded analysis artifact. Do not reach across the isolation boundary.

Stay in scope: small bounded commits only, never reach into another lane's
writable paths. A pane that goes GOAL_DONE because of rate-limit is fine; a
pane that goes GOAL_DONE because *no tasks were queued* is a bug — fix the
queue or follow this rule.

## Legacy Wave-6 lanes (historical plan-audit context)

The previous `nnbar-rebuild` tmux batch used four file-disjoint lanes. Keep
these references only when maintaining old Wave-6 plan-audit material; do not
use them to decide active pane ownership.

| Legacy pane | Lane | Branch | Worktree | Repo | Target file(s) |
| ----------- | ---- | ------ | -------- | ---- | -------------- |
| 0 | L0 | `lane/L0-sim-walkthrough` | `/Volumes/MyDrive/nnbar/nnbar/simulation-L0` | simulation | `docs/rebuild_plans/07_simulation_atomic_walkthrough.md` |
| 1 | L1 | `lane/L1-reco-walkthrough` | `/Volumes/MyDrive/nnbar/nnbar/simulation-L1` | simulation | `docs/rebuild_plans/08_reconstruction_atomic_walkthrough.md` |
| 2 | L2 | `lane/L2-io-macros` | `/Volumes/MyDrive/nnbar/nnbar/simulation-L2` | simulation | `docs/rebuild_plans/09_io_schema_data_dictionary.md`, `docs/rebuild_plans/10_macro_and_sample_inventory.md` |
| 3 | L3 | `lane/L3-foundations-code` | `/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3` | `NNBAR_Detector` | new files under `nnbar_reconstruction/{audit,registry,statistics}/` and `tests/` |

Legacy per-lane specs: `docs/parallel-sessions/L0.md` through
`docs/parallel-sessions/L3.md`.

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
- `docs/parallel-sessions.md` (this file), unless the active task spec
  explicitly assigns the shared protocol refresh
- `docs/rebuild_plans/00_README.md` and 01–06 (foundations)
- Other lanes' `docs/parallel-sessions/*.md` lane specs unless your task
  explicitly assigns shared coordination-doc maintenance
- Other lanes' writable targets

## Required reading (every lane, every iteration)

- `docs/parallel-sessions.md` (this file)
- Your lane-specific `docs/parallel-sessions/*.md` spec (or legacy `L<n>.md`
  for old Wave-6 plan-audit tasks)
- Plan sections your task references (the relevant
  `docs/rebuild_plans/*.md`)
- `CODING_STANDARDS.md` (only on first iteration; sessions remember)
