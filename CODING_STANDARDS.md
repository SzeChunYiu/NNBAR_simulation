# NNBAR rebuild — coding & maintainability standards

Single source of truth for how code is written, structured, reviewed, and
merged in this repository. Every contributor — human or codex-supervisor
session — reads this before writing code. Plans 01 (realism contract),
05 (decision log), 06 (governance), 53 (CI), and 57 (MVA protocol) refer
to this document.

The standards are intentionally short and load-bearing. They are not a
style guide; they are operational rules with audit/CI consequences.

---

## 1. The 500-line rule

**No source file exceeds 500 lines.** This applies to:

- Python modules (`*.py`) under `nnbar_reconstruction/`, `tests/`,
  `scripts/`.
- C++ source and header files (`*.cc`, `*.hh`) under
  `NNBAR_Detector/src/` and `NNBAR_Detector/include/`.
- Shell scripts (`*.sh`) under `scripts/`.

Rationale: a file you can read in one sitting is a file you can review,
own, and change without surprises. 500 lines is an enforced upper
bound; aim for 200 lines.

### 1.1 What counts

Lines counted per `wc -l`. Comments count. Blank lines count. License
headers count.

### 1.2 What to do when a file approaches the limit

1. Stop. Do not push past 450 lines hoping nobody notices.
2. Split. Identify a coherent sub-responsibility and extract it into a
   sibling module / file in the same directory. Update imports.
3. Re-run tests. The split must be behaviour-preserving.
4. Commit the split as its own commit, separate from any feature work.
5. If the split itself produces a > 500 line file, split again.

### 1.3 Existing files over 500 lines (refactoring backlog)

The following files exceed 500 lines on the initial commit and are
**grandfathered** — they remain runnable but no PR may add lines to
them. Every change to one of these triggers a split-extract:

- `nnbar_reconstruction/reconstruction.py` (1764) — split candidates:
  vertex, charged, photon/π⁰, event-variable, selection.
- `nnbar_reconstruction/pi0_study.py` (1974) — split candidates: ladder
  rungs, per-event row builders, scoring.
- `nnbar_reconstruction/charged_study.py` (2241) — split candidates:
  per-species evaluation, hit-coverage classifiers, primary-topology
  bookkeeping.
- `nnbar_reconstruction/cli.py` (519) — split candidates: per-
  subcommand modules under `nnbar_reconstruction/cli/`.
- C++ geometry builders (`Scintillator_geometry.cc` 34 KB,
  `beampipe_geometry.cc` 35 KB, `LeadGlass_geometry.cc` 19 KB) —
  split candidates: per-region helpers, material definitions in their
  own file.

Refactoring these is tracked as a standing item; it does not block
parallel rebuild work.

### 1.4 CI enforcement

Plan 53 CI runs a tier-1 check that no file added or modified by the
PR exceeds 500 lines. Modification of a grandfathered file is allowed
only if the modification reduces line count.

---

## 2. One responsibility per file

Each file owns one concept: one class, one function group, one config
schema. If a file's name needs an "and" to describe it, it is two
files.

Naming: `noun_subject.py` for descriptive responsibility (e.g.
`vertex_fit.py`); `verb_action.py` for behavioural utilities (e.g.
`bootstrap.py`).

---

## 3. Imports and dependencies

### 3.1 Module boundary discipline

- `nnbar_reconstruction/io.py` is the only module that reads parquet
  files.
- `nnbar_reconstruction/audit/realism.py` is the only module that
  walks reco AST.
- `nnbar_reconstruction/registry/` is the only module that touches
  `data/registry/`.
- `nnbar_reconstruction/statistics/` is the only module that
  implements bootstrap / jackknife / F-C / Wilson.

If two modules duplicate one of these responsibilities, refactor.

### 3.2 No cross-import cycles

A module may not import from a module that imports it. CI tier-1
detects cycles.

### 3.3 Third-party imports at top-of-file

No `import` inside functions except where lazy import is genuinely
necessary (heavy optional dependencies, e.g. `pyhf`, `xgboost`).

---

## 4. Naming

### 4.1 Code identifiers

- Python: `snake_case` for functions/variables, `PascalCase` for
  classes, `UPPER_CASE` for module-level constants.
- C++: `lower_snake_case` for variables/functions per current code
  style; `PascalCase` for classes (current code already follows
  this).
- File names: `snake_case.py`, `PascalCase.cc/hh` (matching the
  primary class).

### 4.2 Provenance suffixes

Columns carrying truth (Class B per plan 01) use the suffix `_truth`
when ambiguity is possible. Columns carrying calibration constants
(Class C) use the prefix `cal_` or are documented in plan 09 with
the `would_change_with_real_data` flag.

### 4.3 Decorator markers (plan 01 §5)

Functions reading Class B columns must carry exactly one of:
- `@validation_only`
- `@diagnostic_only`
- `@labeling`

The realism audit rejects unmarked Class B reads.

---

## 5. Tests

### 5.1 New code requires new tests

Every new public function in `nnbar_reconstruction/` lands with a
test under `tests/`. PRs without tests for new public functions are
rejected.

### 5.2 Test file size

Test files follow §1 (500-line cap). Split by feature surface area.

### 5.3 Test naming

`tests/test_<module_name>.py` mirrors the module under test. Functions
named `test_<feature>` describe the property being tested.

### 5.4 Coverage target

70% line coverage on `nnbar_reconstruction/` excluding tests
themselves. Plan 53 CI tracks the trend; a PR that drops coverage by
> 1 percentage point is rejected.

---

## 6. Comments and docstrings

### 6.1 Docstrings

Every public function, class, and module has a docstring. Format:

```
"""<one-line summary>.

<optional 1-3 sentence elaboration>

Args:
    <name>: <description>

Returns:
    <description>

Raises:
    <type>: <when>
"""
```

### 6.2 Inline comments

Comment the *why*, not the *what*. The code already says what.

Bad:
```python
# Multiply by 2
x = x * 2
```

Good:
```python
# Account for double-sided readout: each scintillator hit registers
# in both PMT panes (plan 09 §11).
x = x * 2
```

### 6.3 Plan citations

When implementing a plan-specified rule, cite the plan section in a
comment. This binds the code to its motivating decision:

```python
# Realism contract Class C: see docs/rebuild_plans/01_realism_contract.md
# §2.3. W-value = 23.6 eV per TPCSD.cc:102.
TPC_W_VALUE_EV = 23.6
```

---

## 7. Decision-log discipline

### 7.1 When to add a DEC entry

Plan 05 §7 lists what goes in the decision log. Operationally, every
PR that:

- Changes a numerical threshold in `ReconstructionConfig`.
- Adds or removes a feature in an MVA schema (plan 57).
- Replaces an algorithm at any leaf (plan 24).
- Pins or bumps a dependency version (plan 11).
- Modifies the realism contract or registry policy.

…must include a paired `DEC-YYYY-MM-DD-N` entry in
`docs/governance/DECISION_LOG.md`.

### 7.2 Format

Plan 05 §3. The entry is committed *with* the code change, not after.

---

## 8. Branching and merging

### 8.1 Branch naming

- `lane/L<n>-<short-topic>` for codex-supervisor lanes.
- `feat/<short-topic>` for feature work.
- `fix/<short-topic>` for bug fixes.
- `refactor/<short-topic>` for structure-only work (e.g. 500-line
  splits).

### 8.2 Commit messages

```
<type>: <subject under 72 chars>

<optional body, wrap at 72>

Plan: <plan IDs touched, e.g. 07, 09>
DEC: <decision log entry IDs if any>
Lane: <L0|L1|L2|L3 if applicable>
```

`<type>` ∈ {feat, fix, refactor, docs, test, build, ci, chore}.

### 8.3 Merge to main

Per the governance protocol, lane sessions merge to `main` after
every iteration through `scripts/codex-supervisor/merge.sh <branch>`.

The merge.sh wrapper:

1. Acquires a directory lock (mkdir-based, portable).
2. Switches the main worktree to `main`.
3. Runs `git merge --no-ff --log <branch>`.
4. Releases the lock.

This serialises concurrent merges from disjoint lanes. File-disjoint
lanes never conflict at merge time, so the lock only orders the
metadata update.

### 8.4 Merge messages

```
Merge lane <branch>: <iteration summary>

<list of files changed>
<DEC entries closed if any>
```

### 8.5 No force pushes, no rewrites of `main`

`main` history is append-only. A bad merge gets a `git revert` commit,
not a rewrite.

---

## 9. CI gates (summary; plan 53 owns the full spec)

Tier 1 (every PR / merge):
- Lint passes.
- 500-line rule per §1.4.
- Realism audit per plan 01 §4.
- Registry integrity per plan 03.
- Plan-set audit (YAML headers).
- Reconstruction unit tests.

Tier 2 (nightly):
- Simulation smoke build for each `WITH_*` permutation.
- Reconstruction smoke run.

A merge that fails tier 1 is reverted within one iteration.

---

## 10. Performance budgets

Plan 19 §3 owns the simulation-side budget; the reconstruction side:

- `reconstruct_run` on a 100-event sample completes in < 30 seconds
  on the development laptop.
- Per-event reconstruction memory < 200 MB.

A PR that regresses either by > 10% is rejected unless the regression
is paired with a DEC entry justifying the trade-off.

---

## 11. Documentation alongside code

Every change to a `nnbar_reconstruction/` module updates either:
- the relevant plan section (07, 08, 09 for forensic; 25–37 for
  subsystem); or
- the relevant `*.md` under `docs/`; or
- the function's docstring.

A PR that changes code behaviour without any of the above is
rejected.

---

## 12. References

- Plan 01 — realism contract (Class A/B/C, audit, decorators).
- Plan 05 — decision log format.
- Plan 06 — governance and review gates.
- Plan 53 — CI tiers.
- Plan 57 — MVA method protocol.

This document is itself plan-set-class. Updating it requires the
`Council-and-supervisor` review per plan 06 §3.3.
