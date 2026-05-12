# Paper section 7 — Competitor comparison evidence plan

Status: **BLOCKED**

This specification defines the evidence required before comparing G4GPU results
with Celeritas, AdePT, Opticks, VecGeom, or other acceleration baselines.

## Section purpose

Section 7 positions the measured results against existing accelerator transport
systems while respecting differences in physics coverage, geometry support,
hardware, and integration maturity.

## Required evidence before prose can be drafted

- Competitor versions, commits, build options, and supported physics domains are
  recorded.
- Comparisons use the same workload, physics-list, seed, and hardware matrix
  where possible.
- Any missing competitor baseline has a documented blocker and a fair-scope
  explanation.
- Qualitative comparisons cite primary project papers or documentation.
- Performance comparisons use L3 rows or are clearly marked as out-of-scope.

## Figures and tables

- Table 7.1: competitor feature and physics coverage matrix.
- Table 7.2: measured comparable rows or documented blockers.
- Figure 7.1: speedup comparison for workloads with valid matched baselines.

## Current gaps

- OPEN: `celeritas_baseline_missing` — no matched Celeritas benchmark row exists.
- OPEN: `adept_baseline_missing` — no matched AdePT benchmark row exists.
- OPEN: `opticks_scope_missing` — optical-photon comparison scope is not frozen.
- OPEN: `vecgeom_scope_missing` — VecGeom comparison role is not frozen.

## Acceptance checklist

- [ ] Competitor scope and versions are documented.
- [ ] Matched baselines exist or blockers are evidenced.
- [ ] Qualitative claims cite primary sources.
