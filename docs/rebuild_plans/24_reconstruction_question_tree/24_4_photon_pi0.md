---
id: 24_4_photon_pi0_branch
title: Reconstruction question tree - photon / pi0 branch
version: 0.1
status: draft
owner: Methodology Council
parent: 24_reconstruction_question_tree
last_updated: 2026-05-09
---

# Reconstruction question tree - photon / pi0 branch

This file is a split-out branch of `docs/rebuild_plans/24_reconstruction_question_tree.md`
created to keep each plan file under the 500-line cap. It inherits the
truth-leakage gate, acceptance criteria, dependencies, and references from
plan 24.

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
