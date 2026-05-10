---
id: 07_5_4_beampipe_shielding
title: Simulation atomic walkthrough §5.4 — Beampipe_Shielding builder
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §5.4 `Beampipe_Shielding` builder (src/detector/beampipe_shielding_geometry.cc)

Status: detailed.

## Builder scope and dependencies

`Beampipe_Shielding::Construct_Volumes(mother)` builds three lead
shielding rings around beampipe sections 2, 4, and 8
(src/detector/beampipe_shielding_geometry.cc:55-125). The dimensions
are not self-contained: the builder reads global beampipe radii,
lengths, and positions from `beampipe_geometry.cc`, and lead-glass
shield dimensions `lead_top_z` / `lead_fb_z` from the cosmic-shielding
builder (src/detector/beampipe_shielding_geometry.cc:33-46). The
source declares `Beampipe_2_len` twice, but both declarations refer to
the same external scalar (src/detector/beampipe_shielding_geometry.cc:33-36).

The function allocates a `Beampipe_Shielding_Construction_list`, but it
never pushes any logical volumes into it before returning
(src/detector/beampipe_shielding_geometry.cc:55-59,142). Therefore the
three shielding volumes are physically placed in the world mother, but
no SD attachment target is exposed through this builder's return vector.

## Material and decision branches

`DefineMaterials` creates one material, `Lead_shield`, as elemental lead
with density 11.29 g/cm³ (src/detector/beampipe_shielding_geometry.cc:48-53).
There is no `G4Material::GetMaterial` guard, so repeated calls would
attempt to create the same material name again. After material creation,
`Construct_Volumes` retrieves `Lead_shield` and uses it for every
shielding LV (src/detector/beampipe_shielding_geometry.cc:61-63).

There are no compile-time or runtime geometry branches in this builder.
The only variable behavior is inherited from the external beampipe and
lead-shielding globals used to compute the section-4 and section-8
lengths (src/detector/beampipe_shielding_geometry.cc:69-88). The
section-4 length calculation also prints four separator lines and one
numeric diagnostic line to `std::cout` on every construction
(src/detector/beampipe_shielding_geometry.cc:77-82).

## Volume hierarchy, dimensions, and placements

All three shielding volumes are single-level `G4Cons` annular cylinders
with full 360 degree coverage and no daughter volumes
(src/detector/beampipe_shielding_geometry.cc:95-125).

| Shield | Dimensions | Placement | Citation |
|---|---|---|---|
| `Beampipe_Shielding_2_LV` | lead annulus around beampipe 2, inner radius `Beampipe_2_radius_2`, outer radius `Beampipe_2_radius_2 + 3.0 m`, half-length `Beampipe_2_len/2` | placed at `Beampipe_2_pos_z`, concentric with the 171 m transport pipe | (src/detector/beampipe_shielding_geometry.cc:69-72,95-103) |
| `Beampipe_Shielding_4_LV` | lead annulus around the short upstream detector-side beampipe, inner radius `Beampipe_4_radius_2`, outer radius plus 3.5 m, half-length derived from the upstream end of beampipe 4 to `-(lead_top_z/2 + lead_fb_z)` | placed at `Beampipe_2_pos_z + Beampipe_2_len/2 + Beampipe_Shielding_4_len/2`, i.e. immediately downstream of beampipe 2 by construction | (src/detector/beampipe_shielding_geometry.cc:74-82,106-114) |
| `Beampipe_Shielding_8_LV` | lead annulus around downstream beampipe 8, inner radius `Beampipe_8_radius_2`, outer radius plus 3.5 m, half-length from the lead-shield plane to the downstream end of beampipe 8 | placed at `Beampipe_8_pos_z + Beampipe_8_len/2 - Beampipe_Shielding_8_len/2` | (src/detector/beampipe_shielding_geometry.cc:83-88,117-125) |

The third logical volume is named `Beampipe_8_LV` rather than
`Beampipe_Shielding_8_LV` in the `G4LogicalVolume` constructor, while
its physical placement is named `Beampipe_Shielding_8_PV`
(src/detector/beampipe_shielding_geometry.cc:124-125). All three LVs
are set invisible after construction; color attributes are allocated but
only retained in commented debug calls (src/detector/beampipe_shielding_geometry.cc:131-139).

## Registration and output gaps

Unlike the primary beampipe builder, this file does not create a
`G4Region`, does not assign production cuts, and does not register its
rings with `GeometryManager` (src/detector/beampipe_shielding_geometry.cc:127-142).
Those omissions mean downstream geometry audits must infer this
shielding from source/placement names rather than from the beampipe
registry table.
