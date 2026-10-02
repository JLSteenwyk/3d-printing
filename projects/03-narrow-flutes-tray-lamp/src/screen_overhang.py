"""Optional geometric overhang screening; this is not a slicer or toolpath check."""
from pathlib import Path
import json
import runpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
namespace = runpy.run_path(str(ROOT / "src" / "generate.py"))
body = namespace["body"]
previous = body.slice(0.1)
overhangs = []
for z in np.arange(0.3, 152, 0.2):
    current = body.slice(float(z))
    area = (current - previous.offset(0.25)).area()
    if area > 0.01:
        overhangs.append((round(float(z), 2), round(float(area), 4)))
    previous = current

report = {
    "method": "760 horizontal sections at 0.2 mm pitch; current material compared with previous section expanded 0.25 mm",
    "meaning": "geometric overhang screening, not toolpaths or a slicer validation",
    "layers_with_excess_area": len(overhangs),
    "worst_layers": sorted(overhangs, key=lambda entry: entry[1], reverse=True)[:20],
}
(ROOT / "docs" / "overhang-screen.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
