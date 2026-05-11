# Carbon foil radius and source-vertex alignment audit

Date: 2026-05-11  
Lane: worker-0 / `carbon-foil-alignment`  
Scope: read-only audit report; no production geometry, generator, or Python
configuration constants were changed.

## Executive finding

The current surfaces are not convention-aligned:

- Thesis-facing convention: target radius is 1 m, and the signal vertex
  distribution is a gravity-biased distribution on that foil.
- Geant4 detector geometry: the carbon target is constructed with a 30 cm
  radius and placed at the world origin.
- Particle-gun signal fallback: current signal primaries start at
  `(x, y, z) = (0, 0, 0)` rather than sampling the foil distribution.
- Python config: `target.radius` is 50 cm, with vertex projection cuts measured
  relative to the target plane.
- MCPL mode preserves source positions from the MCPL input, but this audit did
  not find a local frozen sample manifest proving the MCPL vertex distribution
  and gravity bias for the promoted signal sample.

Therefore vertex and photon-conversion validations must remain blocked from
promotion until a decision-log entry chooses the canonical target/source
convention and a sample-registry entry pins the source-vertex evidence.

## Verification preflight

Required files were verified before use with:

```text
rtk proxy bash -lc 'ls -l <path>; wc -l <path>'
```

Observed line counts included:

- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/3_HIBEAM_NNBAR_experiment.tex`: 382 lines.
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/6_Signal_Bkg_simulation.tex`: 160 lines.
- `NNBAR_Detector/src/core/DetectorConstruction.cc`: 383 lines.
- `NNBAR_Detector/src/core/PrimaryGeneratorAction.cc`: 631 lines, read-only.
- `NNBAR_Detector/src/PrimaryGeneratorAction.cc`: 198 lines.
- `nnbar_reconstruction/config/nnbar_geometry.yaml`: 191 lines.
- `docs/rebuild_plans/07_simulation_atomic_walkthrough.md`: 414 lines.
- `docs/rebuild_plans/03_dataset_registry.md`: 293 lines.
- `docs/governance/DECISION_LOG.md`: 512 lines, read-only.

Function line references below were checked with signature greps before this
report was written:

```text
grep -n "^G4VPhysicalVolume\* DetectorConstruction::DefineVolumes" NNBAR_Detector/src/core/DetectorConstruction.cc
grep -n "^void PrimaryGeneratorAction::GenerateSignalPrimaries" NNBAR_Detector/src/core/PrimaryGeneratorAction.cc
grep -n "^void PrimaryGeneratorAction::GeneratePrimaries" NNBAR_Detector/src/PrimaryGeneratorAction.cc
grep -n "^void ActionInitialization::Build" NNBAR_Detector/src/core/ActionInitialization.cc
grep -n "^void G4MCPLGenerator::GeneratePrimaries" NNBAR_Detector/src/generator/G4MCPLGenerator.cc
```

No new CLI command, bibliography key, production constant, or sample path is
introduced by this audit.

## Thesis convention

### Target radius

The Ch. 3 experiment schematic caption states that the annihilation target has
radius 1 m. Verification command:

```text
rtk proxy grep -n "annihilation target is of radius" "/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/3_HIBEAM_NNBAR_experiment.tex"
```

Evidence: `3_HIBEAM_NNBAR_experiment.tex:230`.

### Source-vertex distribution and gravity / optics evidence

Ch. 6 states that the 50,000-event annihilation sample is located on a carbon
foil with 1 m radius and that the vertices are biased toward negative `y` by
gravity. The figure caption separately labels the plotted distribution as a
signal event vertex distribution with gravitational bias. Verification command:

```text
rtk proxy grep -n "carbon foil with a 1m radius\|negative y side\|gravitational bias" "/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/6_Signal_Bkg_simulation.tex"
```

Evidence: `6_Signal_Bkg_simulation.tex:17` and
`6_Signal_Bkg_simulation.tex:22`.

Ch. 6 also ties the signal sample to neutron reflection/focusing and vacuum-tube
propagation, but does not encode the event-by-event vertex distribution in text.
Verification command:

```text
rtk proxy grep -n "reflection and focusing\|propagation through a vacuum tube" "/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/6_Signal_Bkg_simulation.tex"
```

Evidence: `6_Signal_Bkg_simulation.tex:10`.

OPEN: source-vertex distribution evidence — owner: worker-0 with dataset
registry maintainer; target resolution: 2026-05-18. Next check: locate the exact
promoted signal MCPL/Parquet/manifest, pin path and hash in the registry, and
show that the `x,y` vertex distribution has the 1 m foil support and negative-y
gravity bias before any validation is promoted.

## Geant4 geometry convention

`DetectorConstruction::DefineVolumes` constructs the carbon target in
`NNBAR_Detector/src/core/DetectorConstruction.cc:116-151`. The carbon radius is
30 cm, the `G4Cons` z half-length argument is `0.01*cm`, and the placement is at
`G4ThreeVector(0., 0., 0.)`. Verification command:

```text
rtk proxy grep -n "carbon_radius\|carbon_len\|G4Cons(\"CarbonS\"\|CarbonPV" NNBAR_Detector/src/core/DetectorConstruction.cc
```

Evidence:

- `DetectorConstruction.cc:141` — `carbon_radius = 30*cm` and
  `carbon_len = 0.01*cm`.
- `DetectorConstruction.cc:142` — `G4Cons` uses that radius and length.
- `DetectorConstruction.cc:151` — `CarbonPV` is placed at the origin.

The current build convention therefore does not match the thesis 1 m target
radius. It is also not matched to the Python `target.radius` value of 50 cm.

## Generator convention

### MCPL nominal path

When `MCPL_BUILD==1` and particle-gun mode is not forced,
`ActionInitialization::Build` uses `G4MCPLGenerator`; see
`NNBAR_Detector/src/core/ActionInitialization.cc:39-50`. The MCPL generator
reads positions from `m_p->position`, converts them from cm, and passes them to
the particle gun. Verification command:

```text
rtk proxy grep -n "G4ThreeVector pos(m_p->position\|pos \*= CLHEP::cm\|SetParticlePosition(pos)" NNBAR_Detector/src/generator/G4MCPLGenerator.cc
```

Evidence: `G4MCPLGenerator.cc:156-169` and `G4MCPLGenerator.cc:228-241`.

Interpretation: MCPL mode can preserve the thesis-like source-vertex
distribution if the MCPL input itself is correct, but this audit has not found a
local frozen manifest that proves the input distribution and gravity bias.

### Particle-gun signal fallback

`PrimaryGeneratorAction::GenerateSignalPrimaries` sets signal fallback positions
to the origin before calling `SetParticlePosition`; see
`NNBAR_Detector/src/core/PrimaryGeneratorAction.cc:290-343`. Verification
command:

```text
rtk proxy grep -n "Generate random position (at origin\|G4double x = 0.0\|G4double y = 0.0\|G4double z = 0.0\|SetParticlePosition(G4ThreeVector(x, y, z))" NNBAR_Detector/src/core/PrimaryGeneratorAction.cc
```

Evidence: `PrimaryGeneratorAction.cc:298-301` and
`PrimaryGeneratorAction.cc:342`.

The legacy top-level `NNBAR_Detector/src/PrimaryGeneratorAction.cc` contains a
similar origin fallback: it computes random `radius` and `angle_` but comments
out their use for `x` and `y`. Verification command:

```text
rtk proxy grep -n "double radius = G4UniformRand\|x = 0.;\|y = 0.;\|z = 0.\*m\|SetParticlePosition(G4ThreeVector(x, y, z))" NNBAR_Detector/src/PrimaryGeneratorAction.cc
```

Evidence: `PrimaryGeneratorAction.cc:148-153` and
`PrimaryGeneratorAction.cc:165` in the top-level legacy source file.

Impact: particle-gun signal studies do not exercise the 1 m foil radius or the
gravity-biased source distribution unless a separate macro/source path overrides
this behavior.

## Python reconstruction/config convention

`nnbar_reconstruction/config/nnbar_geometry.yaml` declares a target plane at
`z=0`, `target.radius = 50.0` cm, target thickness `0.01` cm, and a vertex
projection cut of 200 cm from target. Verification command:

```text
rtk proxy grep -n "z_position: 0.0\|radius: 50.0\|thickness: 0.01\|max_projection_distance" nnbar_reconstruction/config/nnbar_geometry.yaml
```

Evidence: `nnbar_geometry.yaml:88-90` and `nnbar_geometry.yaml:125`.

The Python-side radius differs from both the thesis 1 m convention and the
Geant4 30 cm convention. This matters for any reconstruction, validation, or
plotting code that interprets target acceptance, vertex residuals, or conversion
geometry using the YAML value.

## Decision-log and registry state

A decision-log search for target-radius/source-vertex convention terms produced
no matching DEC entry:

```text
rtk proxy grep -Ein "target radius|carbon target|carbon foil|foil radius|target convention|source[- ]vertex" docs/governance/DECISION_LOG.md || true
```

The existing nearby decision-log material is an alignment-scenario sigma policy,
not a target-radius convention. Evidence: `docs/governance/DECISION_LOG.md:267-289`.

Plan 03 provides the dataset-manifest schema and examples for signal foil
datasets, but this audit did not find a concrete local frozen registry manifest
that pins the promoted signal source-vertex distribution. Evidence:
`docs/rebuild_plans/03_dataset_registry.md:77-89` and
`docs/rebuild_plans/03_dataset_registry.md:132-136`.

## Mismatch table

| Surface | Verified convention | Source / command | Impact | Required follow-up |
|---|---:|---|---|---|
| Thesis target | 1 m radius | `grep -n "annihilation target is of radius" ...3_HIBEAM...tex` | Defines the physics/documentation convention for target support | DEC must decide whether production geometry/config should use 1 m or explicitly document a reduced-study target |
| Thesis signal sample | 50k vertices on 1 m foil, negative-y gravity bias | `grep -n "carbon foil with a 1m radius\|negative y side" ...6_Signal...tex` | Vertex and photon-conversion validations need this spatial prior | Registry must pin exact sample path/hash and verify vertex distribution |
| Geant4 carbon geometry | 30 cm radius, origin placement | `grep -n "carbon_radius\|G4Cons...\|CarbonPV" DetectorConstruction.cc` | Current geometry clips or changes acceptance relative to 1 m target | After DEC, align C++ geometry or tag all outputs as reduced-radius studies |
| MCPL generator | Uses positions from MCPL input | `grep -n "G4ThreeVector pos(m_p->position..." G4MCPLGenerator.cc` | Correctness depends on input MCPL provenance | Registry check must prove MCPL source distribution before promotion |
| Particle-gun fallback | Signal source at origin | `grep -n "Generate random position (at origin..." PrimaryGeneratorAction.cc` | Fallback cannot validate target-radius or gravity-bias effects | After DEC, either implement foil sampling or block fallback from thesis validations |
| Python config | `target.radius = 50.0` cm; vertex cut 200 cm | `grep -n "z_position...\|radius: 50.0..." nnbar_geometry.yaml` | Reconstruction/config convention disagrees with thesis and Geant4 | After DEC, align YAML and add regression/audit test |
| Decision log | No target-radius/source-vertex DEC found | `grep -Ein "target radius|carbon target|..." DECISION_LOG.md` | No approved methodology basis for silently changing constants | Add DEC before production code/config alignment |

## Blockers

OPEN: target-radius convention DEC — owner: Detector-mechanics POG + worker-0;
target resolution: 2026-05-18. Decide one canonical convention for promoted
signal, vertex, and photon-conversion validations: thesis 1 m radius, reduced
30 cm Geant4 target, 50 cm Python target, or explicitly separated study modes.

OPEN: source-vertex sample registry — owner: dataset registry maintainer +
worker-0; target resolution: 2026-05-18. Pin the exact MCPL/Parquet signal
sample path, file hash, generator command, and vertex-distribution validation
before using source vertices as thesis evidence.

OPEN: code/config alignment task — owner: worker-0 for C++/generator and worker-1
for Python config; target resolution: 2026-05-22. After the DEC, update or guard
`DetectorConstruction.cc`, MCPL/particle-gun behavior, and
`nnbar_geometry.yaml` in a separate compact-safe implementation task with tests.

## Recommended next smallest implementation task

After the target-radius DEC is approved, run a compact implementation task that:

1. adds a fail-closed verifier for the chosen target convention;
2. aligns either Geant4 `carbon_radius` or the documented study tag to the DEC;
3. aligns Python `target.radius` to the same convention or tags it as a
   reconstruction-only acceptance parameter;
4. blocks particle-gun signal runs from being promoted unless they sample the
   approved foil distribution or carry a `source_vertex_origin_fallback=true`
   metadata tag;
5. adds a sample-registry check that compares the promoted MCPL/Parquet vertex
   distribution against the approved support and gravity-bias evidence.
