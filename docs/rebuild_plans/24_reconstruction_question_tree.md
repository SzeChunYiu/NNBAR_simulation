---
id: 24_reconstruction_question_tree
title: Reconstruction fundamental question tree
version: 0.1
status: draft
owner: Methodology Council
depends_on: [00_README, 01_realism_contract, 07_simulation_atomic_walkthrough, 08_reconstruction_atomic_walkthrough, 09_io_schema_data_dictionary]
inputs:
  - {path: docs/detector_fundamental_question_tree.md, schema: detector-side companion}
  - {path: NNBAR_Detector/docs/reconstruction.md, schema: implementation reference}
outputs:
  - {path: docs/rebuild_plans/24_reconstruction_question_tree.md, schema: this file}
  - {path: docs/reconstruction_fundamental_question_tree.md, schema: living tree (mirror)}
acceptance:
  - {test: every leaf has the answer-now / deeper-question / next-measurement triplet, method: tree review, pass_when: all leaves complete}
  - {test: every leaf names its inputs (Class A columns), decision rule, allowed truth use, outputs, downstream consumers, method: per-leaf review, pass_when: full coverage}
  - {test: every subsystem plan 25-37 cites the leaf identities defined here, method: cross-reference, pass_when: zero unmatched}
risks:
  - {risk: leaves get renamed during subsystem-plan writing → cascading rework, mitigation: this plan is signed before 25-37 start (00_README §2)}
  - {risk: tree completeness can never be proven, only refuted, mitigation: §10 reviewer challenge inviting new branches}
estimated_effort: L
last_updated: 2026-05-09
---

# Reconstruction fundamental question tree

*Charter.* Mirror `docs/detector_fundamental_question_tree.md` for
the reconstruction side. Decompose the reconstruction recursively
from the root question down to irreducible decisions ("leaves"). Every
subsystem plan 25–37 takes its scope from the leaves named here.

The tree is *prescriptive* about decomposition and *descriptive* about
the current code. Improvements live in the subsystem plans, scored
against the truth-substitution ladder (plan 38).

This plan also establishes the convention that no leaf may consume a
Class B (truth) column in its decision path (plan 01). Migration of
the existing Class B reads (plan 08 §3.7) is tracked as a per-leaf
exit criterion.

## 1. Root question

**Can this reconstruction prove an antineutron annihilation candidate
from detector observables alone, without using simulation truth?**

Answer now: not yet. The current code reads truth in several decision
paths (plan 08 §3.7). The licentiate-grade selection achieves about
70% signal acceptance with finite-sample zero cosmic survival, but
this rests on truth-aware reconstruction in places. Plan 47 ledger
must reproduce the licentiate first (with truth allowed where the
licentiate allowed it) and then re-quote with the truth-leakage
audit (plan 01) green.

Deeper question: which observables are essential rather than
convenient? Tree branches §2–§7 enumerate them.

## 2. Vertex branch

**What is the irreducible TPC evidence that an event vertex is real
and at the foil?**

Answer now: at least two independent reconstructed track directions
should project consistently to the foil plane (`z=0`) with quality-
dependent residuals.

### 2.1 Leaves under vertex

| Leaf ID | Decision |
|---|---|
| `V.1` | What constitutes a TPC track from hits? |
| `V.2` | What direction is associated with that track? |
| `V.3` | How do we project a track to the foil plane? |
| `V.4` | How do we aggregate multiple track projections into one event vertex? |
| `V.5` | When do we accept the event vertex as foil-compatible? |

**Owning subsystem plan:** plan 25.

### Per-leaf input/output schema (template, populated in plan 25)

```
Leaf V.1: TPC hits → track candidates
  inputs (Class A): TPC parquet columns
                    (Event_ID, x, y, z, t, eDep, photons[=electrons],
                     px, py, pz, xHitID, module_ID, step_info,
                     vol_name)
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name
  decision rule: clustering algorithm produces track candidates
  output: candidate-track table {anchor, direction, hit set, χ² seed}
  allowed truth use (validation only): @validation_only labelled
                    matching to truth Track_ID for efficiency scoring
  downstream consumers: V.2, V.3, V.4 (this plan); plan 25 (subsystem)
```

Leaf V.2: track candidates → fitted track directions
  inputs (Class A): V.1 candidate-track table plus the referenced TPC
                    hit columns (Event_ID, x, y, z, t, eDep, photons,
                    px, py, pz, xHitID, module_ID, step_info, vol_name)
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name,
                       particle_x, particle_y, particle_z
  decision rule: fit or estimate a direction from the ordered Class A
                 hit coordinates; the current baseline is the
                 first-to-last-hit unit vector from plan 08 §3.2
                 (`reconstruction.py:165–184`), with covariance and
                 residuals supplied by plan 26 before sign-off.
  output schema: {event_id: int64, candidate_id: int64,
                  anchor_xyz: float64[3], direction_xyz: float64[3],
                  direction_covariance: float64[3,3],
                  chi2_ndf: float64, n_direction_hits: int32,
                  direction_method: string}
  allowed truth use: validation_only
  downstream consumers: V.3, V.4, C.2, C.4; plans 26, 27, 29, 30

Leaves V.3–V.5 follow the same pattern (populated by plan 30).

### Next measurement (vertex branch)

Truth-free clustering / vertex closure study on signal annihilation
events using only Class A columns; truth used only for validation
scoring.

## 3. Charged-object branch

**What is the irreducible TPC + scintillator evidence that a track is a
charged primary pion or proton?**

Answer now: a TPC-reconstructed track with scintillator-energy
matching consistent with a charged-track ray, characterised by dE/dx
and stopping range that distinguish π from p.

### 3.1 Leaves under charged

| Leaf ID | Decision |
|---|---|
| `C.1` | What constitutes a charged track candidate (post-V.1)? |
| `C.2` | How is dE/dx estimated from TPC step records? |
| `C.3` | How is stopping range estimated from scintillator hits? |
| `C.4` | How are scintillator hits associated to a TPC track? |
| `C.5` | How is the π/p decision made from {dE/dx, range, scintillator E}? |
| `C.6` | When is a candidate rejected (e.g. EM lineage)? |

**Owning subsystem plans:** 25 (V.1 reuse), 27 (dE/dx), 28 (range/
stopping), 29 (charged PID).

Plan 08 §3.4 documents the current code path. Plan 01 §4 audit
flags the current `Name`-gated PID as a Class B violation; the leaf
C.1 exit criterion is the migration of that gate.

### Next measurement (charged branch)

Per-species reconstructed efficiency on `cal_singlepion*` and
`cal_singleproton` samples (plan 23), broken down by C.1–C.6.

## 4. Photon / π⁰ branch

**What is the irreducible lead-glass + scintillator evidence that two
clusters are a π⁰ decay?**

Answer now: two photon-like neutral objects whose summed four-momentum
satisfies the π⁰ mass and opening-angle window, with each cluster
charged-vetoed.

### 4.1 Leaves under photon / π⁰

| Leaf ID | Decision |
|---|---|
| `P.1` | What constitutes a calorimeter cluster (lead-glass and/or scintillator)? |
| `P.2` | What charged/neutral discriminant tags a cluster as photon-like? |
| `P.3` | What direction is associated with a photon (vertex → centroid)? |
| `P.4` | What energy is associated with a photon (deposited; possibly scintillator+lead-glass combined)? |
| `P.5` | How are two photons paired to a π⁰ candidate? |
| `P.6` | When are two photons accidentally compatible (rejection)? |
| `P.7` | What kinematic-fit corrections are applied to π⁰ candidates? |

**Owning subsystem plans:** 26 (clustering), 27 (shower shape), 28
(photon object), 29 (π⁰ pairing in plan numbering note: plan 29 is
charged PID; π⁰ pairing is plan 34), 30 (pairing — sic, plan 34),
35 (kinematic fit).

*Numbering correction:* per 00_README §4.7, plan 34 is π⁰ pairing
and plan 35 is kinematic fit.

### Next measurement (photon / π⁰ branch)

Truth-free clustering closure study on `cal_singlegamma_v1` (plan 23)
+ signal sample (plan 20). Charged-veto closure on signal +
`cal_singlepion*`.

## 5. Event-variable branch

**What is the irreducible event-shape evidence that distinguishes a
multi-pion annihilation from cosmic / beam backgrounds?**

Answer now: combinations of calorimeter total energy, sphericity (or
Fox-Wolfram moments), longitudinal/transverse split, visible
invariant mass, and timing-window sums distinguish the multi-pion
final state from single-track cosmics or thermal beam-induced
events.

### 5.1 Leaves under event variables

| Leaf ID | Decision |
|---|---|
| `E.1` | Total calorimeter energy (Σ scint + lead-glass eDep) |
| `E.2` | Per-hemisphere split (upper/lower scint, upper/lower LG) |
| `E.3` | Longitudinal energy `E_L = Σ E_i cos α_i` |
| `E.4` | Transverse energy `E_T = Σ E_i sin α_i` |
| `E.5` | Sphericity (eigenvalue decomposition of momentum tensor) |
| `E.6` | Fox-Wolfram moments (alternative event-shape) |
| `E.7` | Visible invariant mass from object 4-vectors |
| `E.8` | In-time / out-of-time energy split (Ch 7 timing window) |
| `E.9` | Object multiplicities (charged / photon / π⁰) |

**Owning subsystem plan:** plan 36 (event variables).

### Next measurement (event-variable branch)

Per-variable distribution comparison: signal sample (plan 20) vs
cosmic sample (plan 21) vs beam-neutron sample (plan 22). N-1 plots
in plan 41.

## 6. Selection branch

**Which combination of event variables maximises signal-to-background
under the realism contract?**

Answer now: the licentiate Ch 10 cut-flow achieves ~70% signal
acceptance with zero surviving cosmics in finite sample. Reproduction
gates the rebuild's legitimacy; improvement (cut optimisation,
multivariate replacement) is scored against this baseline.

### 6.1 Leaves under selection

| Leaf ID | Decision |
|---|---|
| `S.1` | Pre-selection (TPC-foil track presence, scint energy window) |
| `S.2` | Pion-multiplicity cut |
| `S.3` | Visible invariant mass cut |
| `S.4` | Sphericity cut |
| `S.5` | Hemisphere balance cut |
| `S.6` | Final-rate computation (with statistical and systematic uncertainty) |

**Owning subsystem plan:** plan 37 (event selection).

### Next measurement (selection branch)

Reproduce the licentiate's cut-flow on the registered signal sample
(plan 20) and cosmic sample (plan 21).

## 7. Truth-leakage gate (recursive predicate)

At every leaf in §2–§6, the audit asks:

> *Does this decision depend on a Class B column?*

The acceptable answers are:

- *No.* Production-ready leaf.
- *Yes, only inside a `@validation_only` decorated function.*
  Acceptable for scoring, never for selection.
- *Yes, but only as a sparse-table fallback when Class A inputs
  are unavailable.* Acceptable temporarily; tracked as a migration
  item.
- *Yes, in a production decision path.* **Audit failure.** The leaf
  is not signed off until it migrates.

Plan 01 §4 implements the audit. Plan 08 §3.7 lists the current
violations. Each violation has an exit criterion in the owning
subsystem plan.

## 8. Visualisation

```
Root: Can reconstruction prove n̄ annihilation from observables alone?
  ├── §2 Vertex                 (V.1 hits→tracks, V.2 direction,
  │                              V.3 foil projection, V.4 aggregation,
  │                              V.5 acceptance)              → plan 25
  ├── §3 Charged objects        (C.1 cand, C.2 dE/dx, C.3 range,
  │                              C.4 scint match, C.5 π/p decision,
  │                              C.6 rejection)               → plans 25, 27, 28, 29
  ├── §4 Photon / π⁰            (P.1 cluster, P.2 ch/n test,
  │                              P.3 direction, P.4 energy,
  │                              P.5 pairing, P.6 accidental,
  │                              P.7 kinematic fit)           → plans 31, 32, 33, 34, 35
  ├── §5 Event variables        (E.1-E.9)                     → plan 36
  ├── §6 Selection              (S.1-S.6)                     → plan 37
  └── §7 Truth-leakage gate     (recursive at every leaf)     → plan 01 audit
```

(Per 00_README §4.7 numbering: plan 31 is cluster, 32 shower shape,
33 photon object, 34 π⁰ pairing, 35 kinematic fit, 36 event
variables, 37 event selection.)

## 9. Acceptance criteria

- §2–§7 are populated with the leaf identities listed.
- Subsystem plans 25–37 cite the leaf identities (V.1, C.2, P.5,
  …) verbatim and their per-leaf input/output/decision schemas
  populate the templates here.
- Plan 38 truth-substitution ladder uses the leaf identities as
  rungs.
- Plan 47 reproduction ledger cites leaf identities in its method
  column.

## 10. Reviewer challenge

This tree is signed off only after a reviewer has tried to find a
reconstruction decision that does not fit any leaf above. New leaves
identified by review become §2–§6 additions in v0.2.

## 11. Risks and mitigations

- *Risk:* leaf renames after subsystem plans land cascade rework.
  *Mitigation:* this plan is signed before 25–37 start; renames
  require a paired DEC entry and revisions to all citing plans.
- *Risk:* tree drifts from code as reconstruction.py evolves.
  *Mitigation:* plan 53 CI rule: edits to public reconstruction
  functions trigger a check that this tree is updated.
- *Risk:* truth-leakage audit becomes too strict and breaks legacy
  studies.
  *Mitigation:* §7 acceptable-answers ladder; sparse-table
  fallbacks remain allowed during migration.

## 12. Dependencies

- **00_README** — plan space.
- **01_realism_contract** — Class A/B/C scheme; §7 audit gate.
- **07, 08** — simulation/reconstruction baselines.
- **09** — column classifications used in per-leaf input lists.
- *Consumed by:* plans 25, 27–37, 38 (rungs), 47 (ledger method),
  50 (defence package).

## 13. References

- `docs/detector_fundamental_question_tree.md` — direct template.
- `NNBAR_Detector/docs/reconstruction.md` — implementation reference
  this tree decomposes.
