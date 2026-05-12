# Paper section 1 — Introduction evidence plan

Status: **BLOCKED**

This specification defines the evidence boundary for the paper introduction. It
may motivate Geant4 acceleration and NNBAR simulation needs, but it must not
state unmeasured speedups as results.

## Section purpose

Section 1 frames the computational problem, summarizes the role of Geant4 in
HEP detector simulation, and explains why reproducible parity-gated acceleration
matters for NNBAR-style full-detector workloads.

## Required evidence before prose can be drafted

- Related-work claims cite primary literature for Geant4, Celeritas, AdePT,
  Opticks, VecGeom, and GPU transport where used.
- Motivation claims about NNBAR workloads refer to W5/W6 evidence plans rather
  than unverified production speedups.
- Any numeric performance statement is labelled as L1 motivation unless it links
  to a harness row.
- The contribution list names artifact classes, not final scientific claims,
  until milestone gates are satisfied.

## Figures and tables

- Figure 1.1: reproducibility flow from hot-path analysis to parity-gated
  benchmark rows.
- Table 1.1: paper contributions mapped to evidence artifacts and claim level.

## Current gaps

- OPEN: `references_not_curated` — DOI/year coverage for related work is not
  complete.
- OPEN: `contribution_claim_levels_missing` — introduction contribution bullets
  are not yet mapped to L0--L4 claim levels.
- OPEN: `nnbar_motivation_evidence_missing` — W5/W6 runtime motivation depends
  on section 8 evidence.

## Acceptance checklist

- [ ] Every numeric claim has a claim-level label or harness row.
- [ ] Related-work references have DOI and year.
- [ ] Contributions are bounded by available artifacts and gates.
