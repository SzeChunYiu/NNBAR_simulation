# G4GPU worker-4 compact queue/catalog audit — 2026-05-13

Lane: worker-4 / G4GPU source-code review + research, isolated  
Iteration type: fallback compact-safe audit after no worker-4 source-review or survey task  
Timestamp: 2026-05-13 07:05 CEST

## Purpose

Worker-4 was asked to complete one compact-safe iteration after re-reading
`docs/parallel-sessions.md` and `docs/parallel-sessions/worker-4.md`. The
legacy local `codex-tasks/worker-4.txt` is inactive, the active G4GPU/review
queues have no worker-4 source-review prompt, and the only G4GPU `NEXT` row is
Phase 4 Opticks integration queued to `codex-tasks/g4gpu/worker-1.txt`, which is
an implementation lane rather than this source-review/report lane.

Per the shared non-idle rule, this iteration produces a bounded audit artifact
instead of claiming an out-of-scope NNBAR or implementation task. It does not
modify Geant4, G4GPU, NNBAR production code, build scripts, SLURM scripts, or
production data.

## Queue and MASTER_PLAN evidence

Read-only queue scan from the simulation worktree:

```text
codex-tasks/worker-4.txt: bytes=214 noncomment_lines=0 first=''
codex-tasks/g4gpu/worker-0.txt: bytes=0 noncomment_lines=0 first=''
codex-tasks/g4gpu/worker-1.txt: bytes=170 noncomment_lines=1 first='/goal You are PANE 1, lane g4gpu-phase4...'
codex-tasks/g4gpu/worker-2.txt: bytes=0 noncomment_lines=0 first=''
codex-tasks/g4gpu/worker-3.txt: bytes=0 noncomment_lines=0 first=''
codex-tasks/review/worker-0.txt: bytes=0 noncomment_lines=0 first=''
codex-tasks/review/worker-1.txt: bytes=0 noncomment_lines=0 first=''
codex-tasks/sim/worker-4.txt: bytes=273 noncomment_lines=1 first='/goal add SetUserMinEkine... in NNBAR_Detector...'
```

G4GPU section status counts from `docs/parallel-sessions/MASTER_PLAN.md`:

```text
NEXT 1
RUNNING 3
PLANNED 4
DONE 36
```

Disposition:

- `codex-tasks/g4gpu/worker-1.txt` is Phase 4 Opticks integration for pane 1;
  worker-4 did not claim it because worker-4 is documentation/source-review
  only.
- `codex-tasks/sim/worker-4.txt` is an NNBAR detector-construction task under
  `NNBAR_Detector/`, explicitly outside the worker-4 G4GPU isolation scope.
- No active review queue prompt was available for a fresh source-review shard.

## Geant4 bottleneck catalog audit

A structural verifier scanned the Geant4 bottleneck catalog files:

- `docs/reports/bottleneck_database_geant4.md`
- every `docs/reports/g4_bottleneck_database_*.md` shard

Required fields checked per `BD-geant4-*` entry were: `File`, `Lines`,
`Current pattern`, `Why slow`, `Proposed fix`, `Expected speedup`, `Validation`,
`Implementation target`, `Citation`, and `Status`.

Verifier result:

```text
G4_CATALOG_AUDIT_OK
files=13
unique_ids=150 min=BD-geant4-001 max=BD-geant4-150
missing_numbers=[]
duplicates={}
missing_field_entries=0
```

Interpretation: the current structured Geant4 bottleneck catalog is contiguous
through `BD-geant4-150`, has no duplicate primary IDs, and each primary entry in
the parsed files exposes the required structured fields.

## File-cap scan

```text
492 docs/reports/bottleneck_database_geant4.md
401 docs/reports/g4_bottleneck_database_pil_geometry.md
238 docs/reports/g4_bottleneck_database_field_transport.md
231 docs/reports/g4_bottleneck_database_process_manager.md
206 docs/reports/g4_bottleneck_database_charged_transport.md
206 docs/reports/g4_bottleneck_database_em_gamma.md
205 docs/reports/g4_bottleneck_database_neutron_hp.md
204 docs/reports/g4_bottleneck_database_decay_stopping.md
203 docs/reports/g4_bottleneck_database_ion_elastic.md
203 docs/reports/g4_bottleneck_database_optical_photons.md
203 docs/reports/g4_bottleneck_database_tracking_manager.md
200 docs/reports/g4_bottleneck_database_hadronic_proton.md
194 docs/reports/g4_bottleneck_database_hits_sd.md
```

Disposition:

- `docs/reports/bottleneck_database_geant4.md` is at 492 lines and must remain
  sealed except for small corrective edits; do not append new entries there.
- `docs/reports/g4_bottleneck_database_pil_geometry.md` is below the 500-line
  cap but should not receive new findings unless they are corrective edits.
- The next new Geant4 source-review shard should reserve `BD-geant4-151`--
  `BD-geant4-160` and use a fresh `docs/reports/g4_bottleneck_database_*.md`
  file.

## Optimization findings and validation strategy

This audit flags no new optimization opportunities. Therefore it has no new
Geant4 source file line ranges, code snippets, standard CS-technique citations,
or physics-preservation validation strategies to attach. Existing optimization
opportunities remain the structured `BD-geant4-001`--`BD-geant4-150` entries.

## Concrete next-step proposal

Planner can queue worker-4 for a non-overlapping Geant4 source-review shard
starting at `BD-geant4-151`, or queue worker-3/phase lanes to implement one of
the existing high-ranked `BD-geant4-*` entries. Any new worker-4 shard should
include exact file paths, line ranges, current-code snippets, expected speedup,
citations for standard techniques, and one validation strategy per
recommendation.

## Verification commands

```text
rtk proxy bash -lc 'set -euo pipefail; python3 - <<PY ... PY; bash scripts/validate-csup-queues.sh'
```

Observed verification:

```text
G4_CATALOG_AUDIT_OK
files=13
unique_ids=150 min=BD-geant4-001 max=BD-geant4-150
missing_numbers=[]
duplicates={}
missing_field_entries=0
scripts/validate-csup-queues.sh: files scanned: 27; prompt lines checked: 31; failures: 0
```
