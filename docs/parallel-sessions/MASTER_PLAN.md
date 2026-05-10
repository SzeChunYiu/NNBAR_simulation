# NNBAR Project Master Plan

Last updated: 2026-05-11

This document is the single source of truth for all outstanding work across both
the NNBAR simulation/reconstruction project and the G4GPU side project.
Every codex lane should read this file at start and at finish to check for new tasks.

---

## Status Legend

- `DONE` — committed and merged
- `RUNNING` — currently in a codex pane
- `NEXT` — ready to start, spec exists
- `PLANNED` — scoped but no spec yet
- `BLOCKED` — waiting on dependency

---

## NNBAR Simulation (C++ / LUNARC)

| Task | Status | Lane | Notes |
|------|--------|------|-------|
| Build binary with Geant4 + MCPL | DONE | lunarc-build | job 3039997 |
| Signal run 1000 events | DONE | — | job 3040024, Parquet output verified |
| **CRY cosmic generator C++** | NEXT | cry-integration | See docs/parallel-sessions/cry-integration.md |
| **CRY SLURM array (30 jobs)** | BLOCKED | — | Needs CRY C++ merged + binary rebuilt first |
| Cosmic weight computation script | PLANNED | — | Python, applies w_{i,j} from thesis Eq. 6.1 |

---

## NNBAR Reconstruction (Python)

| Task | Status | Lane | Notes |
|------|--------|------|-------|
| data_pipeline package | DONE | data-pipeline | Merged |
| clustering enhancements | DONE | clustering | Merged |
| End-to-end pipeline runner + tests | DONE | reco-pipeline | Merged, 3 tests pass |
| **Random Forest Classifier** | NEXT | rfc-classifier | See docs/parallel-sessions/rfc-classifier.md |
| π⁰ 60% lead glass cut verification | PLANNED | — | Check object_identification.py thresholds vs thesis Table 10.1 |
| Opening angle threshold (30°) | PLANNED | — | Verify value in object_identification.py |
| Material budget analysis script | PLANNED | — | Low priority — analysis only |

---

## G4GPU Side Project (geant4-gpu repo)

| Task | Status | Lane | Notes |
|------|--------|------|-------|
| DESIGN_BRIEF + SPEC + VALIDATION docs | DONE | — | Committed in geant4-gpu repo |
| **Phase 0 infrastructure** | DONE | g4gpu-phase0 | libG4GPU.so built on LUNARC, test_stub PASS |
| **Phase 1: Muon physics kernel** | NEXT | g4gpu-phase1 | See docs/parallel-sessions/g4gpu-phase1.md |
| Phase 2: Voxel geometry (3DDA) | PLANNED | — | After Phase 1 tests pass |
| Phase 3: RTX geometry backend | PLANNED | — | Requires OptiX SDK on LUNARC |
| Phase 4: Optical photon (OptiX) | PLANNED | — | Long-term |

---

## Codex Self-Check Protocol

At the end of every lane goal, the codex agent MUST:
1. Re-read this file (MASTER_PLAN.md)
2. Check: are there tasks marked NEXT that match your expertise? If yes, start one.
3. Check: does your completed work unlock a BLOCKED task? If yes, update this file.
4. If no new work available, write "IDLE: no NEXT tasks match this lane's scope" to stdout.

---

## Key Facts Every Lane Needs

- LUNARC SSH: `ssh lunarc "cmd"` — pre-multiplexed
- SLURM account: `lu2026-2-51` | partition: `lu48` (CPU), `gpua40` (GPU)
- Source on LUNARC: `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/`
- Geant4 install: `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/`
- Conda env: `hibeam_env` at same path
- geant4-gpu repo: `/Volumes/MyDrive/nnbar/geant4-gpu/`
- Simulation repo: `/Volumes/MyDrive/nnbar/nnbar/simulation/`
- CRY v1.7 download: https://nuclear.llnl.gov/simulation/ (cry_v1.7.tar.gz)
  CRY data dir after install: `$CRY_DIR/data/`
  CRY lib: `$CRY_DIR/lib/libCRY.a`
