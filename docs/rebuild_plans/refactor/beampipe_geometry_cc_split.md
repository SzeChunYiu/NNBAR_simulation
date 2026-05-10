# `src/Detector_Module/beampipe_geometry.cc` split plan

> **For Codex:** This is a review plan only. Do not move Geant4 code
> until a human approves the split. When implementing, use
> `executing-plans`, preserve geometry constants byte-for-byte in the
> first extraction, and run a build/smoke geometry check after every
> commit.

**Goal:** Split the over-limit beampipe geometry builder into small C++
translation units while preserving beampipe dimensions, materials,
coatings, placements, region cuts, visualization settings, and returned
logical-volume order.

**Current state:** In
`/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3`, `wc -l` reports
503 lines for `src/Detector_Module/beampipe_geometry.cc` and 36 lines
for `include/Detector_Module/beampipe_geometry.hh`. Manual source
inspection before this plan found two current entry points:
`Beampipe::DefineMaterials` and the large
`Beampipe::Construct_Volumes`.

**Non-goal:** Do not fix geometry bugs, simplify constants, rename
Geant4 solids/logical volumes, or change coating/wall material choices
inside this split. Those changes require separate physics review.

---

## Constraints

- Keep every touched C++ source/header below 500 lines, targeting
  150-250 lines.
- Preserve all global `Beampipe_*` and `BeamStop_*` symbols until
  dependent detector modules have migrated.
- Preserve `Beampipe_Construction_list` order exactly; downstream code
  may rely on the returned logical-volume sequence.
- Preserve all Geant4 solid/logical/physical volume names exactly.
- Update `CMakeLists.txt` with every new `.cc` file in the same commit
  series.
- Build after every extraction and run the smallest available detector
  construction smoke macro before final review.

---

## Target module budgets

| Target file | Responsibility | Proposed function list | Budget |
|---|---|---|---:|
| `src/Detector_Module/beampipe_geometry.cc` | Constructor/destructor, globals include, and thin construction coordinator | keep constructor/destructor and a thin `Construct_Volumes` coordinator | 180 |
| `src/Detector_Module/beampipe_dimensions.cc` | Existing global dimension and position definitions | move `Beampipe_*` and `BeamStop_*` global definitions unchanged | 170 |
| `src/Detector_Module/beampipe_materials.cc` | NIST element lookup and material definitions | move `DefineMaterials` unchanged | 120 |
| `src/Detector_Module/beampipe_sections.cc` | Section and coating solids/logical volumes for beampipe parts 1-8 | proposed helpers for conical section, cap section, and coated straight section bundles | 240 |
| `src/Detector_Module/beamstop_geometry.cc` | Beam-stop solid/logical volume and internal absorber/metal placement | proposed helper for beam-stop bundle construction | 120 |
| `src/Detector_Module/beampipe_placements.cc` | Physical placement of beampipe sections and coatings into the mother volume | proposed helper preserving physical-volume names and z positions | 160 |
| `src/Detector_Module/beampipe_appearance.cc` | Visualization attributes, region assignment, production cuts, and return-list assembly | proposed helpers for invisible attributes, region cuts, and logical-volume return ordering | 220 |
| `include/Detector_Module/beampipe_layout.hh` | Optional POD bundle declarations if implementation helpers need shared types | structs for material bundle, section bundle, and construction bundle | 160 |

---

## Decision-log entry stub

`DEC-2026-05-10-L3-beampipe-split`

- **Title:** Behavior-preserving split of beampipe geometry code.
- **Status:** proposed only if implementation changes any geometry,
  material, coating, placement, cut, or return-list behavior.
- **Context:** `beampipe_geometry.cc` exceeds the 500-line cap and
  mixes global dimensions, material construction, solids/logical
  volumes, physical placements, visualization, regions, cuts, and return
  list assembly.
- **Decision:** Extract one-responsibility C++ translation units while
  preserving the public `Beampipe` class API and shared global symbols.
- **Non-decisions:** No physics geometry changes, no material swaps, no
  production-cut tuning, no output ordering changes.
- **Validation:** Build succeeds after each extraction; final smoke run
  constructs the same beampipe volumes and produces the same returned
  logical-volume order for the same macro/config input.

---

## Execution tasks

### Task 1: Move global dimensions without changing symbols

1. Create `src/Detector_Module/beampipe_dimensions.cc`.
2. Move the existing `Beampipe_*` and `BeamStop_*` global definitions
   unchanged.
3. Keep declarations visible to modules that currently use `extern`
   declarations.
4. Build to catch missing-symbol or duplicate-symbol errors.

### Task 2: Move material setup

1. Create `src/Detector_Module/beampipe_materials.cc`.
2. Move `Beampipe::DefineMaterials` unchanged.
3. Add the new file to `CMakeLists.txt`.
4. Build to verify material symbols and class method linkage.

### Task 3: Extract beampipe section construction

1. Introduce a small section-bundle struct for container, wall, and
   coating logical volumes.
2. Extract repeated wall/coating construction for parts 1, 2, 4, 5, and
   8 without changing solid/logical-volume names.
3. Extract cap/coating construction for parts 3, 6, and 7.
4. Build after the extraction.

### Task 4: Extract beam-stop and placements

1. Move beam-stop solid/logical construction and absorber/metal internal
   placements into `beamstop_geometry.cc`.
2. Move top-level `G4PVPlacement` calls into `beampipe_placements.cc`.
3. Preserve every physical-volume name, z-position symbol, and copy
   number exactly.
4. Build and run a smoke macro.

### Task 5: Extract appearance, regions, and return ordering

1. Move visualization attributes and `Beampipe_region` production cuts
   into `beampipe_appearance.cc`.
2. Move `Beampipe_Construction_list` assembly into a helper whose order
   is tested or compared by a smoke assertion.
3. Run final build plus detector construction smoke macro.
4. Confirm every touched C++ source/header is below 500 lines by
   `wc -l`.
