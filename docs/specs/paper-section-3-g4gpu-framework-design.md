# Paper section 3 — G4GPU framework design evidence plan

Status: **BLOCKED**

This specification defines the design evidence needed for the G4GPU framework
section. It must describe architecture and isolation without implying production
adoption in NNBAR before parity gates pass.

## Section purpose

Section 3 explains the isolated G4GPU architecture, backend abstraction, build
strategy, and relationship to vanilla Geant4 and NNBAR detector simulation.

## Required evidence before prose can be drafted

- `docs/policies/g4gpu-isolation.md` is cited for production-boundary rules.
- Each described subsystem links to an isolated G4GPU commit, branch, or design
  report.
- Backend diagrams match implemented or scaffolded interfaces, with L0/L1/L2
  labels where runtime evidence is incomplete.
- Build and dependency claims reference saved configure/build logs.
- Any NNBAR integration statement states that vanilla Geant4 remains production
  until parity and hardware-matrix gates pass.

## Figures and tables

- Figure 3.1: isolated G4GPU architecture and NNBAR boundary.
- Figure 3.2: backend abstraction for CPU, CUDA, RTX, and future targets.
- Table 3.1: subsystem status with commit, tests, claim level, and blockers.

## Current gaps

- OPEN: `architecture_diagram_missing` — no section-ready architecture figure is
  committed.
- OPEN: `subsystem_status_table_missing` — phase commits are recorded in MASTER
  but not normalized into a paper table.
- OPEN: `runtime_backend_evidence_missing` — RTX and kernel scaffolds are not yet
  runtime/parity evidence.

## Acceptance checklist

- [ ] Isolation policy is cited and not contradicted.
- [ ] Every subsystem row links to a commit and verification artifact.
- [ ] Scaffold-only components are labelled L0/L1.
