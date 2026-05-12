# G4GPU bottleneck database gap scan — 2026-05-12

Lane: worker-3 / G4GPU isolated  
Iteration type: fallback gap scan after empty worker-3 queue  
Timestamp: 2026-05-12 11:58 CEST

## Purpose

Worker-3 had no queued G4GPU prompt and the G4GPU section of
`MASTER_PLAN.md` had no `NEXT` row. Instead of repeating the Celeritas job
3047497 monitor only minutes after the 11:46 refresh, this compact iteration
checks the Geant4 bottleneck-report surface for two coordination hazards:

1. file-cap pressure that could cause the next shard to violate the 500-line
   limit; and
2. duplicate or missing primary `BD-geant4-*` identifiers before the next
   source-review or implementation shard is queued.

No LUNARC build, local compiler, CUDA, Geant4/G4GPU executable, SLURM submit,
or NNBAR production edit was performed.

## Queue evidence

Read-only queue check:

```text
codex-tasks/g4gpu/worker-0.txt 0 bytes 0 lines
codex-tasks/g4gpu/worker-1.txt 0 bytes 0 lines
codex-tasks/g4gpu/worker-2.txt 0 bytes 0 lines
codex-tasks/g4gpu/worker-3.txt 0 bytes 0 lines
G4GPU NEXT lines in MASTER: none
```

The closest active worker-3 item remains `MCAccel competitor benchmarks`, but
its Celeritas job evidence was already refreshed at 11:46 CEST and the
scheduler estimate remained 2026-05-13 07:58:30, so another immediate monitor
would add no new artifact.

## File-cap scan

```text
492 docs/reports/bottleneck_database_geant4.md
401 docs/reports/g4_bottleneck_database_pil_geometry.md
206 docs/reports/g4_bottleneck_database_em_gamma.md
206 docs/reports/g4_bottleneck_database_charged_transport.md
205 docs/reports/g4_bottleneck_database_neutron_hp.md
204 docs/reports/g4_bottleneck_database_decay_stopping.md
203 docs/reports/g4_bottleneck_database_ion_elastic.md
203 docs/reports/g4_bottleneck_database_optical_photons.md
203 docs/reports/g4_bottleneck_database_tracking_manager.md
200 docs/reports/g4_bottleneck_database_hadronic_proton.md
194 docs/reports/g4_bottleneck_database_hits_sd.md
```

Disposition:

- `docs/reports/bottleneck_database_geant4.md` is at 492 lines. Treat it as
  sealed; do not append new entries there.
- `docs/reports/g4_bottleneck_database_pil_geometry.md` is below the cap at
  401 lines but should also remain stable unless fixing existing content.
- Future Geant4 bottleneck reviews should create a new shard file rather than
  extending either high-line-count report.

## Primary identifier map

Primary heading parse over `bottleneck_database_geant4.md` and
`g4_bottleneck_database_*.md` found:

```text
primary unique 130; min 001; max 130
primary missing []
primary duplicates {}
next free 10-ID block: BD-geant4-131--140
```

Current primary shards:

```text
docs/reports/bottleneck_database_geant4.md                 23  BD-geant4-001--023
docs/reports/g4_bottleneck_database_hits_sd.md              8  BD-geant4-024--031
docs/reports/g4_bottleneck_database_pil_geometry.md        19  BD-geant4-032--050
docs/reports/g4_bottleneck_database_optical_photons.md     10  BD-geant4-051--060
docs/reports/g4_bottleneck_database_em_gamma.md            10  BD-geant4-061--070
docs/reports/g4_bottleneck_database_neutron_hp.md          10  BD-geant4-071--080
docs/reports/g4_bottleneck_database_charged_transport.md   10  BD-geant4-081--090
docs/reports/g4_bottleneck_database_decay_stopping.md      10  BD-geant4-091--100
docs/reports/g4_bottleneck_database_tracking_manager.md    10  BD-geant4-101--110
docs/reports/g4_bottleneck_database_ion_elastic.md         10  BD-geant4-111--120
docs/reports/g4_bottleneck_database_hadronic_proton.md     10  BD-geant4-121--130
```

## Recommended next compact task

When another Geant4 source-review shard is queued, reserve
`BD-geant4-131--140` in a new report file. Do not append to the 492-line root
Geant4 database. For worker-3 specifically, the next non-repeating compact
monitor should wait until job 3047497 changes state or until after the
scheduler-estimated start window on 2026-05-13.
