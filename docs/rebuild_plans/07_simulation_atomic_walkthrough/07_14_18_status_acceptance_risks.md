---
id: 07_14_18_status_acceptance_risks
title: Simulation atomic walkthrough §§14–18 — limitations, acceptance, risks, dependencies, references
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

## 14. Limitations of this walkthrough

This v0.1 of plan 07 is a structural skeleton with cited file paths
and line numbers for the load-bearing components. The following deeper
sections are stubs that codex-supervisor will fill against this
plan's acceptance criteria:

- *§5.4 builder details.* Each of the seven sub-detector builders is
  several hundred lines (e.g. `Scintillator_geometry.cc` ≈ 34 KB,
  `beampipe_geometry.cc` ≈ 35 KB). Per-builder volumes, materials,
  and placements are deferred to plan 16.
- *§6.2 SD details.* Each non-TPC SD's `ProcessHits` body is short
  (≈ 4 KB on average) and follows the TPC pattern with minor variants;
  per-SD walkthroughs are deferred to plan 14.
- *§9 ParquetOutputManager schema.* The exact field list per parquet
  is the authority of plan 09; this plan only names the files.
- *§10.1 PrimaryGeneratorAction modes.* The 22 KB action source
  contains the mode dispatch logic; plan 18 (calibration samples) and
  plan 21 (cosmic) need to walk specific code paths for their work.

These deferrals are intentional: the structural skeleton is enough to
gate the dependent plans, and the deep dives have natural homes in the
plans that consume them.

## 15. Acceptance criteria

- §3, §4, §5, §6.1, §7 are complete (current draft).
- §5.4, §6.2, §10.1 are filled to the same depth as §6.1 by plan 16,
  plan 14, plan 21 respectively.
- A CI rule blocks PRs that touch `NNBAR_Detector/src/{core,detector,
  sensitive,hits,generator,output,physics,gpu,util}/*` without a
  matching edit to this file.
- Every output parquet file in §9 has its column schema in plan 09.
- Every `WITH_*` build option in §2.1 has an entry in plan 14
  validation suite covering the on/off difference.

## 16. Risks and mitigations

- *Risk:* this walkthrough rots silently when code changes land
  outside the CI rule's regex.
  *Mitigation:* the realism audit (plan 01) imports the file list
  this plan covers and emits a warning when a referenced symbol moves.
- *Risk:* duplicate authority with plan 09 (data dictionary) on
  output-parquet schema.
  *Mitigation:* §9 names the files only; column names, dtypes, units,
  and Class A/B/C live in plan 09. Each plan references the other.
- *Risk:* line numbers drift after refactors.
  *Mitigation:* plan 53 CI runs a "stale line number" linter that
  reports doc references to lines that no longer match the cited
  symbol.

## 17. Dependencies

- **00_README** — plan space.
- **01_realism_contract** — defines Class A/B/C; this walkthrough
  cites the contract for hit-field provenance.
- *Consumed by:* plan 09 (column schema), plan 10 (macros), plan 11
  (build env), plan 12 (physics list), plan 14 (validation), plan 16
  (geometry), plan 17 (field), plan 18 (intercalibration), plans 21,
  22, 23 (samples), plan 47 (reproduction ledger entries citing this
  plan as the simulation reference).

## 18. References

- `docs/detector_fundamental_question_tree.md` — the detector-side
  companion that motivated this rebuild.
- `NNBAR_Detector/docs/Detector_Geometry_Reference.md` — geometry
  reference text used by the geometry audit.
- `NNBAR_Detector/docs/reconstruction.md` — companion reference for
  what the reconstruction expects from this simulation.
