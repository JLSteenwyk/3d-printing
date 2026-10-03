from pathlib import Path
import json
import numpy as np
import manifold3d as md
import trimesh
OUT=Path(__file__).resolve().parent
# Separate rings in one STL: notch count identifies increasing hole size.
parts=[];report=[]
for i,diam in enumerate([37,38,39,40,41]):
 x=(i%3)*58;y=(i//3)*58
 ring=md.Manifold.cylinder(3,26,circular_segments=128)-md.Manifold.cylinder(3.2,diam/2,circular_segments=128).translate((0,0,-.1))
 for j in range(i+1):
  cutter=md.Manifold.cube((1.8,5,3.4)).translate(((j-i/2)*3-0.9,23,-.2))
  ring-=cutter
 ring=ring.translate((x+26,y+26,0));parts.append(ring)
 report.append({'notches':i+1,'hole_diameter_mm':diam,'thickness_mm':3})
solid=md.Manifold.batch_boolean(parts,md.OpType.Add)
a=solid.to_mesh();m=trimesh.Trimesh(np.asarray(a.vert_properties)[:,:3],np.asarray(a.tri_verts),process=True)
assert m.is_watertight and m.is_winding_consistent
assert len(solid.decompose())==5
p=OUT/'socket_hole_fit_gauge_37-41mm.stl';m.export(p)
c=trimesh.load(p,force='mesh');assert c.is_watertight and c.is_winding_consistent
(OUT/'validation.json').write_text(json.dumps({'units':'mm','rings':report,'extents_mm':c.extents.tolist(),'watertight':True,'separate_test_rings':5,'purpose':'Unpowered mechanical fit gauge, not final socket mount'},indent=2))
(OUT/'instructions.txt').write_text('Print flat in PETG at 100% scale, using the intended bracket print settings.\nOne STL contains five separate 3 mm thick test rings.\n1 notch = 37 mm hole; 2 = 38; 3 = 39; 4 = 40; 5 = 41.\nWith the cord unplugged, remove its retaining ring and slide each test ring over the OUTSIDE socket threads. Do not insert a test ring into the electrical opening.\nChoose the smallest hole that slides on freely without threading or force. Screw the original retaining ring back on and check that it clamps the test ring securely against the socket shoulder. Tell us the notch count that works.\nIf all holes are too small or too large, report that rather than forcing a fit.\nThis gauge does not validate the final bracket, heat behavior or cord restraint.\n')
print(json.dumps(report));print(c.extents)
