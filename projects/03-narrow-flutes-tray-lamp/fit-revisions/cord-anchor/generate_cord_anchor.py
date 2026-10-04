from pathlib import Path
import json
import numpy as np,manifold3d as md,trimesh
OUT=Path(__file__).resolve().parent

def box(w,d,h,x,y):return md.Manifold.cube((w,d,h)).translate((x-w/2,y-d/2,0))
s=box(54,10,3,0,12)+box(20,33,3,0,29)
for x in (-20,20):s-=md.Manifold.cylinder(3.2,1.7,circular_segments=64).translate((x,12,-.1))
for x in (-6,6):s-=box(3.2,10,3.2,x,35).translate((0,0,-.1))
a=s.to_mesh();m=trimesh.Trimesh(np.asarray(a.vert_properties)[:,:3],np.asarray(a.tri_verts),process=True)
assert m.is_watertight and m.is_winding_consistent and len(s.decompose())==1
m.export(OUT/'cord_anchor_plate_PETG.stl')
(OUT/'cord-anchor-validation.json').write_text(json.dumps({'units':'mm','thickness':3,'bolt_holes_mm':[[-20,12],[20,12]],'tie_slots_mm':[3.2,10],'watertight':True,'physical_fit_confirmed':False},indent=2))
print('Cord anchor mesh passed.')
