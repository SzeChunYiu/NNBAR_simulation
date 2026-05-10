---
id: 07_5_4_cosmicshielding
title: Simulation atomic walkthrough §5.4 — CosmicShielding builder
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §5.4 `CosmicShielding` builder (src/detector/Cosmic_Shielding_geometry.cc)

Status: detailed.

## Builder scope and exported dimensions

`CosmicShielding::Construct_Volumes(mother)` constructs a rectangular
cosmic-shield enclosure around the detector: top/bottom slabs, left/right
slabs, and front/back slabs, each with an outer shielding layer and an
inner steel-like layer (src/detector/Cosmic_Shielding_geometry.cc:169-241).
The output vector is file-scope, so repeated calls append to the same
`CosmicShielding_Construction_list` rather than a fresh local vector
(src/detector/Cosmic_Shielding_geometry.cc:35,246-288).

Several shield dimensions are global variables. In particular,
`lead_top_z` and `lead_fb_z` are consumed by the beampipe-shielding
builder to size shielding near beampipe sections 4 and 8
(src/detector/Cosmic_Shielding_geometry.cc:68-81). The builder declares
beampipe radii for the front/back beampipe hole; `Beampipe_5_radius_2`
is declared but not used in this file (src/detector/Cosmic_Shielding_geometry.cc:37-39,218-223).

## Materials and decision branches

`DefineMaterials` creates three shielding candidates without guards:
`Lead`, `PE_B4C_concrete`, and `MagnadenseHC`, then creates
`StainlessSteel` only if it does not already exist from the beampipe
builder (src/detector/Cosmic_Shielding_geometry.cc:99-167). The active
outer shield LVs use `MagnadenseHC`, despite variable names such as
`LeadShield_*`; the active top and side inner LVs use `StainlessSteel`
(src/detector/Cosmic_Shielding_geometry.cc:179-181,187-211).
The front/back inner LV is named `SteelShield_fb_LV` but is constructed
with `CosmicShieldingMaterial` (`MagnadenseHC`), not `SteelShieldingMaterial`
(src/detector/Cosmic_Shielding_geometry.cc:229-240).

There are no runtime geometry branches. The only boolean-like placement
choice is the final `pSurfChk` argument: back front/back shields use
`true` overlap checking while most other placements pass `false`
(src/detector/Cosmic_Shielding_geometry.cc:226-240).

## Dimensions and placements

The enclosure uses a 50 cm offset from the lead-glass envelope, a 2 m
outer shield thickness, and a 30 cm steel inner-layer thickness
(src/detector/Cosmic_Shielding_geometry.cc:58-66,83-97).

| Shield component | Dimensions | Placement | Citation |
|---|---|---|---|
| `LeadShield_top_LV` | `lead_top_x = 2*2.75 m + 2*0.5 m`, `lead_top_y = 2 m`, `lead_top_z = 2*3.35 m + 2*0.5 m` | two copies at `±(dist_center_lead_glass + shield_offset + lead_top_y/2)` on y | (src/detector/Cosmic_Shielding_geometry.cc:68-72,187-192) |
| `SteelShield_top_LV` | same x/z as top shield, y thickness 30 cm | two copies just inside the top/bottom outer slabs at `LeadShield_top_y - lead_top_y/2 - steel_top_y/2` | (src/detector/Cosmic_Shielding_geometry.cc:83-88,194-198) |
| `LeadShield_side_LV` | x thickness 2 m, y spans the full top/bottom envelope, z = `lead_top_z` | two copies at `±(lead_top_x/2 + lead_side_x/2)` on x | (src/detector/Cosmic_Shielding_geometry.cc:73-81,200-205) |
| `SteelShield_side_LV` | x thickness 30 cm, y shortened by top/bottom lead and steel layers, z = `lead_side_z` | two copies just inside the side outer slabs at `LeadShield_side_x - lead_side_x/2 - steel_side_x/2` | (src/detector/Cosmic_Shielding_geometry.cc:89-97,207-211) |
| `LeadShield_fb_LV` | front/back slab with x/y envelope `lead_fb_x`/`lead_fb_y`, z thickness 2 m | two copies at `±(lead_top_z/2 + lead_fb_z/2)` with a cylindrical beampipe hole subtracted | (src/detector/Cosmic_Shielding_geometry.cc:78-81,214-228) |
| `SteelShield_fb_LV` | front/back inner slab with x/y reduced by outer+steel thickness and z thickness 30 cm | two copies just inside the outer front/back slabs with the same beampipe hole subtracted | (src/detector/Cosmic_Shielding_geometry.cc:94-97,229-240) |

The front/back slabs subtract `virtual_Beampipe_4_S`, a full 360° cone
from radius 0 to `Beampipe_4_radius_2` with half-length equal to half
the 2 m shield thickness, to leave a central beam-pipe aperture
(src/detector/Cosmic_Shielding_geometry.cc:216-224,229-237).

## Regions, outputs, and visual state

The returned list contains all six logical volumes: outer top, side, and
front/back, followed by inner top, side, and front/back
(src/detector/Cosmic_Shielding_geometry.cc:242-251). `Shield_region`
contains those same six LVs and assigns production cuts of 5 cm for
gammas, 5 mm for electrons and positrons, and 15 mm for protons
(src/detector/Cosmic_Shielding_geometry.cc:253-273). The file does not
register shield geometry with `GeometryManager`, and no active sensitive
detector is attached to these returned LVs in the current
`ConstructSDandField` path.

Visual settings make top and side outer shields invisible, front/back
outer shields green, and front/back inner shields black; top and side
inner steel LVs are not explicitly assigned a visual attribute
(src/detector/Cosmic_Shielding_geometry.cc:275-286).
