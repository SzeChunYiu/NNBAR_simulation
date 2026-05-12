# Geant4 source-review completion audit

Date: 2026-05-12  
Lane:  / worker-0 compact completion pass

## Scope

This audit closes the cumulative acceptance gate for
. The source-review database now
uses sharded report files because the root database is near the 500-line cap.
This pass made two metadata-only corrections before closure:

- normalized  entries
  -- from  to the required
   field name;
- disambiguated the multi-file  fields in
   for ,
  , and  so each source range maps to its
  intended Geant4 file.

No C++, CUDA, NNBAR production, SLURM, macro, reconstruction, or data files were
changed.

## Shard inventory

| Shard | ID range | Entries | Lines |
| --- | ---: | ---: | ---: |
|  | 001-023 | 23 | 492 |
|  | 024-031 | 8 | 194 |
|  | 032-050 | 19 | 401 |
|  | 051-060 | 10 | 203 |
|  | 061-070 | 10 | 206 |
|  | 071-080 | 10 | 205 |
|  | 081-090 | 10 | 206 |
|  | 091-100 | 10 | 204 |
|  | 101-110 | 10 | 203 |
|  | 111-120 | 10 | 203 |
|  | 121-130 | 10 | 200 |
|  | 131-140 | 10 | 231 |
|  | 141-150 | 10 | 238 |

Coverage evidence: 150 contiguous, unique  headings; no duplicate or
missing IDs; every entry carries the required structured fields (,
, , , ,
, , , ,
, , and ). Every shard remains below
500 lines.

## Cumulative top-10 implementation ranking

Ranked by expected impact, validation clarity, and implementation effort from
all open source-review entries:

1.  /  — vectorized and branch-reduced physics
   vector lookup/interpolation for the cross-section hot path.
2.  /  — branchless CSG box/tube distance tests
   as an upstreamable geometry L0 win.
3.  /  — process dispatch descriptors plus a
   compact PostStep invocation list.
4.  /  — HP cross-section lookup and cumulative
   sampling acceleration.
5.  /  — hadronic cross-section store and target
   sampling cache/perfect-hash work.
6.  /  — scalar EM rejection-sampler reductions
   for Compton and pair production.
7.  — replace scalar HepJamesRandom hot-loop generation with a
   validated faster RNG/QMC-compatible path.
8.  /  — pool/arena allocation for secondaries,
   tracks, steps, and particle-change boundaries.
9.  — hits-collection ID perfect hash to remove repeated string
   scans in detector setup/initialization paths.
10.  /  — field-manager and navigator relocation
    caching for charged-particle field transport.

## Verification evidence

Fresh local checks from the simulation worktree:

/tmp/geant4-v11.2.2

Queue validation was run after the metadata corrections and completion-status
edit; see the MASTER_PLAN completion note for the exact validator output.

## Completion decision

 satisfies the lane acceptance criteria: all original hot
paths are covered, the database exceeds the 50-entry target, the required fields
are present on every entry, a cumulative top-10 implementation ranking exists,
source windows are parseable against the Geant4 source cache, and every shard is
under the file cap. The lane is ready to transition from  to  in
.
