# G4GPU Phase 8 survey line-cap drift audit

Date: 2026-05-17
Pane/lane: PANE 4 / `worker-4` (G4GPU source-code review + research, isolated)
Role type: `specialist-contractor`
Manager / escalation: `VALIDATOR`
Factory item: A1 / artifact-ledger evidence for G4GPU survey hygiene
Branch/worktree: `main` at `/Volumes/MyDrive/nnbar/nnbar/simulation`
Writable lease used this iteration: this report only under `docs/reports/g4gpu_*.md`

## Start-of-iteration protocol evidence

- Read `docs/parallel-sessions.md`, `docs/parallel-sessions/AI_FACTORY.md`,
  `docs/parallel-sessions/TEAM_PLAN.md`, and `docs/parallel-sessions/worker-4.md`.
- Read the company operating model and version board addenda required by the factory protocol.
- Active task directory: `codex-tasks/g4gpu/`.
- Blocker queue checked: `codex-tasks/g4gpu/blockers.txt` contains no active `/goal` line.
- Lane queue checked: `codex-tasks/g4gpu/worker-4.txt` is empty.
- MASTER_PLAN scan: no `NEXT` G4GPU source-review, survey, research, or algorithm row matched worker-4 scope.

## Compact gap selected

With no claimable queue item, worker-4 followed the gap-scan fallback and checked
line-cap risk in the lane report surface. The current working tree has a Phase 8
survey drift:

```text
docs/reports/algorithm_survey_for_geant4.md: 1393 lines
```

The active cap from `docs/parallel-sessions.md` is 500 lines per file. The same
artifact was previously accepted in `MASTER_PLAN.md` with evidence claiming
`algorithm_survey_check lines=407`, so the present 1393-line state is a
post-acceptance drift or uncommitted expansion, not the accepted baseline.

## Root-cause evidence

- `git diff --numstat -- docs/reports/algorithm_survey_for_geant4.md` reports
  `1366` insertions and `380` deletions relative to `HEAD`.
- `git status --short -- docs/reports/algorithm_survey_for_geant4.md` reports the
  file as modified before this iteration.
- The file is not in this iteration's writable lease because worker-4's current
  hard allowed list is `docs/reports/g4_*.md`, `docs/reports/g4gpu_*.md`, and
  `docs/reports/ml_*.md`; directly rewriting the dirty non-matching file would
  risk committing another pane's in-flight content.

## Recommended bounded fix

Queue a validator-owned or Phase 8 owner-owned split task instead of letting the
large report continue to grow:

1. Freeze `docs/reports/algorithm_survey_for_geant4.md` as a <=500-line index
   containing the executive summary, acceptance checklist, and links to parts.
2. Move deterministic method details into `docs/reports/g4gpu_phase8_algorithm_survey_methods_part1_20260517.md`
   and `docs/reports/g4gpu_phase8_algorithm_survey_methods_part2_20260517.md`.
3. Move rankings, validation gates, package proposals, matrices, and references
   into `docs/reports/g4gpu_phase8_algorithm_survey_validation_refs_20260517.md`.
4. Re-run a structural survey check that verifies D01--D28, references R1--R47,
   ML disclaimer, validation gates, and at least seven Phase 8+ packages across
   the split files, not just the index.
5. Only then update `MASTER_PLAN.md` evidence from the stale 407-line claim to
   the split-manifest evidence.

## Handoff

Factory item: A1 / G4GPU survey hygiene artifact
Blocker queue checked: `codex-tasks/g4gpu/blockers.txt` -- no active `/goal` line
Verification evidence: queue validation passed and this report is under the
worker-4 writable report lease.
Next validator action: assign a split-manifest task to the Phase 8 survey owner
or explicitly extend worker-4's lease to edit `algorithm_survey_for_geant4.md`.

## Verification commands run

```text
python line-count check:
docs/reports/algorithm_survey_for_geant4.md: 1393 lines

bash scripts/validate-csup-queues.sh:
files scanned: 54
prompt lines checked: 74
failures: 0
OK: every prompt line passes all mechanical checks.
```
