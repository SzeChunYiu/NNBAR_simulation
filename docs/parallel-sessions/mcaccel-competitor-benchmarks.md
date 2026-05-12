# Lane: mcaccel-competitor-benchmarks

## Goal

Establish reproducible measurements of every published competitor on identical
workloads so we can prove (in a headline-plot chart) that we beat each one.

Without this benchmark, the claim "nobody beats us" is unfalsifiable. With it,
every commit can be plotted against AdePT, Celeritas, Opticks, VecGeom, etc.

Read first: `docs/specs/g4gpu-line-by-line-acceleration.md`.

## Competitor matrix

| Project | Repo | Reference benchmark | Hardware | Their published speedup |
|---------|------|---------------------|----------|-------------------------|
| AdePT | `apt-sim/AdePT` (CERN) | TestEm3 (EM shower CMS HCAL) | A100/A40 | 10–50× |
| Celeritas | `celeritas-project/celeritas` | TestEm3 + Hadr04 + ZDC | A100/A40 | 10–30× |
| Opticks | `simoncblyth/opticks` | OpNovice2-like LZ/JUNO optical | A100 | ~1000× |
| VecGeom | `apt-sim/VecGeom` | Pure-CPU geom navigation harness | xeon | 1.5–3× |
| GeantV (legacy) | archived | TaskBench (no longer maintained) | xeon | ~3× before cancellation |
| WARP | github WARP-Sim/WARP | PWR pin cell criticality | V100 | 50–100× |
| Serpent-MC GPU branch | VTT internal | OECD benchmarks | A100 | 30–60× |

## What this lane produces

1. **`benchmarks/competitors/README.md`** — table of every competitor with
   build instructions on LUNARC and a short note on what their benchmark
   measures (so we can replicate).
2. **`benchmarks/competitors/<name>/build.sh`** per competitor — clone +
   build + run the headline benchmark on LUNARC.
3. **`benchmarks/competitors/<name>/results.parquet`** — captured timing +
   output histograms for each.
4. **`docs/reports/competitor_benchmarks_baseline.md`** — table summarising
   wall time, throughput (events/s), and key output distribution moments.
   This is the baseline we beat.

## Iteration cycle

1. Read this spec
2. Mark `mcaccel-competitor-benchmarks` RUNNING in MASTER_PLAN.md
3. Pick one competitor (start with AdePT — most actively developed and most
   directly comparable EM target)
4. Clone, build on LUNARC, run their headline benchmark, capture timing and
   output distributions
5. Commit results
6. Mark this subtask done; if all competitors covered, mark the lane DONE

## Important

- **All builds and runs on LUNARC**, never locally.
- Use the gpua40 partition for GPU benchmarks; pin to a single A40 and
  document GPU UUID for reproducibility.
- Where a competitor's benchmark requires unreasonable setup (e.g. WARP needs
  full reactor MC infrastructure), document the gap in `OPEN:` and move on.

## Acceptance

- All seven competitor entries in the matrix have either a captured baseline
  result OR a documented `OPEN:` reason
- The summary report has the side-by-side timing table
- `benchmarks/competitors/run_all.sh` reproduces the matrix from scratch in
  one command (modulo manual cluster scheduling)

## Stop condition

After committing one competitor's results, stop and let the next iteration
take the next one. This is intentionally spread across multiple iterations.

## Iteration log

### 2026-05-11 — AdePT compact dependency blocker (worker-3)

- Added `benchmarks/competitors/adept/build.sh` for an A40-only AdePT
  Example1/TestEm3 compact run with fixed seeds, provenance capture, and
  parquet summary output.
- Preserved the successful LUNARC configure probe evidence showing AdePT commit
  `47694da970baebf8a7e5d7454910aac2313f33e3` can configure against CUDA 12.8,
  Geant4 11.4.1, G4HepEm, HepMC3, VecCore, and VecGeom via the CERN
  `devAdePT` LCG view.
- Submitted policy-partition job 3041518 on `gpua40`; it was estimated for
  2026-05-12 09:51:19 and was cancelled after the immediate smoke job exposed
  the setup blocker.
- Submitted smoke job 3041525 on idle `gpua40i`; it failed in 17 seconds before
  configure/build/run because no `devAdePT` setup path was readable from the
  GPU allocation.

OPEN: rerun AdePT on `gpua40` after the CERN `devAdePT` CVMFS view is visible
from GPU nodes, or after a project-local AdePT dependency stack is cached under
`/projects/hep/fs10/shared/nnbar/billy/mcaccel-competitors/adept/`.

### 2026-05-11 — Celeritas compact baseline (pane 4)

- AdePT intentionally left to worker-3; this pane selected Celeritas.
- Created `benchmarks/competitors/celeritas/build.sh` and
  `benchmarks/competitors/run_all.sh` scaffolding.
- LUNARC configure probe for upstream Celeritas succeeded with CUDA 12.8,
  Geant4 11.2.2, and ORANGE geometry; HepMC3 and VecGeom were not found in
  the compact environment.
- Submitted SLURM job 3041282 to `gpua40` for a one-A40 `celer-sim` simple-cms
  gamma primary run; `scontrol` reported `PENDING (Resources)` with estimated
  start `2026-05-12T09:51:19`; remote results target is
  `/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/results/results.parquet`.

OPEN: Full Celeritas reference coverage still needs TestEm3/Hadr04/ZDC-style
inputs with HepMC3/VecGeom or a precise blocker report.

### 2026-05-12 — Celeritas queued-job closeout (pane 4)

- Checked SLURM job 3041282 after it left the queue; `sacct` reports
  `FAILED`, elapsed `00:01:46`, exit `127:0`, node `cg05`.
- Remote logs show configure completed and `cmake --build` linked
  `build-a40/bin/celer-sim`, but the script attempted to run the stale
  `build-a40/app/celer-sim/celer-sim` path.
- Patched `benchmarks/competitors/celeritas/build.sh` to use the produced
  `bin/celer-sim` path and added an explicit missing-executable guard.
- No new SLURM job was submitted in this closeout iteration; the Celeritas
  timing baseline remains `OPEN` until the corrected script is resubmitted on
  LUNARC and `results.parquet` is produced.

### 2026-05-12 — Celeritas rerun pending refresh (worker-3)

- Guarded LUNARC check at 2026-05-12T09:02 CEST found corrected rerun job
  3047497 still `PENDING` on `Resources`, with `StartTime=2026-05-12T12:01:31`
  and `SchedNodeList=cg06`.
- No stdout/stderr logs existed for job 3047497 yet, and no remote
  `results/results.parquet` was present.
- No new SLURM job was submitted; the Celeritas row stays `QUEUED` until job
  3047497 completes and the parquet result can be read back.

### 2026-05-12 — Celeritas rerun second pending refresh (worker-3)

- Guarded LUNARC check at 2026-05-12T09:55 CEST found corrected rerun job
  3047497 still `PENDING` on `Resources`, with `TIME=0:00`,
  `StartTime=2026-05-12T12:01:31`, and `SchedNodeList=cg06`.
- `sacct -X` still reports `Start=Unknown`, `End=Unknown`, and
  `NodeList=None assigned`; no allocation has started.
- No stdout/stderr logs for job 3047497 existed yet, and no remote
  `results/results.parquet` was present.
- No new SLURM job was submitted; keep Celeritas `QUEUED` until job 3047497
  completes or fails and the result/log evidence can be read back.

### 2026-05-12 — Celeritas rerun priority refresh (worker-3)

- Guarded LUNARC check at 2026-05-12T10:40 CEST found corrected rerun job
  3047497 still `PENDING` on `Priority`, with `TIME=0:00`,
  `StartTime=2026-05-13T07:58:30`, and `SchedNodeList=cg06`.
- `sacct -X` still reports `Start=Unknown`, `End=Unknown`, and
  `NodeList=None assigned`; no allocation has started.
- No stdout/stderr logs for job 3047497 existed yet, and no remote
  `results/results.parquet` was present.
- No new SLURM job was submitted; keep Celeritas `QUEUED` until job 3047497
  completes or fails and the result/log evidence can be read back.
