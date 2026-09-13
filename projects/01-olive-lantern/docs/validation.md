# Validation record

Original sections generated September 12, 2026; cap added and all meshes
regenerated and checked September 13, 2026.

- All six binary STLs have the expected record lengths.
- All six generated meshes have nondegenerate triangles, closed manifold
  edges, consistent winding, positive volume, and dimensions below the P2S's
  nominal 256 mm limits. Detailed output: `mesh-report.json`.
- Full-size parts: 243.6 × 243.6 × 216 mm base and middle; top height 210 mm.
- Default assembly: one base, five middles, one top; 1470 mm tall with seated
  shoulders. Modeled material volume: 1303.3 cm³ before slicer adjustments.
- Separate cap: Ø224 × 9.2 mm, printed face-down and flipped for assembly;
  seated assembly height 1473.2 mm. Its collar has 0.35 mm radial clearance
  at the receiving rim and 6 mm engagement. The Ø60 mm vent remains open.
  The cap has not been slicer- or physically validated; its intended print
  orientation places the full annular roof on the bed and needs no roof bridge.
- Base geometry was sliced by the installed Bambu Studio 2.8.2.61 CLI with
  resolved P2S 0.4 mm and PETG Translucent profiles, 0.20 mm layers, 3 walls,
  zero sparse infill, Arachne, a 3 mm outer brim, and 40 mm/s outer walls.
  It returned success and produced layer statistics. Fuzzy skin was off for
  this geometry trial; the documented height masking remains a GUI setup step.
- The CLI emitted `Invalid T command (T65535)` while processing the machine
  profile. Consequently this is not a qualified machine-code export, and no
  G-code is supplied. Slice the STLs in the GUI with your selected machine and
  filament profile and inspect the preview before printing.
- No physical print, thermal, stability, or lamp fit validation has been done.
  The short rings and then the base are the intended first physical trials.

The initial CLI attempt loaded unresolved inherited profiles, defaulted to a
200 mm bed, and rejected placement. A second run resolved the installed profile
inheritance and used the correct 256 mm bed. The original failure was a CLI
profile-loading problem, not a mesh-size result.
