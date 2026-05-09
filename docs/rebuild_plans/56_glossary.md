---
id: 56_glossary
title: Glossary — terms maintained alongside code
version: 0.1
status: draft
owner: Software Quality
depends_on: [00_README]
outputs:
  - {path: docs/rebuild_plans/56_glossary.md, schema: this file}
  - {path: docs/glossary.md, schema: living glossary}
acceptance:
  - {test: every plan-set acronym and shorthand is defined here, method: cross-reference scan, pass_when: zero undefined}
  - {test: terms match thesis Ch 14 glossary; deltas are flagged, method: comparison, pass_when: zero unflagged divergences}
risks:
  - {risk: thesis edits change a term; glossary lags, mitigation: §3 review on every thesis-freeze}
estimated_effort: S
last_updated: 2026-05-09
---

# Glossary

*Charter.* Single source of truth for every term used in the rebuild
plan-set, code, and ledger. Supersedes thesis Ch 14 glossary for
code-level usage; deltas are flagged.

## 1. Core terms

| Term | Definition |
|---|---|
| **NNBAR** | Neutron-antineutron oscillation experiment at ESS |
| **HIBEAM** | High Intensity Baryon Extraction And Measurement; the upstream phase of NNBAR |
| **TPC** | Time Projection Chamber; the tracking detector |
| **PMT** | Photomultiplier Tube |
| **MCPL** | Monte Carlo Particle List; the file format for primary particles |
| **CRY** | Cosmic-Ray Shower library (LLNL) |
| **SD** | Sensitive Detector (Geant4 class) |
| **POG** | Physics Object Group (working group structure) |
| **CP** | Combined Performance (working group) |
| **WG** | Working Group |
| **DAG** | Directed Acyclic Graph |
| **DEC-YYYY-MM-DD-N** | decision-log entry (plan 05) |
| **gate** | sign-off boundary (plan 06) |
| **leaf** | irreducible reconstruction decision (plan 24) |
| **ladder** | truth-substitution validation instrument (plan 38) |
| **ledger** | thesis reproduction ledger (plan 47) |
| **registry** | dataset registry (plan 03) or reviewer-question registry (plan 51) |
| **Class A** | experiment-equivalent column (plan 01 §2.1) |
| **Class B** | truth-only column (plan 01 §2.2) |
| **Class C** | MC-tuned calibration constant (plan 01 §2.3) |
| **digitisation seam** | the future-realism interface (plan 02) |
| **W-value** | mean energy per electron-ion pair (plan 17 §3) |
| **realism contract** | plan 01 |
| **fiducial volume** | detector region accepted by acceptance gate (plan 43) |
| **F-C** | Feldman-Cousins (plan 04 §5) |
| **CLs** | confidence-level method (plan 46 §2) |
| **N-1 plot** | distribution of variable C with all other cuts applied (plan 41) |
| **ROC curve** | signal acceptance vs background rejection (plan 41) |
| **IBU** | Iterative Bayesian Unfolding (plan 42) |

## 2. Geant4 / Hep terms

| Term | Definition |
|---|---|
| **FTFP_BERT** | Geant4 hadronic physics list (Fritiof + Bertini cascade) |
| **HP** | High-Precision neutron data (G4NDL) |
| **dE/dx** | mean energy loss per unit length |
| **MIP** | Minimum-Ionising Particle |
| **X₀** | radiation length |
| **λ_I** | nuclear interaction length |
| **PDG** | Particle Data Group |
| **G4** | Geant4 |
| **CMS PF** | CMS Particle Flow algorithm |
| **PandoraPFA** | Pandora Particle Flow Algorithm |
| **ACTS** | A Common Tracking Software toolkit |
| **GPS** | General Particle Source (Geant4) |

## 3. Update protocol

- New terms added on first use in any plan or code.
- Definitions cite the originating plan / paper.
- Thesis Ch 14 (overleaf-hibeam-thesis `14_HIBEAM_NNBAR_glossary.tex`)
  is the user-facing version; this glossary is the code-facing
  version. Differences are flagged and reconciled at thesis-freeze.

## 4. Acceptance criteria

- Every shorthand or acronym in plans 00–57 is defined.
- §3 reconciliation with thesis glossary done at thesis-freeze.

## 5. Dependencies

- **00_README** — plan space.
- *Consumed by:* every plan, every note, every ledger row.
