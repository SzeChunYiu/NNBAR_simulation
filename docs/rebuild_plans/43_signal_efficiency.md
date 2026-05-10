---
id: 43_signal_efficiency
title: Signal efficiency — acceptance × selection × reconstruction
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 13_signal_model, 20_sample_signal, 30_subsystem_vertex, 37_subsystem_event_selection, 60_fiducial_volume_and_edge_effects]
outputs:
  - {path: docs/rebuild_plans/43_signal_efficiency.md, schema: this file}
acceptance:
  - {test: efficiency factorisation produced (acceptance, reconstruction, selection) per stage, method: §1 deliverable, pass_when: each stage quantified}
  - {test: per-final-state-channel breakdown reported, method: §2 deliverable, pass_when: ≥ 5 channels}
  - {test: licentiate "≈ 70% signal acceptance" reproduced after reconstruction × selection, method: ledger row plus §3.1 gates, pass_when: LIC-CH10-NUM-1 is green or yellow under plan 47 §2}
  - {test: factorisation manifest carries fiducial profile and geometry version from plan 60, method: §1.3 manifest gate, pass_when: every efficiency row has profile + geometry tag}
risks:
  - {risk: per-channel efficiency is correlated; sum is not factorisable simply, mitigation: §1 explicit covariance reporting}
estimated_effort: M
last_updated: 2026-05-10
---

# Signal efficiency

*Charter.* Decompose the signal efficiency into its three factors and
report each separately. The headline number is the product; the
factorisation reveals where loss occurs.

## 1. Factorisation

**Verified CLI surface (A+ gate, 2026-05-10).** The live L3
worktree exposes `summarize`, `scan-pid`, `response-matrix`,
`cutflow`, and `validate-reco` under
`python -m nnbar_reconstruction.cli --help`;
`summarize --help` supports `--all-runs`, `--tables-dir`,
`--table`, `--bootstrap`, and `--json`.
It does not expose signal-efficiency commands yet, so those steps below
are L3/software implementation gates until their `--help` surface
exists.

The headline efficiency is measured as conditional factors on the same
registered signal sample, with covariance saved so reviewers can see
which loss term dominates:

```
epsilon_signal = epsilon_acceptance * epsilon_reconstruction * epsilon_selection
```

### 1.1 Runnable procedure

1. Build reconstruction tables for the frozen signal sample with the
   verified multi-run plan 09 §14 command:

   ```bash
   python -m nnbar_reconstruction.cli summarize \
       NNBAR_Detector/output/sig_foil_v3 --all-runs \
       --tables-dir output/reco/sig_foil_v3/ \
       --table output/reco/sig_foil_v3/runs.csv \
       --json output/reco/sig_foil_v3/summary.json
   ```

2. Assert `output/reco/sig_foil_v3/manifest.json` records the
   plan 09 §15 event-id offset and source hashes before the staged
   efficiency producer consumes the reconstruction tables.
3. **Blocked L3/software implementation gate:** no verified
   signal-efficiency CLI exists in the live L3 worktree. Before this
   section is runnable, a help-verified producer must read
   `Particle_output_*.parquet`, `Interaction_output_*.parquet`,
   `vertices.csv`, `events.csv`, `charged.csv`, `photons.csv`,
   `pi0.csv`, and plan 16 geometry; run 200 bootstrap replicas; and
   write to `output/efficiency/sig_foil_v3/`.
4. Write `factorisation.json`, `factorisation.parquet`,
   `factorisation_covariance.npz`, and `factorisation_manifest.json`.
   The manifest stores input hashes, geometry/alignment scenario, event
   counts at each denominator, Wilson intervals (plan 04 §4), and
   jackknife uncertainties for conditional efficiencies (plan 04 §3).
5. Assert the product of conditional factors equals the direct
   `passes_preliminary_selection / n_generated` efficiency to `1e-12`
   in the saved JSON before uncertainties are attached.

### 1.2 Stage definitions, tolerances, and cross-references

| Stage | Numerator / denominator | Inputs from plan 09 | Tolerance / assertion | Ladder leaf | Ledger hook |
|---|---|---|---|---|---|
| acceptance | generated events with final-state pions entering TPC or lead-glass fiducial / all generated foil-origin events | `Particle_output` and `Interaction_output` truth plus plan 16 geometry | Wilson 68% interval saved; fiducial denominator must match manifest event count exactly. | S.1 precursor / E.1-E.2 | LIC-CH06 signal acceptance via plan 47 §1 |
| reconstruction | accepted events with V.5 vertex and at least one reconstructed charged, photon, or π0 object / accepted events | `vertices.csv`, `charged.csv`, `photons.csv`, `pi0.csv` | jackknife σ saved; zero missing `event_id` joins allowed. | V.5, C.1-C.6, P.1-P.7 | LIC-CH10-CUTFLOW |
| selection | reconstructed events passing `passes_preliminary_selection` / reconstructed events | `events.csv` per-cut booleans from plan 37 §1 | direct count must equal cumulative cut-flow S.6 exactly; Wilson interval saved. | S.1-S.6 | LIC-CH10-CUTFLOW |
| total signal efficiency | selected events / all generated foil-origin events | all above | product and direct ratio must agree to `1e-12`; quote with covariance, not independent-factor multiplication. | S.6 | licentiate ≈70% row in plan 47 |

Truth columns are used to define denominators and final-state acceptance
only. Reconstruction and selection numerators are computed from Class A
reconstruction outputs and cut-flow booleans.

### 1.3 Fiducial-profile handoff from plan 60

Plan 60 owns the fiducial profiles and per-observable acceptance
budget. Plan 43 consumes that budget; it does not redefine edge cuts.
Every inclusive and by-channel efficiency artifact must therefore carry
these fields:

| Field | Required value / source | Why it is mandatory |
|---|---|---|
| `dataset_id` | current plan 03 frozen id, with `sig_foil_v3` retained as the plan 20 alias when used | joins plan 43 counts to registry provenance |
| `fiducial_profile` | one of plan 60 `none`, `loose`, `tight` | identifies whether the quoted efficiency is diagnostic, default, or systematic-envelope |
| `geometry_version` | plan 16 geometry/alignment tag used by the fiducial producer | prevents geometry drift from masquerading as efficiency drift |
| `edge_budget_row` | plan 60 §7 observable key | binds each efficiency number to its denominator/numerator policy |
| `dominant_edge_nuisances` | plan 45 nuisance ids, usually N8/N10 plus calibration hooks as needed | lets plan 47 display edge-related systematics beside statistics |

The default thesis-facing signal-efficiency row uses the `loose`
fiducial profile. The `none` profile is diagnostic only, and the
`tight` profile supplies the edge systematic unless plan 60's
profile-comparison table justifies a different envelope. The manifest
assertion is: every row in `factorisation.parquet` and
`channel_efficiency.parquet` has non-null `fiducial_profile`,
`geometry_version`, and `edge_budget_row`; otherwise the affected plan
47 row is `not-attempted`.

## 2. Per-channel breakdown

Per-channel efficiencies use truth final-state topology for grouping and
the same staged numerators from §1 for acceptance, reconstruction, and
selection. The channel label is a diagnostic/ledger dimension; it is not
read by the reconstruction or selection path.

### 2.1 Runnable procedure

1. Reuse `output/efficiency/sig_foil_v3/factorisation_manifest.json`
   from §1 to ensure the event set and hashes are identical.
2. **Blocked L3/software implementation gate:** the same verified
   signal-efficiency producer from §1.1 must support a by-channel mode
   before this section is runnable. It must read the §1 manifest, plan
   13 topology labels, the same truth/reco inputs, and write to
   `output/efficiency/sig_foil_v3/by_channel/` with matching hashes.
3. Write `channel_efficiency.parquet`, `channel_efficiency.json`,
   `channel_covariance.npz`, and `channel_manifest.json`. The parquet
   has one row per `(channel, stage)` with denominator, numerator,
   conditional efficiency, Wilson interval, and jackknife uncertainty.
4. Assert at least five named channels plus `other` are present. Any
   named channel with fewer than 100 generated events is retained in the
   machine artifact but rolled into `other` for thesis-facing plots.

### 2.2 Channel rows, tolerances, and cross-references

| Channel group | Truth label rule | Reporting tolerance | Ladder leaf | Ledger/systematics hook |
|---|---|---|---|---|
| `pi+ pi- pi0` | exactly one π+, one π-, one π0 ancestry in `Interaction_output` | report if denominator ≥100; otherwise merge into `other` for plots. | E.9 / S.6 | plan 13 nominal, plan 47 §1 |
| `pi+ pi- 2pi0` | one π+, one π-, two π0 ancestors | same denominator rule; covariance with total efficiency saved. | E.9 / S.6 | plan 13 nominal, N5 |
| `pi+ pi- 3pi0` | one π+, one π-, three π0 ancestors | same denominator rule; selection loss must include S.2/S.3 cut contributions. | E.9 / S.6 | plan 13 nominal, N5 |
| `2pi+ 2pi-` | two π+ and two π- with no π0 ancestor | same denominator rule; reconstruction factor must cite charged-PID leaves C.1-C.6. | C.1-C.6 / S.6 | plan 29, plan 47 §1 |
| `2pi+ 2pi- pi0` | two π+, two π-, one π0 ancestor | same denominator rule; store charged and π0 reconstruction losses separately. | C.1-C.6, P.5-P.7 / S.6 | plans 29, 34-35 |
| `other` | all rare, resonant, η/ω/ρ/K-containing, or low-count groups | always reported; uncertainty can be asymmetric Wilson interval. | E.9 / S.6 | plan 13 §4, plan 45 N5 |

The sum of channel numerators and denominators must reproduce the
inclusive §1 counts exactly. A mismatch is a blocking event-join or
truth-labeling bug, not an uncertainty.

## 3. Acceptance criteria

- §1 three numbers reported with uncertainties.
- §2 per-channel table produced.
- Reproducible from `sig_foil_v3` only.
- §4 software handoff is complete: inclusive and by-channel producers
  have explicit inputs, outputs, failure assertions, provenance fields,
  a required manifest schema, the existing cut-flow and jackknife
  support helpers are cited, and a no-invented-CLI rule is in force.

### 3.1 Machine-checkable gate mapping

The efficiency job is complete only when the manifest can answer each
ledger question below without a hand edit. These gates are assertions on
the artifacts produced by §§1-2, not new reconstruction logic.

| Gate | Required artifact field | Pass assertion | Ladder / subsystem cross-reference | Ledger row |
|---|---|---|---|---|
| factorisation closure | `factorisation.json:direct_total`, `product_total` | direct selected/generated ratio equals the conditional-factor product to the §1 `1e-12` tolerance. | S.6 with V.5, C.1-C.6, P.1-P.7 contributors | LIC-CH10-NUM-1 |
| uncertainty completeness | `factorisation_covariance.npz`, per-stage Wilson/jackknife fields | every stage in §1.2 has a central value, Wilson interval, jackknife uncertainty, and covariance entry. | plan 04 §3-§4; plan 38 observable budget | LIC-CH10-CUTFLOW |
| channel coverage | `channel_efficiency.parquet`, `channel_manifest.json` | the five named §2.2 channels plus `other` are present, and their summed counts reproduce the inclusive §1 counts exactly. | E.9/S.6, charged leaves C.1-C.6, π0 leaves P.5-P.7 | plan 47 §1 channel rows |
| sample provenance | `factorisation_manifest.json`, `channel_manifest.json` | dataset id is `sig_foil_v3` alias plus current plan 03 registry id; truth, reco, geometry, fiducial profile, and command hashes match between inclusive and by-channel runs. | plan 03 signal registry; plans 16 and 60 geometry/profile | plan 47 `sample` and `command` fields |
| fiducial-budget completeness | `factorisation_manifest.json`, `channel_manifest.json`, plan 60 §7 row key | every efficiency row has non-null fiducial profile, geometry version, edge budget row, and dominant edge nuisance ids. | plan 60 §7; plan 45 N8/N10 | plan 47 systematic/caveat fields |
| publication handoff | rendered Markdown table plus machine artifacts | the thesis-facing table quotes inclusive efficiency, staged factors, channel rows, and fiducial profile from the machine artifacts without recomputation. | plans 43→46/47/50 | LIC-CH06/LIC-CH10 signal-efficiency rows |

If any gate fails, plan 47 marks the affected row `red` or
`not-attempted`; downstream significance in plan 46 must not consume the
headline signal efficiency.

## 4. Software handoff and blocker contract

The verified live CLI can build the reconstruction tables consumed by
this plan, can verify the selection-factor cut-flow support with
`cutflow` (`nnbar_reconstruction/cli.py:254-263`), and the current statistics support includes
`jackknife_efficiency` (`nnbar_reconstruction/statistics/jackknife.py:31-89`) for the
plan-04 block-jackknife uncertainty. That helper is regression covered
by `test_jackknife_efficiency_uses_plan_04_block_size`
(`tests/test_statistics.py:41-54`), while the cut-flow CLI is covered by
`test_cutflow_cli_reads_events_csv` (`tests/test_selection.py:103-119`).
The live software still does not
expose the inclusive or by-channel signal-efficiency producers. Until
those producers have help-verified surfaces, this plan's runnable steps
stop at table production, cut-flow support, jackknife support, and
manifest assertions.

L3/software handoff requirements:

1. The inclusive efficiency producer reads frozen truth parquet,
   `vertices.csv`, `events.csv`, `charged.csv`, `photons.csv`,
   `pi0.csv`, plan 16 geometry, and the plan 60 fiducial profile. It
   writes the §1.1 factorisation artifacts and fails if direct/product
   closure differs by more than `1e-12`.
2. The by-channel producer reads the same manifest and plan 13 topology
   labels, writes the §2.1 channel artifacts, and fails if the five
   named §2.2 channels plus `other` do not sum back to inclusive counts.
3. Both producers record input hashes, geometry version, fiducial
   profile, bootstrap seed, Wilson/jackknife settings, covariance
   artifact path, ladder leaves, and plan 47 ledger hooks.
4. Rendered Markdown tables are consumers of machine artifacts only;
   they must not recompute efficiencies or silently omit DQM/fiducial
   warnings.
5. New command lines may be added only after their CLI surfaces are
   verified under the A+ examiner gate. Until then, the blocked sections
   remain precise software requirements, not runnable instructions.

### 4.1 Efficiency artifact manifest schema

The inclusive and by-channel efficiency producers must write manifest
rows that bind every quoted number to frozen reconstruction, fiducial,
and DQM inputs:

```yaml
schema_version: plan43_signal_efficiency@stage-e1
dataset_id: sig_foil_v3
plan03_registry_id: sig_foil_500MeV_v3
producer_mode: inclusive | by_channel
truth_inputs_hash: <sha256 of Particle/Interaction truth inputs>
reco_table_hashes: {vertices: <sha256>, events: <sha256>, charged: <sha256>, photons: <sha256>, pi0: <sha256>}
fiducial_manifest_hash: <sha256 of plan-60 manifest>
dqm_manifest_hash: <sha256 of plan-66 manifest>
geometry_version: <plan-16 geometry/alignment tag>
fiducial_profile: none | loose | tight
bootstrap_replicas: 200
uncertainty_artifacts: {wilson: <path>, jackknife: <path>, covariance: <path>}
factorisation_closure: pass | warn | fail
channel_count_closure: pass | warn | fail | not_applicable
ledger_rows: [LIC-CH06, LIC-CH10-NUM-1, LIC-CH10-CUTFLOW]
producer_help_verified: true
```

The manifest is invalid if any efficiency row lacks a fiducial profile,
geometry version, DQM status, or direct/product closure status. A
by-channel manifest is also invalid unless the named channels in §2.2
plus `other` sum back to the inclusive counts.

## 5. Risks

- *Risk:* fiducial-volume definition is geometric and can drift if
  geometry changes.
  *Mitigation:* §1 acceptance is computed from the registered
  geometry (plan 16); sample re-registration on geometry change.

## 6. Dependencies

- **04** — uncertainty.
- **13, 20, 30, 37, 60** — inputs and fiducial-profile budget.
- *Consumed by:* plan 47 (ledger), plan 50, plan 46 (significance).
