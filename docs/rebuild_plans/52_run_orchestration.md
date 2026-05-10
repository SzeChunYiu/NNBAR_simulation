---
id: 52_run_orchestration
title: Run orchestration — batch system, seeds, hash sealing
version: 0.1
status: draft
owner: Software Quality
depends_on: [00_README, 03_dataset_registry, 11_build_and_runtime_environment, 50_reviewer_defense_package, 51_reviewer_question_registry, 53_ci_regression_suite, 54_open_data_archival, 55_internal_note_template, 56_glossary]
outputs:
  - {path: docs/rebuild_plans/52_run_orchestration.md, schema: this file}
  - {path: docs/rebuild_plans/52_run_orchestration_l1_command_templates.md, schema: L1 command-template registry}
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
overlay ids refreshed by the rerun. It also carries the plan-51 owner
sign-off reference when a rerun is used to answer or close a reviewer
question and the review-evidence links that will be reconciled by plans
50, 51, 52, 53, 54, 55, and 56. If one member is not yet implementable (for
example, no Lambda-enriched slice exists), the manifest keeps a blocked
row with the missing input named rather than silently omitting the question.


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
  request_owner: L1-owner-or-methodology-council
  seed_formula: sha256(dataset_id || run_index || "simulation")[:8]
  bundle_member_ids: {EM chain closure: em_object_chain, Ch 10 selection cut-flow: ch10_cutflow, Pile-up L11 overlay: pileup_l11, Strange V0 contamination: strange_v0, TOF timing closure: tof_timing, Bayesian limit cross-check: bayesian_limits, Unbounded caveat status: unbounded_caveats, Defence routing: defence_routing}
  review_evidence_links: &l1_review_evidence_links
    overlay_rollup: <plan50-rollup-id>
    defence_routing_crosswalk: <plan50-crosswalk-id-or-null>
    staleness_summary: <plan50-staleness-id>
    ci_report: <plan53-l1-report-id>
    archive_inventory: <plan54-inventory-id-or-null>
    archive_drill: <plan54-drill-id-or-null>
    rerun_transcript: <plan52-transcript-row-or-null>
    note_annex: <plan55-annex-id-or-null>
    glossary_audit: <plan56-audit-id>
  rows:
    - bundle_member: EM chain closure
      status: ready | blocked
      owner_signoff_ref: RQ-L1-EM-P1-CLUSTERING:<owner-hash-or-null>
      required_inputs:
        - dataset_id: cal_singlegamma_v1
          run_indices: [0, 1, 2]
          source_hash: <sha256>
      refreshes:
        - artifact_id: p1_p7_closure_rows
          output_hash: <sha256>
        - artifact_id: photon_promotion_examples
          output_hash: <sha256>
        - artifact_id: photon_pi0_response_and_handoff_summary
          output_hash: <sha256>
      defence_overlay_ids:
        - em_cluster_truth_blindness
        - pi0_cut_decomposition
      review_evidence_links: *l1_review_evidence_links
      blocker: null
    - bundle_member: Ch 10 selection cut-flow
      status: ready | blocked
      owner_signoff_ref: RQ-L1-SELECTION-CUTFLOW:<owner-hash-or-null>
      required_inputs:
        - dataset_id: sig_foil_v3
          run_indices: [0, 1]
          source_hash: <sha256>
        - dataset_id: cosmic_cry_essLund_overburdenA_v1
          run_indices: [0, 1]
          source_hash: <sha256>
      refreshes:
        - artifact_id: plan37_cutflow_counts
          output_hash: <sha256>
        - artifact_id: selection_truth_blind_hash
          output_hash: <sha256>
      defence_overlay_ids:
        - selection_cutflow_identity
      review_evidence_links: *l1_review_evidence_links
      blocker: null
    - bundle_member: Pile-up L11 overlay
      status: blocked
      owner_signoff_ref: RQ-L1-PILEUP-L11:<owner-hash-or-null>
      required_inputs:
        - dataset_id: sig_foil_v3
          source_hash: <sha256-or-null>
        - dataset_id: cosmic_cry_essLund_overburdenA_v1
          source_hash: <sha256-or-null>
      refreshes:
        - artifact_id: plan58_pileup_overlay_closure
          output_hash: null
      defence_overlay_ids:
        - pileup_l11_status
      review_evidence_links: *l1_review_evidence_links
      blocker: paired pile-up closure artifact is not attached to a concrete result yet
    - bundle_member: Strange V0 contamination
      status: blocked
      owner_signoff_ref: RQ-L1-STRANGE-BARYON:<owner-hash-or-null>
      required_inputs:
        - dataset_id: beam_neutron_hibeam_secondaries_v1:lambda_enriched
          source_hash: null
      refreshes:
        - artifact_id: plan59_lambda_enriched_v0_closure
          output_hash: null
      defence_overlay_ids:
        - strange_v0_contamination
      review_evidence_links: *l1_review_evidence_links
      blocker: Lambda-enriched strange-background closure artifact is not attached to a concrete result yet
    - {bundle_member: TOF timing closure, status: blocked,
       owner_signoff_ref: RQ-L1-TOF:<owner-hash-or-null>,
       required_inputs: [{dataset_id: cal_timing_slice_v1, source_hash: null}, {dataset_id: cosmic_cry_essLund_overburdenA_v1, source_hash: <sha256-or-null>}],
       refreshes: [{artifact_id: plan61_tof_resolution_roc, output_hash: null}, {artifact_id: plan61_signal_loss_interval, output_hash: null}], defence_overlay_ids: [tof_timing_resolution],
       review_evidence_links: *l1_review_evidence_links, blocker: calibrated timing slice and TOF closure artifact are not attached to a concrete result yet}
    - {bundle_member: Bayesian limit cross-check, status: blocked,
       owner_signoff_ref: RQ-L1-BAYES-LIMIT:<owner-hash-or-null>,
       required_inputs: [{artifact_id: plan46_low_count_fixture_or_result, source_hash: null}],
       refreshes: [{artifact_id: plan64_prior_sensitivity_table, output_hash: null}, {artifact_id: plan64_primary_method_ratio, output_hash: null}], defence_overlay_ids: [bayesian_prior_sensitivity],
       review_evidence_links: *l1_review_evidence_links, blocker: Bayesian prior-sensitivity result table is not attached to a concrete result yet}
    - bundle_member: Unbounded caveat status
      status: blocked
      owner_signoff_ref: RQ-L1-UNBOUNDED-CAVEATS:<owner-hash-or-null>
      required_inputs:
        - artifact_id: plan45_numeric_bound_or_caveat_row
          source_hash: null
      refreshes:
        - artifact_id: unbounded_caveat_status_overlay
          output_hash: null
      defence_overlay_ids:
        - unbounded_caveat_status
      review_evidence_links: *l1_review_evidence_links
      blocker: numeric nuisance bound or caveat row not attached to a concrete result yet
    - bundle_member: Defence routing
      status: ready | blocked
      owner_signoff_ref: L1-routing-owner:<owner-hash-or-null>
      required_inputs:
        - artifact_id: plan50_to_plan56_routing_fixture_bundle
          source_hash: <sha256-or-null>
      refreshes:
        - artifact_id: l1_defence_routing_crosswalk
          output_hash: <sha256-or-null>
      defence_overlay_ids: [em_cluster_truth_blindness, pi0_cut_decomposition, selection_cutflow_identity, pileup_l11_status, strange_v0_contamination, tof_timing_resolution, bayesian_prior_sensitivity, unbounded_caveat_status]
      review_evidence_links: *l1_review_evidence_links
      blocker: null when plan50/51/52/53/54/55/56 hashes agree; otherwise names the drifting fixture
```

Manifest review rules:

| Rule | Failure caught |
|---|---|
| every §4 bundle member has one row | reviewer rerun omits a known L1 question family |
| `bundle_member_ids` matches the plan-53/54 L1 member ids | rerun labels drift from CI/archive member ids |
| every ready row records source and output hashes | refreshed artifacts cannot be tied to frozen inputs |
| every blocked row names the missing input | unavailable samples are hidden as silent skips |
| overlay ids point back to plan 50 | rerun evidence is disconnected from the defence package |
| review-evidence links point to overlay roll-up, defence-routing crosswalk, rerun transcript, staleness, CI, archive, note, and glossary artifacts | rerun evidence cannot be reconciled with reviewer-facing artifacts |
| seed formula matches §2 exactly | reviewer rerun is not bitwise reproducible |
| answered or closed reviewer questions carry an owner sign-off ref | rerun evidence closes a question without accountable approval |

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
      command_template_verifier_hash: sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
      input_hashes: [sha256:<hash>]
      output_hashes: [sha256:<hash>]
      started_at: <timestamp>
      finished_at: <timestamp>
      exit_status: pass | fail | blocked
      verifier_summary: <short status or blocker>
      owner_signoff_ref: RQ-L1-SELECTION-CUTFLOW:<owner-hash-or-null>
      review_artifact_hashes:
        package: sha256:<hash>
        rerun_manifest: sha256:<hash>
        rerun_transcript: sha256:<hash>
        command_template_verifier: sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
        defence_routing_crosswalk: sha256:<hash-or-null>
        staleness_summary: sha256:<hash>
        ci_report: sha256:<hash>
        archive_inventory: sha256:<hash-or-null>
        archive_drill: sha256:<hash-or-null>
        note_annex: sha256:<hash-or-null>
        glossary_audit: sha256:<hash>
    - bundle_member: Unbounded caveat status
      command_template_id: blocked_missing_input_v1
      command_template_verifier_hash: null
      input_hashes: []
      output_hashes: []
      started_at: null
      finished_at: null
      exit_status: blocked
      verifier_summary: numeric nuisance bound or caveat row not attached to a concrete result yet
      owner_signoff_ref: RQ-L1-UNBOUNDED-CAVEATS:<owner-hash-or-null>
      review_artifact_hashes:
        package: sha256:<hash-or-null>
        rerun_manifest: sha256:<hash-or-null>
        rerun_transcript: sha256:<hash-or-null>
        command_template_verifier: null
        defence_routing_crosswalk: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        archive_inventory: sha256:<hash-or-null>
        archive_drill: sha256:<hash-or-null>
        note_annex: sha256:<hash-or-null>
        glossary_audit: sha256:<hash-or-null>
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
| transcript owner sign-off refs match the manifest and plan 51 | execution evidence is promoted under a different approval than the request |
| transcript review-artifact hashes match plan 50/53/54/55/56 links, including the defence-routing crosswalk | execution evidence is promoted after review artifacts drift |

A rerun is promotable only when every `ready` row in §4.1 has a
matching transcript row with `exit_status: pass`. Blocked rows remain
visible and propagate to the plan-50 roll-up instead of being excluded
from the transcript.


### 4.3 L1 command-template registry

The command-template registry and verifier transcript are split into
`docs/rebuild_plans/52_run_orchestration_l1_command_templates.md` to keep
this parent plan below the line cap. The companion file owns the stable
`command_template_id` rows, verified CLI help transcript, help-surface hash,
and blocked-template rules consumed by plans 50, 53, 54, 55, and 56.

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
- Rerun manifests/transcripts that close reviewer questions carry the
  same plan-51 owner sign-off refs as the plan-50 defence package.
- Rerun manifests/transcripts that support thesis-facing notes carry the
  same review-evidence links and review-artifact hashes used by plans
  50, 51, 53, 54, 55, and 56.

## 7. Dependencies

- **03** — dataset IDs.
- **11** — build environment.
- *Consumed by:* every sample regen.

## 8. References

- LUNARC user documentation.
- `cluster-status` skill description in the user's environment.
