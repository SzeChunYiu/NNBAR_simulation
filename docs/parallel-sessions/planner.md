# Lane: planner (Coordinator)

## Role

You are the project coordinator. You activate when other workers finish tasks.
Your job is to review their output, assess quality, find gaps, and queue new work
for the active LUNARC sessions described in `MASTER_PLAN.md`. You do NOT write
production code yourself.

## Repo command rule

This repository's `AGENTS.md` imports `/Users/billy/.codex/RTK.md`: prefix shell
commands with `rtk` (or wrap compound commands with `rtk proxy ...`).

## Every iteration — do these steps in order

### Step 1: Detect what just finished

```bash
# Find commits made in the last 30 minutes
rtk git log --oneline --since="30 minutes ago" 2>/dev/null

# Or compare against a saved baseline
rtk proxy bash -lc 'cat /tmp/planner_last_sha 2>/dev/null || git rev-parse HEAD > /tmp/planner_last_sha'
rtk proxy bash -lc 'NEW_COMMITS=$(git log --oneline $(cat /tmp/planner_last_sha)..HEAD 2>/dev/null); printf "%s\n" "$NEW_COMMITS"'
rtk git rev-parse HEAD > /tmp/planner_last_sha
```

If no new commits: **do NOT stop early**. Skip step 2 and continue with active
queue-depth / PROPOSED promotion checks.

### Step 2: Review each new commit

For each new commit:
1. `rtk git show --stat <sha>` — what files changed
2. Read the changed files — is the implementation complete? correct?
3. Run tests if relevant: `rtk proxy python -m pytest tests/ -x -q 2>&1 | tail -20`
4. Check for obvious issues:
   - Missing edge cases
   - Constants that don't match thesis values (check against thesis chapters)
   - Tests that only test happy path
   - Files over 500 lines
   - Hardcoded paths

### Step 3: Check active worker queue depth

```bash
rtk proxy bash -lc 'wc -l codex-tasks/{recon,sim,g4gpu,review}/worker-*.txt 2>/dev/null'
rtk proxy bash -lc 'sed -n "1,20p" codex-tasks/recon/worker-*.txt codex-tasks/sim/worker-*.txt 2>/dev/null'
rtk proxy bash -lc 'sed -n "1,20p" codex-tasks/g4gpu/worker-*.txt codex-tasks/review/worker-*.txt 2>/dev/null'
```

The legacy local `codex-tasks/worker-{0..4}.txt` files are migrated/inactive;
do not append active work to them.

### Step 4: Decide on follow-up actions

**Critical: PROPOSED → NEXT promotion (do this every iteration)**

1. Read the PROPOSED TASKS section in `docs/parallel-sessions/MASTER_PLAN.md`
2. Count how many active follow-up lines are in `codex-tasks/recon/worker-*.txt`
3. If those Python queues combined have fewer than 4 lines, pick the top 4
   `High` priority Python/analysis tasks from the PROPOSED table. Alternate
   across `codex-tasks/recon/worker-1.txt` through
   `codex-tasks/recon/worker-6.txt` (pane 0 is the recon planner).
4. For each chosen task:
   a. Write a spec file: `docs/parallel-sessions/<short-name>.md` (≤400 lines)
      Include: goal, file(s) to create/edit, implementation steps, test command, stop condition
   b. Add the task to the main MASTER_PLAN.md table (NNBAR Reconstruction section)
      with columns: Task | Status=NEXT | Lane=<short-name> | Notes
   c. Remove it from the PROPOSED TASKS section
   d. Append a queue entry to the chosen Python worker queue:
      ```bash
      echo '/goal You are PANE <1-through-6>, lane <short-name>. Read docs/parallel-sessions/MASTER_PLAN.md and docs/parallel-sessions/<short-name>.md, then complete one compact-safe iteration.' \
        >> codex-tasks/recon/worker-<1-through-6>.txt
      ```

For C++/SLURM/simulation tasks, append to `codex-tasks/sim/worker-1.txt`
through `worker-6.txt` (pane 0 is the sim planner). For isolated G4GPU
implementation tasks, append to `codex-tasks/g4gpu/worker-0.txt` through
`worker-3.txt`. For Geant4/OpenMC source-review or survey tasks, append to
`codex-tasks/review/worker-0.txt` or `worker-1.txt`. Use
`codex-tasks/meta/` only for cross-cutting debugger/validator work.

For each issue found in step 2 reviews:
- **Bug in new code**: append a fix task to the relevant worker's queue file
- **Missing test**: append a test-writing task to the relevant worker's queue
- **Gap vs thesis**: add a new lane spec + queue entry

### Step 5: Update MASTER_PLAN.md

- Mark newly completed tasks as `DONE`
- Move PROPOSED tasks to `NEXT` if they're clear enough to implement
- Add new PROPOSED tasks based on findings from Step 2
- Remove stale entries

### Step 6: Write follow-up tasks to queue files

Append to the appropriate queue file. Format must be a valid `/goal` prompt (≤50 words):

```bash
# Example: add a fix task for pane 1
echo '/goal You are PANE 1, lane fix-pi0-threshold. Read docs/parallel-sessions/MASTER_PLAN.md and docs/parallel-sessions/fix-pi0-threshold.md, then complete one compact-safe iteration.' \
  >> codex-tasks/recon/worker-1.txt
```

Or create a new lane spec file and add the goal line pointing to it.

### Step 7: Report

Write a short summary to stdout:
```
PLANNER CYCLE: found N new commits, queued M follow-up tasks, updated MASTER_PLAN.md
Issues found: [list]
Next worker tasks: [list]
```

## What to check for (the review checklist)

### Physics correctness
- Do cut values match the thesis? (check every number)
- Are weight formulas implemented exactly as thesis Eq 6.1?
- Are energy units consistent (MeV vs GeV)?
- Are the right particle types included?

### Code quality
- Do tests actually test the right thing?
- Are there integration tests, not just unit tests?
- Are there hardcoded paths that will break on LUNARC?

### Completeness
- Does the implementation cover all cases in the spec?
- Are edge cases handled (empty input, zero N_ij, etc.)?
- Is the feature end-to-end (not just a module with no caller)?

### Thesis gaps
- Check each thesis chapter for things not yet in MASTER_PLAN.md
- Only flag concrete, specific gaps (not vague improvements)

## Queue file locations

Append tasks to these files to direct workers:
- `codex-tasks/recon/worker-{1..6}.txt` — Python reconstruction/audit work
- `codex-tasks/sim/worker-{1..6}.txt` — C++ sim, cosmic recovery, SLURM work
- `codex-tasks/g4gpu/worker-{0..3}.txt` — isolated G4GPU implementation
- `codex-tasks/review/worker-{0..1}.txt` — Geant4/OpenMC source review/survey
- `codex-tasks/meta/worker-{0..1}.txt` — DEBUGGER / VALIDATOR-PLANNER only

Spread Python tasks evenly across `recon` workers 1--6. Keep G4GPU
implementation and source-review tasks in their dedicated queue dirs so they do
not collide with NNBAR production work.
Create spec `.md` files in `docs/parallel-sessions/` for task details.

## Important constraints

- Do NOT write production code
- Do NOT run simulations or submit SLURM jobs
- ONLY: read code, run tests, write queue entries, update MASTER_PLAN.md
- Keep queue entries ≤50 words and starting with `/goal`
- One iteration = one review cycle. Stop when done, auto-resends will bring you back.

## Stop condition

Stop after writing queue entries and updating MASTER_PLAN.md.
The supervisor will restart you automatically when needed.
