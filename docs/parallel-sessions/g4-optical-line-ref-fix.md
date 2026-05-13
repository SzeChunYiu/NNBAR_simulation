# Lane: g4-optical-line-ref-fix

## Goal

Audit and correct the Geant4 optical-photon bottleneck shard added in
`docs/reports/g4_bottleneck_database_optical_photons.md` so every source
snippet and line range is exact against Geant4 `v11.2.2`.

Planner precheck found the BD-geant4-053 LUT sampler line window exists, but
its snippet paraphrases the casts around `G4RandFlat::shootInt`; correct that
entry and scan BD-geant4-051--060 for any similar snippet/range drift.

## Writable files

- `docs/reports/g4_bottleneck_database_optical_photons.md`
- `docs/parallel-sessions/MASTER_PLAN.md` (row note only, if verification status changes)

Do not edit Geant4 source, NNBAR production code, benchmark code, or generated
data. Do not add new BD entries in this lane.

## Required checks

1. Re-read `docs/parallel-sessions.md`, `MASTER_PLAN.md`, and this spec.
2. Use `/tmp/geant4-v11.2.2` if present; otherwise check the LUNARC source tree
   named in the report after running the required `ssh -O check lunarc ...`
   socket guard.
3. For each BD-geant4-051--060 row, verify that the cited file exists, the cited
   line range is inside the file, and the `Current pattern` snippet text is an
   exact or explicitly marked paraphrase of text in that range.
4. Fix imprecise snippets rather than changing physics conclusions. Keep the
   report under 500 lines.

## Verification

```bash
rtk wc -l docs/reports/g4_bottleneck_database_optical_photons.md docs/parallel-sessions/MASTER_PLAN.md
rtk proxy python - <<'PY'
from pathlib import Path
checks = [
('/tmp/geant4-v11.2.2/source/processes/optical/src/G4OpBoundaryProcess.cc', 146, 205, ['fMaterial2->GetMaterialPropertiesTable', 'GetProperty(kGROUPVEL)', 'groupvel->Value']),
('/tmp/geant4-v11.2.2/source/processes/optical/src/G4OpBoundaryProcess.cc', 659, 720, ['G4RandGauss::shoot', 'std::sin(alpha)', 'rotateUz']),
('/tmp/geant4-v11.2.2/source/processes/optical/src/G4OpBoundaryProcess.cc', 820, 891, ['thetaIndex = (G4int)G4RandFlat::shootInt', 'phiIndex   = (G4int)G4RandFlat::shootInt', 'GetAngularDistributionValue']),
('/tmp/geant4-v11.2.2/source/processes/optical/src/G4OpBoundaryProcess.cc', 1076, 1348, ['fFinish == polished', 'sint2 >= 1.0', 'goto leap']),
('/tmp/geant4-v11.2.2/source/processes/optical/src/G4OpBoundaryProcess.cc', 1443, 1495, ['fRealRIndexMPV->Value', 'fImagRIndexMPV->Value', 'GetReflectivity']),
('/tmp/geant4-v11.2.2/source/processes/electromagnetic/xrays/src/G4Cerenkov.cc', 215, 388, ['Rindex->Value', 'new G4DynamicParticle', 'new G4Track']),
('/tmp/geant4-v11.2.2/source/processes/electromagnetic/xrays/src/G4Scintillation.cc', 347, 619, ['N_timeconstants', 'GetConstProperty', 'new G4DynamicParticle', 'new G4Track']),
('/tmp/geant4-v11.2.2/source/processes/electromagnetic/xrays/src/G4Scintillation.cc', 638, 651, ['tau2', 'G4Log', 'G4Exp']),
('/tmp/geant4-v11.2.2/source/processes/optical/src/G4OpWLS.cc', 89, 226, ['proposedSecondaries', 'GetEnergy', 'AddSecondary']),
('/tmp/geant4-v11.2.2/source/processes/optical/src/G4OpRayleigh.cc', 105, 185, ['cost', 'std::pow', 'cosTheta']),
]
for path, lo, hi, needles in checks:
    lines = Path(path).read_text(errors='replace').splitlines()
    window = '\n'.join(lines[lo-1:hi])
    missing = [needle for needle in needles if needle not in window]
    if missing:
        raise SystemExit(f'{Path(path).name}:{lo}-{hi} missing {missing}')
print('OPTICAL_LINE_REFS_OK')
PY
rtk bash scripts/validate-csup-queues.sh
```

## Stop condition

Commit only the corrected report/MASTER_PLAN row note. If the source tree is
missing or a cited line range cannot be verified, leave a precise `OPEN:` note
in the report and stop.
