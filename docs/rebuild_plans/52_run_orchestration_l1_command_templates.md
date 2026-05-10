---
id: 52_run_orchestration_l1_command_templates
title: Run orchestration — L1 command-template registry
version: 0.1
status: draft
owner: Computing WG
depends_on: [52_run_orchestration, 50_reviewer_defense_package, 51_reviewer_question_registry, 53_ci_regression_suite]
outputs:
  - {path: docs/rebuild_plans/52_run_orchestration_l1_command_templates.md, schema: split L1 command-template registry}
acceptance:
  - {test: every executable L1 command template has a verified help transcript, method: review, pass_when: verifier exits zero and required options are present}
last_updated: 2026-05-10
---

# L1 command-template registry

This companion file keeps plan 52 below the line cap while preserving the
L1 command-template registry and CLI verifier transcript used by defence
rerun manifests and CI.

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
l1_command_template_verifiers:
  - template_id: validate_reco_cutflow_v1
    verified_command: python -m nnbar_reconstruction.cli validate-reco --help
    verified_from: /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3
    required_options: [--runs, --json]
    verifier_exit_status: 0
    help_output_hash: sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
    verified_at: 2026-05-10
    help_surface:
      positional: [output_dir]
      options_present: [--run, --runs, --all-runs, --min-class-count, --min-accuracy, --min-balanced-f1, --json]
  - template_id: validate_reco_allruns_v1
    verified_command: python -m nnbar_reconstruction.cli validate-reco --help
    verified_from: /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3
    required_options: [--all-runs, --json]
    verifier_exit_status: 0
    help_output_hash: sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
    verified_at: 2026-05-10
    help_surface:
      positional: [output_dir]
      options_present: [--run, --runs, --all-runs, --min-class-count, --min-accuracy, --min-balanced-f1, --json]
```

A+ verifier evidence (2026-05-10): from the L3 worktree, `python -m
nnbar_reconstruction.cli validate-reco --help` exited 0 and printed the
`output_dir` positional plus `--runs`, `--all-runs`, and `--json`. The
same help transcript validates both executable templates; the blocked
template intentionally has no command surface.

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
