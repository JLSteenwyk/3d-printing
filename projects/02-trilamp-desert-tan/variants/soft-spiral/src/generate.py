"""Soft spiral shade with offset capsule openings in the valleys; original inner mount retained."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import manifold3d as M
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parents[1]
sys.path.insert(0,str(BASE/'src'))
# Import by filename to avoid this script's identical module name.
import importlib.util
spec=importlib.util.spec_from_file_location('original_helpers',BASE/'src/generate.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
P=dict(columns=32,rows=35,row_pitch=5.2,first_turn=3,notch_width=5.6,
       notch_height=1.6,height=210,fold_depth=.8,orientation='soft_spiral')

def soft_shell():
 import trimesh
 n=192;nz=420
 theta=np.arange(n)*2*np.pi/n
 z=np.linspace(0,210,nz+1)
 # Fade the folded texture into smooth end bands used for handling and seating.
 t=np.clip(np.minimum((z-12)/8,(205-z)/5),0,1)
 fade=t*t*(3-2*t)
 radius=42.5-.4*fade[:,None]*(1-np.cos(2*np.pi*(z[:,None]/5.2-theta[None,:]/(2*np.pi))))
 outer=np.stack([radius*np.cos(theta),radius*np.sin(theta),np.broadcast_to(z[:,None],radius.shape)],axis=2).reshape(-1,3)
 iz=np.concatenate([[0.,10.],z[z>=10]])
 ir=np.vstack([np.full((2,n),38.8),radius[z>=10]-1.2])
 inner=np.stack([ir*np.cos(theta),ir*np.sin(theta),np.broadcast_to(iz[:,None],ir.shape)],axis=2).reshape(-1,3)
 v=np.vstack([outer,inner]);off=len(outer);f=[]
 for verts_count,offset,reverse in [(len(z),0,False),(len(iz),off,True)]:
  for j in range(verts_count-1):
   for i in range(n):
    a=offset+j*n+i;b=offset+j*n+(i+1)%n;c=b+n;d=a+n
    f.extend([(a,c,b),(a,d,c)] if reverse else [(a,b,c),(a,c,d)])
 for i in range(n):
  a=i;b=(i+1)%n
  f.extend([(a,a+off,b+off),(a,b+off,b)])
  a=n*nz+i;b=n*nz+(i+1)%n;c=off+(len(iz)-1)*n+(i+1)%n;d=off+(len(iz)-1)*n+i
  f.extend([(a,b,c),(a,c,d)])
 mesh=trimesh.Trimesh(v,np.asarray(f))
 assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
 return M.Manifold(M.Mesh64(np.asarray(mesh.vertices,dtype=np.float64),np.asarray(mesh.faces,dtype=np.uint64)))

def build(source):
 original=helpers.read_source(source);original_solid=helpers.solid(original)
 tube=soft_shell()
 lowbox=M.Manifold.cube((100,100,10)).translate((-50,-50,0))
 original_bottom=original_solid^lowbox^M.Manifold.cylinder(10,39,circular_segments=192)
 base=tube+original_bottom
 w=P['notch_width'];h=P['notch_height'];r=h/2
 straight=(w-h)/2;points=[]
 for center,start in [(straight,-np.pi/2),(-straight,np.pi/2)]:
  for a in np.linspace(start,start+np.pi,17):
   points.append((center+r*np.cos(a),r*np.sin(a)))
 slope=P['row_pitch']/(2*np.pi*41.3)
 points=[(x,z-slope*x) for x,z in points]
 notch=M.Manifold.extrude(M.CrossSection([points]),8).rotate((90,0,0)).translate((0,45,0))
 cuts=[]
 for row in range(P['rows']):
  # Golden-angle fraction shifts slit ends along successive spiral turns.
  shift=(row*.38196601125)%1
  for col in range(P['columns']):
   frac=(col+shift)/P['columns']
   angle=frac*360
   # At y-positive start angle pi/2: valley phase has z/pitch - theta/tau = k + .5.
   z=P['row_pitch']*(P['first_turn']+row+.75+frac)
   cuts.append(notch.translate((0,0,z)).rotate((0,0,angle)))
 shade=M.Manifold.batch_boolean([base]+cuts,M.OpType.Subtract)
 import trimesh
 clean=shade.simplify(.0002).to_mesh64()
 # Preserve valid skinny cap triangles; area-based removal would leave holes.
 # Match STL float32 and 3MF six-decimal precision before validating.
 vertices=np.round(np.asarray(clean.vert_properties[:,:3],dtype=np.float32).astype(np.float64),6)
 m=trimesh.Trimesh(vertices,clean.tri_verts,process=True)
 f=m.faces
 m.update_faces((f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,0]!=f[:,2]))
 m.remove_unreferenced_vertices()
 print('Mesh checks',m.is_watertight,m.is_winding_consistent,len(m.faces),flush=True)
 assert m.is_watertight and m.is_winding_consistent and m.volume>0 and len(m.split())==1
 check=M.Manifold.cylinder(14,38.7,circular_segments=256)
 original_mount=original_solid^check;new_mount=shade^check
 diff=abs((original_mount-new_mount).volume())+abs((new_mount-original_mount).volume())
 assert diff<1e-5
 m.export(ROOT/'models/shade.stl')
 roundtrip=trimesh.load_mesh(ROOT/'models/shade.stl')
 assert roundtrip.is_watertight and roundtrip.is_winding_consistent, 'STL precision check'
 rounded=trimesh.Trimesh(np.round(roundtrip.vertices,6),roundtrip.faces)
 assert rounded.is_watertight, '3MF precision check'
 hole_area=(w-h)*h+np.pi*(h/2)**2
 report=dict(parameters=P,source=str(source),source_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),
   source_designer='XYZilla',mesh_cleanup_tolerance_mm=.0002,watertight=True,consistent_winding=True,components=1,faces=len(m.faces),
   bounds_mm=m.bounds.tolist(),inner_mount_comparison_radius_mm=38.7,inner_mount_symmetric_difference_mm3=diff,radial_wall_thickness_mm=1.2,nominal_outer_diameter_mm=85,
   approximate_projected_open_fraction_per_pattern_cell=P['columns']*hole_area/(2*np.pi*41.9*P['row_pitch']),
   notch_count=P['columns']*P['rows'],helical_rise_per_revolution_mm=P['row_pitch'],slit_slope_degrees=float(np.degrees(np.arctan(slope))),volume_mm3=m.volume,
   minimum_circumferential_gap_mm=2*np.pi*41.3/P['columns']-P['notch_width'],
   minimum_vertical_gap_mm=P['row_pitch']-P['notch_height'])
 (ROOT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
 import prepare_studio
 prepare_studio.ROOT=ROOT
 prepare_studio.package('TriLamp_Soft_Spiral_Desert_Tan_P2S.3mf',['shade'],[(128,128)],title='TriLamp — Soft Spiral',description='Personal adaptation of TriLamp by XYZilla, MakerWorld 772090. Original inner mount; softly rounded spiral folds with capsule openings tucked into valleys. Shade only.')

if __name__=='__main__':
 build(Path(sys.argv[1]))
