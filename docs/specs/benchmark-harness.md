# Benchmark Harness — Contract and Implementation Spec

Companion to `docs/specs/paper-methodology.md`. This document specifies
exactly what the benchmark harness must do, what it outputs, and how every
optimization result feeds into it.

---

## Overview

The harness is a single Python package at
`benchmarks/harness/` that:

1. Takes an optimization ID, workload ID, physics-list ID, hardware ID, and
   seed list as inputs.
2. Builds and runs both the vanilla Geant4 reference and the optimized build.
3. Measures wall-clock time, per-step time, CPU instructions, and cache misses.
4. Extracts physics observables from both runs.
5. Applies the KS parity gate.
6. Writes a single Parquet row to `benchmarks/results/results.parquet`.

---

## Directory layout

```
benchmarks/
  harness/
    __init__.py
    run.py              # CLI entry point: python -m benchmarks.harness.run <args>
    builder.py          # cmake configure + build for vanilla and optimized
    runner.py           # sbatch submission + output collection
    parity.py           # KS test + CI computation
    schema.py           # Parquet row schema (single source of truth)
    hardware.py         # Hardware fingerprinting + SLURM evidence collection
  reference/
    <workload>/
      <physics_list>/
        seed_<N>.parquet  # vanilla reference runs
    MANIFEST.sha256
  results/
    results.parquet       # all harness rows, append-only
  competitors/
    celeritas/            # existing Celeritas benchmark scripts
    adept/                # existing AdePT benchmark scripts
  hardware_evidence/
    <jobid>.txt           # scontrol show job output
  build_logs/
    <opt_id>_<hw_id>.txt  # cmake configure + build log
```

---

## Parquet row schema (`benchmarks/harness/schema.py`)

One row per (optimization × workload × physics_list × hardware × seed_set).

| Column | Type | Description |
|---|---|---|
| `opt_id` | str | Optimization identifier, e.g. `BD-geant4-032` or `phase3-rtx` |
| `opt_branch` | str | Git branch or commit hash of the optimized build |
| `opt_cmake_flags` | str | Full cmake flags string used to build |
| `workload_id` | str | W1–W6 |
| `physics_list` | str | PL1–PL4 string (e.g. `FTFP_BERT`) |
| `hw_id` | str | H1–H4 |
| `slurm_job_id` | str | SLURM job ID for the measurement run |
| `geant4_version` | str | `v11.2.2` |
| `n_events` | int | Events per run |
| `n_seeds` | int | Number of seeds (must be 20 for L3) |
| `seeds` | list[int] | The 20 seeds used |
| `wall_s_vanilla` | float | Mean wall-clock seconds, vanilla (N seeds) |
| `wall_s_opt` | float | Mean wall-clock seconds, optimized (N seeds) |
| `wall_s_vanilla_std` | float | Standard deviation over N seeds |
| `wall_s_opt_std` | float | Standard deviation over N seeds |
| `speedup_mean` | float | `wall_s_vanilla / wall_s_opt` |
| `speedup_ci95_lo` | float | Lower bound of 95% CI on speedup |
| `speedup_ci95_hi` | float | Upper bound of 95% CI on speedup |
| `steps_per_event_vanilla` | float | Mean steps/event, vanilla |
| `steps_per_event_opt` | float | Mean steps/event, optimized |
| `ks_edep_p` | float | KS p-value, Edep_total distribution |
| `ks_stepcount_p` | float | KS p-value, step_count distribution |
| `ks_secondary_p` | float | KS p-value, secondary_multiplicity |
| `ks_firststepl_p` | float | KS p-value, first_step_length |
| `ks_neutron_p` | float | KS p-value, neutron_capture_rate (W4 only; null otherwise) |
| `parity_pass` | bool | True if all KS p-values > 0.05 |
| `claim_level` | str | L0/L1/L2/L3/L4 per methodology spec |
| `result_tag` | str | SPEEDUP / NEUTRAL / REGRESSION / PARITY_FAIL |
| `perf_instructions` | float | CPU instructions (perf stat), optimized, if available |
| `perf_cache_misses` | float | LLC cache misses (perf stat), if available |
| `notes` | str | Free-text; must be empty for L3 rows |
| `timestamp` | str | ISO-8601 UTC |

---

## CLI entry point

```bash
python -m benchmarks.harness.run \
  --opt-id BD-geant4-032 \
  --opt-branch lane/g4gpu-phase5d-jit-poststep-gpil \
  --workload W1 W2 \
  --physics-list PL1 PL2 \
  --hw H1 \
  --n-seeds 20 \
  --submit          # actually submit sbatch; omit for dry-run
```

Without `--submit`, prints the sbatch script and exits without submitting.
This is the harness equivalent of `sbatch --test-only`.

---

## Build contract (`benchmarks/harness/builder.py`)

```
build_vanilla(geant4_prefix, workload, output_dir) -> build_path
build_optimized(geant4_prefix, opt_branch, cmake_flags, workload, output_dir) -> build_path
```

- Both builds use the LUNARC Geant4 v11.2.2 install at
  `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env`.
- Build logs are saved to `benchmarks/build_logs/<opt_id>_<hw_id>.txt`.
- Builder fails loudly if the build log contains `Error` or the binary is
  absent — never silently proceeds with a stale binary.

---

## Runner contract (`benchmarks/harness/runner.py`)

The runner writes an sbatch script and submits it. The sbatch script:

1. Loads the required modules (GCC/13.2.0, CUDA/12.8.0).
2. Runs vanilla and optimized builds N times in sequence, one seed per run.
3. Pipes each run's stdout to `benchmarks/raw/<opt_id>/<workload>/<seed>.txt`.
4. After all runs: calls `python -m benchmarks.harness.run --collect` which
   reads the raw outputs and writes the Parquet row.

The sbatch script MUST be submitted from the LUNARC holder pane via `sbatch`;
it MUST NOT execute the Geant4 binary directly on the holder node.

---

## Parity gate (`benchmarks/harness/parity.py`)

```python
def parity_gate(vanilla_parquet, opt_parquet) -> PurityResult:
    # Returns PurityResult(pass=bool, ks_stats=dict, failing_observables=list)
```

- Reads per-seed observable arrays from both Parquet files.
- Runs `scipy.stats.ks_2samp` on each observable.
- Returns `pass=True` only if all p-values > 0.05.
- On failure, `failing_observables` names each failed observable and its p-value.

---

## Adding a new optimization to the harness

1. Assign the BD or phase ID (e.g. `BD-geant4-036`).
2. Create a branch in the geant4-gpu repo with the optimization applied.
3. Add a row to `benchmarks/optimizations_registry.yaml`:
   ```yaml
   BD-geant4-036:
     branch: lane/bd-geant4-036-em-lambda-cache
     cmake_flags: "-DG4GPU_BD036=ON"
     description: "EM PostStep GPIL material/lambda state cache"
     depends_on: []
   ```
4. Run `python -m benchmarks.harness.run --opt-id BD-geant4-036 --workload W1 W2 --physics-list PL1 PL2 --hw H3 --n-seeds 5 --submit` for a quick L2 smoke test.
5. After L2 smoke passes, run with `--n-seeds 20 --hw H1 H3 H4` for L3.
6. The harness appends the row to `benchmarks/results/results.parquet`.
7. Update MASTER_PLAN: change the BD entry status from `RUNNING` to `DONE` with
   the claim level and result tag from the row.

---

## Reference dataset generation

Before the first optimized run, generate the vanilla reference for each
workload × physics-list combination:

```bash
python -m benchmarks.harness.run \
  --opt-id vanilla \
  --workload W1 W2 W3 W4 W5 W6 \
  --physics-list PL1 PL2 PL3 PL4 \
  --hw H3 \
  --n-seeds 20 \
  --generate-reference \
  --submit
```

This writes to `benchmarks/reference/` and updates `MANIFEST.sha256`.
The reference must never be regenerated without a MASTER_PLAN planner entry.

---

## Result interpretation rules

| `result_tag` | `speedup_ci95_lo` | `parity_pass` | Paper treatment |
|---|---|---|---|
| SPEEDUP | > 1.00 | True | Results table, main text |
| NEUTRAL | ≤ 1.00, ≥ 0.95 | True | Supplementary Table S1 |
| REGRESSION | < 0.95 | True | Supplementary Table S1, noted in text |
| PARITY_FAIL | any | False | Supplementary Table S2, not in speedup table |

---

## Implementation tasks for codex (ordered)

1. **`benchmarks/harness/schema.py`** — Parquet schema (dataclass + pyarrow schema). No deps.
2. **`benchmarks/harness/parity.py`** — KS gate (scipy). Focused test: two identical arrays → p=1.0; two very different → p<0.05.
3. **`benchmarks/harness/builder.py`** — cmake configure + build wrapper. Focused test: build vanilla TestEm0 on LUNARC.
4. **`benchmarks/harness/runner.py`** — sbatch script writer + submitter. Focused test: `--submit` dry-run prints valid sbatch, `bash -n` passes.
5. **`benchmarks/harness/hardware.py`** — hardware fingerprint (reads `/proc/cpuinfo`, `nvidia-smi`, SLURM env vars). Focused test: local mock.
6. **`benchmarks/harness/run.py`** — CLI wiring. Focused test: `--help` exits 0; dry-run with `W1 PL1 H3` prints sbatch and exits 0.
7. **`benchmarks/reference/` generation** — sbatch job using the runner, submitted to LUNARC lu48 for W1–W4 (CPU), gpua40 for W5–W6.

Each task is a separate codex goal. Tasks 1–6 can proceed locally. Task 7
requires LUNARC SLURM and must go through the runner's sbatch path.
