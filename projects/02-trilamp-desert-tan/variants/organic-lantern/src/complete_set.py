"""Generate the matching cap and locally extract the three original tall stand parts.
The original source 3MF is required for stand extraction; it is not bundled.
"""
from pathlib import Path
import sys,json,zipfile,xml.etree.ElementTree as E
import numpy as np,trimesh,manifold3d as M
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parents[1]
sys.path.insert(0,str(BASE/'src'))
import prepare_studio
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'

def to_mesh(s):
 a=s.to_mesh64();m=trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts)
 assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
 return m

def cap():
 edge=[(41.5+np.cos(a),1+np.sin(a)) for a in np.linspace(-np.pi/2,np.pi/2,25)]
 roof=M.Manifold.revolve(M.CrossSection([[(0,0)]+edge+[(0,2)]]),256)
 plug=M.Manifold.revolve(M.CrossSection([[(39.55,1.8),(40.95,1.8),(40.95,5.4),(40.55,6),(39.55,6)]]),256)
 vents=[]
 for radius in (24,33):
  r=1.2;half=np.radians(25)
  # Annular capsule with rounded endpoints, 2.4 mm wide and 50 degree arc.
  pts=[]
  for a in np.linspace(-half,half,49):pts.append(((radius+r)*np.cos(a),(radius+r)*np.sin(a)))
  center=np.array([radius*np.cos(half),radius*np.sin(half)])
  for a in np.linspace(half,half+np.pi,17):pts.append(tuple(center+r*np.array([np.cos(a),np.sin(a)])))
  for a in np.linspace(half,-half,49):pts.append(((radius-r)*np.cos(a),(radius-r)*np.sin(a)))
  center=np.array([radius*np.cos(-half),radius*np.sin(-half)])
  for a in np.linspace(-half+np.pi,-half+2*np.pi,17):pts.append(tuple(center+r*np.array([np.cos(a),np.sin(a)])))
  cutter=M.Manifold.extrude(M.CrossSection([pts]),4).translate((0,0,-1))
  for angle in range(0,360,60):vents.append(cutter.rotate((0,0,angle)))
 result=M.Manifold.batch_boolean([roof+plug]+vents,M.OpType.Subtract)
 m=to_mesh(result);m.export(ROOT/'models/cap.stl')
 report={'watertight':True,'components':1,'bounds_mm':m.bounds.tolist(),'volume_mm3':m.volume,
  'insert_outer_diameter_mm':81.9,'insert_height_mm':4,'roof_height_mm':2,
  'nominal_min_radial_clearance_mm':41.3*np.cos(np.pi/192)-40.95,
  'vent_count':12,'vent_width_mm':2.4,'print_orientation':'Exterior face down; locating ring up'}
 if (ROOT/'models/shade.stl').exists():
  shade=trimesh.load_mesh(ROOT/'models/shade.stl')
  shade_s=M.Manifold(M.Mesh64(np.asarray(shade.vertices,dtype=np.float64),np.asarray(shade.faces,dtype=np.uint64)))
  installed=result.rotate((180,0,0)).translate((0,0,212))
  interference=(installed^shade_s).volume();assert abs(interference)<1e-5
  report['assembled_cap_shade_interference_mm3']=interference
 else:
  report['assembled_cap_shade_interference_mm3']=None
 (ROOT/'cap-validation.json').write_text(json.dumps(report,indent=2))
 print('Cap',report)

def extract_stands(source):
 specs=[('stand_tall','3D/Objects/object_2.model',False),('stand_base','3D/Objects/object_4.model',True),('stand_collar','3D/Objects/object_6.model',False)]
 report=[]
 with zipfile.ZipFile(source) as z:
  for name,path,flip in specs:
   root=E.fromstring(z.read(path))
   v=np.array([[float(p.get(k)) for k in ('x','y','z')] for p in root.iter('{'+NS+'}vertex')])
   f=np.array([[int(p.get(k)) for k in ('v1','v2','v3')] for p in root.iter('{'+NS+'}triangle')])
   if flip:v[:,1:]*=-1
   v[:,:2]-=(v[:,:2].min(0)+v[:,:2].max(0))/2;v[:,2]-=v[:,2].min()
   m=trimesh.Trimesh(v,f)
   assert m.is_watertight and m.is_winding_consistent
   m.export(ROOT/'models'/f'{name}.stl')
   report.append({'name':name,'original_mesh':path,'bounds_mm':m.bounds.tolist(),'watertight':True,'faces':len(m.faces),'rotation_x_degrees':180 if flip else 0})
 (ROOT/'stands-validation.json').write_text(json.dumps(report,indent=2));print('Stands',report)

def package():
 prepare_studio.ROOT=ROOT
 prepare_studio.package('TriLamp_Organic_Lantern_Cap_P2S.3mf',['cap'],[(128,128)],title='Organic Lantern — matching vented cap',description='Independently designed removable cap with curved vents for the Organic Lantern shade.')
 prepare_studio.package('TriLamp_Original_Tall_Stands_P2S.3mf',['stand_tall','stand_base','stand_collar'],[(162,101),(68,120),(115,211)],fuzz=False,title='TriLamp original tall stand — three parts',description='Original TriLamp stand parts by XYZilla, extracted from the user-supplied source for personal use.')
 prepare_studio.package('TriLamp_Organic_Lantern_Full_Set_P2S.3mf',['shade','cap','stand_tall','stand_base','stand_collar'],[(73,128),(178,128),(469.2,101),(375.2,120),(422.2,211)],plate_ids=[1,1,2,2,2],title='Organic Lantern — full tall lamp set',description='Organic Lantern shade and matching cap, plus original TriLamp tall stand parts by XYZilla. Personal local set.')

if __name__=='__main__':
 cap()
 if len(sys.argv)>1:
  extract_stands(Path(sys.argv[1]));package()
 else:
  prepare_studio.ROOT=ROOT
  prepare_studio.package('TriLamp_Organic_Lantern_Cap_P2S.3mf',['cap'],[(128,128)],title='Organic Lantern — matching vented cap',description='Independently designed removable cap with curved vents for the Organic Lantern shade.')
