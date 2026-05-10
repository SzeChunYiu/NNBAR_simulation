---
id: 07_5_4_scintillator
title: Simulation atomic walkthrough §5.4 — Scintillator builder
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §5.4 `Scintillator` builder (src/detector/Scintillator_geometry.cc)

Status: detailed.

## Builder scope and output contract

`Scintillator::Construct_Volumes(mother)` builds the side and front/back
plastic-scintillator hodoscope around the TPC, writes a CSV-like module
position file at `./output/Scintillator_Module_Position.txt`, registers
module centers with `GeometryManager`, and returns only the four active
bar logical volumes that should receive `ScintillatorSD`
(src/detector/Scintillator_geometry.cc:111-118,261-294,429-490,574-579).
Wrapper module and layer LVs are placement scaffolding only.

## Material and optical branch

`DefineMaterials` creates BC-408-like `Scint` at 1.023 g/cm³ with H/C
fractions 0.524573 / 0.475427, then attaches a 12-point optical property
table: refractive index 1.58, attenuation length 210 cm, and matched fast
/ slow scintillation spectra over 2.08-3.44 eV
(src/detector/Scintillator_geometry.cc:51-88). The only compile-time
branch is `WITH_SCINTILLATION`: enabled builds set scintillation yield to
10000 photons/MeV, while default fast-mode builds set yield to zero
(src/detector/Scintillator_geometry.cc:90-98). The time constants are
0.9 ns and 2.1 ns, but all yield is assigned to component 1
(src/detector/Scintillator_geometry.cc:100-106).

Reflective wrapping is applied later as a polished dielectric-metal skin
surface with 95% reflectivity and zero detection efficiency over 2.0-3.5
eV on all four active bar LVs (src/detector/Scintillator_geometry.cc:493-526).
That optical surface is created regardless of whether optical photon
generation is disabled by `WITH_SCINTILLATION`.

## Side module hierarchy and dimensions

The side hodoscope module is a 40 cm × 30 cm × 40 cm default-material box
made from ten 3 cm layers. Layers alternate by `i % 2`: even layers use
horizontal bars and odd layers use vertical bars
(src/detector/Scintillator_geometry.cc:132-143,178-186,219-222).

| Active side bar LV | Dimensions | Placement inside layer | Citation |
|---|---|---|---|
| `Scint_barH_LV` | scintillator bar 10 cm × 3 cm × 40 cm | four bars tiled across x in each horizontal layer | (src/detector/Scintillator_geometry.cc:188-193,224-227) |
| `Scint_barV_LV` | scintillator bar 40 cm × 3 cm × 10 cm | four bars tiled across z in each vertical layer | (src/detector/Scintillator_geometry.cc:197-201,224-227) |

The side module grid uses 10 modules across x and 11 modules along z.
Gaps `dx` and `dz` are computed from the beampipe radius, TPC drift
length/wall thickness, a 20 cm offset `dy`, and the beampipe-5/6 length
span (src/detector/Scintillator_geometry.cc:145-163). The code builds
110 local grid positions, then places four rotated surfaces: top (0°),
left (270°), bottom (180°), and right (90°), for 440 side modules total
(src/detector/Scintillator_geometry.cc:234-279). Copy numbers are
contiguous by surface (`i`, `110+i`, `220+i`, `330+i`), and each copy is
registered with `GeometryManager` plus written to the position file
(src/detector/Scintillator_geometry.cc:271-296).

## Front/back module hierarchy and dimensions

The front/back module is a 30 cm × 30 cm × 30 cm default-material box
made from ten 3 cm z-layers (src/detector/Scintillator_geometry.cc:303-312,341-350).
Two active bar LVs populate alternating layers:

| Active front/back bar LV | Dimensions | Placement inside layer | Citation |
|---|---|---|---|
| `Scint_fb_bar1V_LV` | scintillator bar 5 cm × 30 cm × 3 cm | six bars tiled across x in vertical-bar layers | (src/detector/Scintillator_geometry.cc:352-358,366-377) |
| `Scint_fb_bar1H_LV` | scintillator bar 30 cm × 5 cm × 3 cm | six bars tiled across y in horizontal-bar layers | (src/detector/Scintillator_geometry.cc:360-364,366-377) |

The front/back surface sits 20 cm beyond the TPC/end beampipe envelope;
`scint_fb_top_dist` records the distance from detector center to the
front scintillator outer surface (src/detector/Scintillator_geometry.cc:303-317).
Group 1 covers top/bottom rectangles on the front and back faces with a
15 × 4 module grid, then places four copies of each local grid point:
front top, front bottom, back top, and back bottom
(src/detector/Scintillator_geometry.cc:319-339,390-438). Group 2 covers
left/right rectangles on the same front/back faces with a 4 × 7 grid and
again places four copies per point
(src/detector/Scintillator_geometry.cc:442-490). Front placements use a
0° x-rotation; back placements use 180° around x
(src/detector/Scintillator_geometry.cc:386-388,424-427,477-480).

## Registration, cuts, and visibility

Every side and front/back module placement is written to
`Scintillator_Module_Position.txt` in centimeters and registered with
`GeometryManager` in millimeters. Surface IDs are 0 top, 1 right, 2
bottom, 3 left, 4 front, and 5 back
(src/detector/Scintillator_geometry.cc:281-294,429-490). The output file
is closed after the final front/back group is written
(src/detector/Scintillator_geometry.cc:493).

`Scint_region` contains only the four active bar LVs and sets production
cuts to 6 cm for gammas and 2 mm for electrons, positrons, and protons
(src/detector/Scintillator_geometry.cc:528-545). Module boxes are colored
blue/dark blue for visual scaffolding, while layer LVs and active bar LVs
are made invisible (src/detector/Scintillator_geometry.cc:547-571).
