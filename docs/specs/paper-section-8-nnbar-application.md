# Paper section 8 — NNBAR detector simulation application evidence plan

Status: **BLOCKED**

This specification defines the evidence required before the paper can describe
end-to-end NNBAR detector simulation acceleration for W5/W6 workloads.

## Section purpose

Section 8 demonstrates how the acceleration study applies to full NNBAR signal
and cosmic workloads while preserving the production boundary that NNBAR uses
vanilla Geant4 until parity gates pass.

## Required evidence before prose can be drafted

- W5 signal and W6 cosmic samples are generated through the benchmark harness,
  not ad-hoc holder-node runs.
- Sample paths, Parquet manifests, seed sets, SLURM job IDs, build logs, and
  hardware evidence are recorded.
- Physics parity passes for every optimized row cited in the section.
- Reconstruction-facing outputs remain schema-compatible with existing NNBAR
  validation tools.
- Any blocked CRY/cosmic or π0/photon validation issue is either resolved or
  clearly excluded from the acceleration claim.

## Figures and tables

- Table 8.1: W5/W6 runtime and parity rows by hardware.
- Table 8.2: output-schema and reconstruction validation checks.
- Figure 8.1: NNBAR simulation pipeline with benchmark harness boundaries.
- Figure 8.2: wall-clock contribution breakdown for W5/W6.

## Current gaps

- OPEN: `w5_w6_harness_rows_missing` — no benchmark rows exist for NNBAR full
  event workloads.
- OPEN: `cosmic_recovery_blocked` — CRY cosmic production remains blocked for
  unresolved bin-5 paths.
- OPEN: `photon_pi0_validation_blocked` — photon conversion and π0 response
  gates remain fail-closed.
- OPEN: `production_boundary_not_approved` — no parity-approved switch from
  vanilla Geant4 exists.

## Acceptance checklist

- [ ] W5/W6 rows are measured through the harness.
- [ ] Parity passes for every optimized NNBAR row.
- [ ] Reconstruction compatibility checks pass on generated outputs.
