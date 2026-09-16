"""Bowed organic shade with gently undulating valleys; original inner mount retained."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
import manifold3d as M
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parents[1]
sys.path.insert(0,str(BASE/'src'))
# Import by filename to avoid this script's identical module name.
import importlib.util
spec=importlib.util.spec_from_file_location('original_helpers',BASE/'src/generate.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
P=dict(columns=36,rows=26,row_pitch=7.0,first_turn=2,notch_width=5.6,
       notch_height=2.0,notch_crown=.25,height=210,fold_depth=.45,belly_radius_gain=5.0,orientation='organic_lantern')

def soft_shell():
 import trimesh
 n=192;nz=420
 theta=np.arange(n)*2*np.pi/n
 z=np.linspace(0,210,nz+1)
 # Fade the folded texture into smooth end bands used for handling and seating.
 t=np.clip(np.minimum((z-12)/8,(205-z)/5),0,1)
 fade=t*t*(3-2*t)
 belly=5*np.sin(np.pi*np.clip((z-14)/189,0,1))**2
 radius=42.5+belly[:,None]-.225*fade[:,None]*(1-np.cos(2*np.pi*(z[:,None]/7.0-theta[None,:]/(2*np.pi))))
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
 # Shape the wall first; cut openings afterwards to avoid twisted slit roofs.
 bm=base.to_mesh64();v=np.array(bm.vert_properties[:,:3],copy=True)
 z=v[:,2].copy();theta=np.arctan2(v[:,1],v[:,0])
 envelope=np.sin(np.pi*np.clip((z-14)/189,0,1))**2
 radial_offset=.65*envelope*np.sin(2*theta+z/65)
 rad=np.linalg.norm(v[:,:2],axis=1)
 v[:,:2]*=(1+radial_offset/np.maximum(rad,1e-9))[:,None]
 v[:,2]+=2.3*envelope*np.sin(3*theta+z/48)+.65*envelope*np.sin(5*theta-z/71)
 base=M.Manifold(M.Mesh64(np.ascontiguousarray(v,dtype=np.float64),np.array(bm.tri_verts,dtype=np.uint64,order="C",copy=True)))
 cuts=[];areas=[];widths=[];slopes=[]
 for row in range(P['rows']):
  shift=(row*.38196601125)%1
  for col in range(P['columns']):
   # Fade the row offset to zero at the helix seam so adjoining turns
   # cannot overlap their first/last openings and form unsupported roof islands.
   frac=(col+shift*np.sin(np.pi*col/(P['columns']-1))**2)/P['columns'];angle=frac*360
   # Smoothly vary length around and along the shade, without random noise.
   w=5.1+.5*np.sin(col*1.618+row*.79);h=P['notch_height'];r=h/2
   # A convex rounded slit with one continuous roof curve. A flat-to-arch
   # join creates a downward cusp when tilted; this superellipse avoids it.
   angles=np.linspace(0,2*np.pi,65)[:-1]
   points=[]
   for a in angles:
    co,si=np.cos(a),np.sin(a)
    x=w/2*np.sign(co)*abs(co)**(2/3)
    y=(h/2+(P['notch_crown'] if si>=0 else 0))*np.sign(si)*abs(si)**(2/3)
    points.append((x,y))
   z=P['row_pitch']*(P['first_turn']+row+.75+frac)
   theta=np.pi/2+np.radians(angle)
   u=np.clip((z-14)/189,0,1);env=np.sin(np.pi*u)**2
   # Follow each valley tangentially while keeping the roof straight through the wall.
   radius=42.5+5*env
   slope=(P['row_pitch']/(2*np.pi)+env*(6.9*np.cos(3*theta+z/48)+3.25*np.cos(5*theta-z/71)))/radius
   slopes.append(float(np.degrees(np.arctan(slope))))
   points=[(x,y-slope*x) for x,y in points]
   notch=M.Manifold.extrude(M.CrossSection([points]),16).rotate((90,0,0)).translate((0,52,0))
   z+=2.3*env*np.sin(3*theta+z/48)+.65*env*np.sin(5*theta-z/71)
   cuts.append(notch.translate((0,0,z)).rotate((0,0,angle)))
   areas.append(w*(h+P['notch_crown'])*math.gamma(4/3)**2/math.gamma(5/3));widths.append(w)
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
 assert diff<.001
 final_solid=M.Manifold(M.Mesh64(np.asarray(m.vertices,dtype=np.float64),np.asarray(m.faces,dtype=np.uint64)))
 assert final_solid.status()==M.Error.NoError
 final_mount=final_solid^check
 final_diff=abs((original_mount-final_mount).volume())+abs((final_mount-original_mount).volume())
 assert final_diff<.001, final_diff
 m.export(ROOT/'models/shade.stl')
 roundtrip=trimesh.load_mesh(ROOT/'models/shade.stl')
 assert roundtrip.is_watertight and roundtrip.is_winding_consistent, 'STL precision check'
 rounded=trimesh.Trimesh(np.round(roundtrip.vertices,6),roundtrip.faces)
 assert rounded.is_watertight, '3MF precision check'
 hole_area=float(np.mean(areas))
 report=dict(parameters=P,source=str(source),source_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),
   source_designer='XYZilla',mesh_cleanup_tolerance_mm=.0002,watertight=True,consistent_winding=True,components=1,faces=len(m.faces),
   bounds_mm=m.bounds.tolist(),inner_mount_comparison_radius_mm=38.7,inner_mount_symmetric_difference_mm3=final_diff,nominal_radial_wall_thickness_mm=1.2,end_outer_diameter_mm=85,nominal_belly_diameter_mm=95,
   nominal_unwarped_projected_open_fraction_at_end_radius=P['columns']*hole_area/(2*np.pi*41.9*P['row_pitch']),
   total_projected_open_area_mm2=sum(areas),notch_width_range_mm=[min(widths),max(widths)],
   notch_count=P['columns']*P['rows'],helical_rise_per_revolution_mm=P['row_pitch'],slit_slope_degrees_range=[min(slopes),max(slopes)],volume_mm3=m.volume,
   nominal_unwarped_circumferential_gap_at_end_radius_mm=2*np.pi*41.3/P['columns']-P['notch_width'],
   nominal_vertical_gap_before_wave_shaping_mm=P['row_pitch']-P['notch_height']-P['notch_crown'])
 (ROOT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
 import prepare_studio
 prepare_studio.ROOT=ROOT
 prepare_studio.package('TriLamp_Organic_Lantern_Desert_Tan_P2S.3mf',['shade'],[(128,128)],title='TriLamp — Organic Lantern',description='Personal adaptation of TriLamp by XYZilla, MakerWorld 772090. Original inner mount; bowed silhouette and flowing shallow waves with varied capsule openings tucked into valleys. Shade only.')

if __name__=='__main__':
 build(Path(sys.argv[1]))
