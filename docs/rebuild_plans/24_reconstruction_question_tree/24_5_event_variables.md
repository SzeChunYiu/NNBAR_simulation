---
id: 24_5_event_variables_branch
title: Reconstruction question tree - event-variable branch
version: 0.1
status: draft
owner: Methodology Council
parent: 24_reconstruction_question_tree
last_updated: 2026-05-09
---

# Reconstruction question tree - event-variable branch

This file is a split-out branch of `docs/rebuild_plans/24_reconstruction_question_tree.md`
created to keep each plan file under the 500-line cap. It inherits the
truth-leakage gate, acceptance criteria, dependencies, and references from
plan 24.

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
