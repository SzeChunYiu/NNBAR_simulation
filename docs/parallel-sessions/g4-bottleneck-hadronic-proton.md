# Lane: g4-bottleneck-hadronic-proton

## Goal

Write one structured Geant4 v11.2.2 source-review shard for hadronic proton/ion
physics at `docs/reports/g4_bottleneck_database_hadronic_proton.md`.

## Writable scope

- `docs/reports/g4_bottleneck_database_hadronic_proton.md`
- `docs/parallel-sessions/MASTER_PLAN.md` only for the final status note

Do not edit NNBAR production code, Geant4 source, G4GPU source, SLURM scripts,
or data files.

## Required entry range

- Use `BD-geant4-121` through `BD-geant4-130`.
- Do not repeat any existing or queued IDs in `BD-geant4-001` through
  `BD-geant4-120`.

## Review scope

Cover hadronic proton/ion physics hot paths, including:

- `G4ProtonInelasticProcess`
- `G4BinaryLightIonReaction`
- `G4INCLXXInterface`
- `G4IntraNucleiCascader`
- cross-section lookup/interpolation paths relevant to proton/ion transport

Use the existing structured shard format from `docs/reports/g4_bottleneck_*`.

## Verification

1. Confirm the Geant4 v11.2.2 source mirror exists, typically
   `/tmp/geant4-v11.2.2`. If it is absent, stop with a blocker note instead of
   inventing line references.
2. For every cited function/class/source range, run a signature grep against the
   source mirror and ensure the match lies inside the cited range.
3. Verify the report has exactly ten new entries with all required fields.
4. Run `wc -l docs/reports/g4_bottleneck_database_hadronic_proton.md` and keep
   the file under 500 lines.

## Stop condition

Commit only the report plus the `MASTER_PLAN.md` status update. Mark the shard
`DONE` only after the line-reference checks and file-cap check pass; otherwise
leave a precise blocker in the status note.
