# Paper section 4 — Optimization catalogue evidence plan

Status: **BLOCKED**

This specification defines how optimization ideas become paper subsections. It
connects bottleneck IDs, implementation branches, verification status, and
benchmark rows.

## Section purpose

Section 4 catalogs the optimization families: PostStep GPIL dispatch, lambda
and table caching, geometry navigation, RTX backend work, and GPU particle or
physics-kernel offload.

## Required evidence before prose can be drafted

- Each subsection maps to one or more BD IDs or phase IDs.
- Each implementation has an isolated branch/commit, test evidence, and claim
  level.
- Each performance or parity statement links to section 5/6 harness rows.
- Deferred or negative outcomes remain visible with blocker or result tags.
- No optimization is described as publishable until its parity and hardware
  requirements are satisfied.

## Figures and tables

- Table 4.1: optimization catalogue with BD IDs, branch, status, and claim level.
- Figure 4.1: data/control-flow sketch for PostStep GPIL dispatch.
- Figure 4.2: geometry/backend path showing scalar, CUDA, and RTX options.

## Current gaps

- OPEN: `catalogue_table_missing` — phase and BD evidence is not normalized into
  a paper-ready catalogue.
- OPEN: `implementation_rows_missing` — many BD entries are source-review ideas
  without implementation commits.
- OPEN: `parity_links_missing` — optimization entries lack section 6 parity rows.

## Acceptance checklist

- [ ] Every subsection has BD/phase IDs and claim levels.
- [ ] Every implementation claim links to tests and commits.
- [ ] Negative and deferred outcomes remain listed.
