# Lane: pi0-foil-energy-scan-ext

## Goal

Create the simulation macro and SLURM wrapper for an extended mono-π0 energy
scan at the foil origin: 100, 200, 300, 400, and 500 MeV, 200 events each.

## Files to create/edit

- Create `NNBAR_Detector/macro/studies/pi0_foil_energy_scan_ext.mac`
- Create `NNBAR_Detector/slurm/pi0_energy_scan_ext.sbatch`
- Read existing `NNBAR_Detector/macro/studies/pi0_foil_energy_scan.mac` first.

## Implementation steps

1. Mirror the naming convention `build_lunarc/output/pi0_mono_{E}mev/` used by
   the existing mono-π0 outputs.
2. Make the wrapper an array over the five requested energies and keep event
   count at 200 per energy.
3. Validate macro command spelling locally and run `bash -n` on the wrapper.
4. If submitting, use the LUNARC SSH socket guard from the repo instructions and
   record job id/output path evidence in `MASTER_PLAN.md` after completion.

## Test command

```bash
rtk proxy bash -lc "bash -n NNBAR_Detector/slurm/pi0_energy_scan_ext.sbatch && grep -n pi0_mono NNBAR_Detector/macro/studies/pi0_foil_energy_scan_ext.mac"
```

## Stop condition

Stop after macro/wrapper validation and, only if the lane deliberately submits,
a single guarded LUNARC submission with job evidence. Do not edit reconstruction
Python.
