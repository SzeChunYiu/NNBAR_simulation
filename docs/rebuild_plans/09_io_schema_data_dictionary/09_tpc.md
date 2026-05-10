---
id: 09_tpc
title: IO schema — TPC_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§8"
---

## 8. TPC table — full column listing (canonical example)

The TPCSD writer (plan 07 §6.1) produces one row per recorded step
(first/last in volume only), then `NNbarRun::RecordEvent` filters out
zero-electron rows and ionisation-process secondaries. Positions and
track length are persisted in **cm**.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:281`; consumed_by=reconstruction and validation joins |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier | B | §3.4 | produced_by=`TPCSD.cc:56,123` → `NNbarRun.cc:254,281`; consumed_by=sparse diagnostic fallback only |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track id | B | §3.4 | produced_by=`TPCSD.cc:57,124` → `NNbarRun.cc:255,281`; consumed_by=diagnostic ancestry only |
| `Name` | string | dimensionless | particle PDG name | B | §3.5 | produced_by=`TPCSD.cc:53-55,122` → `NNbarRun.cc:256,281`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name, or `primary` | B | §3.5 | produced_by=`TPCSD.cc:58-59,125` → `NNbarRun.cc:257,282`; consumed_by=diagnostic process studies |
| `Step_info` | int32 | dimensionless | provenance flag (`1` first from outside, `0` otherwise, `999` origin inside TPC) | A | §3.7 | produced_by=`TPCSD.cc:145-150` → `NNbarRun.cc:258,282`; consumed_by=TPC hit filtering diagnostics |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.5 | produced_by=`TPCSD.cc:85,126` → `NNbarRun.cc:259,282`; consumed_by=truth-leak audit and diagnostics |
| `Current_Vol` | string | dimensionless | current TPC physical-volume name | A | §3.7 | produced_by=`TPCSD.cc:86,127` → `NNbarRun.cc:260,282`; consumed_by=geometry diagnostics |
| `Module_ID` | int32 | dimensionless | TPC module index from `replicaNumber(1)` | A | §3.7 | produced_by=`TPCSD.cc:88-91,139` → `NNbarRun.cc:274,283`; consumed_by=track/hit geometry |
| `Layer_ID` | int32 | dimensionless | TPC layer index from `replicaNumber(0)` | A | §3.7 | produced_by=`TPCSD.cc:88-91,138` → `NNbarRun.cc:275,283`; consumed_by=track/hit geometry |
| `x`, `y`, `z` | float64 | cm | midpoint of pre/post step in the TPC | A | §3.1 | produced_by=`TPCSD.cc:64-71,128-130` → `NNbarRun.cc:262-284`; consumed_by=track and vertex reconstruction |
| `px`, `py`, `pz` | float64 | dimensionless | pre-step momentum unit-vector components | A | §3.3 | produced_by=`TPCSD.cc:84,133-135` → `NNbarRun.cc:265-285`; consumed_by=track-direction reconstruction |
| `t` | float64 | ns | global track time at the TPC hit | A | §3.2 | produced_by=`TPCSD.cc:74-75,131` → `NNbarRun.cc:268,286`; consumed_by=timing diagnostics |
| `KE` | float64 | MeV | mean of pre/post-step kinetic energy | A | §3.3 | produced_by=`TPCSD.cc:77-82,132` → `NNbarRun.cc:269,286`; consumed_by=energy-spectrum diagnostics |
| `eDep` | float64 | MeV | step total energy deposit in the TPC | A | §3.3 | produced_by=`TPCSD.cc:61-62,136` → `NNbarRun.cc:270,286`; consumed_by=dE/dx reconstruction |
| `trackl` | float64 | cm | Geant4 step length for the TPC hit | A | §3.3 | produced_by=`TPCSD.cc:72,143` → `NNbarRun.cc:271,286`; consumed_by=track-length and dE/dx reconstruction |
| `electrons` | float64 | electrons | Poisson electron count from `eDep / 23.6 eV` | A+C | §3.3 + §3.8 | produced_by=`TPCSD.cc:94-101,142` → `NNbarRun.cc:276,286`; 23.6 eV W-value is Class C and audited by plan 17 |

`TPC_output_*.parquet` is loaded by:
- `nnbar_reconstruction.cli.summarize` → `reconstruct_run`
- `nnbar_reconstruction.cli.scan-pid` → `reconstruct_charged_objects`
- `nnbar_reconstruction.cli.validate-reco`
- `pi0_study.evaluate_pi0_mass_ladder`
- `charged_study.evaluate_charged_stress`
- `pi0_fake_study.evaluate_pi0_fake_background`

Truth columns currently consumed by the reconstruction decision path
(flagged for migration per plan 08 §3.7): `Name`, `Track_ID`
(sparse-table fallback only), `Origin` (diagnostic).
