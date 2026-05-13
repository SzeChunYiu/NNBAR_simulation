# Lane: carbon-foil-alignment

## Goal

Make the carbon foil radius and source-vertex assumptions auditable across the
thesis, Geant4 geometry, particle-gun fallback, and Python configuration before
vertex or photon-conversion validations are promoted. This first compact-safe
iteration should verify the mismatch and produce a blocker/decision surface; do
not silently change geometry constants without a decision-log entry.

## Writable scope

- Create: `docs/reports/carbon_foil_vertex_alignment.md`
- Optional create: `scripts/verify_carbon_foil_alignment.py`
- Modify only for lane status: `docs/parallel-sessions/MASTER_PLAN.md`

Forbidden:

- Do not submit SLURM jobs or run detector simulations.
- Do not edit production C++/Python geometry constants in this first audit unless
  an approved decision-log entry already resolves the target convention.
- Do not invent thesis values, sample paths, or generator behavior; unresolved
  evidence must be marked `OPEN:` with a concrete owner and next check.
- Do not cite unverified line numbers, unsupported CLIs, or non-existent files.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `CODING_STANDARDS.md`
4. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/3_HIBEAM_NNBAR_experiment.tex`
5. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/6_Signal_Bkg_simulation.tex`
6. `NNBAR_Detector/src/core/DetectorConstruction.cc`
7. `NNBAR_Detector/src/core/PrimaryGeneratorAction.cc`
8. `NNBAR_Detector/src/PrimaryGeneratorAction.cc`
9. `nnbar_reconstruction/config/nnbar_geometry.yaml`
10. `docs/rebuild_plans/07_simulation_atomic_walkthrough.md`
11. `docs/rebuild_plans/03_dataset_registry.md`
12. `docs/governance/DECISION_LOG.md`

Before committing any path, value, function, or command claim, apply the verifier
rules in `docs/parallel-sessions.md`. Use `rtk proxy ls`, `rtk proxy grep -n`,
and quoted `wc -l` output rather than guessed line references.

## One compact-safe iteration

1. Claim the lane by changing its MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that status-only change.
2. Verify the thesis and repo surfaces exist, then grep for target/foil radius,
   source vertex distribution, carbon volume construction, particle-gun source
   position, and Python `target.radius` configuration.
3. Create `docs/reports/carbon_foil_vertex_alignment.md` with sections:
   - thesis convention: target radius, source-vertex distribution, and gravity or
     beam-optics bias evidence;
   - Geant4 geometry convention: carbon volume dimensions/material and placement;
   - generator convention: MCPL vs particle-gun fallback source position and any
     configurable target-radius surface;
   - Python reconstruction/config convention: target radius and vertex cuts;
   - mismatch table: verified value, source file, verification command, impact,
     and required DEC/sample-registry follow-up;
   - recommended next smallest implementation task after the convention is
     approved.
4. If adding the optional script, keep it read-only and fail-closed: it may grep
   known config/source surfaces and report mismatches, but it must not modify
   constants.
5. Mark the MASTER_PLAN row `DONE` only after the report exists, touched files are
   under file caps, and notes summarize whether a decision-log entry or code
   alignment task remains open.

## Verification command

```bash
rtk proxy wc -l docs/reports/carbon_foil_vertex_alignment.md
rtk proxy grep -n "OPEN:\|target radius\|carbon\|particle-gun\|target.radius" docs/reports/carbon_foil_vertex_alignment.md
# If the optional helper exists:
rtk python scripts/verify_carbon_foil_alignment.py
rtk proxy wc -l scripts/verify_carbon_foil_alignment.py
```

## Stop condition

Stop after committing the audit report and MASTER_PLAN status update, or after
recording a concrete `OPEN:` blocker with verified evidence. Leave production
geometry/config/generator edits for a separate compact-safe implementation task
unless the convention is already approved in the decision log.
