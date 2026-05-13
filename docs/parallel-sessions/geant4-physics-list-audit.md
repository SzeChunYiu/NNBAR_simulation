# Lane: geant4-physics-list-audit

## Goal

Create a compact reproducibility audit for the Geant4 physics-list/version
contract. The audit must document what the checked-out detector source actually
registers, how that differs from thesis-era expectations, and what validation
tags are needed before neutron/background or material-budget numbers are cited.

Do **not** run new simulations in this iteration.

## Writable scope

- Create: `docs/reports/geant4_physics_list_reproducibility.md`
- Modify only for status updates: `docs/parallel-sessions/MASTER_PLAN.md`
- Optional helper only if it stays under 200 lines:
  `scripts/verify_physics_list.py`

Forbidden:

- Do not edit `NNBAR_Detector/src/PhysicsList.cc` or C++ detector source in
  this audit-only iteration.
- Do not submit SLURM jobs.
- Do not change Python analysis/reconstruction files.

## Required reading

- `docs/parallel-sessions.md`
- `docs/parallel-sessions/MASTER_PLAN.md`
- `docs/rebuild_plans/12_physics_list_audit.md`
- `docs/rebuild_plans/45_systematics_taxonomy.md`
- `CODING_STANDARDS.md`

## One-iteration cycle

1. Claim the lane by changing the MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that one-line change.
2. Verify source/report files before citing them:
   ```bash
   rtk proxy ls NNBAR_Detector/src/PhysicsList.cc \
     NNBAR_Detector/src/core/PhysicsList.cc \
     docs/rebuild_plans/12_physics_list_audit.md
   rtk proxy wc -l NNBAR_Detector/src/PhysicsList.cc \
     NNBAR_Detector/src/core/PhysicsList.cc \
     docs/rebuild_plans/12_physics_list_audit.md
   ```
3. Run source greps and quote their output in the report instead of inventing
   line references:
   ```bash
   rtk proxy grep -n "RegisterPhysics" NNBAR_Detector/src/PhysicsList.cc
   rtk proxy grep -n "G4HadronPhysicsFTFP_BERT" NNBAR_Detector/src/PhysicsList.cc
   ```
   If you inspect another duplicate `PhysicsList.cc`, run the same greps there
   and explain which source path is authoritative.
4. Create `docs/reports/geant4_physics_list_reproducibility.md` with:
   - observed constructors from source;
   - thesis/rebuild-plan expectation for EM option4 and FTFP_BERT_HP;
   - Geant4 version evidence from checked-in build files or a guarded LUNARC
     query; if unavailable, mark `OPEN:` rather than guessing;
   - a table of required validation tags, at minimum `nominal_non_hp` and
     `nominal_hp`;
   - explicit downstream observables at risk: neutron/background rates,
     photon/material-budget response, and systematics row N4.
5. If you run any LUNARC command, first run the socket guard:
   ```bash
   rtk proxy bash -lc "ssh -O check lunarc 2>/dev/null && echo Connected || /Users/billy/lunarc-init.sh"
   ```
   Then use guarded RTK SSH only, for example:
   ```bash
   rtk proxy ssh lunarc "geant4-config --version 2>/dev/null || true"
   ```
6. Verify:
   ```bash
   rtk proxy wc -l docs/reports/geant4_physics_list_reproducibility.md
   rtk proxy grep -n "OPEN:\|nominal_non_hp\|nominal_hp\|N4" \
     docs/reports/geant4_physics_list_reproducibility.md
   ```
   If you added the optional helper:
   ```bash
   rtk python scripts/verify_physics_list.py
   rtk proxy wc -l scripts/verify_physics_list.py
   ```
7. Mark the MASTER_PLAN row `DONE` only after the report exists and the
   verification output is recorded in the commit message or lane handoff.

## Stop condition

Stop after the report is committed and the MASTER_PLAN row is `DONE`, or after
recording a concrete blocker with `OPEN:` evidence. Leave any simulation campaign
or source-code physics-list switch as a separate future task.
