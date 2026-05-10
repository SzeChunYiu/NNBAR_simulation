---
id: 54_open_data_archival
title: Open-data archival — Zenodo, DOI, RECAST-style preservation
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [00_README, 03_dataset_registry, 11_build_and_runtime_environment, 47_reproduction_ledger]
outputs:
  - {path: docs/rebuild_plans/54_open_data_archival.md, schema: this file}
acceptance:
  - {test: thesis-freeze package contains samples + plots + ledger + code at a Zenodo DOI, method: DOI registration, pass_when: DOI minted}
  - {test: Docker / Singularity image reproduces a smoke run from scratch, method: container build, pass_when: smoke reproduces}
  - {test: per-sample retention policy (plan 03 §11) enforced, method: registry audit, pass_when: zero retain-violations}
risks:
  - {risk: Zenodo size cap (50 GB / record) exceeded by full samples, mitigation: §3 split by sample tier}
estimated_effort: M
last_updated: 2026-05-09
---

# Open-data archival

*Charter.* At thesis-freeze, the rebuild publishes a self-contained
artifact set under a Zenodo DOI and a reproducible container. The
purpose is not "code release"; it is "the thesis is reproducible by
a stranger in five years."

## 1. Archival package contents

For each thesis-freeze:

- *Code.* Snapshot of `NNBAR_Detector/` and `nnbar_reconstruction/`
  at the freeze rev.
- *Plans.* Snapshot of `docs/rebuild_plans/` (this directory).
- *Decision log.* Snapshot of `docs/governance/DECISION_LOG.md`.
- *Ledger.* Snapshot of `docs/thesis_reproduction_ledger.md`.
- *Defence packages.* `output/defense/*.yml`.
- *Samples.* Selected (not all — see §3 retention) frozen samples.
- *Container.* Docker / Singularity image with pinned Geant4,
  Python, Arrow, etc.
- *README.* Top-level "how to reproduce" pointing at the container
  and the ledger.

### 1.1 L1 EM/selection defence artifact pack

The thesis-freeze archive must preserve the L1 defence overlays as a
coherent artifact pack so a reviewer can rerun or inspect the EM and
selection claims without reconstructing the whole plan tree by hand.

| Pack member | Minimum archived artifact | Why it is retained |
|---|---|---|
| EM-object chain | plan-31 through plan-35 closure rows, method ids, and Class-B drop-hash summaries | proves photon/pi0 evidence is truth-blind and replayable |
| Ch 10 cut-flow | plan-37 independent `pass_*` counts and cumulative cut-flow rows | preserves the exact selection identity used by ledger rows |
| pile-up L11 | plan-58 overlay manifests, occupancy tables, and L11 status rows | shows whether independent-event assumptions are still caveated |
| strange V0 | plan-59 branching snapshot, V0 candidate summary, and residual intervals | preserves K_S/Lambda/Sigma contamination evidence |
| TOF timing | plan-61 TOF candidate summaries, resolution budgets, and ROC rows | preserves timing-separation evidence and caveats |
| Bayesian limits | plan-64 prior-sensitivity table and plan-46 comparison ratios | preserves low-count prior-sensitivity evidence |
| defence routing | plan-50 overlays, plan-51 question seeds, plan-55 annex, plan-56 glossary terms | lets a future reader map artifacts to reviewer questions |

If a pack member is blocked at freeze, archive the blocked manifest row,
the missing input name, and the owning plan instead of dropping the row.
That rule keeps open caveats visible in the DOI record.

## 2. Reproducibility container

The container builds from a clean base, fetches pinned dependencies
(Geant4, Arrow, etc.), and runs a smoke sample to confirm the build
works. Recipe in `containers/Dockerfile`.

The container is *not* expected to scale to full statistics on a
single machine; it demonstrates reproducibility, not throughput.
Full-statistics regeneration runs on LUNARC per plan 52.

## 3. Retention policy

Plan 03 §11 retention policy applies. At thesis-freeze:

- *Tier A.* Headline samples (`sig_foil_v3`, `cosmic_cry_*_v1`,
  `beam_neutron_*_v1`) — archived to Zenodo with full statistics.
- *Tier B.* Calibration samples — archived (smaller volume).
- *Tier C.* Study/scan samples (varied parameter scans) — manifests
  archived; underlying parquet may be retired per plan 03.

## 4. RECAST-style preservation

The defence packages (plan 50) plus the container plus the ledger
constitute a RECAST-style preserved analysis: a reviewer can
reproduce a numeric claim by:

1. Pulling the Zenodo DOI.
2. Running the container.
3. Following the `reproducing_command` in the relevant defence
   package.

## 5. Acceptance criteria

- §1 archival package present in `release/` directory at thesis-
  freeze.
- §2 container builds and runs smoke.
- §3 retention policy enforced; manifests retained for retired
  samples.
- §4 a sampler reviewer pull-and-reproduce drill is executed once
  before final freeze.

## 6. Dependencies

- **03, 11, 47** — inputs.
- *Consumed by:* thesis-freeze gate.

## 7. References

- Zenodo documentation.
- RECAST framework (Cranmer et al.).
- HEP analysis preservation guidelines (HSF).
