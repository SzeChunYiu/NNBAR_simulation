---
id: 07_5_4_leadglass
title: Simulation atomic walkthrough §5.4 — LeadGlass builder
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §5.4 `LeadGlass` builder (src/detector/LeadGlass_geometry.cc)

Status: detailed.

## Builder scope and input files

`LeadGlass::Construct_Volumes(mother)` builds one reusable lead-glass
module logical hierarchy, places copies on the four barrel surfaces plus
front/back surfaces from CSV position tables, registers every block with
`GeometryManager`, and returns the lead-glass body LV plus PMT-window LV
for SD attachment (src/detector/LeadGlass_geometry.cc:160-176,191-193,231-308,375-393).
The output vector is file-scope (`LeadGlass_Construction_list`), so
repeated calls append to the same vector rather than a fresh local one
(src/detector/LeadGlass_geometry.cc:52,375-393).

Placement data is loaded from `./data/lead_glass_position/lead_glass_position.csv`
for barrel surfaces and `./data/lead_glass_position/lead_glass_position_fb.csv`
for front/back surfaces (src/detector/LeadGlass_geometry.cc:54-60,191-192).
The importer is fail-closed: missing or empty files raise Geant4 fatal
exceptions instead of silently constructing no calorimeter
(src/detector/LeadGlass_geometry.cc:60-95).

## Materials and optical properties

`DefineMaterials` creates Schott-SF5-like `LeadGlass` at 6.22 g/cm³ with
O/Si/Ti/As/Pb mass fractions, an `AlMgF2` material, and a quartz-like
`PMT_window_mat` with refractive index 1.53 (src/detector/LeadGlass_geometry.cc:101-130).
The lead-glass material receives an 18-point refractive-index table from
2325.4 nm to 365.0 nm; photon energies are derived from wavelength before
calling `AddProperty("RINDEX", ...)` (src/detector/LeadGlass_geometry.cc:132-157).
`AlMgF2` is defined but the coating logical volume itself uses the
default material; the reflective coating behavior is implemented by an
optical skin surface, not by assigning `AlMgF2` as the LV material
(src/detector/LeadGlass_geometry.cc:120-122,210-215,318-334).

## Module hierarchy and dimensions

Each placed `LeadGlass_module_LV` is a default-material wrapper around
three daughter volumes (src/detector/LeadGlass_geometry.cc:202-220):

| Daughter LV | Material | Dimensions and placement | Citation |
|---|---|---|---|
| `LeadGlassLV` | `LeadGlass` | 8 cm × 25 cm × 8 cm block, shifted within the wrapper so the PMT window occupies the positive-y end | (src/detector/LeadGlass_geometry.cc:179-208) |
| `LeadGlass_CoatingLV` | `Galactic` default material plus optical skin | subtraction shell from the wrapper minus an 8 cm × (25 cm + PMT thickness) × 8 cm hollow, yielding side coating with 0.01 mm x/z thickness | (src/detector/LeadGlass_geometry.cc:183,202-215) |
| `PMTLV` | `PMT_window_mat` | 8 cm × 0.01 mm × 8 cm virtual PMT window placed at the module's positive-y end | (src/detector/LeadGlass_geometry.cc:185,217-220) |

The source comments describe the intended model as reflective sides,
absorbing bottom, and transparent PMT coupling; the implemented surfaces
are a 95% reflective coating skin and a PMT skin with 25% efficiency
(src/detector/LeadGlass_geometry.cc:193-200,310-354).

## Barrel and front/back placement logic

For barrel surfaces, the builder creates four rotation-vector arrays,
then loops over the CSV rows for each of four 90°-spaced surfaces
(src/detector/LeadGlass_geometry.cc:226-243). For each row, source x/y
positions are read in centimeters, y is shifted by +1.5 cm, coordinates
are rotated by `i * 90°`, and the module gets copy number
`i * data_lead_glass_pos.size() + j` (src/detector/LeadGlass_geometry.cc:245-256).
The module rotation first tilts around the radial surface axis by the
negative CSV angle column and then rotates around z by the CSV azimuth
minus the surface angle (src/detector/LeadGlass_geometry.cc:249-256).
Each barrel block is registered with surface index 0 top, 1 right, 2
bottom, or 3 left (src/detector/LeadGlass_geometry.cc:258-263).

For front/back surfaces, copy numbers start after the four barrel grids
(src/detector/LeadGlass_geometry.cc:266-280). Front blocks use
`x = csv[0]`, `y = csv[2]`, `z = -csv[1]`, rotations `rotateX(-csv[3]+90°)`
and `rotateZ(csv[5])`, and surface index 4
(src/detector/LeadGlass_geometry.cc:274-289). Back blocks start after
the front block count, use `z = +csv[1]`, rotations `rotateX(csv[3]-90°)`
and `rotateZ(csv[5])`, and surface index 5
(src/detector/LeadGlass_geometry.cc:291-308).

## Optical surfaces, cuts, and visibility

The coating skin surface is polished dielectric-metal with 95% reflectivity
and zero detection efficiency over 2.0-3.5 eV; the PMT skin is polished
dielectric-metal with zero reflectivity and 25% efficiency over the same
energy range (src/detector/LeadGlass_geometry.cc:318-354). `LeadGlass_region`
contains only `LeadGlassLV` and sets 5 mm production cuts for gammas,
electrons, positrons, and protons; PMT and coating volumes do not receive
separate regions in this file (src/detector/LeadGlass_geometry.cc:357-369).
The active lead-glass body is green in visualisation, while the wrapper,
coating, and PMT LVs are invisible (src/detector/LeadGlass_geometry.cc:378-391).
