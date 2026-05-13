# Paper section 2 — Geant4 hot-path analysis evidence plan

Status: **BLOCKED**

This specification defines the evidence required for the paper's hot-path
analysis section. It governs how the bottleneck database, source-review notes,
and profiling evidence can be used before any optimization result is discussed.

## Section purpose

Section 2 explains how candidate acceleration targets were selected from
Geant4 source review and measured profiles. It may include L1 literature-backed
or source-structure hypotheses only when they are labelled as motivation; the
section must distinguish those hypotheses from measured L2/L3 bottleneck
attribution.

## Required evidence before prose can be drafted

- The 50-entry Geant4 bottleneck database has stable IDs, file paths, line
  references, and mechanism descriptions.
- Any profile percentage is tied to a workload, physics list, hardware ID,
  command, and saved profiler output.
- Any expected speedup remains labelled as an estimate unless a harness row or
  profiler-backed measurement supports it.
- Source excerpts are limited to short, line-anchored references and do not
  replace primary citation or profiler evidence.
- G4GPU isolation is explicit: hot-path analysis may motivate isolated G4GPU
  branches but does not imply NNBAR production code has changed.

## Figures and tables

- Table 2.1: bottleneck database clusters, BD IDs, source files, and mechanism.
- Table 2.2: profile-attribution evidence by workload and physics list.
- Figure 2.1: hot-path taxonomy across EM, hadronic, geometry, and event/kernel
  overhead groups.
- Figure 2.2: representative profiler stack or flame graph for a measured L2+
  row.

## Current gaps

- OPEN: `profile_matrix_missing` — profile evidence is not yet connected to the
  fixed W1--W6 workload and physics-list matrix.
- OPEN: `l1_speedups_unmeasured` — many `Expected speedup` entries in
  `docs/reports/bottleneck_database_geant4.md` remain estimates rather than
  harness-supported measurements.
- OPEN: `harness_rows_missing` — `benchmarks/results/results.parquet` is absent.
- OPEN: `source_line_audit_incomplete` — every BD row needs a short source-line
  audit trail before final prose can cite it.

## Acceptance checklist

- [ ] Every cited BD ID has a source-line and mechanism entry.
- [ ] Every profile number has saved profiler evidence and environment metadata.
- [ ] L1 estimates are labelled as motivation, not results.
- [ ] L2/L3 attribution rows link to the benchmark harness or saved profiler
      artifact.
- [ ] Section 5 receives a queued harness task for any hot-path claim promoted
      beyond motivation.
