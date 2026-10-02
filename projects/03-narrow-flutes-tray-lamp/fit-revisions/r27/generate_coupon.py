"""Revised trial coupon: inner tray corner R27 mm; original exterior retained."""
from pathlib import Path
import json, math
import numpy as np
import manifold3d as md
import trimesh

OUT=Path(__file__).resolve().parent
W,D=240.03,200.66
CW,CD=W+1.2,D+1.2
OW,OD=CW+6,CD+6
OR=18.6
CR=27.6

def cs(w,d,r):
    pts=[]
    for cx,cy,a in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)]:
        for t in np.linspace(math.radians(a),math.radians(a+90),max(24,math.ceil(r*math.pi/2/.3)),endpoint=True):
            pts.append((cx+r*math.cos(t),cy+r*math.sin(t)))
    return md.CrossSection([pts])

def box(w,d,h,x,y,z):
    return md.Manifold.cube((w,d,h)).translate((x-w/2,y-d/2,z))

def extrude(s,z0,z1):return s.extrude(z1-z0).translate((0,0,z0))
outer=cs(OW,OD,OR)
pocket=cs(CW,CD,CR)
hole=cs(CW-8,CD-8,CR-4)
solid=extrude(outer-hole,0,2)+extrude(outer,2,10)
solid-=extrude(pocket,1.98,8.8)+pocket.extrude(1.22,scale_top=((CW+.8)/CW,(CD+.8)/CD)).translate((0,0,8.8))
solid=solid ^ box(80,80,11,OW/2-40,OD/2-40,0)
solid=solid.translate((-OW/2+80,-OD/2+80,0))
a=solid.to_mesh()
m=trimesh.Trimesh(np.asarray(a.vert_properties)[:,:3],np.asarray(a.tri_verts),process=True)
m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
assert m.is_watertight and m.is_winding_consistent and m.volume>0
assert len(solid.decompose())==1
path=OUT/'tray_corner_coupon_R27.stl'
m.export(path)
check=trimesh.load(path,force='mesh')
assert check.is_watertight and check.is_winding_consistent
report={'units':'mm','trial_tray_corner_radius':27,'pocket_corner_radius':CR,'side_clearance':.6,'original_exterior_corner_radius':OR,'extents_mm':check.extents.tolist(),'watertight':bool(check.is_watertight),'connected_solids':1,'expected_diagonal_gap_reduction_mm':12*(math.sqrt(2)-1),'physical_fit_confirmed':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
