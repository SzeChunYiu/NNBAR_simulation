---
id: 53_ci_regression_suite
title: CI regression suite — automated tests on every change
version: 0.1
status: draft
owner: Software Quality
depends_on: [00_README, 01_realism_contract, 03_dataset_registry, 19_simulation_validation_suite, 47_reproduction_ledger]
outputs:
  - {path: docs/rebuild_plans/53_ci_regression_suite.md, schema: this file}
  - {path: .github/workflows/ or .gitlab-ci.yml, schema: pipeline definition}
acceptance:
  - {test: realism audit runs on every PR, method: CI log, pass_when: green}
  - {test: registry integrity check runs on every PR touching data/registry, method: CI log, pass_when: green}
  - {test: simulation smoke test runs on every PR touching NNBAR_Detector/, method: CI log, pass_when: green}
  - {test: reconstruction smoke test runs on every PR touching nnbar_reconstruction/, method: CI log, pass_when: green}
  - {test: ledger refresh runs on every PR with code touching ledger-relevant modules, method: CI log, pass_when: green or yellow only}
risks:
  - {risk: CI runtime grows unmanageable, mitigation: §3 selective triggering by path}
estimated_effort: M
last_updated: 2026-05-09
---

# CI regression suite

*Charter.* Every PR runs a tiered set of automated checks. Plan 53
defines the tiers, the triggering rules, and the failure semantics.

## 1. Tiers

### Tier 1 — fast (every PR)

- Lint: pyright / ruff on `nnbar_reconstruction/`; clang-format on
  C++ headers.
- Realism audit (plan 01 §4).
- Registry integrity (plan 03 acceptance §10): hashes match for
  every frozen sample referenced by the PR.
- Reconstruction unit tests (`pytest NNBAR_Detector/tests/`).
- Plan-set audit: every plan file in `docs/rebuild_plans/` has a
  valid YAML header (plan 00 §7).

### Tier 2 — slow (PR + nightly)

- Simulation smoke build for every `WITH_*` permutation (plan 19
  §4).
- Simulation smoke run with 100 events on each build (plan 19 §3).
- Reconstruction smoke on the smoke sample.

### Tier 3 — release (manual + weekly)

- Full plan-47 ledger refresh: re-run reproducing commands for every
  green ledger row.
- Truth-substitution ladder rerun on signal sample (plan 38).
- Sanity plots (plan 19 §2) regenerated and visually compared.

## 2. Triggering

PR diff path determines the tier:

- `nnbar_reconstruction/**` → Tier 1 reconstruction tests.
- `NNBAR_Detector/{src,include,macro,CMakeLists.txt}/**` → Tier 1
  simulation smoke + Tier 2 nightly.
- `data/registry/**` → Tier 1 registry integrity.
- `docs/rebuild_plans/**` → Tier 1 plan-set audit.
- `docs/governance/**` → Tier 1 decision-log integrity.

## 3. Failure semantics

- *Tier 1 failure* blocks merge unconditionally.
- *Tier 2 failure* blocks merge for changes inside Tier 2 trigger
  paths; warns otherwise.
- *Tier 3 failure* opens a tracking issue; never blocks merge but
  changes ledger row status to red until investigated.

## 4. Coverage targets

- Reconstruction module test coverage ≥ 70% line coverage.
- Realism audit coverage = 100% of files under
  `nnbar_reconstruction/` minus test files.
- Plan-file YAML header coverage = 100%.

## 5. Acceptance criteria

- §1 tiers implemented in `.github/workflows/` (or equivalent).
- §2 triggering wired by path filter.
- §3 failure semantics documented and enforced.
- §4 coverage targets met on `main`.

## 6. Risks

- *Risk:* nightly load is heavy; cluster contention.
  *Mitigation:* nightly Tier 2 batches across 24 hours; Tier 3
  weekly.
- *Risk:* smoke samples drift from being representative.
  *Mitigation:* Tier 3 ledger refresh is the production check.

## 7. Dependencies

- **01, 03, 19, 47** — checks consumed by tiers.
- *Consumed by:* every other plan's "CI rule" entry.

## 8. References

- pytest + GitHub Actions standard practice.
- ATLAS / CMS CI conventions.
