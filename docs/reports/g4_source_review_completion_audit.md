# Geant4 source-review completion audit

Date: 2026-05-12  
Lane: g4-source-review / worker-0 compact completion pass

## Scope

This audit closes the cumulative acceptance gate for the `g4-source-review`
lane. The source-review database now uses sharded report files because the root
database is near the 500-line cap. This pass made two metadata-only corrections
before closure:

- normalized `docs/reports/g4_bottleneck_database_process_manager.md` entries
  from `Validation strategy` to the required `Validation` field name;
- disambiguated the multi-file `Lines` fields in
  `docs/reports/g4_bottleneck_database_hits_sd.md` for `BD-geant4-024`,
  `BD-geant4-026`, and `BD-geant4-031` so each source range maps to its
  intended Geant4 file.

No C++, CUDA, NNBAR production, SLURM, macro, reconstruction, or data files were
changed.

## Shard inventory

| Shard | ID range | Entries | Lines |
| --- | ---: | ---: | ---: |
| `docs/reports/bottleneck_database_geant4.md` | 001-023 | 23 | 492 |
| `docs/reports/g4_bottleneck_database_hits_sd.md` | 024-031 | 8 | 194 |
| `docs/reports/g4_bottleneck_database_pil_geometry.md` | 032-050 | 19 | 401 |
| `docs/reports/g4_bottleneck_database_optical_photons.md` | 051-060 | 10 | 203 |
| `docs/reports/g4_bottleneck_database_em_gamma.md` | 061-070 | 10 | 206 |
| `docs/reports/g4_bottleneck_database_neutron_hp.md` | 071-080 | 10 | 205 |
| `docs/reports/g4_bottleneck_database_charged_transport.md` | 081-090 | 10 | 206 |
| `docs/reports/g4_bottleneck_database_decay_stopping.md` | 091-100 | 10 | 204 |
| `docs/reports/g4_bottleneck_database_tracking_manager.md` | 101-110 | 10 | 203 |
| `docs/reports/g4_bottleneck_database_ion_elastic.md` | 111-120 | 10 | 203 |
| `docs/reports/g4_bottleneck_database_hadronic_proton.md` | 121-130 | 10 | 200 |
| `docs/reports/g4_bottleneck_database_process_manager.md` | 131-140 | 10 | 231 |
| `docs/reports/g4_bottleneck_database_field_transport.md` | 141-150 | 10 | 238 |

Coverage evidence: 150 contiguous, unique `BD-geant4-*` headings; no duplicate
or missing IDs; every entry carries the required structured fields (`File`,
`Lines`, `Hot-path % (profile-measured)`, `Category`, `Current pattern`, `Why
slow`, `Proposed fix`, `Expected speedup`, `Validation`, `Implementation
target`, `Citation`, and `Status`). Every shard remains below 500 lines.

## Cumulative top-10 implementation ranking

Ranked by expected impact, validation clarity, and implementation effort from
all open source-review entries:

1. `BD-geant4-039` / `BD-geant4-040` — `PhysicsVector value lookup mixes
   cached-bin, bounds, and general-bin paths` plus `PhysicsVector interpolation
   pays a division and spline branch per lookup`: vectorized and branch-reduced
   physics-vector lookup/interpolation for the cross-section hot path.
2. `BD-geant4-048` / `BD-geant4-049` — `Box DistanceToIn uses branchy scalar
   slab tests` plus `Tube DistanceToIn branch ladder duplicates z, radius, and
   phi cases`: branchless CSG box/tube distance tests as upstreamable geometry
   L0 wins.
3. `BD-geant4-032` / `BD-geant4-139` — `PostStep GPIL scans every candidate
   process through an indirect call` plus `PostStep DoIt dispatch scans inverse
   order and condition flags after the winner is known`: process dispatch
   descriptors plus a compact PostStep invocation list.
4. `BD-geant4-071` / `BD-geant4-072` — `HP cross-section lookup scans forward
   from a hash hint and branches through interpolation policy` plus `HP vector
   sampling linearly searches cumulative bins and rejection-samples the local
   segment`: HP cross-section lookup and cumulative sampling acceleration.
5. `BD-geant4-122` / `BD-geant4-123` — `Hadronic cross-section store scans
   material elements and dataset fallbacks per query` plus `Hadronic target
   sampling linearly scans element and isotope cumulative weights`: hadronic
   cross-section store and target-sampling cache/perfect-hash work.
6. `BD-geant4-063` / `BD-geant4-070` — `Klein-Nishina Compton sampling uses
   scalar rejection and immediate heap allocation` plus `Pair-production epsilon
   sampling repeats screening/LPM functions in rejection loop`: scalar EM
   rejection-sampler reductions for Compton and pair production.
7. `BD-geant4-012` — `HepJamesRandom flatArray is scalar and branch-heavy
   despite being called in sampling loops`: replace scalar hot-loop generation
   with a validated faster RNG/QMC-compatible path.
8. `BD-geant4-013` / `BD-geant4-017` — `G4ParticleChange creates heap tracks
   for every secondary crossing the model boundary` plus `G4Step owns step
   points and secondary vectors through per-object heap allocations`: pool/arena
   allocation for secondaries, tracks, steps, and particle-change boundaries.
9. `BD-geant4-026` — `Hits-collection ID lookup is a linear string scan with
   per-query concatenation`: hits-collection ID perfect hash to remove repeated
   string scans in detector setup/initialization paths.
10. `BD-geant4-141` / `BD-geant4-144` — `Field-manager lookup and
    reconfiguration are repeated on every charged step` plus `Every non-first
    field substep relocates the navigator before chord intersection`:
    field-manager and navigator-relocation caching for charged-particle field
    transport.

## Verification evidence

Fresh local checks from the simulation worktree:

- `rtk wc -l docs/reports/g4_source_review_completion_audit.md` keeps this
  report under the 500-line cap.
- The completion-audit text verifier prints `G4_AUDIT_TEXT_OK` after checking
  for blank placeholder patterns and required tokens including
  `g4-source-review`, `BD-geant4-`, `NEXT`, `DONE`, and
  `docs/reports/g4_bottleneck_database`.
- The shard inventory checker finds 150 contiguous unique `BD-geant4-*` IDs,
  0 missing required fields, and maximum shard length 492 lines.
- Earlier source-window verification for the completion pass validated the
  cited Geant4 windows against `/tmp/geant4-v11.2.2` with 0 unparsed ranges and
  0 problems; this text repair does not change any shard source range.
- `rtk bash scripts/validate-csup-queues.sh` passes after the repair-lane
  `NEXT` -> `DONE` status edit.

## Completion decision

`g4-source-review` satisfies the lane acceptance criteria: all original hot
paths are covered, the database exceeds the 50-entry target, the required
fields are present on every entry, a cumulative top-10 implementation ranking
exists, source windows are parseable against the Geant4 source cache, and every
shard is under the file cap. The follow-up text-repair lane is ready to
transition from `NEXT` to `DONE` in `docs/parallel-sessions/MASTER_PLAN.md`.
