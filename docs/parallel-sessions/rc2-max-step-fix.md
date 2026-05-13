# RC-2: G4UserLimits maximum-step gate for cosmic stall fix

**Goal:** Every logical volume in the NNBAR detector must have a finite
`SetMaxAllowedStep(...)` guard so no particle can take unlimited tiny steps.

**Root cause:** High-energy cosmic protons create hadronic showers with slow
secondaries (neutrons, nuclear fragments). Without a max-step limit these
particles accumulate millions of steps → event never finishes. RC-1 (1 ms
radioactive-decay threshold) does NOT help because the stall is in the
tracking step loop, not in decay sampling.

**Evidence:** `docs/reports/g4userlimits_audit.md` (2026-05-12) confirms that
TPC/LeadGlass/Scintillator have `G4UserLimits` objects with no
`SetMaxAllowedStep` call; Carbon/Silicon/Beampipe have no `G4UserLimits` at
all.

**Thread-probe confirmation (jobs 3047491_4/5):** both 1-thread and 4-thread
modes stall at events 238 / 491 respectively → stall is physics-based, not a
deadlock.

## Required change — DetectorConstruction.cc

In `src/core/DetectorConstruction.cc` (LUNARC:
`/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/src/core/DetectorConstruction.cc`),
for EVERY logical volume (LV) that has sensitive detector assignment, add:

```cpp
lv->SetUserLimits(new G4UserLimits(
    10.0 * cm,       // max step
    DBL_MAX,         // max track
    DBL_MAX,         // max time
    0.0,             // min KE (keep existing or 0)
    0.0              // min range (keep existing or 0)
));
```

Or, if a volume already has a `G4UserLimits` object:

```cpp
auto* ul = new G4UserLimits();
ul->SetMaxAllowedStep(10.0 * cm);
lv->SetUserLimits(ul);
```

**Max step value:** 10 cm is conservative for shower tracking. Physics tracks
with genuine long straight paths (muons, high-E electrons) are unaffected
because their steps naturally stay below 10 cm in the magnetic field. If 10 cm
is too aggressive for track purity, 50 cm is acceptable; the goal is to prevent
~1 mm steps looping forever, NOT to kill normally-tracked particles.

## Volumes to cover

From the audit, minimum required volumes (by logical-volume name pattern):
- `scintillatorLV` / any scintillator barrel LV
- `leadGlassLV` / any lead-glass block LV
- `tpcLV` / TPC drift region LV
- `carbonFoilLV` / foil LV
- `siliconLV` / silicon tracker LV
- `beampipeLV` / beam pipe LV

Plus any "world" / envelope LV so external particles are capped too.

## Verification test

After the patch, add a grep assertion in the spec:

```bash
grep -c "SetMaxAllowedStep" src/core/DetectorConstruction.cc
```

Must return ≥ 6 (one per volume class). Fewer → assert failure, do not commit.

## File constraints

- **Edit only:** `src/core/DetectorConstruction.cc`
- Do NOT edit any .slurm / .sbatch / .mac files
- Do NOT add global `G4UserLimits` in the world volume that would override
  physics list limits
- Do NOT remove the existing KE/time guards already in TPC/LG/Scintillator

## Output on completion

Write `docs/reports/rc2_max_step_patch.md` with:
- List of volumes patched and step values used
- grep count confirming ≥ 6 `SetMaxAllowedStep` calls
- Confirmation no existing limits were removed
