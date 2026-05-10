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


### 4.2 L1 rerun execution transcript

The manifest in §4.1 names what should be rerun; the execution
transcript records what actually ran. The transcript is generated beside
the manifest for each reviewer-triggered rerun and is linked from the
plan-50 overlay roll-up.

```yaml
l1_defence_rerun_transcript:
  transcript_version: 1
  manifest_hash: sha256:<hash>
  runner:
    host_class: local | lunarc | container
    build_id: build-prod-<rev>
    environment_lock: <lockfile hash or module snapshot>
  executed_rows:
    - bundle_member: Ch 10 selection cut-flow
      command_template_id: validate_reco_cutflow_v1
      command_template_verifier_hash: sha256:<hash>
      input_hashes: [sha256:<hash>]
      output_hashes: [sha256:<hash>]
      started_at: <timestamp>
      finished_at: <timestamp>
      exit_status: pass | fail | blocked
      verifier_summary: <short status or blocker>
```

Transcript review rules:

| Rule | Failure caught |
|---|---|
| transcript manifest hash matches §4.1 | rerun evidence belongs to a different request |
| transcript row names the command-template verifier hash | rerun output is trusted without A+ command-surface evidence |
| each executed row has input and output hashes | outputs cannot be tied to frozen inputs |
| failed rows keep verifier summaries | rerun failures are hidden as missing artifacts |
| blocked rows preserve the upstream owner | reviewer-triggered rerun becomes an unowned deferral |
| host class and environment lock are recorded | local, LUNARC, and container reruns cannot be compared |

A rerun is promotable only when every `ready` row in §4.1 has a
matching transcript row with `exit_status: pass`. Blocked rows remain
visible and propagate to the plan-50 roll-up instead of being excluded
from the transcript.


### 4.3 L1 command-template registry

Transcript `command_template_id` values are registered in the plan before
being used. A template is a replay contract: it names the command surface,
allowed arguments, expected outputs, and the evidence that turns a row from
`blocked` to `pass`.

| Template id | Command surface | Applies to | Required evidence |
|---|---|---|---|
| `validate_reco_cutflow_v1` | `python -m nnbar_reconstruction.cli validate-reco <output_dir> --runs <csv> --json <report>` | Ch 10 selection cut-flow reruns | JSON validation report, input hash list, output hash list, plan-37 cut-flow artifact hash |
| `validate_reco_allruns_v1` | `python -m nnbar_reconstruction.cli validate-reco <output_dir> --all-runs --json <report>` | EM-chain or selection smoke reruns when run ids are discovered from output files | JSON validation report plus discovered-run manifest |
| `blocked_missing_input_v1` | no execution command | any row whose required sample or artifact does not exist yet | blocker text, upstream owner, and expected input id |

Template review rules:

| Rule | Failure caught |
|---|---|
| command templates use only verified CLI help output | rerun manifest invents unsupported command flags |
| blocked templates have no fake command | missing evidence is disguised as a skipped successful run |
| every executable template writes a JSON report | transcript has no machine-readable verifier summary |
| selected template matches the bundle member | EM closure accidentally uses a cut-flow-only transcript |
| template id is immutable once archived | old reruns cannot be replayed after command semantics drift |

The two executable templates use the currently verified `validate-reco`
CLI surface. If L3 later adds a dedicated cut-flow or response-matrix CLI,
that new command must receive a new template id rather than changing the
meaning of these archived templates.


### 4.4 L1 command-template verifier transcript

Each command template in §4.3 carries a verifier transcript so the A+
examiner gate can be replayed without trusting the plan prose. The
transcript is captured when a template is introduced or changed.

```yaml
l1_command_template_verifier:
  template_id: validate_reco_cutflow_v1
  verified_command: python -m nnbar_reconstruction.cli validate-reco --help
  verified_from: /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3
  required_options: [--runs, --all-runs, --json]
  verifier_exit_status: 0
  help_output_hash: sha256:<hash>
  verified_at: <timestamp>
```

Verifier review rules:

| Rule | Failure caught |
|---|---|
| verifier command exits zero | template points to a missing CLI surface |
| required options are present in help output | template uses an unsupported flag |
| help hash changes reopen template review | CLI semantics drift after the template is archived |
| verifier path is the L3 worktree | orchestration repo accidentally checks the wrong module |
| blocked templates carry no verifier command | unavailable inputs are not represented as fake CLI success |

The verifier transcript is archived with the command-template registry and
is consumed by plan 53's command-template CI check.

## 5. Pre-submit checks

- Cluster quota (storage + CPU hours).
- Build is up to date (compare current `git rev` to `build_id` in
  manifest).
- Macro and config files are unchanged (hash check).

## 6. Acceptance criteria

- §1 scripts produced for each registered sample (plan 03 entries).
- §2 seed binding implemented.
- §3 finaliser job standardised.
- §5 pre-submit checks target `scripts/orchestrate/preflight.sh` before
  production orchestration is promoted.
- L1 reviewer-triggered reruns produce the §4.2 transcript and link it
  from the plan-50 overlay roll-up.
- Transcript rows use a §4.3 command template with verifier hash evidence
  for verified CLI surface or an explicit blocked template.
- Executable L1 command templates carry the §4.4 verifier transcript.

## 7. Dependencies

- **03** — dataset IDs.
- **11** — build environment.
- *Consumed by:* every sample regen.

## 8. References

- LUNARC user documentation.
- `cluster-status` skill description in the user's environment.
