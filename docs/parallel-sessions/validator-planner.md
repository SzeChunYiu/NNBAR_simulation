# VALIDATOR-PLANNER lane instructions (nnbar-lunarc-meta pane 1)

This pane is the project's continuous academic quality enforcer and queue
manager. It never implements other lanes' tasks. It runs until every gap is
closed, every claim is evidenced, and every paper milestone gate in
`docs/specs/paper-methodology.md` is met.

---

## Required reading (every iteration, in order)

1. `docs/parallel-sessions/MASTER_PLAN.md` — full project state
2. `docs/specs/paper-methodology.md` — academic quality standard and milestone gates
3. `docs/specs/benchmark-harness.md` — harness contract; check implementation progress
4. `git log --oneline -30` — what changed since last iteration

---

## Protocol per iteration

### Phase 1 — Evidence validation

For each lane that committed since the last iteration
(`git log --oneline -30`, filter commits touching `docs/parallel-sessions/`,
`nnbar_reconstruction/`, `NNBAR_Detector/`, `benchmarks/`, `docs/reports/`):

1. Confirm the claimed evidence physically exists:
   - Source files: `wc -l <file>` matches the claimed line count.
   - Test results: re-run `pytest -x -q <focused_test_file>` and confirm it passes.
   - Parquet outputs: `find build_lunarc/output -name '*.parquet' -size +100c` for
     any claimed simulation sample.
   - Harness rows: `python -c "import pandas as pd; df=pd.read_parquet('benchmarks/results/results.parquet'); print(df[df.opt_id=='<id>'][['result_tag','claim_level','parity_pass']])"`.
2. Check claim level per `docs/specs/paper-methodology.md`:
   - Is it L1 (predicted only)? If so, is a harness task queued to elevate it to L2?
   - Is it L2 (single hardware)? If so, is the multi-hardware L3 task queued?
   - Does a `PARITY_FAIL` exist? Tag it visibly in the MASTER_PLAN note.
3. If evidence is missing or claim level is overstated:
   - Append a precise `OPEN:` blocker to the lane's `.md` spec.
   - Change the MASTER_PLAN row status back to `RUNNING` if the gap is material.

### Phase 2 — Gap scan (7 questions, every iteration)

Work through each question. For each gap found, queue one bounded task.

**Q1: L1-only predictions needing harness elevation**
```bash
grep -r "Expected speedup\|OPEN:\|L1\|predicted" docs/reports/bottleneck_database_geant4.md \
  docs/reports/g4_bottleneck_database_pil_geometry.md | grep -v "DONE\|L2\|L3"
```
For each L1 prediction with no harness row: queue
`/goal run benchmark harness for <BD-id> per docs/specs/benchmark-harness.md`
in `codex-tasks/g4gpu/worker-<N>.txt`.

**Q2: Physics-list / hardware matrix gaps**
Check `benchmarks/results/results.parquet` (if it exists) for missing
(workload × physics_list × hw_id) combinations per `docs/specs/paper-methodology.md`.
For each missing combination: queue reference generation or harness run.

**Q3: Thesis reproduction ledger rows without samples**
```bash
grep "sample_path_not_checked\|sample_missing\|BLOCKED" \
  nnbar_reconstruction/analysis/*.py docs/parallel-sessions/MASTER_PLAN.md | head -20
```
For each missing sample: queue the corresponding sbatch calibration/cosmic/signal
job (submit via sbatch, not inline).

**Q4: `OPEN:` markers unresolved for > 2 iterations**
```bash
grep -r "OPEN:" docs/reports/ docs/parallel-sessions/ | grep -v "DONE\|resolved" | head -20
```
For each stale `OPEN:`: write a bounded task that either resolves it or explicitly
defers it with a follow-up paper reference.

**Q5: Benchmark harness implementation gaps**
Check whether `benchmarks/harness/schema.py`, `parity.py`, `builder.py`,
`runner.py`, `hardware.py`, `run.py` exist and pass their focused tests.
For each missing module: queue the next harness implementation task per
`docs/specs/benchmark-harness.md §Implementation tasks`.

**Q6: Paper outline gaps**
The paper outline in `docs/specs/paper-methodology.md §Paper structure` has 9
sections. For each section: does a spec or evidence base exist?
For any section with no spec: write
`docs/specs/paper-section-<N>-<slug>.md` as a stub naming the required evidence
and the figures/tables that will populate it.

**Q7: Scope expansion opportunities**
After closing known gaps, ask: is there a natural academic extension that
strengthens the paper?

Examples of justified expansions:
- A new workload (W7: medical physics phantom) exercising a different geometry class
- A new competitor (Opticks, VecGeom) with a published baseline
- A new physics domain (optical photons, heavy-ion transport) showing the same
  optimizations generalise
- A new hardware target (AMD GPU / HIP) testing CUDA kernel portability

For each justified expansion: write a `docs/specs/scope-extension-<slug>.md`
and add a `PLANNED` row to MASTER_PLAN. Do NOT implement without planner review.

### Phase 3 — Queue management

For each codex-tasks queue file:

1. `codex-tasks/<session>/worker-<N>.txt` — if empty AND a NEXT task exists
   for that session, write the next `/goal` line there.
2. If a queue has stale or superseded goals (the referenced file is now DONE),
   clear the line and add the updated one.
3. After writing queue files, rsync them to LUNARC:
   ```bash
   rsync -av codex-tasks/ lunarc:/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/codex-tasks/
   ```

### Phase 4 — Status update and commit

1. Update MASTER_PLAN for any status transitions evidenced this iteration.
2. Update milestone gate checkboxes in `docs/specs/paper-methodology.md` if
   a gate was just satisfied.
3. Commit:
   ```
   docs(validator): <one-line summary of gaps found and tasks queued>

   Gaps: <list>
   Tasks queued: <list>
   Milestone progress: <N>/11 gates met
   ```

---

## Academic quality checklist (run before any DONE promotion)

- [ ] Evidence physically exists (file, test pass, Parquet row)
- [ ] Claim level is L2 or L3 (not L1 prediction)
- [ ] Parity gate passed (`parity_pass = True` in harness row) if physics changed
- [ ] Hardware matrix requirement met for the claimed level
- [ ] No `OPEN:` markers remain in the lane's `.md` spec
- [ ] Focused pytest passes in this repo (not just on LUNARC)
- [ ] File line caps respected (no file > 500 lines without planner note)
- [ ] No placeholder text (`TODO`, `TBD`, `FIXME`, `placeholder`) in committed files
- [ ] If a thesis number is cited: the specific thesis section is named and the
      sample that reproduces it is identified

---

## Boundaries

- Never edits production simulation or reconstruction code.
- Never promotes a thesis number — only records evidence presence/absence.
- Never submits an sbatch job directly — queues the task for the responsible lane.
- Never re-implements work another lane owns — files a precise `OPEN:` and
  queues a fix task instead.
- Respects G4GPU isolation: `docs/policies/g4gpu-isolation.md`.
- The loop continues every iteration. There is no "done" state for this lane
  until all milestone gates in `docs/specs/paper-methodology.md` are checked.
