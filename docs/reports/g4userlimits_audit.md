# G4UserLimits sensitive-volume coverage audit

Date: 2026-05-12  
Lane: worker-2 lane-swap from `codex-tasks/sim/worker-2.txt`  
Scope: audit only; no C++ source, macro, SLURM, or data-output changes.

## Executive result

The requested finite-max-step gate is **not satisfied** in the active detector
source.  TPC, LeadGlass, and Scintillator have `G4UserLimits` objects with
finite minimum kinetic-energy and maximum track-time guards, but none calls
`SetMaxAllowedStep(...)` or uses a non-default constructor argument for the
maximum step.  Carbon, Silicon, and Beampipe sensitive volumes have no
`G4UserLimits` assignment at all.

The Geant4 header in the LUNARC environment confirms the default constructor
argument for the maximum step is `DBL_MAX`; therefore a bare `new G4UserLimits()`
does not satisfy a finite max-step requirement.

No code change was made in this compact iteration.  The recommended follow-up
is a small C++ patch that adds explicit finite `SetMaxAllowedStep(...)` values
for every sensitive logical volume listed below, plus a static grep/test gate
that fails if any sensitive output list lacks both `SetUserLimits` and a finite
max-step assignment.

## Evidence commands

Authoritative active checkout checked on LUNARC:

```text
cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim
REMOTE_HEAD c95b172
REMOTE_BRANCH lane/pi0-mono-sample-staging
```

Local mirror uses the nested source prefix `NNBAR_Detector/`; the active LUNARC
checkout uses the same files without that prefix.  The relevant greps matched in
both places.

```text
# User-limit grep, active LUNARC checkout
src/detector/LeadGlass_geometry.cc:398:  G4UserLimits* lgLimits = new G4UserLimits();
src/detector/LeadGlass_geometry.cc:399:  lgLimits->SetUserMinEkine(1.0 * keV);
src/detector/LeadGlass_geometry.cc:400:  lgLimits->SetUserMaxTime(100.0 * CLHEP::microsecond);
src/detector/LeadGlass_geometry.cc:402:    lv->SetUserLimits(lgLimits);
src/detector/Scintillator_geometry.cc:582:  G4UserLimits* scintLimits = new G4UserLimits();
src/detector/Scintillator_geometry.cc:583:  scintLimits->SetUserMinEkine(1.0 * keV);
src/detector/Scintillator_geometry.cc:584:  scintLimits->SetUserMaxTime(100.0 * CLHEP::microsecond);
src/detector/Scintillator_geometry.cc:586:    lv->SetUserLimits(scintLimits);
src/detector/TPC_geometry.cc:218:    G4UserLimits* tpcWallLimits = new G4UserLimits();
src/detector/TPC_geometry.cc:219:    tpcWallLimits->SetUserMinEkine(1.0*keV);
src/detector/TPC_geometry.cc:220:    tpcWallLimits->SetUserMaxTime(10.0*ms);
src/detector/TPC_geometry.cc:221:    TPCLV_1->SetUserLimits(tpcWallLimits);
src/detector/TPC_geometry.cc:222:    TPCLV_2->SetUserLimits(tpcWallLimits);
src/detector/TPC_geometry.cc:243:    G4UserLimits* tpcLimits = new G4UserLimits();
src/detector/TPC_geometry.cc:244:    tpcLimits->SetUserMinEkine(1.0*keV);
src/detector/TPC_geometry.cc:245:    tpcLimits->SetUserMaxTime(10.0*ms);
src/detector/TPC_geometry.cc:246:    TPC_1_layer_LV->SetUserLimits(tpcLimits);
src/detector/TPC_geometry.cc:247:    TPC_2_layer_LV->SetUserLimits(tpcLimits);
```

```text
# Global max-step grep, active and local checkouts
SetMaxAllowedStep: no matches in src/include or NNBAR_Detector/src/include.
```

```text
# Geant4 API default in the LUNARC environment
G4UserLimits.hh:55:  G4UserLimits(G4double ustepMax = DBL_MAX, ...)
G4UserLimits.hh:72:  virtual void SetMaxAllowedStep(G4double ustepMax);
```

Sensitive detector wiring in the active checkout:

```text
src/core/DetectorConstruction.cc:312:  SetSensitiveDetector("CarbonLV", Carbon_Detector);
src/core/DetectorConstruction.cc:317:  for (size_t i=0;i<Silicon_output.size();i++){Silicon_output[i] -> SetSensitiveDetector(siliconDetector);}
src/core/DetectorConstruction.cc:322:  for (size_t i=0;i<Beampipe_output.size();i++){Beampipe_output[i] -> SetSensitiveDetector(tubeDetector);}
src/core/DetectorConstruction.cc:327:  for (size_t i=0;i<TPC_output.size();i++){TPC_output[i] -> SetSensitiveDetector(TPCDetector);}
src/core/DetectorConstruction.cc:332:  for (size_t i=0;i<Scintillator_output.size();i++){Scintillator_output[i] -> SetSensitiveDetector(scintDetector);}
src/core/DetectorConstruction.cc:337:  LeadGlass_output[0] -> SetSensitiveDetector(LeadGlassDetector);
src/core/DetectorConstruction.cc:342:  LeadGlass_output[1] -> SetSensitiveDetector(PMTDetector);
```

Returned sensitive output lists in the active checkout:

```text
src/detector/TPC_geometry.cc:198:    TPC_Construction_list.push_back(TPCLV_1);
src/detector/TPC_geometry.cc:199:    TPC_Construction_list.push_back(TPCLV_2);
src/detector/TPC_geometry.cc:200:    TPC_Construction_list.push_back(TPC_1_layer_LV);
src/detector/TPC_geometry.cc:201:    TPC_Construction_list.push_back(TPC_2_layer_LV);
src/detector/Silicon_geometry.cc:136:    Silicon_Construction_list.push_back(siliconLV_1);
src/detector/Silicon_geometry.cc:137:    Silicon_Construction_list.push_back(siliconLV_2);
src/detector/beampipe_geometry.cc:496:  Beampipe_Construction_list.push_back(Beampipe_1_LV);
src/detector/beampipe_geometry.cc:497:  Beampipe_Construction_list.push_back(Beampipe_2_LV);
src/detector/beampipe_geometry.cc:498:  Beampipe_Construction_list.push_back(Beampipe_3_LV);
src/detector/beampipe_geometry.cc:499:  Beampipe_Construction_list.push_back(Beampipe_4_LV);
src/detector/beampipe_geometry.cc:500:  Beampipe_Construction_list.push_back(Beampipe_5_LV);
src/detector/beampipe_geometry.cc:501:  Beampipe_Construction_list.push_back(Beampipe_6_LV);
src/detector/beampipe_geometry.cc:502:  Beampipe_Construction_list.push_back(Beampipe_7_LV);
src/detector/beampipe_geometry.cc:503:  Beampipe_Construction_list.push_back(Beampipe_8_LV);
src/detector/beampipe_geometry.cc:504:  Beampipe_Construction_list.push_back(Beampipe_3_coating_LV);
src/detector/beampipe_geometry.cc:505:  Beampipe_Construction_list.push_back(Beampipe_7_coating_LV);
src/detector/beampipe_geometry.cc:506:  Beampipe_Construction_list.push_back(Beampipe_6_coating_LV);
src/detector/beampipe_geometry.cc:507:  Beampipe_Construction_list.push_back(BeamStop_LV);
src/detector/beampipe_geometry.cc:508:  Beampipe_Construction_list.push_back(Beampipe_1_wall_LV);
src/detector/beampipe_geometry.cc:509:  Beampipe_Construction_list.push_back(Beampipe_2_wall_LV);
src/detector/beampipe_geometry.cc:510:  Beampipe_Construction_list.push_back(Beampipe_4_wall_LV);
src/detector/beampipe_geometry.cc:511:  Beampipe_Construction_list.push_back(Beampipe_5_wall_LV);
src/detector/beampipe_geometry.cc:512:  Beampipe_Construction_list.push_back(Beampipe_8_wall_LV);
src/detector/beampipe_geometry.cc:513:  Beampipe_Construction_list.push_back(Beampipe_1_coating_LV);
src/detector/beampipe_geometry.cc:514:  Beampipe_Construction_list.push_back(Beampipe_2_coating_LV);
src/detector/beampipe_geometry.cc:515:  Beampipe_Construction_list.push_back(Beampipe_4_coating_LV);
src/detector/beampipe_geometry.cc:516:  Beampipe_Construction_list.push_back(Beampipe_5_coating_LV);
src/detector/beampipe_geometry.cc:517:  Beampipe_Construction_list.push_back(Beampipe_8_coating_LV);
src/detector/LeadGlass_geometry.cc:376:  LeadGlass_Construction_list.push_back(leadglassLV);
src/detector/LeadGlass_geometry.cc:377:  LeadGlass_Construction_list.push_back(PMTLV);
src/detector/Scintillator_geometry.cc:575:  Scintillator_output.push_back(scint_barH_LV);
src/detector/Scintillator_geometry.cc:576:  Scintillator_output.push_back(scint_barV_LV);
src/detector/Scintillator_geometry.cc:577:  Scintillator_output.push_back(scint_bar_fb1H_LV);
src/detector/Scintillator_geometry.cc:578:  Scintillator_output.push_back(scint_bar_fb1V_LV);
```

## Requested sensitive-volume matrix

| Subsystem | Sensitive logical volume(s) | Current limit state | Finite max-step state | Recommended fix |
| --- | --- | --- | --- | --- |
| TPC wall | `TPCLV_1`, `TPCLV_2` | `G4UserLimits` present; min KE 1 keV; max time 10 ms | **MISSING**; no `SetMaxAllowedStep` | Add `tpcWallLimits->SetMaxAllowedStep(<finite>)`; choose value by geometry-preserving closure test and document the chosen number. |
| TPC gas | `TPC_1_layer_LV`, `TPC_2_layer_LV` | `G4UserLimits` present; min KE 1 keV; max time 10 ms | **MISSING**; no `SetMaxAllowedStep` | Add `tpcLimits->SetMaxAllowedStep(<finite>)`; verify TPC hit counts and energy deposition are stable versus a finer reference. |
| Carbon foil | `CarbonLV` | **MISSING**; no `G4UserLimits` found near carbon construction or sensitive-detector binding | **MISSING** | Create a carbon-specific `G4UserLimits`, assign it to `carbonLV`, and set a finite max step derived from the foil thickness / vertex-closure tolerance. |
| Silicon | `siliconLV_1`, `siliconLV_2` | **MISSING**; no `G4UserLimits` in `Silicon_geometry.cc` | **MISSING** | Add a silicon-specific `G4UserLimits` before returning `Silicon_Construction_list`; set finite max step and verify SiliconSD hit multiplicity/energy stability. |
| Beampipe wrappers | `Beampipe_1_LV`, `Beampipe_2_LV`, `Beampipe_3_LV`, `Beampipe_4_LV`, `Beampipe_5_LV`, `Beampipe_6_LV`, `Beampipe_7_LV`, `Beampipe_8_LV`, `BeamStop_LV` | **MISSING**; no `G4UserLimits` in `beampipe_geometry.cc` | **MISSING** | Add a shared or per-material beampipe `G4UserLimits` to every returned TubeSD volume; include finite max step and keep existing production cuts unchanged. |
| Beampipe walls | `Beampipe_1_wall_LV`, `Beampipe_2_wall_LV`, `Beampipe_4_wall_LV`, `Beampipe_5_wall_LV`, `Beampipe_8_wall_LV` | **MISSING** | **MISSING** | Same beampipe fix; include all wall volumes because the detector-construction loop assigns TubeSD to the full returned list. |
| Beampipe coatings | `Beampipe_1_coating_LV`, `Beampipe_2_coating_LV`, `Beampipe_3_coating_LV`, `Beampipe_4_coating_LV`, `Beampipe_5_coating_LV`, `Beampipe_6_coating_LV`, `Beampipe_7_coating_LV`, `Beampipe_8_coating_LV` | **MISSING** | **MISSING** | Same beampipe fix; B4C/coating regions should get an explicit finite max step or be excluded by documented detector-policy decision. |

## RC-2 context volumes

| Subsystem | Sensitive logical volume(s) | Current limit state | Finite max-step state | Recommended fix |
| --- | --- | --- | --- | --- |
| LeadGlass | `leadglassLV`, `PMTLV` | `G4UserLimits` present; min KE 1 keV; max time 100 µs | **MISSING**; no `SetMaxAllowedStep` | Extend the RC-2 guard with an explicit finite max step; verify lead-glass energy response against the RC-2 smoke sample. |
| Scintillator | `scint_barH_LV`, `scint_barV_LV`, `scint_bar_fb1H_LV`, `scint_bar_fb1V_LV` | `G4UserLimits` present; min KE 1 keV; max time 100 µs | **MISSING**; no `SetMaxAllowedStep` | Extend the RC-2 guard with an explicit finite max step; verify scintillator hit timing and energy sums against the RC-2 smoke sample. |

## Follow-up gate recommendation

Add a lightweight verifier such as `scripts/verify_g4_user_limits.py` that parses
these construction files and fails unless:

1. every sensitive output-list logical volume has a `SetUserLimits` assignment;
2. every assigned `G4UserLimits` object has either a finite constructor first
   argument or a `SetMaxAllowedStep(...)` call;
3. the verifier is run in the sim lane before any production cosmic recovery is
   promoted from RUNNING/BLOCKED to DONE.

Until that patch lands, report finite max-step coverage as **OPEN** for all
requested sensitive volumes.
