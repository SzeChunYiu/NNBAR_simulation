---
id: 47_reproduction_ledger
title: Thesis reproduction ledger — every number, every figure
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [00_README, 03_dataset_registry, 04_statistical_uncertainty, 05_decision_log, 24_reconstruction_question_tree, 38_truth_substitution_ladder, 45_systematics_taxonomy]
outputs:
  - {path: docs/rebuild_plans/47_reproduction_ledger.md, schema: this file}
  - {path: docs/thesis_reproduction_ledger.md, schema: living ledger}
  - {path: data/ledger/rows.yml, schema: machine-readable rows}
acceptance:
  - {test: every numeric claim and figure in licentiate Ch 5–10 has a row, method: chapter scan, pass_when: full coverage}
  - {test: every PhD-only addition (Ch 13 reproducibility appendix, Ch 10 HIBEAM TPC) has cross-references to its repo, method: cross-repo check, pass_when: zero unmatched}
  - {test: every row has a reproduction status, method: review, pass_when: every row is reproduced, mismatch, blocked-no-sample, or not-attempted}
risks:
  - {risk: figures need image equality, not just numeric equality, mitigation: §3 figure protocol}
  - {risk: ledger drift as thesis edits land, mitigation: §4 living-document protocol}
estimated_effort: XL
last_updated: 2026-05-10
---

# Thesis reproduction ledger

*Charter.* Every numeric claim and every figure in the thesis is a
row. Every row links to: a sample (plan 03), a reproducing command
(plan 10), a reproduced value, a comparison status, the dominant
nuisances (plan 45), and the leaf (plan 24) the row exercises. Plan
47 is the artifact that lets a reviewer verify every single thesis
number in finite time.

## 0.1 Wave 6 derivation — why each ledger row is load-bearing

### Physics derivation

**What is physically measured.** A ledger row measures one thesis
claim: a number, equation, table entry, plotted distribution, or figure
panel. The ground-truth object is not "the whole rebuild"; it is the
specific observable and source sample named by the row. Each row binds
the thesis claim to a sample id, command surface, reproduced value,
uncertainty convention, status, leaf owner, and delta explanation.

**Estimator rationale.** The ledger is the audit estimator for thesis
reproducibility because it decomposes a defence-scale narrative into
individually falsifiable claims. Numeric rows use direct value
comparison against tolerance. Figure rows use visual, bin-by-bin, and
distributional equality. Mismatch rows are valid evidence only when the
reproduced artifact, delta, and hypothesised cause are recorded; blocked
rows are valid evidence only when the missing sample or command surface
is named rather than invented.

**Statistical character.** Ledger uncertainty combines statistical
uncertainty from plan 04, systematic/nuisance uncertainty from plan 45,
and provenance uncertainty from missing or non-isomorphic samples. A
`reproduced` status requires agreement under the row's tolerance; a
`mismatch` status requires a concrete reproduced value and delta; a
`blocked-no-sample` status is fail-closed and must not be counted as
agreement. Aggregating rows without respecting these statuses would
overstate the rebuild's evidence.

### Logic gaps

- **Default numeric tolerance ±5%.** Grounding: §2 status definition.
  `OPEN:` replace the default with row-specific tolerances for every
  defence-critical number, derived from plan 04 and the relevant
  subsystem plan; target resolution date 2026-06-22.
- **Figure equality χ²/dof <2 and visual agreement.** Grounding: §3
  default figure protocol. `OPEN:` digitise or export the underlying
  thesis/rebuild data for each defence-critical plot so visual
  agreement is not the sole evidence; target resolution date
  2026-06-29.
- **Row coverage completeness.** Grounding: §5 currently reports 161
  rows spanning Chapters 5--10. `OPEN:` re-run the chapter scanner after
  each thesis edit and add a row-level diff artifact; target resolution
  date 2026-06-15.
- **Command-surface provenance.** Grounding: the A+ gate forbids
  invented CLI surfaces. `OPEN:` every command intended for execution
  must have a current help check or source-backed API verifier attached
  to the row before it can be counted as reproduced; target resolution
  date 2026-06-22.
- **Mismatch cause taxonomy.** Grounding: Wave 5 required nonempty
  mismatch notes. `OPEN:` replace broad proxy explanations with
  row-specific causes tied to plans 12, 17, 18, 39, or 40 as exact
  artifacts become available; target resolution date 2026-06-29.

### Closure test for the derivation

1. Parse `data/ledger/rows.yml` and verify row count, chapter span,
   statuses, and the invariant that reproduced/mismatch rows have
   nonempty `reproduced_value` and `delta` fields.
2. For a selected row, run or verify the declared command/API surface,
   regenerate the output artifact, and compare it to the thesis value
   using the row's numeric or figure-equality protocol.
3. Copy the reproduced value, uncertainty, status, delta, and source
   artifact path into both the YAML and living markdown ledger.
4. Reject any aggregate claim whose supporting rows include
   `blocked-no-sample`, missing deltas, stale command surfaces, or
   figure-only visual comparisons without the required numeric
   protocol.

## 1. Row schema

```yaml
- id: LIC-CH06-FIG-3
  source:
    document: licentiate
    chapter: 6
    section: 6.3
    label_or_caption: "Figure 3: per-event scintillator energy distribution"
  thesis_value: <number or "figure">
  reproducing:
    sample: sig_foil_v3
    command: |
      python -m nnbar_reconstruction.cli summarize \
          NNBAR_Detector/output/sig_foil_v3 --run 0 \
          --json output/ledger/LIC-CH06-FIG-3.json
    output_artifact: output/ledger/LIC-CH06-FIG-3.json
  reproduced_value: <number or path-to-figure>
  uncertainty:
    statistical: ±X.X (per plan 04 §2)
    systematic: ±Y.Y (per plan 45)
  status: reproduced | mismatch | blocked-no-sample | not-attempted
  decision_log: [DEC-2026-XX-XX-N]
  leaf: V.4   # or P.5, etc.
  notes: <optional caveats, limitations from plan 01 §6 that apply>
```

## 2. Status definitions

- **reproduced** — the row has a reproduced value and agrees with the
  thesis within the row's stated tolerance or the default ±5% numeric
  tolerance when no row-specific tolerance is recorded.
- **mismatch** — the row has a reproduced value and a nonempty `delta`,
  but the rebuild artifact does not satisfy numeric/figure equality.
  Honest mismatches are acceptable A+ evidence; they block promotion of
  downstream claims that require agreement.
- **blocked-no-sample** — the CLI may exist, but the required local
  sample/output directory is absent, or the required command surface is
  not implemented. The row is fail-closed rather than fabricated.
- **not-attempted** — sample regen or command has not yet been tried.

## 3. Figure equality

Numeric figures (plotted distributions) are compared via:

1. *Visual diff* — overlay reproduced vs thesis figure.
2. *Bin-by-bin numeric diff* — extract data from thesis figure
   (digitised) or rebuild plot, compare with χ²/dof.
3. *K-S statistic* between underlying samples.

Pass criteria are per-figure; default is χ²/dof < 2 and visual
agreement.

## 4. Living-document protocol

The ledger lives at `docs/thesis_reproduction_ledger.md` (separate
from this plan, which describes how to maintain the ledger).

- *Thesis edits.* When the thesis changes a number, the ledger row's
  `thesis_value` field updates and the row may flip `reproduced` →
  `mismatch` if the reproduced value no longer agrees.
- *Code edits.* When code changes that affect a row, plan 53 CI re-
  runs the row; status updates automatically.
- *New samples.* When a sample is registered (plan 03), every row
  pointing at it is re-evaluated.

## 5. Initial coverage list

The living ledger now exists at `docs/thesis_reproduction_ledger.md`,
with the machine-readable mirror at `data/ledger/rows.yml`. Seeding has
added **161 rows** from Chapters 5--10 of the licentiate/PhD
thesis pair:

- 20 Chapter 5 rows for detector-model figures, lead-glass calibration
  numbers, gamma-conversion maps, and PhD-only data-product provenance.
- 23 Chapter 6 rows for signal vertex/kinematic figures, CRY event-
  plane settings, cosmic kinetic/angle figures, the three-year cosmic
  count table, per-bin cosmic rates, simulated sample count, and the
  cosmic weighting equation.
- 43 Chapter 7 rows for event pre-selection thresholds, track-
  projection equations, vertex-resolution figures, timing-window rules,
  charged/neutral object-reconstruction formulae, dE/dx diagnostics,
  pion multiple-scattering/range checks, pi0 mass reconstruction, and
  the PhD-only HIBEAM TPC ML feature-boundary DEC.
- 31 Chapter 8 rows for charged-object PID rules and fractions, electron-pair
  proximity, pi0 truth/reco object-definition figures, cosmic false-pi0
  composition, local pi0 significance metrics, energy/opening-angle threshold
  scans, pi0 survival-fraction criteria, and split subfigure coverage.
- 35 Chapter 9 rows for visible invariant mass, sphericity, total and
  top/bottom energy, longitudinal/transverse energy, out-of-time
  energy, pion multiplicity, preliminary event-selection cutflow, and
  split subfigure coverage.
- 9 Chapter 10 rows for the disabled PhD selection-draft boundary,
  the licentiate legacy selection/ML efficiency claims, cutflow table,
  secondary-foil sentinel note, RFC caveat, correlation matrices, and
  precision-recall curve.

A+ truthing on 2026-05-10 has updated all rows out of the seed-only
`not-attempted` state: **1 row is `reproduced`**, **43 rows are
`mismatch` with nonempty `reproduced_value` and `delta` fields**, **117 rows are
`blocked-no-sample`**, and **0 rows remain `not-attempted`**. The current
row count satisfies the Wave 2 ≥30-row seed requirement, the Wave 3
≥60-row ledger-count/span target across Chapters 5--10, and the Wave 4
≥30 reproduced-or-mismatch target. Remaining work is to replace generic
diagnostic mismatches with row-specific figure/numeric equality and to
unblock rows whose exact samples or CLI surfaces are still absent.

## 6. Acceptance criteria

- §1 row schema instantiated for every claim.
- §2 statuses assigned.
- §3 figure-equality protocol applied where applicable.
- §4 living-document protocol implemented; plan 53 CI runs row
  refresh on every PR.

## 7. Risks

- *Risk:* digitising thesis figures introduces extraction error.
  *Mitigation:* §3 visual-diff plus K-S between sample-level data
  reduces dependence on bin-by-bin numerical equality.
- *Risk:* ledger size becomes unwieldy.
  *Mitigation:* per-chapter sub-files (`docs/thesis_reproduction_
  ledger/ch_05.md`, …) when the row count exceeds 100.

## 8. Dependencies

- **03, 04, 05, 24, 38, 45** — every row cites these.
- *Consumed by:* plan 49 (improvements gate on reproduced rows or
  explicitly reviewed mismatches), plan 50 (defence package), plan 53
  (CI).

## 9. References

- HIBEAM PhD `13_HIBEAM_reproducibility_appendix.tex` — direct
  template.
