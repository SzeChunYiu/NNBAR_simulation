# Lane: pi0-multiplicity-study

## Goal

Create a compact simulation study for 1, 2, and 3 π0 events at 150 MeV to feed
the multi-π0 response audit.

## Files to create/edit

- Create `NNBAR_Detector/macro/studies/pi0_multiplicity_1pi0.mac`
- Create `NNBAR_Detector/macro/studies/pi0_multiplicity_2pi0.mac`
- Create `NNBAR_Detector/macro/studies/pi0_multiplicity_3pi0.mac`
- Create `NNBAR_Detector/slurm/pi0_multiplicity_study.sbatch`

## Implementation steps

1. Verify the signal-particle macro command spelling in
   `NNBAR_Detector/src/core/PrimaryGeneratorAction.cc` before writing macros.
2. Use a 3-task SLURM array, 500 events per task, and outputs under
   `build_lunarc/output/pi0_multiplicity_N/`.
3. Run local macro greps and `bash -n` on the wrapper.
4. If submitting, use the LUNARC SSH socket guard from the repo instructions and
   record job id/output path evidence in `MASTER_PLAN.md` after completion.

## Test command

```bash
rtk proxy bash -lc "bash -n NNBAR_Detector/slurm/pi0_multiplicity_study.sbatch && grep -R signal_particle NNBAR_Detector/macro/studies/pi0_multiplicity_*pi0.mac"
```

## Stop condition

Stop after macros/wrapper validation and, only if the lane deliberately submits,
a single guarded LUNARC submission with job evidence. Do not edit reconstruction
Python.
