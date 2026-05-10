---
id: 24_6_selection_branch
title: Reconstruction question tree - selection branch
version: 0.1
status: draft
owner: Methodology Council
parent: 24_reconstruction_question_tree
last_updated: 2026-05-09
---

# Reconstruction question tree - selection branch

This file is a split-out branch of `docs/rebuild_plans/24_reconstruction_question_tree.md`
created to keep each plan file under the 500-line cap. It inherits the
truth-leakage gate, acceptance criteria, dependencies, and references from
plan 24.

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
