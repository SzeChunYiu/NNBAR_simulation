# RC-2 maximum-step patch report

Date: 2026-05-12  
Lane: worker-0  
Scope: C++ source patch plus report only; no SLURM submission.

## Source patched

`NNBAR_Detector/src/core/DetectorConstruction.cc` now installs a finite
`G4UserLimits::SetMaxAllowedStep(10.0 * cm)` guard for each sensitive detector
volume class wired by `DetectorConstruction`:

| Volume class | Logical-volume coverage | Step cap |
| --- | --- | --- |
| Carbon target | `CarbonLV` | `10.0 * cm` |
| Silicon tracker | every entry returned in `Silicon_output` | `10.0 * cm` |
| Beampipe / beam-stop / coatings / walls | every entry returned in `Beampipe_output` | `10.0 * cm` |
| TPC | every entry returned in `TPC_output` | `10.0 * cm` |
| Scintillator | every entry returned in `Scintillator_output` | `10.0 * cm` |
| Lead glass / PMT | every entry returned in `LeadGlass_output` | `10.0 * cm` |

No world-volume user limit was added, matching the lane constraint not to install
a global world limit that could override physics-list behavior.

## Existing-limit preservation

For each volume, the patch first reads the existing `G4UserLimits` pointer.  If
one exists, it mutates only the maximum-step field; if none exists, it creates a
new `G4UserLimits` object for that volume before setting the maximum step.
Therefore the TPC, scintillator, and lead-glass minimum kinetic-energy and
maximum-time guards documented by the prior audit are not removed or replaced.

## Static verification

```text
$ grep -c "SetMaxAllowedStep" NNBAR_Detector/src/core/DetectorConstruction.cc
6
```

The required grep count is at least 6, one source assignment per sensitive
volume class above.

Additional local static checks:

```text
$ git -C NNBAR_Detector diff --check -- src/core/DetectorConstruction.cc
DIFF_CHECK_OK

$ wc -l NNBAR_Detector/src/core/DetectorConstruction.cc
441 NNBAR_Detector/src/core/DetectorConstruction.cc
```

No CMake, compiler, SLURM, macro, or large simulation command was run locally.
