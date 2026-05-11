# Lane: openmc-line-reference-fix

## Goal

Fix the OpenMC bottleneck database line-reference verifier issue found by the
planner review. In OpenMC `v0.15.3`, `calculate_urr_xs` starts at line 871, but
BD-openmc-007 currently cites lines 879--950 while also naming that function.
The compact unit must re-run the line-reference checks and correct the report or
wording so every function/line claim is verifier-clean.

## Files

- Modify: `docs/reports/bottleneck_database_openmc.md`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only
- Read-only remote source: `/projects/hep/fs10/shared/nnbar/billy/openmc` on LUNARC

Do not edit NNBAR production code, OpenMC source, or submit SLURM jobs.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `docs/parallel-sessions/openmc-source-review.md`, and `CODING_STANDARDS.md`.
2. Before any `ssh lunarc` command, run the standard socket check:
   `ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh`.
3. In the LUNARC OpenMC tree, verify `git describe --tags --exact-match` is
   `v0.15.3` and grep every function named by `docs/reports/bottleneck_database_openmc.md`.
4. Correct BD-openmc-007 so the named `calculate_urr_xs` signature line is
   inside the cited range, or remove the function-name claim from that entry.
5. Scan the remaining BD-openmc entries for the same pattern and fix any other
   mismatch discovered by the verifier.
6. Update this lane's `MASTER_PLAN.md` row to `DONE` only after the report and
   verification note are consistent.

## Verification

Run:

```bash
rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
rtk proxy bash -lc 'ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/openmc && git describe --tags --exact-match && grep -n \"void Nuclide::calculate_xs\|void Nuclide::calculate_urr_xs\|void Material::calculate_neutron_xs\|void Particle::update_neutron_xs\|double Reaction::xs\|void ThermalScattering::calculate_xs\|void ThermalData::calculate_xs\|void CorrelatedAngleEnergy::sample\|void KalbachMann::sample\|void get_energy_index\|void CoherentElasticAE::sample\|void IncoherentInelasticAE::sample\|WindowedMultipole::evaluate\" src/nuclide.cpp src/material.cpp src/particle.cpp src/reaction.cpp src/thermal.cpp src/secondary_correlated.cpp src/secondary_kalbach.cpp src/secondary_thermal.cpp src/wmp.cpp"'
rtk proxy bash -lc 'grep -c "^### BD-openmc-" docs/reports/bottleneck_database_openmc.md && grep -c "| Validation |" docs/reports/bottleneck_database_openmc.md && grep -c "| Status | OPEN |" docs/reports/bottleneck_database_openmc.md'
rtk wc -l docs/reports/bottleneck_database_openmc.md docs/parallel-sessions/MASTER_PLAN.md
```

Expected: OpenMC tag is `v0.15.3`; every named function signature is inside its
cited range or no longer cited as a function claim; report entry/validation/open
status counts remain 12; touched local files remain <=500 lines.

## Stop condition

Stop after the report line-reference fix and `MASTER_PLAN.md` status update are
committed. Do not broaden the OpenMC review beyond verifier cleanup.
