# Soft Spiral — tall shade, matching cap, and full local set

[Cap 3MF](studio/TriLamp_Soft_Spiral_Cap_P2S.3mf) ·
[Cap STL](models/cap.stl) · [Cap preview](previews/cap.png) ·
[Shade color preview](previews/colors.png)

Soft Spiral uses rounded horizontal folds and small capsule openings in their
valleys, with fine fuzzy skin for a softer finish. Desert Tan and the illustrative
muted grey-blue preview use the same geometry. The inner keyed mounting recess
is retained from the supplied tall TriLamp shade.

## Complete set

| Part | Availability |
| --- | --- |
| Soft Spiral shade | Generate locally using the original 3MF |
| Matching vented cap | Printable files linked above |
| Original tall stand, `TriLampStand.stl` | Obtain from XYZilla; extracted by the local build |
| Original stand base, `TriLampStand2.stl` | Obtain from XYZilla; extracted by the local build |
| Original collar, `TriLampStand3.stl` | Obtain from XYZilla; extracted by the local build |

The full local project has two plates: shade + cap, then the three stand parts.
All use P2S / standard 0.4 mm nozzle / PLA Matte / Textured PEI settings. The
stand geometry is unmodified; its base is flipped to match the original profile's
printing orientation. Change the stand material preset if printing it in PETG.

### Matching cap

A removable drop-in cap, independently designed for the final Soft Spiral shade:
85 mm maximum diameter, a 2 mm roof, and a 4 mm locating ring. The ring has
approximately **0.34 mm minimum radial clearance** and a tapered entry. Twelve
rounded concentric vents match the softer surface treatment. The cap is retained
by gravity, not a latch. Print exterior face down, then flip to install.

Fuzzy skin is limited to the short roof perimeter; the locating ring stays smooth.
It adds 2 mm to the assembled shade height. Geometry checks find no interference
with the shade. **Cap estimate: 15 g / 42 min.**

### Shade and colors

210 mm tall × 85 mm maximum diameter; 1.2 mm radial body wall. Spiral pitch is
5.2 mm, with 0.8 mm crest-to-valley relief. The 1,120 small openings are
5.6 × 1.6 mm, with rounded ends and offsets between turns. The repeating pattern
has approximately 20% projected open area; light passes through these openings
in opaque filament. Actual light output has not been measured.

Desert Tan display color is #E8DBB7. Grey-blue is **illustrative #6F8491**, not a
matched Bambu swatch. Both generated color files use PLA Matte settings; choose
your actual filament profile, especially for PETG or another material.

## Build the full set locally

Download the original all-variants project from
[XYZilla's TriLamp page](https://makerworld.com/en/models/772090).
The tested input is `TriLamp-AllVariants(4).3mf`, with the tall stand on plate 6.
Bambu Studio must be installed. The scripts currently resolve presets from its
standard macOS application path.

From this repository's root:

```bash
python3 -m venv .venv
.venv/bin/pip install numpy trimesh manifold3d scipy networkx shapely matplotlib
.venv/bin/python projects/02-trilamp-desert-tan/variants/soft-spiral/src/build_all.py '/path/to/TriLamp-AllVariants(4).3mf'
```

The build generates and validates these local files under this folder's `studio/`:

- `TriLamp_Soft_Spiral_Desert_Tan_P2S.3mf`
- `TriLamp_Soft_Spiral_Grey_Blue_PLA_P2S.3mf`
- `TriLamp_Soft_Spiral_Cap_P2S.3mf`
- `TriLamp_Original_Tall_Stands_P2S.3mf`
- `TriLamp_Soft_Spiral_Full_Set_P2S.3mf`

For just the independent cap, run `src/complete_set.py` without a source argument.
The cap does not require the original file. To regenerate pictures, run
`src/preview.py` and `src/preview_cap.py` after generating the meshes.

## Printing and validation

0.20 mm layers, three walls, Arachne, 15% infill, five top/bottom layers, supports
off, vase mode off, 4 mm outer brim. Outer walls 35 mm/s, inner walls 60 mm/s,
bridges 25 mm/s. PLA nozzle temperature 220 °C.

Shade fuzzy skin: External, 0.12 mm thickness / 0.40 mm point distance, Z 14–203 mm.
Cap fuzzy skin: Z 0–1.8 mm. The stand parts have fuzzy skin off. Global fuzzy skin
is None because object height ranges control it. Open a 3MF as a project to retain
these settings, then slice before printing.

The two-plate set sliced in Bambu Studio 2.08.02.61 with return code 0, supports
off, and no plate warnings. **Full-set estimate: 159 g / 11 h 52 min.**
Physical fit, print finish, and operating temperature remain untested. Use the
original LED-001 setup and keep cap vents clear.

[Cap geometry checks](cap-validation.json) ·
[Cap slicing results](cap-slice-validation.json) ·
[Full-set slicing results](full-set-slice-validation.json)

## Publication and attribution

Original **TriLamp by XYZilla**, MakerWorld model 772090. The supplied 3MF identifies
its Standard Digital File License. The original stand meshes, source-derived shade
meshes, and full-set 3MF are not mirrored in this public repository; obtain separate
permission before redistributing them. Git ignores those local generated files.
Our code, independently designed cap, previews, and reports are included here.
