---
id: 48_prior_art_survey
title: Prior-art survey — methods we may borrow
version: 0.1
status: draft
owner: Methodology Council
depends_on: [00_README, 24_reconstruction_question_tree]
outputs:
  - {path: docs/rebuild_plans/48_prior_art_survey.md, schema: this file}
acceptance:
  - {test: each leaf in plan 24 has at least one prior-art entry, method: leaf cross-reference, pass_when: full coverage}
  - {test: each entry has a citation that resolves to a paper or codebase, method: link verification, pass_when: zero broken refs}
risks:
  - {risk: borrowed method ports incorrectly because of NNBAR-specific geometry / physics, mitigation: §3 adaptation notes}
estimated_effort: M
last_updated: 2026-05-09
---

# Prior-art survey

*Charter.* For each reconstruction leaf in plan 24, list candidate
methods drawn from existing HEP / particle-physics practice that
could be borrowed when plan 49 selects an improvement target. The
survey is descriptive; selection is plan 49's job.

## 1. Tracking and vertexing

| Method | Origin | Useful for | Adaptation note |
|---|---|---|---|
| Hough transform (helical) | ALICE TPC | V.1 (track finding) | NNBAR has no B-field → use straight-line variant |
| Kalman filter | ATLAS / CMS / ACTS | V.2 (track fit) | covariance for free; ACTS already vendored |
| Riemann fit | various | V.1, V.2 | analytic for circles; not directly applicable without B |
| Billoir χ² vertex fit | LHCb / ATLAS | V.4 | covariance-weighted aggregation |
| Adaptive vertex fit | CMS | V.4 | iterative outlier-aware |
| ACTS toolkit | open-source | V.1–V.4 | already at `acts_tracking/`; modular |

## 2. Calorimetry and EM objects

| Method | Origin | Useful for | Adaptation note |
|---|---|---|---|
| Topological clustering | ATLAS | P.1 | well-studied, threshold-tunable |
| Sliding-window clustering | LHC EM cals | P.1 | simpler |
| PandoraPFA particle flow | ILC / CMS | P.1, P.2 | most ambitious; biggest gain |
| Shower-shape moments | ATLAS / CMS | P.2 | standard EM/hadron discriminant |
| Photon mass-constrained kinematic fit | Belle II / GlueX | P.7 | improves σ(M) ~ 20-40% |
| Vertex-constrained event fit | various | P.7 | ties photons + tracks to common vertex |

## 3. PID and event-shape

| Method | Origin | Useful for | Adaptation note |
|---|---|---|---|
| dE/dx truncated mean | ALICE | C.2 | well-studied; cut fractions tunable |
| Likelihood-ratio PID | LHCb | C.5 | needs labelled training data (plan 23) |
| BDT / NN PID | CMS / ATLAS | C.5 | per plan 57 protocol |
| Sphericity tensor | original Bjorken-Brodsky | E.5 | already in code |
| Fox-Wolfram moments | original Fox-Wolfram | E.6 | added in plan 36 |
| Thrust | Brandt-Dahmen | E.6 | added in plan 36 |
| Flavour-tagging-style multivariate event tag | Belle / BaBar | S.6 | NNBAR analogue: signal vs cosmic |

## 4. Citation chain

Each entry above resolves to a paper or codebase. Codex-supervisor
populates the citation block in v0.2; representative subset:

- ALICE TPC: ALICE Collaboration, *Int. J. Mod. Phys. A* 29 (2014).
- ACTS: <https://github.com/acts-project/acts>.
- ATLAS topo-clusters: ATLAS PUB-2008-002 and successors.
- PandoraPFA: J. Marshall, M. Thomson, *EPJ C* 75 (2015) 439.
- Belle II kinematic-fit: Belle II software documentation.
- Fox-Wolfram: Fox & Wolfram, *Phys. Rev. Lett.* 41 (1978) 1581.
- Cowan asymptotic significance: Cowan et al., *EPJ C* 71 (2011)
  1554.
- pyhf: Heinrich et al., <https://pyhf.readthedocs.io>.

## 5. Adaptation notes

NNBAR-specific constraints that affect borrowing:

- *No B-field.* Tracking methods relying on curvature/momentum
  (Riemann fits, helix Hough) require the straight-line analogue.
- *TPC sparse hit recording.* TPCSD records only first/last steps in
  volume (plan 07 §6.1). Methods assuming dense step-level data need
  adaptation or a switch to dense recording.
- *Lead-glass + scintillator combined calorimetry.* Many EM methods
  assume one calorimeter; particle-flow-style methods naturally
  handle the combination but need careful weighting.
- *Geant4-only data.* No real-data calibration; every borrowed
  method gets a "MC-only" caveat in the limitations registry until
  commissioning.

## 6. Acceptance criteria

- §1, §2, §3 cover every leaf in plan 24.
- §4 citations resolve.
- §5 adaptation notes explicit.

## 7. Dependencies

- **24** — leaf identities.
- *Consumed by:* plan 49 (improvement selection), plan 50.

## 8. References

(Full bibliography in v0.2; representative subset in §4.)
