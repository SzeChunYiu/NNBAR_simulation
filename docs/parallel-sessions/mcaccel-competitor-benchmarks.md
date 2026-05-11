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
