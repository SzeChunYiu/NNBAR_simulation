---
id: 38_truth_substitution_ladder
title: Truth-substitution ladder — the validation instrument
version: 0.1
status: draft
owner: Combined Performance
depends_on: [00_README, 01_realism_contract, 04_statistical_uncertainty, 24_reconstruction_question_tree]
inputs:
  - {path: data/registry/sig_foil_v3, schema: signal sample}
  - {path: data/registry/cal_*, schema: calibration samples}
outputs:
  - {path: docs/rebuild_plans/38_truth_substitution_ladder.md, schema: this file}
  - {path: nnbar_reconstruction/ladder/, schema: ladder execution code}
  - {path: output/ladder/<dataset_id>/<config>/, schema: per-rung outputs}
acceptance:
  - {test: every leaf in plan 24 §2–§6 has a canonical truth definition, method: §3 enumeration, pass_when: full coverage}
  - {test: factorisation choice (additive vs Shapley) is named and justified, method: §4 review, pass_when: signed by Methodology Council}
  - {test: every ladder run is deterministic given a seed binding, method: §5 RNG, pass_when: identical outputs for identical seeds}
  - {test: error-budget matrix produced for the primary observable (visible invariant mass), method: §6 deliverable, pass_when: matrix in plan 47 ledger}
risks:
  - {risk: truth definition disagrees between leaves, mitigation: §3 single source of truth per leaf}
  - {risk: leaf substitutions are not orthogonal — joint substitutions don't equal sum of singletons, mitigation: §4 named factorisation}
estimated_effort: L
last_updated: 2026-05-09
---

# Truth-substitution ladder

*Charter.* The central scientific instrument of the rebuild. For
every leaf in plan 24, run reconstruction in three modes and measure
the impact on a fixed set of event observables. The matrix of
deltas is the *error budget* and the *oracle upper bound* for every
reconstruction algorithm.

In a Geant4-only world, the truth is abundant — it lives alongside
reco in every parquet (plan 09). The ladder uses this abundance
deliberately: not as a label, but as a benchmark.

## 1. Three ladder modes

For each leaf L in plan 24 §2–§6:

- **`reco-only`** — the deployable pipeline. Class A only.
- **`truth-at-L`** — the leaf L is replaced by its truth-canonical
  output (§3). Every other leaf runs reco-only.
- **`truth-everywhere-else`** — the inverse. Leaf L runs reco; every
  other leaf is truth.

These three modes give two scientific quantities per leaf:

- **Information value** of fixing leaf L:
  `IV(L) = obs(truth-at-L) - obs(reco-only)`
- **Damage** of leaf L in isolation:
  `D(L) = obs(truth-only) - obs(truth-everywhere-else)`

`IV(L)` answers: *"if we made leaf L perfect, how much would the
observable improve?"*
`D(L)` answers: *"how much does our current reco at leaf L hurt the
observable?"*

## 2. Observable budget

The primary observable: **event visible invariant mass** (per plan
24 §5 leaf E.7). Secondary observables:

- vertex z-residual, vertex r-residual (plan 24 §2)
- charged-track multiplicity (§3)
- π⁰ multiplicity (§4)
- π⁰ mass peak μ, σ (§4 leaves P.5–P.7)
- sphericity (§5 leaf E.5)
- E_L, E_T (§5 leaves E.3–E.4)
- total calorimeter energy (§5 leaf E.1)
- thesis Ch 10 selection acceptance (§6)
- cosmic-rejection survival fraction on the cosmic sample (§6)

The matrix is `leaf × observable`; rows are leaves, columns are
observables.

## 3. Canonical truth definitions per leaf

Each leaf has a single canonical truth output. This is critical because
"truth photon direction" is not unique — *at production* / *at first
conversion* / *at lead-glass entry* are different vectors that change
the ladder's numerical result.

| Leaf | Canonical truth |
|---|---|
| V.1 (TPC track) | hit list grouped by `(Event_ID, Track_ID)`; only steps from primary or charged π/p tracks |
| V.2 (track direction) | momentum direction at production from `Particle_output` |
| V.3 (foil projection) | true production vertex (`Vx, Vy, Vz`) projected to `z=0` |
| V.4 (aggregation) | mean of true track foil-projections |
| V.5 (acceptance) | true vertex within foil radius |
| C.1–C.6 (charged) | Class B charged-track + truth π/p assignment from `Name` |
| P.1 (cluster) | hits grouped by ancestry through `Interaction` table to gamma source |
| P.2 (charged/neutral) | truth `Name == gamma` and `Parent_ID` not in TPC charged track set |
| P.3 (photon direction) | momentum direction at gamma production from `Particle_output` (see §3.1 for choice) |
| P.4 (photon energy) | true gamma kinetic energy at production |
| P.5 (π⁰ pairing) | photons sharing a common π⁰ parent in the `Interaction` table |
| P.6 (accidental rejection) | by construction zero in truth |
| P.7 (kinematic fit) | n/a — truth four-vectors are exact |
| E.1–E.9 (event variables) | computed on truth four-vectors |
| S.1–S.6 (selection) | applied to truth-derived event variables |

### 3.1 Special case: photon direction

The choice between *at production* / *at first conversion* / *at
lead-glass entry* changes the ladder by O(few mrad) of multiple
scattering. Plan 38 picks **at gamma production** as the canonical
truth — this is the well-defined source. Multiple-scattering and
conversion effects between production and detection enter the *reco*
path, not the *truth* path.

## 4. Factorisation choice

Leaf substitutions are not independent. When truth is injected at
leaf L, downstream leaves consume changed inputs. The ladder cannot
say `Σ_L IV(L) = obs(truth-only) - obs(reco-only)` exactly.

Two factorisation conventions:

- **Additive along a fixed leaf order.** Compute deltas in order
  V.1 → V.2 → … → S.6, each conditional on prior leaves having
  truth substituted. Easy to compute; result depends on the
  ordering.
- **Shapley permutation averaging.** Average IV(L) over all
  permutations of leaf orderings. Gives an order-independent
  attribution. Costlier (`N!` evaluations; in practice, sample
  permutations).

**Decision (plan 38 v0.1):** use **additive along fixed leaf order**
for the primary report (cheap and reproducible), with a Shapley
sub-sample (256 permutations) for cross-check on the headline result
(visible invariant mass).

The chosen leaf order is the *plan 24 enumeration order*: V.1, V.2,
V.3, V.4, V.5, C.1, C.2, …, S.6. Recorded as a DEC (plan 05).

## 5. RNG / seed binding

Every ladder run is deterministic. Per plan 04 §2:

```
seed = sha256(dataset_id || ladder_config_id || "ladder")[:8]
```

The seed binding makes ladder runs reproducible across machines and
across time. Plan 03 manifest records the `ladder_config_id`.

## 6. Output: the error-budget matrix

For each `(leaf, observable)` pair:

```
           reco-only    IV(L)         D(L)
visible_M  X.XXX MeV    +Δ.ΔΔΔ MeV   +δ.δδδ MeV
sphericity 0.XXX        +Δ.ΔΔΔ        +δ.δδδ
…
```

Plus the `truth-only` column for the absolute oracle bound.

The matrix is a YAML file per ladder run plus a rendered Markdown
table in plan 47 ledger.

## 7. Example: the visible-invariant-mass row

Codex-supervisor produces a ladder report for visible-invariant-mass
on the signal sample (plan 20):

```yaml
observable: visible_invariant_mass
sample: sig_foil_v3
config: ladder_v0.1_additive
seed: <auto-derived per §5>
results:
  reco_only: {value_MeV: 1450.0, stat_unc_MeV: 5.0}
  truth_only: {value_MeV: 1840.0, stat_unc_MeV: 1.0}    # ≈ 2 m_n
  per_leaf:
    V.4:  {IV_MeV: 5.0,   D_MeV: 8.0}
    P.3:  {IV_MeV: 80.0,  D_MeV: 70.0}
    P.4:  {IV_MeV: 200.0, D_MeV: 180.0}
    …
```

The per-leaf IV column tells codex-supervisor where to invest
improvement effort. In a hypothetical run like the above, photon
energy P.4 dominates the gap; plan 28 (photon objects) and plan 18
(intercalibration) become priority.

## 8. Acceptance criteria

- §3 truth-canonical table is complete; every leaf has a
  definition.
- §4 factorisation choice is signed (DEC entry).
- §5 seed binding is implemented.
- §7 example matrix is produced for at least visible_invariant_mass
  on the signal sample (plan 20).
- Subsystem plans 25–37 each cite a target leaf in plan 38's matrix.

## 9. Risks and mitigations

- *Risk:* truth substitution at leaf L mid-pipeline produces an
  invalid intermediate (e.g. a truth π⁰ pair feeds an event-variable
  function expecting reco objects).
  *Mitigation:* §3 canonical definitions explicitly include the
  *output schema* per leaf so substitution is well-typed.
- *Risk:* additive factorisation hides cross-leaf effects.
  *Mitigation:* Shapley cross-check on visible_invariant_mass.

## 10. Dependencies

- **01** — Class B substitution allowed only in the ladder (a
  `@validation_only` flow).
- **04** — uncertainty conventions for IV/D values.
- **24** — leaves and order.
- *Consumed by:* plans 25–37 (each references its leaf in the
  matrix), plan 49 (improvements scored here), plan 47 (ledger),
  plan 50 (defence package).

## 11. References

- Shapley, *Contributions to the Theory of Games*, 1953 (the
  permutation-averaging idea).
- HIBEAM PhD reproducibility appendix DEC-2026-04-24-1 (truth-
  vertex source) — same discipline of single canonical truth per
  decision.
