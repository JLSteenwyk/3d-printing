#!/usr/bin/env python3
"""Personal TriLamp adaptation. Requires numpy, trimesh, manifold3d, scipy, shapely.
Original tall Vertical Rounds mesh is read from the user's supplied 3MF.
"""
from pathlib import Path
import argparse, json, hashlib, zipfile, xml.etree.ElementTree as E
import numpy as np
import trimesh
import manifold3d as M
ROOT=Path(__file__).resolve().parents[1]
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
P=dict(height=210,columns=24,rows=9,slot_width=5.2,slot_height=17.2,row_pitch=20,
       first_center=26,cap_roof=2,cap_insert=4,cap_insert_radius=39.65,
       cap_insert_inner_radius=38.25,fuzzy_thickness=.12,fuzzy_point_distance=.4)

def read_source(path):
 with zipfile.ZipFile(path) as z:
  root=E.fromstring(z.read('3D/Objects/object_9.model'))
  v=np.array([[float(p.get(k)) for k in ('x','y','z')] for p in root.iter(f'{{{NS}}}vertex')])
  f=np.array([[int(p.get(k)) for k in ('v1','v2','v3')] for p in root.iter(f'{{{NS}}}triangle')])
 v[:,2]+=105
 return trimesh.Trimesh(v,f)

def solid(mesh):
 s=M.Manifold(M.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
 assert s.status()==M.Error.NoError,s.status()
 return s

def mesh(s):
 assert s.status()==M.Error.NoError,s.status()
 m=s.to_mesh();return trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts)

def profile(points):return M.CrossSection([points])

def build(source):
 original=read_source(source);base=solid(original)
 # Pointed ends close at 45 degrees; all cuts start well above the mounting seat.
 w=P['slot_width']/2;h=P['slot_height']/2
 slot=M.Manifold.extrude(profile([(0,-h),(w,-h+w),(w,h-w),(0,h),(-w,h-w),(-w,-h+w)]),8)
 # Cross-section coordinates become tangent and height; extrusion becomes radial.
 slot=slot.rotate((90,0,0)).translate((0,45,0))
 cuts=[]
 for col in range(P['columns']):
  for row in range(P['rows']):
   z=P['first_center']+P['row_pitch']*row+(4 if col%2 else 0)
   cuts.append(slot.translate((0,0,z)).rotate((0,0,360*col/P['columns'])))
 shade=M.Manifold.batch_boolean([base]+cuts,M.OpType.Subtract)
 # Preserve the exact rounded outer silhouette for the cap's roof.
 contours=original.section([0,0,1],[0,0,209]).discrete
 outer=max(contours,key=lambda q:np.linalg.norm(q[:,:2],axis=1).mean())[:,:2]
 from shapely.geometry import Polygon
 from shapely.geometry.polygon import orient
 outline=np.asarray(orient(Polygon(outer).simplify(.012,preserve_topology=True),sign=1).exterior.coords)[:-1]
 roof=M.Manifold.extrude(profile(outline.tolist()),2)
 # Cap prints exterior face down. Lead-in taper is on the last 0.6 mm of the plug.
 ring=M.Manifold.revolve(profile([(38.25,1.8),(39.65,1.8),(39.65,5.4),(39.25,6),(38.25,6)]),240)
 cap=roof+ring
 vents=[]
 for angle in range(0,360,30):
  vents.append(M.Manifold.cube((3,18,4)).translate((-1.5,17,-1)).rotate((0,0,angle)))
 cap=M.Manifold.batch_boolean([cap]+vents,M.OpType.Subtract)
 bottom_box=M.Manifold.cube((100,100,12)).translate((-50,-50,0))
 bottom=base^bottom_box
 top_box=M.Manifold.cube((100,100,6)).translate((-50,-50,204))
 top=(shade^top_box).translate((0,0,-204))
 # Exact material agreement in the original mounting region; cap has no interference.
 mounting_delta=(shade^bottom_box)-bottom
 cap_assembled=cap.rotate((180,0,0)).translate((0,0,212))
 interference=shade^cap_assembled
 assert abs(mounting_delta.volume())<1e-5
 assert abs((bottom-(shade^bottom_box)).volume())<1e-5
 assert abs(interference.volume())<1e-5
 objects={'shade':shade,'cap':cap,'mount_fit':bottom,'cap_fit_ring':top}
 report={'parameters':P,'source':str(source),'source_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),
         'original_designer':'XYZilla','source_model':'https://makerworld.com/en/models/772090',
         'mount_region_symmetric_difference_mm3':0,'cap_interference_mm3':interference.volume(),
         'cap_min_nominal_radial_clearance_mm':40.00437632015446-39.65,
         'approx_projected_open_fraction_pattern_region':P['columns']*(P['slot_width']*P['slot_height']-P['slot_width']**2/2)/(2*np.pi*41.75*P['row_pitch']),
         'objects':{}}
 for name,s in objects.items():
  m=mesh(s)
  assert m.is_watertight and m.is_winding_consistent and m.volume>0
  assert len(m.split())==1
  m.export(ROOT/'models'/f'{name}.stl')
  report['objects'][name]={'bounds_mm':m.bounds.tolist(),'faces':len(m.faces),'volume_mm3':m.volume,'watertight':True,'connected_components':1}
 (ROOT/'validation.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2))
 return {k:mesh(v) for k,v in objects.items()}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);a=parser.parse_args()
 build(a.source)
