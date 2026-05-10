---
id: 07_10_primary_generators
title: Simulation atomic walkthrough §10 — primary generators
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

## 10. Primary generators

### 10.1 `PrimaryGeneratorAction` (src/core/PrimaryGeneratorAction.cc, 22 KB)

The largest non-geometry source file in the simulation. It supports
multiple primary-emission modes selected via the messenger
(`PrimaryGeneratorMessenger`, §10.2). Modes documented at
`reconstruction.md` and inferred from messenger commands:

- **Default GPS-style signal mode** (`MCPL_BUILD=OFF`, no `-g`
  override needed if MCPL is off). Emits a single primary per event
  per the kinematic distribution configured by macro commands
  (`/calibration/*`, `/source/*`).
- **Particle-gun mode** (`-g` or `/generator/use_particle_gun true`):
  emits a single primary at a fixed direction/energy.
- **MCPL mode** (`MCPL_BUILD=ON` or `/particle_generator/set_mcpl_file
  <path>`): reads primaries from a vendored MCPL file via
  `G4MCPLGenerator` (§10.3).
- **Calibration list / multi-primary mode**
  (`/calibration/signal_particles ...`): emits multiple named
  primaries from the same vertex, used by the
  `multiprimary_pion_proton_foil_stress.mac` study.

The action records primary truth (PDG name, momentum, position) into
the `Particle_output` table per event.

### 10.2 `PrimaryGeneratorMessenger` (src/core/PrimaryGeneratorMessenger.cc)

Defines the macro-command UI for the generator. Per `reconstruction.md`
and macro inspection, supported directories include:

- `/particle_generator/set_mcpl_file <path>` — set MCPL input.
- `/calibration/*` — calibration single-particle and multi-particle
  configurations (energy ranges, particle lists, vertex constraints).
- `/source/*` — beam-direction and beam-shape commands (when used).

The exact command tree is dumped by Geant4's `/help`; plan 10 (macro
inventory) documents which commands each macro file invokes.

### 10.3 `G4MCPLGenerator` (src/generator/G4MCPLGenerator.cc, 11.8 KB)

Wraps the MCPL C library to expose MCPL primaries to Geant4. Behaviour
is per the standard MCPL contract (one particle per record). Plan 17
(neutron-beam sample) and plan 21 (CRY cosmic sample) consume this
generator if the chosen integration path is "external generator → MCPL
→ Geant4".

### 10.4 `G4MCPLWriter` (src/generator/G4MCPLWriter.cc, 4.5 KB)

Writes primaries out as MCPL. Used when the simulation produces an
intermediate MCPL file (e.g. for cross-check between two physics-list
configurations).
