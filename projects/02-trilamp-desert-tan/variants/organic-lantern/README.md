# Organic Lantern — bowed shade and rounded cap

[Color preview](previews/colors.png) · [Cap STL](models/cap.stl) ·
[Cap 3MF](studio/TriLamp_Organic_Lantern_Cap_P2S.3mf)

A warmer revision of Soft Spiral with a fuller middle, gently wandering shallow
waves, and staggered rounded slits of varying lengths. Fine external fuzzy skin
is enabled at 0.12 mm thickness / 0.4 mm point distance, with the fitting bands
kept smooth. Desert Tan and muted grey-blue use the same geometry; the blue
preview is illustrative rather than a matched filament swatch.

## Geometry

- Shade height: 210 mm; unchanged 85 mm end diameter.
- Middle: approximately 95 mm diameter, with a subtle asymmetric contour.
- Wave depth reduced from 0.8 to 0.45 mm; spacing increased from 5.2 to 7 mm.
- 936 rounded slits, nominally 4.6–5.6 mm long and 2.25 mm high before
  tilting to follow the waves, with continuous gently arched roofs.
- Approximate projected opening area: 9,488 mm² versus 9,420 mm² previously.
  This preserves aperture area, not a measured light-output guarantee. Opaque
  filament sends light through the openings; it will not glow like translucent PLA.
- Original keyed mounting geometry retained; both end interfaces remain fixed.
- Removable cap: 85 mm diameter, rounded 1 mm edge radius, 2 mm roof, 4 mm
  locating ring, and twelve curved vents. The previous Soft Spiral cap also fits.

The previews render the actual assembled meshes. Fuzzy skin is applied during
slicing and is not shown in these previews. Physical fit and illumination have
not been tested on a printed prototype.

## Local printable files

The build creates shade-only Desert Tan and grey-blue projects, a cap project,
a three-part original stand project, and a full five-part project on two plates.
Plate 1 holds the shade and cap; plate 2 holds the original tall stand parts.
Projects use Bambu P2S / 0.4 mm nozzle / PLA Matte / 0.2 mm layers / Textured PEI,
with supports disabled. Cap prints exterior face down and locating ring up;
flip it to install. Change the filament preset when using a different material.

## Build from the original

Obtain the original all-variants 3MF from
[TriLamp by XYZilla on MakerWorld](https://makerworld.com/en/models/772090).
The original file's Standard Digital File License restricts redistribution.
Original stands and meshes containing the original mount stay local; this
repository publishes our code, independent cap, and previews.

From the repository root on macOS with Bambu Studio installed:

```sh
python3 -m venv .venv
.venv/bin/pip install numpy trimesh manifold3d scipy networkx shapely matplotlib
.venv/bin/python projects/02-trilamp-desert-tan/variants/organic-lantern/src/build_all.py '/path/to/TriLamp-AllVariants(4).3mf'
```

The build validates the mesh, compares the retained mount against the original,
checks cap interference, exports native Bambu Studio projects, and slices the
complete set. It reports slicer warnings if any occur. Files are written to
this variant's `models/` and `studio/` directories. Use `--studio` to specify
another Bambu Studio executable path.

## Validation of this revision

Both plates sliced successfully in Bambu Studio 2.08.02.61 with supports off
and no plate warnings. Shade + cap: approximately **105 g / 8 h 37 min**.
The complete set including the three original stand parts: approximately
**164 g / 12 h 8 min**. These are slicer estimates, not measured print times.
Meshes are closed solids, the retained mount matches within export precision,
and the cap has no modeled interference with the shade.
