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

## 4. L1 EM/selection defence rerun bundle

Stage E.3 defence packages need a small, replayable run bundle for the
L1 EM-object and selection questions. This bundle is not a new physics
sample; it is an orchestration manifest that names the already-registered
samples and the artifacts that must be refreshed together when a reviewer
asks for reproduction.

| Bundle member | Required sample / source | Refreshed artifacts | Consumed by |
|---|---|---|---|
| EM chain closure | `cal_singlegamma_v1`, `cal_singleelectron_v1`, `sig_foil_v3` aliases or current plan-03 ids | P.1-P.7 closure rows, Class-B drop hashes, photon/pi0 response summaries | plans 31-35, 50, 55 |
| Ch 10 selection cut-flow | signal plus cosmic rows used by plan 37/47 | independent `pass_*` counts, cumulative cut-flow counts, final S.6 interval | plans 37, 47, 50 |
| pile-up overlay | `sig_foil_v3` plus `cosmic_cry_essLund_*` paired rows | overlay manifest, occupancy tails, L11 status row | plans 58, 45, 50 |
| strange-background closure | Lambda-enriched beam-neutron slice and K_S sideband when available | V0-candidate summary, rejection efficiency, residual survivor interval | plans 59, 44, 50 |
| TOF timing closure | `cal_*` timing slices plus `cosmic_cry_essLund_*` rows | TOF candidate table, resolution budget, ROC rows, signal-loss interval | plans 61, 41, 50 |
| Bayesian limit cross-check | plan-46 low-count fixtures and thesis-facing sparse-count rows | Jeffreys/flat prior table and primary-method comparison ratios | plans 64, 46, 50 |

A defence rerun manifest stores the dataset ids, run indices, seed
formula version, source hashes, produced artifact hashes, and the plan-50
overlay ids refreshed by the rerun. If one member is not yet implementable
(for example, no Lambda-enriched slice exists), the manifest keeps a
blocked row with the missing input named rather than silently omitting the
question.


### 4.1 Defence rerun manifest fixture

The bundle is materialised as a small YAML manifest so reviewers can see
which EM/selection artifacts were refreshed together. It is intentionally
separate from the physics dataset registry: registry rows define frozen
samples, while this manifest defines a reproducible reviewer rerun over
those samples.

```yaml
l1_defence_rerun_manifest:
  manifest_version: 1
  requested_by: reviewer-question-id
  seed_formula: sha256(dataset_id || run_index || "simulation")[:8]
  rows:
    - bundle_member: EM chain closure
      status: ready | blocked
      required_inputs:
        - dataset_id: cal_singlegamma_v1
          run_indices: [0, 1, 2]
          source_hash: <sha256>
      refreshes:
        - artifact_id: p1_p7_closure_rows
          output_hash: <sha256>
        - artifact_id: photon_pi0_response_summary
          output_hash: <sha256>
      defence_overlay_ids:
        - l1-em-chain
      blocker: null
```

Manifest review rules:

| Rule | Failure caught |
|---|---|
| every §4 bundle member has one row | reviewer rerun omits a known L1 question family |
| every ready row records source and output hashes | refreshed artifacts cannot be tied to frozen inputs |
| every blocked row names the missing input | unavailable samples are hidden as silent skips |
| overlay ids point back to plan 50 | rerun evidence is disconnected from the defence package |
| seed formula matches §2 exactly | reviewer rerun is not bitwise reproducible |

The CI check in plan 53 consumes this fixture shape. A weekly failure is
acceptable only when the blocked row names an upstream owner and the
plan-50 defence package marks the same question as not yet reproducible.

## 5. Pre-submit checks

- Cluster quota (storage + CPU hours).
- Build is up to date (compare current `git rev` to `build_id` in
  manifest).
- Macro and config files are unchanged (hash check).

## 6. Acceptance criteria

- §1 scripts produced for each registered sample (plan 03 entries).
- §2 seed binding implemented.
- §3 finaliser job standardised.
- §5 pre-submit checks land in `scripts/orchestrate/preflight.sh`.

## 7. Dependencies

- **03** — dataset IDs.
- **11** — build environment.
- *Consumed by:* every sample regen.

## 8. References

- LUNARC user documentation.
- `cluster-status` skill description in the user's environment.
