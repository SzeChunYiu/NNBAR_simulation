# `src/Detector_Module/Scintillator_geometry.cc` split plan

> **For Codex:** This is a review plan only. Do not move Geant4 code
> until a human approves the split. When implementing, use
> `executing-plans`, run a build/smoke geometry check after every
> extraction, and keep all copy-number and placement behavior unchanged.

**Goal:** Split the over-limit scintillator geometry builder into small
C++ translation units while preserving detector geometry, material
properties, copy-number indexing, and output-file semantics.

**Current state:** In
`/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3`, `wc -l` reports
516 lines for `src/Detector_Module/Scintillator_geometry.cc` and 32
lines for `include/Detector_Module/Scintillator_geometry.hh`.
Manual source inspection before this plan found two current entry
points: `Scintillator::DefineMaterials` and the large
`Scintillator::Construct_Volumes`.

**Non-goal:** Do not tune dimensions, optical constants, region cuts,
module positions, or visualization colors. Any geometry-value change is
not part of this split and needs a separate decision-log entry.

---

## Constraints

- Keep each touched C++ source/header below 500 lines, targeting
  150-250 lines per file.
- Preserve the `Scintillator` public API in
  `include/Detector_Module/Scintillator_geometry.hh`.
- Preserve the `./output/Scintillator_Module_Position.txt` format and
  all copy-number offsets exactly.
- Prefer file-local helper structs/functions in new `.cc` files unless
  a helper must be shared by another detector module.
- Update `CMakeLists.txt` in the same commit series so every new `.cc`
  file is compiled.
- Build after every extraction; run the smallest available detector
  construction smoke macro before final review.

---

## Target module budgets

| Target file | Responsibility | Proposed function list | Budget |
|---|---|---|---:|
| `src/Detector_Module/Scintillator_geometry.cc` | Constructor/destructor and top-level orchestration | keep constructor/destructor and a thin `Construct_Volumes` coordinator | 160 |
| `src/Detector_Module/Scintillator_materials.cc` | BC-408 material and optical material-properties table | move `DefineMaterials` unchanged | 120 |
| `src/Detector_Module/Scintillator_layout.cc` | Pure dimension/layout calculations for barrel and front/back groups | proposed helpers for barrel dimensions, front/back dimensions, and group offsets | 180 |
| `src/Detector_Module/Scintillator_bars.cc` | Logical-volume construction for modules, layers, and bars | proposed helpers for barrel module, front/back module, and bar/layer placement | 220 |
| `src/Detector_Module/Scintillator_placements.cc` | Physical placements and module-position output rows | proposed helpers for barrel placements, front/back group-1 placements, and front/back group-2 placements | 240 |
| `src/Detector_Module/Scintillator_appearance.cc` | Optical surfaces, production cuts, and visualization attributes | proposed helpers for skin surfaces, region cuts, and vis attributes | 180 |
| `include/Detector_Module/Scintillator_layout.hh` | Optional shared layout structs if anonymous-namespace helpers become too large | small POD structs for dimensions, rotations, and logical-volume bundle | 160 |

---

## Decision-log entry stub

`DEC-2026-05-10-L3-scintillator-split`

- **Title:** Behavior-preserving split of scintillator geometry code.
- **Status:** proposed only if implementation changes any geometry,
  optical, copy-number, or output-file behavior.
- **Context:** `Scintillator_geometry.cc` exceeds the 500-line cap and
  mixes material definition, geometry dimensions, logical-volume
  creation, physical placement, output bookkeeping, optics, regions,
  and colors.
- **Decision:** Extract one-responsibility C++ translation units while
  keeping the public `Scintillator` class API stable.
- **Non-decisions:** No geometry-value changes, no material tuning, no
  copy-number reindexing, no output-schema changes.
- **Validation:** Build succeeds after each extraction; final geometry
  smoke run produces the same scintillator module-position file for the
  same macro/config input.

---

## Execution tasks

### Task 1: Move material setup

1. Create `src/Detector_Module/Scintillator_materials.cc`.
2. Move `Scintillator::DefineMaterials` unchanged.
3. Add the new file to `CMakeLists.txt`.
4. Build to verify duplicate-symbol and missing-symbol errors are absent.

### Task 2: Isolate layout values

1. Extract the barrel and front/back dimension calculations into local
   layout structs.
2. Keep units attached to the same constants; do not simplify numeric
   expressions in this extraction.
3. Build and compare emitted dimensions/log lines from a smoke run.

### Task 3: Isolate logical-volume construction

1. Move module/layer/bar `G4Box` and `G4LogicalVolume` creation into
   helper functions returning a small bundle struct.
2. Keep material names and logical-volume names byte-for-byte unchanged.
3. Build after the extraction.

### Task 4: Isolate physical placements and output rows

1. Move barrel side/top/bottom placements into one helper.
2. Move front/back group-1 and group-2 placements into separate helpers.
3. Preserve `scint_index_count` increments and CSV row order exactly.
4. Build and compare `Scintillator_Module_Position.txt` against a
   pre-split run.

### Task 5: Isolate appearance, optics, and regions

1. Move `G4OpticalSurface`, `G4LogicalSkinSurface`, `G4Region`,
   production cuts, and visualization attributes into one helper.
2. Preserve all surface names, cut values, and colors.
3. Run final build plus detector construction smoke macro.
4. Confirm every touched C++ source/header is below 500 lines by
   `wc -l`.
