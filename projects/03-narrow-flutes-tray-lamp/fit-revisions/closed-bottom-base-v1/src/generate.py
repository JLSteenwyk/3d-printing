from pathlib import Path
import math,json,zipfile,xml.etree.ElementTree as ET
import numpy as np,manifold3d as md,trimesh
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parents[1]
for folder in ('models','docs','previews'): (OUT/folder).mkdir(exist_ok=True)
def rounded(w,d,r,step=0.3):
    """CCW perimeter sampled approximately by arc length; analytic normals."""
    pts=[]; normals=[]
    def line(a,b,n):
        count=max(1,math.ceil(math.dist(a,b)/step))
        for t in np.arange(count)/count:
            pts.append(np.array(a)*(1-t)+np.array(b)*t); normals.append(n)
    def arc(c,start):
        count=max(8,math.ceil(math.pi*r/2/step))
        for theta in np.linspace(start,start+math.pi/2,count,endpoint=False):
            n=np.array([math.cos(theta),math.sin(theta)])
            pts.append(np.array(c)+r*n); normals.append(n)
    line((-w/2+r,-d/2),(w/2-r,-d/2),(0,-1))
    arc((w/2-r,-d/2+r),-math.pi/2)
    line((w/2,-d/2+r),(w/2,d/2-r),(1,0))
    arc((w/2-r,d/2-r),0)
    line((w/2-r,d/2),(-w/2+r,d/2),(0,1))
    arc((-w/2+r,d/2-r),math.pi/2)
    line((-w/2,d/2-r),(-w/2,-d/2+r),(-1,0))
    arc((-w/2+r,-d/2+r),math.pi)
    return np.array(pts),np.array(normals)

def cs(w,d,r):
    return md.CrossSection([rounded(w,d,max(.5,r),.65)[0]])

def box(w,d,h,x=0,y=0,z=0):
    return md.Manifold.cube((w,d,h)).translate((x-w/2,y-d/2,z))

def cylinder(d,h,x=0,y=0,z=0):
    return md.Manifold.cylinder(h,d/2,circular_segments=64).translate((x,y,z))

def extrude(section,z0,z1):
    return section.extrude(z1-z0).translate((0,0,z0))

def mesh(solid):
    m=solid.to_mesh()
    result=trimesh.Trimesh(np.asarray(m.vert_properties)[:,:3],
                           np.asarray(m.tri_verts),process=True)
    result.update_faces(result.nondegenerate_faces())
    result.update_faces(result.unique_faces())
    result.remove_unreferenced_vertices()
    return result


# Interface dimensions from the existing V3 lamp CAD, millimetres.
OW,OD,OR=247.23,207.86,18.6
NW,ND,NR=240.43,201.06,15.2
floor=2.4; collar_height=10.; clearance=.4
TW,TD,TR=OW+4,OD+4,OR+2
outer=cs(TW,TD,TR);inner=cs(NW+2*clearance,ND+2*clearance,NR+clearance)
# Broad, closed floor; small underside edge chamfer grows outward at 45 degrees.
bottom=cs(TW-2,TD-2,TR-1)
base=bottom.extrude(1,scale_top=(TW/(TW-2),TD/(TD-2)))
base+=extrude(outer,.98,floor)
base+=extrude(outer-inner,floor-.02,floor+collar_height)

def house_cut(width,eave,base_z,wall_depth=42):
 w=width/2
 section=md.CrossSection([np.array([[-w,0],[w,0],[w,eave],[0,eave+w],[-w,eave]])])
 return section.extrude(wall_depth).rotate((90,0,0)).translate((0,wall_depth/2,base_z))
# Align fourteen existing lower ventilation openings; leave the floor intact.
ventcuts=[]
for x in np.linspace(-91,91,8): ventcuts.append(house_cut(20,2,floor+1).translate((x,ND/2,0)))
for y in np.linspace(-65,65,6): ventcuts.append(house_cut(20,2,floor+1).rotate((0,0,90)).translate((-NW/2,y,0)))
base-=md.Manifold.batch_boolean(ventcuts,md.OpType.Add)
# Open-to-top notch lets the base seat around the existing cord.
base-=box(24,30,collar_height+.2,0,TD/2,floor)
base=base.simplify(.005)
name='bottom_base_closed_floor_v1'
m=mesh(base);m.export(OUT/'models'/(name+'.stl'))
assert m.is_watertight and m.is_winding_consistent and len(base.decompose())==1
assert np.all(m.extents<=256)
# Cheap corner coupon includes the same floor, collar and 0.4 mm running clearance.
coupon=base ^ box(65,65,20,TW/2-32.5,-TD/2+32.5,0)
cm=mesh(coupon);cm.apply_translation(-cm.bounds[0]);cm.export(OUT/'models'/'base_corner_fit_coupon_v1.stl')
assert cm.is_watertight and len(coupon.decompose())==1

def make_3mf(mesh,path,title):
 ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
 def tag(s):return '{'+ns+'}'+s
 model=ET.Element(tag('model'),{'unit':'millimeter'})
 ET.SubElement(model,tag('metadata'),{'name':'Title'}).text=title
 res=ET.SubElement(model,tag('resources'));obj=ET.SubElement(res,tag('object'),{'id':'1','type':'model'})
 mm=ET.SubElement(obj,tag('mesh'));vs=ET.SubElement(mm,tag('vertices'));ts=ET.SubElement(mm,tag('triangles'))
 for v in mesh.vertices:ET.SubElement(vs,tag('vertex'),{k:format(float(x),'.9g') for k,x in zip(('x','y','z'),v)})
 for f in mesh.faces:ET.SubElement(ts,tag('triangle'),{k:str(int(x))for k,x in zip(('v1','v2','v3'),f)})
 build=ET.SubElement(model,tag('build'));ET.SubElement(build,tag('item'),{'objectid':'1'})
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED)as z:
  z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
  z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model"/></Relationships>')
  z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
 with zipfile.ZipFile(path)as z:
  assert z.testzip()is None
  r=ET.fromstring(z.read('3D/3dmodel.model'))
  vertices=np.array([[float(v.get(k))for k in ('x','y','z')]for v in r.findall('.//'+tag('vertex'))])
  faces=np.array([[int(f.get(k))for k in ('v1','v2','v3')]for f in r.findall('.//'+tag('triangle'))])
  assert np.allclose(vertices,mesh.vertices)and np.array_equal(faces,mesh.faces)
make_3mf(m,OUT/'models'/(name+'.3mf'),'Closed-floor lamp base V1 — geometry only')
make_3mf(cm,OUT/'models'/'base_corner_fit_coupon_v1.3mf','Base corner fit coupon V1 — geometry only')
report={'extents_mm':m.extents.tolist(),'volume_cm3':float(m.volume/1000),'floor_mm':floor,'collar_height_above_floor_mm':collar_height,'side_clearance_mm':clearance,'corner_coupon_extents_mm':cm.extents.tolist(),'watertight':True,'connected_parts':1,'lower_vent_count':14,'cord_notch_width_mm':24,'geometry_only_3mf':True,'slice_verified':False,'physical_fit_verified':False,'thermal_validation_complete':False,'support_intent':'none, floor-down','lamp_height_increase_mm':floor}
(OUT/'docs'/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
