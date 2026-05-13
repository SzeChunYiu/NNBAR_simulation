# RC-4: Add SetUserMinEkine to all under-protected volumes

## Root cause (traced 2026-05-12)

`run_cosmic_array.slurm` (job 3048056) stalls at proton bin5 event 2553 and
mu- bin5 event 381 — same events as the pre-RC-2 runs.

Investigation:

- RC-1 (radioactive decay threshold 1 ms): active, confirmed via log marker.
- RC-2 (SetMaxAllowedStep = 10 cm): applied to 6 sensitive volumes. NOT sufficient.

Root cause: hadronic recoil nuclei (Pb-208, C-12, Si-28, etc.) created by
50-200 GeV hadronic showers have kinetic energies of O(100 eV–100 keV). Their
range in dense material is O(1 nm–1 μm), far below the 10 cm maxStep. Therefore
RC-2 does NOT reduce step count for these particles — they still take thousands of
1-nm steps until range = 0.

The EXISTING `SetUserMinEkine(1.0 * keV)` on TPC, Scintillator, and LeadGlass
kills these recoil nuclei early. But Carbon, Silicon, Beampipe, and CosmicShielding
volumes have NO minEkine guard.

## Fix

In `NNBAR_Detector/src/core/DetectorConstruction.cc`, inside the RC-2 block:

### Carbon
```cpp
carbonLimits->SetMaxAllowedStep(cosmicMaxStep);
carbonLimits->SetUserMinEkine(1.0 * keV);   // RC-4: kill hadronic recoils
carbonLimits->SetUserMaxTime(10.0 * ms);    // RC-4: catch long-lived isotopes (backstop)
```

### Silicon (loop over Silicon_output)
```cpp
siliconLimits->SetMaxAllowedStep(cosmicMaxStep);
siliconLimits->SetUserMinEkine(1.0 * keV);
siliconLimits->SetUserMaxTime(10.0 * ms);
```

### Beampipe (loop over Beampipe_output)
```cpp
beampipeLimits->SetMaxAllowedStep(cosmicMaxStep);
beampipeLimits->SetUserMinEkine(1.0 * keV);
beampipeLimits->SetUserMaxTime(10.0 * ms);
```

### CosmicShielding (NEW — add after the beampipe block)
```cpp
for (auto* lv : CosmicShielding_output) {
    auto* shieldLimits = lv->GetUserLimits();
    if (shieldLimits == nullptr) {
        shieldLimits = new G4UserLimits();
        lv->SetUserLimits(shieldLimits);
    }
    shieldLimits->SetMaxAllowedStep(cosmicMaxStep);
    shieldLimits->SetUserMinEkine(1.0 * keV);
    shieldLimits->SetUserMaxTime(10.0 * ms);
}
```

Note: `CosmicShielding_output` is a member variable of type `std::vector<G4LogicalVolume*>`.
Check that this member exists in the class declaration (DetectorConstruction.hh).
If the type is different, adapt the loop accordingly.

## Physics safety

- Signal pi0 → γγ: photons at 75-140 MeV, EM shower electrons/positrons >> 1 MeV.
  A 1 keV threshold has ZERO effect on signal acceptance.
- Cosmic background: we are estimating rates, not doing precision calorimetry.
  1 keV is far below any observable ionization signal in TPC/scintillator.
- The `SetUserMaxTime(10 ms)` backstop matches the existing TPC walls setting;
  100 μs on LG/scintillator is already tighter.

## Verification

After implementing:
```bash
grep -c "SetUserMinEkine" NNBAR_Detector/src/core/DetectorConstruction.cc
```
Expected: ≥ 4 matches (Carbon, Silicon, Beampipe, CosmicShielding).

## After fix

1. Sync DetectorConstruction.cc to LUNARC
2. Build new binary (sbatch slurm/build_nnbar.slurm)
3. Re-submit ONLY tasks 5 (mu- bin5) and 26 (proton bin5):
   ```bash
   sbatch --exclude=cn018 --array=5,26 slurm/run_cosmic_array.slurm
   ```
4. Monitor: if event 2553 (proton) and event 381 (mu-) now progress past the stall
   point, RC-4 is confirmed.

## Expected result

Tasks 5 and 26 should complete within 12 hours with non-stub Parquet output.
The specific events 2553/381 should no longer stall because the recoil nuclei
are killed at 1 keV before they can accumulate millions of sub-nm steps.
