# Lane: g4-pil-geometry-structured-shard

## Goal

Convert the legacy Geant4 PIL and geometry free-form findings into the
structured bottleneck-database format without repeating existing structured
entries. This is a documentation/source-review lane only; do not edit Geant4,
G4GPU, NNBAR production code, scripts, macros, SLURM files, or reconstruction
code.

## Writable scope

- Create or update: `docs/reports/g4_bottleneck_database_pil_geometry.md`
- Update after completion only: `docs/parallel-sessions/MASTER_PLAN.md`
- Do not append entries to `docs/reports/bottleneck_database_geant4.md`; that
  file is already near the 500-line cap.
- Do not edit `docs/reports/g4_bottleneck_database_hits_sd.md` except to check
  ID continuity.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/parallel-sessions/g4-source-review.md`
4. `docs/specs/mcaccel-bottleneck-methodology.md`
5. `docs/reports/g4_source_review_hotpaths.md`
6. `docs/reports/bottleneck_database_geant4.md`
7. `docs/reports/g4_bottleneck_database_hits_sd.md`

## One compact-safe iteration

1. Confirm existing structured IDs end at `BD-geant4-031` across the main
   database and hit/SD shard.
2. Create `docs/reports/g4_bottleneck_database_pil_geometry.md` if needed.
   The file must explain that it is a shard for structured PIL/geometry
   conversion of the legacy report.
3. Convert one compact batch of legacy PIL/geometry findings into structured
   entries, starting at `BD-geant4-032`. A good batch size is 8--10 entries,
   but stop earlier if the shard approaches 400 lines.
4. Each new entry must use the exact table fields from
   `docs/specs/mcaccel-bottleneck-methodology.md`: File, Lines, Hot-path %,
   Category, Current pattern, Why slow, Proposed fix, Expected speedup,
   Validation, Implementation target, Citation, and Status.
5. For every new file/line claim, inspect the Geant4 `v11.2.2` source under
   `/tmp/geant4-v11.2.2` and quote only ranges that contain the referenced
   function or code pattern. If the source tree is absent, use the guarded
   LUNARC socket command from `docs/parallel-sessions/MASTER_PLAN.md`, inspect
   the source remotely, and record the blocker if source still cannot be found.
6. Do not invent profile self-percentages. Use the existing hot-path aggregate
   percentages or mark exact per-line values `OPEN:` with the required Phase 5
   perf-map follow-up.
7. Update `MASTER_PLAN.md` only after the shard passes verification: mark this
   lane `DONE`, state the ID range added, and leave `g4-source-review` RUNNING
   until the cumulative database reaches the 50+ entry acceptance target.

## Verification commands

Run these from the simulation repo root before committing:

```bash
rtk wc -l docs/reports/g4_bottleneck_database_pil_geometry.md docs/parallel-sessions/MASTER_PLAN.md
rtk proxy python - <<'PY'
from pathlib import Path
paths = [
    Path('docs/reports/bottleneck_database_geant4.md'),
    Path('docs/reports/g4_bottleneck_database_hits_sd.md'),
    Path('docs/reports/g4_bottleneck_database_pil_geometry.md'),
]
ids = []
for path in paths:
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith('### BD-geant4-'):
                ids.append(line.split()[1])
print('ids', len(ids), ids[:1], ids[-1:])
assert len(ids) == len(set(ids)), 'duplicate BD-geant4 IDs'
assert 'BD-geant4-032' in ids, 'new shard did not start at BD-geant4-032'
PY
```

Also include the exact source-inspection snippets you used for each new line
range in the commit message or handoff note.

## Stop condition

Stop after one verified shard batch is committed and this lane row is marked
`DONE` in `MASTER_PLAN.md`. If source-line verification fails, do not guess;
write the smallest blocker note in the shard and stop.
