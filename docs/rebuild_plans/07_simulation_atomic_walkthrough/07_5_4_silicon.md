---
id: 07_5_4_silicon
title: Simulation atomic walkthrough §5.4 — Silicon builder
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §5.4 `Silicon` builder (src/detector/Silicon_geometry.cc)

Status: detailed.

## Builder scope and dependencies

`Silicon::Construct_Volumes(mother)` builds two concentric silicon
barrels and two inner Li6F coating barrels around the detector-side
beampipe section (src/detector/Silicon_geometry.cc:75-129). The only
external geometry scalar used in active dimensions is
`Beampipe_5_len`; `Beampipe_5_radius_2` is declared but not consumed
(src/detector/Silicon_geometry.cc:34-37,92-96). The function returns
only the two silicon logical volumes, not the Li6F coating logical
volumes (src/detector/Silicon_geometry.cc:136-138,172).

## Materials and branches

`DefineMaterials` unconditionally creates `Silicon` at 2.33 g/cm³, then
condition-checks shared neutron-absorber materials (`B4C`, `el_Li6`,
`Li6F`) that may already have been defined by the beampipe builder
(src/detector/Silicon_geometry.cc:38-73). The active silicon shells use
`Silicon`; the inner coating shells use `Li6F`
(src/detector/Silicon_geometry.cc:84-87,102-129). There are no runtime
geometry branches after material setup; both silicon barrels and both
coating barrels are always placed in `mother`.

## Volume hierarchy, dimensions, and placements

The builder uses four independent top-level `G4Cons` cylinders with full
360 degree angular coverage. None are nested inside another silicon
mother volume.

| Volume | Material | Dimensions | Placement and sensitivity |
|---|---|---|---|
| `siliconLV_1` / `siliconPV_1` | `Silicon` | inner radius 103.0 cm, outer radius 103.2 cm, half-length `(Beampipe_5_len - 10 cm)/2`, full azimuth | placed at the world origin with copy number 0; returned for `SiliconSD` attachment (src/detector/Silicon_geometry.cc:92-104,136) |
| `siliconLV_2` / `siliconPV_2` | `Silicon` | inner radius 107.0 cm, outer radius 107.2 cm, same half-length and full azimuth | placed at the world origin with copy number 1; returned for `SiliconSD` attachment (src/detector/Silicon_geometry.cc:92-108,137) |
| `Silicon_Coating_LV` / `silicon_coating_PV` | `Li6F` | inner radius 102.9 cm, outer radius 103.0 cm, same half-length and full azimuth | placed at the world origin with copy number 0; not returned and therefore not attached to `SiliconSD` by `DetectorConstruction` (src/detector/Silicon_geometry.cc:96,114-129) |
| `Silicon_Coating_2_LV` / `silicon_coating_2_PV` | `Li6F` | inner radius 106.9 cm, outer radius 107.0 cm, same half-length and full azimuth | placed at the world origin with copy number 1; not returned and therefore not attached to `SiliconSD` by `DetectorConstruction` (src/detector/Silicon_geometry.cc:96,122-129) |

The hard-coded radii make the two active silicon layers 4 cm apart in
radius, while the Li6F coatings sit immediately inside each silicon
layer. The barrel length is coupled to the beampipe-5 length but shortened
by 10 cm, leaving 5 cm clearance at each end if `Beampipe_5_len` remains
5 m (src/detector/Silicon_geometry.cc:92-96).

## Region, production cuts, and visual state

`Silicon_region` contains only `siliconLV_1` and `siliconLV_2`, then
assigns 0.01 mm production cuts for gammas, electrons, positrons, and
protons (src/detector/Silicon_geometry.cc:143-153). The Li6F coating
volumes are not region roots and do not get their own production-cut
assignment in this file.

Both silicon LVs are colored orange for visualisation; the coating
visibility calls are present only as commented-out invisible settings
(src/detector/Silicon_geometry.cc:157-170). The file does not register
silicon geometry with `GeometryManager`, so downstream geometry audits
must infer this builder from placements and returned LVs rather than a
silicon-specific registry table.
