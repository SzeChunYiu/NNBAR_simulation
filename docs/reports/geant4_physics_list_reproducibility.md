# Geant4 physics-list reproducibility audit

Date: 2026-05-11  
Lane: worker-0 / `geant4-physics-list-audit`  
Scope: documentation-only audit; no new simulation was run.

## Evidence commands recorded this iteration

File existence and line counts:

```text
$ rtk proxy ls NNBAR_Detector/src/PhysicsList.cc NNBAR_Detector/src/core/PhysicsList.cc docs/rebuild_plans/12_physics_list_audit.md docs/rebuild_plans/45_systematics_taxonomy.md CODING_STANDARDS.md
CODING_STANDARDS.md
NNBAR_Detector/src/PhysicsList.cc
NNBAR_Detector/src/core/PhysicsList.cc
docs/rebuild_plans/12_physics_list_audit.md
docs/rebuild_plans/45_systematics_taxonomy.md

$ rtk proxy wc -l NNBAR_Detector/src/PhysicsList.cc NNBAR_Detector/src/core/PhysicsList.cc docs/rebuild_plans/12_physics_list_audit.md docs/rebuild_plans/45_systematics_taxonomy.md CODING_STANDARDS.md
172 NNBAR_Detector/src/PhysicsList.cc
234 NNBAR_Detector/src/core/PhysicsList.cc
440 docs/rebuild_plans/12_physics_list_audit.md
446 docs/rebuild_plans/45_systematics_taxonomy.md
350 CODING_STANDARDS.md
```

Source-list check:

```text
$ rtk proxy ls NNBAR_Detector/src/physics/PhysicsList.cc
ls: NNBAR_Detector/src/physics/PhysicsList.cc: No such file or directory

$ rtk proxy grep -n "file(GLOB SOURCES\|src/core/\*.cc\|file(GLOB PHYSICS_SOURCES\|src/physics/PhysicsList.cc\|list(APPEND SOURCES" NNBAR_Detector/CMakeLists.txt
532:file(GLOB SOURCES
533:    ${PROJECT_SOURCE_DIR}/src/core/*.cc
545:file(GLOB PHYSICS_SOURCES ${PROJECT_SOURCE_DIR}/src/physics/PhysicsList.cc)
546:list(APPEND SOURCES ${PHYSICS_SOURCES})
```

`NNBAR_Detector/src/physics/PhysicsList.cc` does not exist in this checkout;
therefore the CMake source glob makes `NNBAR_Detector/src/core/PhysicsList.cc`
the authoritative compiled physics-list source. The root-level
`NNBAR_Detector/src/PhysicsList.cc` is kept below as a legacy duplicate check
because the rebuild plan still names it.

## Observed constructor registrations

Authoritative source, `NNBAR_Detector/src/core/PhysicsList.cc`:

```text
$ rtk proxy grep -n "RegisterPhysics" NNBAR_Detector/src/core/PhysicsList.cc
75:    RegisterPhysics(new G4EmStandardPhysics());
78:    RegisterPhysics(new G4EmStandardPhysics_option4());
81:  RegisterPhysics(new G4EmStandardPhysics_option4());
83:  //RegisterPhysics(new G4EmExtraPhysics());
84:  RegisterPhysics(new G4DecayPhysics());
85:  RegisterPhysics(new G4HadronElasticPhysics());
86:  RegisterPhysics(new G4HadronPhysicsFTFP_BERT()); //_HP will slow down a lot
87:  RegisterPhysics(new G4StoppingPhysics() );
88:  RegisterPhysics(new G4IonPhysics());
89:  RegisterPhysics(new G4NeutronTrackingCut());
90:  RegisterPhysics(new G4RadioactiveDecayPhysics());
92:  RegisterPhysics(new G4StepLimiterPhysics());
110:    RegisterPhysics(opticalPhysics);
123:  RegisterPhysics(opticalPhysics);

$ rtk proxy grep -n "G4HadronPhysicsFTFP_BERT" NNBAR_Detector/src/core/PhysicsList.cc
46:#include "G4HadronPhysicsFTFP_BERT.hh"
47:#include "G4HadronPhysicsFTFP_BERT_HP.hh"
86:  RegisterPhysics(new G4HadronPhysicsFTFP_BERT()); //_HP will slow down a lot
```

Legacy duplicate, `NNBAR_Detector/src/PhysicsList.cc`:

```text
$ rtk proxy grep -n "RegisterPhysics" NNBAR_Detector/src/PhysicsList.cc
59:  RegisterPhysics(new G4EmStandardPhysics_option4());
60:  //RegisterPhysics(new G4EmExtraPhysics());
61:  RegisterPhysics(new G4DecayPhysics());
62:  RegisterPhysics(new G4HadronElasticPhysics());
63:  RegisterPhysics(new G4HadronPhysicsFTFP_BERT()); //_HP will slow down a lot
64:  RegisterPhysics(new G4StoppingPhysics() );
65:  RegisterPhysics(new G4IonPhysics());
66:  RegisterPhysics(new G4NeutronTrackingCut());
67:  RegisterPhysics(new G4RadioactiveDecayPhysics());
79:  RegisterPhysics(opticalPhysics);

$ rtk proxy grep -n "G4HadronPhysicsFTFP_BERT" NNBAR_Detector/src/PhysicsList.cc
41:#include "G4HadronPhysicsFTFP_BERT.hh"
42:#include "G4HadronPhysicsFTFP_BERT_HP.hh"
63:  RegisterPhysics(new G4HadronPhysicsFTFP_BERT()); //_HP will slow down a lot
```

Observed current contract:

| Area | Source-observed behavior | Reproducibility consequence |
|---|---|---|
| EM physics | CPU branch registers `G4EmStandardPhysics_option4`; Celeritas-enabled branch can register base `G4EmStandardPhysics`. | CPU nominal matches the precision-EM expectation. Celeritas-on samples must carry an EM-equivalence validation tag before photon/material-response claims. |
| Hadronic inelastic | Both checked files include `_HP` but instantiate `G4HadronPhysicsFTFP_BERT()`, not `_HP`. | Current source is non-HP. Cosmic-neutron and beam-neutron background rows cannot be final-rate evidence until an HP build/tag is validated. |
| Elastic, decay, stopping, ion, neutron cut, radioactive decay | All are registered in the authoritative source. | Matches plan 12 constructor coverage, but neutron-tracking cut values remain `OPEN:` in plan 12. |
| Step limiter | Authoritative `src/core/PhysicsList.cc` registers `G4StepLimiterPhysics`; root duplicate does not. | Plan 12's root-file statement is stale for the compiled source and should be updated in a later plan-editing task. |
| Optical physics | Authoritative source registers optical physics only under the non-Celeritas/no-fast-mode branches shown by the preprocessor blocks. | Optical-on/off must be a recorded build/runtime tag; fast-mode rows are not optical-yield closure. |

## Thesis and rebuild-plan expectation

Plan 12 expects precision EM (`G4EmStandardPhysics_option4`) for CPU Geant4
EM response, and explicitly separates non-HP and HP hadronic tags. Plan 12 §3
names `nominal` as the current configuration and `nominal_hp` as the same list
with `G4HadronPhysicsFTFP_BERT_HP`. Plan 45 row N4 defines the physics-list
systematic as a discrete envelope over `nominal_hp`, `qgsp_bert`, `qgsp_bic`,
and `em_opt0`.

The checked source therefore differs from thesis-era/final-background
expectations in two ways:

1. The active hadronic constructor is non-HP, while final cosmic-neutron and
   beam-neutron background rows require an HP-tagged build before citation.
2. The compiled source has a Celeritas branch that can use base
   `G4EmStandardPhysics`; any Celeritas-on sample needs paired CPU/Celeritas EM
   closure before photon conversion, calorimeter response, or material-budget
   claims are promoted.

## Geant4 version evidence

Checked-in CMake does not pin a literal Geant4 version; it calls
`find_package(Geant4 REQUIRED ...)` and reports `${Geant4_VERSION}` at configure
time. Guarded LUNARC evidence from this iteration found:

```text
$ rtk proxy ssh lunarc ... grep -n "Geant4\|GEANT4" build/CMakeCache.txt | head -80
271://The directory containing a CMake configuration file for Geant4.
272:Geant4_DIR:PATH=/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/install/geant4-11.2.2/lib/cmake/Geant4
563:FIND_PACKAGE_MESSAGE_DETAILS_Geant4:INTERNAL=[/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/install/geant4-11.2.2/lib/cmake/Geant4/Geant4Config.cmake][v11.2.2()]

$ rtk proxy ssh lunarc ... /projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/bin/geant4-config --version
11.2.2

$ rtk proxy ssh lunarc ... grep "Geant4 version Name" build/mcpl_missing_input.log
Geant4 version Name: geant4-11-02-patch-02 [MT]   (21-June-2024)
```

`OPEN:` the remote `build/CMakeCache.txt` still records a Mac-local
`Geant4_DIR` path even though the LUNARC conda `geant4-config` reports 11.2.2.
Before any final thesis row cites a production build ID, record the exact
configure command, `Geant4_DIR`, Geant4 data directories, and source commit in a
plan-03 registry entry.

## Required validation tags

| Tag | Physics-list content | Required before citation | Downstream observables at risk |
|---|---|---|---|
| `nominal_non_hp` | Source-observed CPU list: `G4EmStandardPhysics_option4` plus `G4HadronPhysicsFTFP_BERT` without HP. | Signal legacy-comparability rows only; not final neutron-background baseline. | Prompt hadronic multiplicity, signal visible energy, material response from non-HP secondary transport. |
| `nominal_hp` | Same intended list but with `G4HadronPhysicsFTFP_BERT_HP`. | Required for cosmic-neutron and beam-neutron background-rate rows before final citation. | Neutron/background rates, capture-gamma tails, delayed deposits, systematics row N4. |
| `celeritas_em` | Authoritative source branch using base `G4EmStandardPhysics` when Celeritas is enabled. | Paired CPU/Celeritas closure with identical primaries/seeds. | Photon conversion, lead-glass/scintillator response, photon/material-budget response. |
| `qgsp_bert` | Plan-12/45 discrete physics-list endpoint. | Plan-45 N4 envelope measurement and plan-47 ledger row. | Hadronic multiplicity and background-shape envelope. |
| `qgsp_bic` | Plan-12/45 alternative cascade endpoint. | Plan-45 N4 envelope measurement and plan-47 ledger row. | Secondary-interaction and neutron-transport envelope. |

## Conclusions for current work

- The checked-out source currently supports a documented `nominal_non_hp` tag;
  it does not yet prove a validated `nominal_hp` production tag.
- Any final cosmic or beam-neutron background number needs the `nominal_hp`
  validation tag or must carry an explicit `OPEN:`/missing-systematic flag.
- Photon/material-budget response is coupled to the EM branch and to Geant4
  11.2.2 data/configuration evidence; Celeritas-on outputs require paired EM
  closure before thesis citation.
- Plan 45 nuisance N4 remains the governing systematic row for physics-list
  variations, and should consume measured tag deltas rather than prose-only
  assumptions.
