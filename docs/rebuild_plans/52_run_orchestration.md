---
id: 52_run_orchestration
title: Run orchestration — batch system, seeds, hash sealing
version: 0.1
status: draft
owner: Software Quality
depends_on: [00_README, 03_dataset_registry, 11_build_and_runtime_environment]
outputs:
  - {path: docs/rebuild_plans/52_run_orchestration.md, schema: this file}
  - {path: scripts/orchestrate/, schema: SLURM submission scripts}
acceptance:
  - {test: every registered sample has a SLURM job script that reproduces it, method: per-sample script presence, pass_when: full coverage}
  - {test: seed binding is deterministic from sample id, method: §2 verification, pass_when: identical seeds for identical IDs}
  - {test: hash seal applied at job exit, method: §3, pass_when: hashes match registry}
risks:
  - {risk: cluster-side disk fills mid-run, mitigation: §4 quota checks pre-submit}
estimated_effort: M
last_updated: 2026-05-09
---

# Run orchestration

*Charter.* The operational layer between plan 03 (dataset registry)
and the actual simulation runs. Owns the SLURM scripts, seed binding,
output partitioning, and hash sealing. Production runs land on the
LUNARC cluster (per the user's `cluster-status` skill).

## 1. SLURM scripts

For each registered sample, codex-supervisor generates a job script
in `scripts/orchestrate/<dataset_id>.slurm`. Template:

```bash
#!/bin/bash
#SBATCH --job-name=<dataset_id>
#SBATCH --partition=lu48
#SBATCH --time=24:00:00
#SBATCH --array=0-N
#SBATCH --output=log/<dataset_id>/run_%a.out

module load <pinned modules>
cd /path/to/build-prod

EVENTS_PER_TASK=$(( <total_events> / N ))
SEED=<derived from sample_id and SLURM_ARRAY_TASK_ID>

./nnbar-detector-simulation \
    -m <macro> \
    -t 1 \
    --seed $SEED \
    -o output/<dataset_id>/run_$SLURM_ARRAY_TASK_ID
```

Per plan 11 §10, LUNARC is the production target.

## 2. Seed binding

Per plan 04 §2 convention:

```
seed = sha256(dataset_id || run_index || "simulation")[:8]
```

Job array index `SLURM_ARRAY_TASK_ID` becomes `run_index`. Runs
are deterministic given the dataset id.

## 3. Hash sealing

After all array tasks complete, a finaliser job:

1. SHA-256 every output parquet under `output/<dataset_id>/`.
2. Update `data/registry/<dataset_id>/hashes.txt`.
3. Update `data/registry/<dataset_id>/manifest.yml` `events_produced`
   from row counts.
4. Flip status to `frozen` per plan 03 §6 if all freeze acceptance
   criteria pass.

## 4. Pre-submit checks

- Cluster quota (storage + CPU hours).
- Build is up to date (compare current `git rev` to `build_id` in
  manifest).
- Macro and config files are unchanged (hash check).

## 5. Acceptance criteria

- §1 scripts produced for each registered sample (plan 03 entries).
- §2 seed binding implemented.
- §3 finaliser job standardised.
- §4 pre-submit checks land in `scripts/orchestrate/preflight.sh`.

## 6. Dependencies

- **03** — dataset IDs.
- **11** — build environment.
- *Consumed by:* every sample regen.

## 7. References

- LUNARC user documentation.
- `cluster-status` skill description in the user's environment.
