# Lane: g4gpu-fullevent-validation-v7

## Goal

Design the V7 full-event validation harness and B1-B5 benchmark scaffold per
`docs/VALIDATION.md` in the geant4-gpu repo: run an NNBAR-shaped 10 GeV
cosmic muon event through G4GPU and compare against vanilla Geant4 via
KS/mean/RMS on per-sub-detector E_dep, hit multiplicity, hit position. This
compact unit delivers the plan markdown, a skeleton Python runner, and a
SLURM submission script; GPU execution happens only post-commit. Tracks
MASTER_PLAN row "G4GPU full-event validation and benchmarks" (PROPOSED).

## Files

Work in the geant4-gpu repo ONLY:

- Repo: `/Volumes/MyDrive/nnbar/geant4-gpu/`
- Branch: `lane/g4gpu-fullevent-v7`
- Create: `validation/v7_nnbar_event/README.md` (harness design + acceptance)
- Create: `validation/v7_nnbar_event/run_v7.py` (skeleton runner: loads two
  ROOT/Parquet outputs, runs KS per observable, emits JSON summary)
- Create: `validation/v7_nnbar_event/submit_v7.slurm` (LUNARC `gpua40` job
  skeleton; account `lu2026-2-51`)
- Create: `validation/v7_nnbar_event/benchmarks_b1_b5.md` (B1-B5 scope: batch throughput, speedup vs Geant4, Nsight utilization, event speedup, GPU scaling)
- Update: `/Volumes/MyDrive/nnbar/nnbar/simulation/docs/parallel-sessions/MASTER_PLAN.md`
  row status/notes only.

Read-only references: `/Volumes/MyDrive/nnbar/geant4-gpu/docs/VALIDATION.md`
sections V7 and B1-B5, `/Volumes/MyDrive/nnbar/nnbar/simulation/NNBAR_Detector/macro/`
(geometry-shape reference only — do not copy or link), MASTER_PLAN G4GPU
section.

**G4GPU isolation:** Do NOT `#include`/import any NNBAR_Detector header, do
NOT link an NNBAR library, do NOT edit NNBAR production code. The README may
describe NNBAR geometry shape (sub-detector list, layer counts) as data; it
must not call NNBAR code. See `docs/policies/g4gpu-isolation.md`.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `docs/policies/g4gpu-isolation.md`,
   `CODING_STANDARDS.md`, geant4-gpu `docs/VALIDATION.md` (V7 + B1-B5), and
   the existing `validation/` tree in geant4-gpu.
2. Mark the MASTER_PLAN "G4GPU full-event validation and benchmarks" row
   RUNNING with lane `g4gpu-fullevent-validation-v7`.
3. Write `validation/v7_nnbar_event/README.md`: enumerate the V7 observables
   (per-sub-detector total E_dep, hit multiplicity, 2D x-y hit position),
   primary spec (10 GeV cosmic muon, 10,000 events each), acceptance (KS
   p>0.05, mean within 1σ, RMS within 2σ), output paths
   (`output/v7_g4gpu.root`, `output/v7_geant4_ref.root`,
   `output/v7_summary.json`), and the explicit failure modes.
4. Write `validation/v7_nnbar_event/run_v7.py`: skeleton that takes
   `--candidate` and `--reference` ROOT/Parquet paths, loads per-sub-detector
   histograms via `uproot` or `pyarrow`, runs `scipy.stats.ks_2samp` per
   observable, writes `output/v7_summary.json` with `{test, observable,
   status, ks_pvalue, mean_delta, rms_delta}`, and returns nonzero on any
   tolerance breach. Stub the input-loading branches with `NotImplementedError`
   carrying the SPEC ref so the next iteration wires the real ROOT readers.
5. Write `validation/v7_nnbar_event/submit_v7.slurm`: GPU job on partition
   `gpua40`, account `lu2026-2-51`, 1 GPU, walltime 2h, modules per existing
   geant4-gpu Phase 1/2 jobs; invokes `run_v7.py` with placeholder inputs.
   Job submission is GATED — see step 7.
6. Write `validation/v7_nnbar_event/benchmarks_b1_b5.md`: per benchmark
   describe batch-size sweep (1K-256K), throughput metric, Nsight Compute
   targets (>70% mem BW, >50% SM occupancy), and acceptance plot per
   VALIDATION.md.
7. Commit harness scaffold on `lane/g4gpu-fullevent-v7`. ONLY AFTER the
   commit lands, submit ONE shakedown GPU SLURM job (`gpua40`) to confirm
   the runner exits cleanly — it should hit `NotImplementedError` and exit
   nonzero, proving path/modules/scheduler are wired. Record job id, push
   to GitHub, update MASTER_PLAN notes with commit hash + job id +
   "scaffold only; V7 + B1-B5 execution deferred". No 10,000-event run.

## Verification

```bash
rtk wc -l /Volumes/MyDrive/nnbar/geant4-gpu/validation/v7_nnbar_event/README.md \
          /Volumes/MyDrive/nnbar/geant4-gpu/validation/v7_nnbar_event/run_v7.py \
          /Volumes/MyDrive/nnbar/geant4-gpu/validation/v7_nnbar_event/submit_v7.slurm \
          /Volumes/MyDrive/nnbar/geant4-gpu/validation/v7_nnbar_event/benchmarks_b1_b5.md
rtk proxy bash -lc 'grep -RIn "NNBAR_Detector\|nnbar_reconstruction" /Volumes/MyDrive/nnbar/geant4-gpu/validation/v7_nnbar_event || echo "ISOLATION_OK"'
rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
rtk proxy bash -lc 'cd /Volumes/MyDrive/nnbar/geant4-gpu && python -c "import ast; ast.parse(open(\"validation/v7_nnbar_event/run_v7.py\").read())" && echo "PARSE_OK"'
```

Expected: isolation grep prints `ISOLATION_OK`; Python file parses; each
touched file is ≤500 lines; shakedown SLURM job (post-commit) appears in
`squeue` history.

## Stop condition

Stop after the V7 harness scaffold (README + runner + SLURM + B1-B5 plan)
is committed and one shakedown GPU job has been recorded in the MASTER_PLAN
notes. Do NOT run the 10,000-event reference or any B1-B5 throughput sweep
in this iteration — defer to the next compact unit with planner sign-off.
