# RC-2 maximum-step coverage check

Date: 2026-05-12  
Lane: worker-2 lane-swap from `codex-tasks/sim/worker-2.txt`  
Scope: audit only; no C++ source, macro, SLURM, or data-output changes.

## Executive result

The current nested `NNBAR_Detector` checkout satisfies the narrow
`SetMaxAllowedStep` grep gate in `docs/parallel-sessions/rc2-max-step-fix.md`:
`NNBAR_Detector/src/core/DetectorConstruction.cc` contains six
`SetMaxAllowedStep(cosmicMaxStep)` calls, one for each sensitive output class
named by the patch spec: carbon, silicon, beampipe, TPC, scintillator, and
lead-glass/PMT.

The spec is not fully self-consistent at the envelope boundary.  It asks for
"Plus any `world` / envelope LV" coverage, but its file constraints also say
"Do NOT add global `G4UserLimits` in the world volume".  The implemented patch
follows the prohibition: `worldLV` has no `SetUserLimits` call.  Passive
shielding/envelope-like logical volumes built after the RC-2 block are also not
covered by the six-call sensitive-volume patch.

## Evidence commands

```text
$ wc -l NNBAR_Detector/src/core/DetectorConstruction.cc docs/parallel-sessions/rc2-max-step-fix.md
441 NNBAR_Detector/src/core/DetectorConstruction.cc
 86 docs/parallel-sessions/rc2-max-step-fix.md
527 total

$ grep -c "SetMaxAllowedStep" NNBAR_Detector/src/core/DetectorConstruction.cc
6

$ grep -c "SetUserLimits" NNBAR_Detector/src/core/DetectorConstruction.cc
6
```

`NNBAR_Detector` is a nested checkout on `main`; its most recent
`DetectorConstruction.cc` commit is `c921c0a fix(cosmic): cap sensitive volume
step lengths`.

## Current `SetUserLimits` matrix

This table lists every logical-volume target currently assigned by a
`SetUserLimits` call found in `NNBAR_Detector/src/core/DetectorConstruction.cc`
plus pre-existing geometry helpers that create user limits before the core
RC-2 block mutates them.

| Source | Logical-volume target | Existing user-limit purpose | Has finite max step after current RC-2 patch? |
| --- | --- | --- | --- |
| `DetectorConstruction.cc` | `carbonLV` / `CarbonLV` | Creates `G4UserLimits` if absent. | **Yes**: `carbonLimits->SetMaxAllowedStep(cosmicMaxStep)` |
| `DetectorConstruction.cc` | every `Silicon_output` entry (`siliconLV_1`, `siliconLV_2`) | Creates `G4UserLimits` if absent. | **Yes**: `siliconLimits->SetMaxAllowedStep(cosmicMaxStep)` |
| `DetectorConstruction.cc` | every `Beampipe_output` entry (beampipe wrappers, walls, coatings, `BeamStop_LV`) | Creates `G4UserLimits` if absent. | **Yes**: `beampipeLimits->SetMaxAllowedStep(cosmicMaxStep)` |
| `TPC_geometry.cc` + `DetectorConstruction.cc` | `TPCLV_1`, `TPCLV_2` | TPC wall min kinetic energy and max time. | **Yes**: core loop preserves the existing object and sets max step. |
| `TPC_geometry.cc` + `DetectorConstruction.cc` | `TPC_1_layer_LV`, `TPC_2_layer_LV` | TPC gas min kinetic energy and max time. | **Yes**: core loop preserves the existing object and sets max step. |
| `Scintillator_geometry.cc` + `DetectorConstruction.cc` | `scint_barH_LV`, `scint_barV_LV`, `scint_bar_fb1H_LV`, `scint_bar_fb1V_LV` | Scintillator min kinetic energy and max time. | **Yes**: core loop preserves the existing object and sets max step. |
| `LeadGlass_geometry.cc` + `DetectorConstruction.cc` | `leadglassLV`, `PMTLV` | Lead-glass/PMT min kinetic energy and max time. | **Yes**: core loop preserves the existing object and sets max step. |

Sensitive-detector wiring in `DetectorConstruction.cc` matches the six covered
classes: `CarbonLV`, `Silicon_output`, `Beampipe_output`, `TPC_output`,
`Scintillator_output`, `LeadGlass_output[0]`, and `LeadGlass_output[1]`.

## Volumes the spec or patch misses

| Volume family | Evidence | Current max-step state | Why it matters |
| --- | --- | --- | --- |
| `worldLV` / `World` | Constructed in `DetectorConstruction.cc`; no `SetUserLimits` grep match. | **Not capped.** | The spec both requests world/envelope coverage and forbids a global world limit. This needs an explicit decision, not an implicit pass. |
| `CosmicShielding_output` | `DetectorConstruction.cc` constructs it after the RC-2 block; `Cosmic_Shielding_geometry.cc` returns lead/steel shield LVs. | **Not capped.** | Passive lead/steel shielding is envelope-like material but is outside the sensitive-volume output lists named by the patch. |
| `Beampipe_Shielding_output` | `DetectorConstruction.cc` constructs it after the RC-2 block; `beampipe_shielding_geometry.cc` creates shielding LVs but returns an empty output list in the inspected file. | **Not capped.** | Even adding a loop over `Beampipe_Shielding_output` would not cover the current LVs unless the construction list is populated. |

## Recommendation

Treat the six sensitive-volume max-step patch as covered, but keep the RC-2
envelope question **OPEN** until the planner chooses one of these policies:

1. explicitly scope RC-2 to sensitive detector output lists only and amend
   `docs/parallel-sessions/rc2-max-step-fix.md` to remove the contradictory
   world/envelope requirement; or
2. add a follow-up patch for passive shielding/envelope volumes without a
   global world-volume limit, including a verifier that proves
   `CosmicShielding_output` and beampipe shielding logical volumes are actually
   reachable from returned output lists.

No source changes were made in this audit.
