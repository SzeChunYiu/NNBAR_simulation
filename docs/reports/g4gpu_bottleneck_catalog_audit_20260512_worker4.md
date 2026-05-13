# G4GPU bottleneck catalog audit — worker-4, 2026-05-12

Lane: worker-4 / G4GPU source-code review + research, isolated  
Iteration type: fallback compact gap scan after empty worker-4/G4GPU queue  
Timestamp: 2026-05-12 13:59 CEST

## Purpose

The active worker-4 queue surface had no queued source-review or survey prompt,
and the G4GPU section of `docs/parallel-sessions/MASTER_PLAN.md` had no `NEXT`
row. Per the shared non-idle iteration rule, this compact iteration audits the
Geant4 bottleneck-report catalog after the latest source-review shards so the
next planner/worker can safely continue without reusing IDs or appending to a
near-cap file.

This is a coordination and evidence artifact only. It does not add new
optimization findings, does not modify Geant4/G4GPU/NNBAR source code, does not
build anything, and does not submit SLURM jobs.

## Queue and task-state evidence

Read-only queue scan:

```text
codex-tasks/g4gpu/worker-0.txt: bytes=0 noncomment_lines=0
codex-tasks/g4gpu/worker-1.txt: bytes=0 noncomment_lines=0
codex-tasks/g4gpu/worker-2.txt: bytes=0 noncomment_lines=0
codex-tasks/g4gpu/worker-3.txt: bytes=0 noncomment_lines=0
G4GPU NEXT=0
G4GPU RUNNING=3
```

The legacy local `codex-tasks/worker-4.txt` is marked inactive and points to the
active LUNARC queue directories. `codex-tasks/sim/worker-4.txt` contains an
NNBAR detector-construction task and is outside this lane's isolation scope, so
it was not claimed.

## Catalog inventory verifier

Verifier command run from the simulation worktree:

```text
python3 - <<'PY'
from pathlib import Path
import re
files = [Path('docs/reports/bottleneck_database_geant4.md')] + \
        sorted(Path('docs/reports').glob('g4_bottleneck_database_*.md'))
required = ['File','Lines','Current pattern','Why slow','Proposed fix',
            'Expected speedup','Validation','Implementation target',
            'Citation','Status']
# Parse primary headings of the form: ### BD-geant4-NNN ...
PY
```

Result:

```text
files=13
unique_ids=150 min=BD-geant4-001 max=BD-geant4-150
missing_numbers=[]
duplicates={}
missing_field_entries=0
```

Interpretation: the current Geant4 bottleneck catalog is contiguous through
`BD-geant4-150`, has no duplicate primary IDs, and every primary entry in the
13 parsed files exposes the required structured fields checked above.

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
- `docs/reports/g4_bottleneck_database_pil_geometry.md` is below the cap but is
  large enough that future new findings should use a new shard, not this file.
- The next source-review shard, if queued, should reserve `BD-geant4-151`--
  `BD-geant4-160` and live in a fresh `docs/reports/g4_bottleneck_database_*.md`
  file.

## Isolation and recommendation

No optimization opportunities are newly flagged in this report, so there are no
new source file line ranges, code snippets, or physics-preservation validation
plans to attach. Existing optimization opportunities remain the structured
`BD-geant4-001`--`BD-geant4-150` entries.

Concrete next-step proposal: planner can either queue an implementation task for
one of the existing high-ranked `BD-geant4-*` entries or queue worker-4 for a new
non-overlapping Geant4 source-review shard starting at `BD-geant4-151`. Any new
source-review shard should include exact file paths, line ranges, current-code
snippets, expected speedup, citations for standard techniques, and a validation
strategy per recommendation.
