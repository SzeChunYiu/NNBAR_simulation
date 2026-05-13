# OpenMC continuous-energy data staging smoke check (worker-0, 2026-05-12)

## Scope

Compact blocker-disposition iteration for `mcaccel-openmc-adapter`. The check
verifies that a staged OpenMC continuous-energy HDF5 library is now usable on
LUNARC for the two Iteration-1 targets that previously failed before transport.
No NNBAR production detector code, SLURM production script, macro, or data file
was modified.

## Inputs checked on LUNARC

- OpenMC binary: `/projects/hep/fs10/shared/nnbar/billy/openmc/build-lunarc/bin/openmc`.
- Cross-section XML: `/projects/hep/fs10/shared/nnbar/billy/openmc-data/nndc_hdf5/cross_sections.xml`.
- XML inventory smoke: `grep -c` found `U235.h5`, `U238.h5`, `H1.h5`, `O16.h5`, and `Zr90.h5` exactly once each.
- Verification run directory: `/projects/hep/fs10/shared/nnbar/billy/openmc-ce-data-verify-worker0-20260512T135823+0200`.
- Stale `openmc.log` files in that directory preserve the earlier missing-XML failure for contrast; the successful smoke evidence is in `openmc-ce-verify.out` / `openmc-ce-verify.log`.

## Smoke verification commands

Each target copied the prior reduced benchmark input into the verification run
directory, removed only generated statepoint/summary files in that copy, then
ran with:

```bash
export OPENMC_CROSS_SECTIONS=/projects/hep/fs10/shared/nnbar/billy/openmc-data/nndc_hdf5/cross_sections.xml
/projects/hep/fs10/shared/nnbar/billy/openmc/build-lunarc/bin/openmc -s 1 -n 100 .
```

## Results

| Target | Exit | Cross-section read | Total elapsed | Output evidence |
| --- | ---: | ---: | ---: | --- |
| HEU-MET-FAST-001 case 1 | 0 | 1.7424 s | 1.8748 s | `statepoint.4.h5` 31 KiB; `summary.h5` 79 KiB |
| PWR pin cell | 0 | 1.9335 s | 1.9899 s | `statepoint.4.h5` 31 KiB; `summary.h5` 45 KiB |

Both `openmc-ce-verify.out` logs printed `Reading cross sections XML file...`
and the successful verification logs did not reproduce the earlier
`No cross_sections.xml` / `OPENMC_CROSS_SECTIONS` failure.

## Disposition

The continuous-energy data gate is smoke-unblocked for reduced HEU and PWR
runs. This does **not** complete the Iteration-3 QMC/RNG adapter or the full
benchmark gate: production particle counts, keff/reaction-rate acceptance, and
bit-exact RNG/trace comparisons still need a later adapter implementation on
LUNARC.
