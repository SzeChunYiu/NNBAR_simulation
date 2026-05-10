---
id: 07_5_4_beampipe
title: Simulation atomic walkthrough §5.4 — Beampipe builder
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §5.4 `Beampipe` builder (src/detector/beampipe_geometry.cc)

Status: detailed.

## Builder scope and output contract

`Beampipe::Construct_Volumes(mother)` always constructs the full
beamline wall/coating model and returns the logical volumes that
`DetectorConstruction::ConstructSDandField` later attaches to `TubeSD`
(src/detector/beampipe_geometry.cc:210). The return vector contains
all eight structural beampipe sections, three cap-coating LVs, the
beam stop, five wall child LVs, and five coating child LVs
(src/detector/beampipe_geometry.cc:496-518). There is no geometry
on/off branch inside this builder after material setup; the tree is
unconditionally placed in the supplied mother volume
(src/detector/beampipe_geometry.cc:455-466).

## Shared constants and z-reference chain

All beampipe sections use 2 cm aluminum wall thickness, 1 cm B4C
coating thickness, and full 360 degree azimuthal coverage
(src/detector/beampipe_geometry.cc:39-43). Section positions are
computed from `Beampipe_5_pos_z = 0`, so the detector-attached
section is the origin reference; sections 6 and 7 cap its upstream and
downstream ends, section 4 sits upstream, section 3 caps section 4 to
the long transport pipe, section 2 is the 171 m transport pipe, section
1 is the upstream expanding cone, and section 8 plus the beam stop sit
downstream (src/detector/beampipe_geometry.cc:113-135).

## Materials

`DefineMaterials` creates or retrieves the material palette before any
volumes are built (src/detector/beampipe_geometry.cc:139-208). The
active geometry uses:

| Material | Use | Definition citation |
|---|---|---|
| `Galactic` | mother void for hollow beam sections and beam stop parent | retrieved in Construct_Volumes (src/detector/beampipe_geometry.cc:216-218) |
| `Aluminum` | beampipe wall/cap material | 2.7 g/cm³ material guard (src/detector/beampipe_geometry.cc:193-197) |
| `B4C` | neutron-absorber coating and beam-stop absorber | 2.52 g/cm³ B/C material guard (src/detector/beampipe_geometry.cc:181-185) |
| `Copper` | beam-stop metal block | 8.9 g/cm³ material creation (src/detector/beampipe_geometry.cc:157-158) |

`Li6`, `Li6F`, `LiF`, cadmium, and stainless steel are also defined or
guarded, but this builder does not assign them to any active logical
volume (src/detector/beampipe_geometry.cc:160-207). The material guards
are the only decision branches in `DefineMaterials`; `Copper` is
created unconditionally while the other custom materials use
`G4Material::GetMaterial(..., false)` checks
(src/detector/beampipe_geometry.cc:157-199).

## Volume hierarchy and dimensions

The ordinary cylindrical/conical sections use a three-volume pattern:
a default-material mother, an aluminum wall child, and a B4C coating
child. Cap sections are aluminum ring LVs plus separate B4C cap-coating
LVs placed directly in the detector mother.

| Section | Hierarchy and material | Dimensions | Placement |
|---|---|---|---|
| `Beampipe_1` | hollow conical mother with aluminum `Beampipe_1_wall_LV` and B4C `Beampipe_1_coating_LV` children | outer radii 1.0 m → 1.8 m, wall inner radii 0.98 m → 1.78 m, coating inner radii 0.97 m → 1.77 m, length 14.4 m (src/detector/beampipe_geometry.cc:45-52,230-248) | children at local origin; mother at `Beampipe_1_pos_z` (src/detector/beampipe_geometry.cc:250-251,455) |
| `Beampipe_2` | hollow cylindrical mother with aluminum wall and B4C coating children | radius 1.8 m, wall inner radius 1.78 m, coating inner radius 1.77 m, length 171 m (src/detector/beampipe_geometry.cc:54-58,254-272) | children at local origin; mother at `Beampipe_2_pos_z` (src/detector/beampipe_geometry.cc:274-275,456) |
| `Beampipe_3` | aluminum cap LV plus separate B4C cap-coating LV | cap radius 1.06 m → 1.8 m, cap thickness 2 cm; coating radius 1.04 m → 1.77 m, thickness 2 cm (src/detector/beampipe_geometry.cc:65-73,278-290) | wall cap at `Beampipe_3_pos_z`; coating at `Beampipe_3_coating_pos_z` (src/detector/beampipe_geometry.cc:457-458) |
| `Beampipe_4` | short hollow cylindrical mother with aluminum wall and B4C coating children | wall radius 1.04 m → 1.06 m, coating radius 1.03 m → 1.04 m, length 3.5 m (src/detector/beampipe_geometry.cc:60-63,293-314) | children at local origin; mother at `Beampipe_4_pos_z` (src/detector/beampipe_geometry.cc:313-314,459) |
| `Beampipe_5` | detector-region hollow cylinder with aluminum wall and shortened B4C coating children | wall radius 1.12 m → 1.14 m, nominal length 5.0 m; coating radius 1.11 m → 1.12 m with full length shortened by the section-6/7 coating thicknesses to avoid cap overlap (src/detector/beampipe_geometry.cc:75-78,316-335) | children at local origin; mother at the global origin (src/detector/beampipe_geometry.cc:337-338,460) |
| `Beampipe_6` | upstream aluminum cap LV plus separate B4C cap-coating LV | cap radius 1.06 m → 1.14 m, thickness 2 cm; coating radius 1.04 m → 1.11 m, thickness 2 cm (src/detector/beampipe_geometry.cc:80-88,341-352) | wall cap at `Beampipe_6_pos_z`; coating at `Beampipe_6_coating_pos_z` (src/detector/beampipe_geometry.cc:461-462) |
| `Beampipe_7` | downstream aluminum cap LV plus separate B4C cap-coating LV | same cap/coating radii and thickness as section 6 (src/detector/beampipe_geometry.cc:90-98,355-366) | wall cap at `Beampipe_7_pos_z`; coating at `Beampipe_7_coating_pos_z` (src/detector/beampipe_geometry.cc:463-464) |
| `Beampipe_8` | downstream hollow cylinder with aluminum wall and B4C coating children | wall radius 1.02 m → 1.06 m, coating radius 1.01 m → 1.02 m, length 16.5 m (src/detector/beampipe_geometry.cc:100-103,369-390) | children at local origin; mother at `Beampipe_8_pos_z` (src/detector/beampipe_geometry.cc:389-390,465) |
| `BeamStop` | default-material parent with B4C absorber and copper metal children | radius 0 → 1.01 m, total length 3.3 m = 30 cm absorber + 3.0 m metal (src/detector/beampipe_geometry.cc:105-110,393-414) | absorber and metal are offset within the beam-stop parent; parent is placed at `BeamStop_pos_z` (src/detector/beampipe_geometry.cc:413-414,466) |

All beampipe and beam-stop visual attributes are set invisible after
construction, even though color attributes are allocated for debugging
(src/detector/beampipe_geometry.cc:416-453).

## Region, production cuts, and geometry registry

The builder creates `Beampipe_region`, adds the structural wall/mother
logical volumes for sections 1-8, and assigns production cuts of 1 cm
for gammas and 1 mm for electrons, positrons, and protons
(src/detector/beampipe_geometry.cc:472-494). Cap/coating LVs and the
beam-stop internals are returned to the caller, but the region root list
is narrower than the return vector (src/detector/beampipe_geometry.cc:472-518).

The builder registers a geometry-manager inventory after placements:
sections 1-8 are registered as wall/cap sections, section 9 as
`BeamStop`, and IDs 101-108 as B4C coatings
(src/detector/beampipe_geometry.cc:523-637). Those registry rows record
positions in mm, start/end radii in mm, half-lengths in mm, and the
material string used by downstream geometry audits
(src/detector/beampipe_geometry.cc:526-586,589-635).
