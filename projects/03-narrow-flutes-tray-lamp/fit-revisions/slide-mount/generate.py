from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET
import numpy as np,manifold3d as md,trimesh
OUT=Path(__file__).resolve().parent

def box(w,d,h,x=0,y=0,z=0):return md.Manifold.cube((w,d,h)).translate((x-w/2,y-d/2,z))
def cyl(d,h,x=0,y=0,z=0):return md.Manifold.cylinder(h,d/2,circular_segments=96).translate((x,y,z))
def three(m,path):
 ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns);t=lambda s:'{'+ns+'}'+s
 root=ET.Element(t('model'),{'unit':'millimeter'});res=ET.SubElement(root,t('resources'));obj=ET.SubElement(res,t('object'),{'id':'1','type':'model'});mesh=ET.SubElement(obj,t('mesh'));vs=ET.SubElement(mesh,t('vertices'));ts=ET.SubElement(mesh,t('triangles'))
 for v in m.vertices:ET.SubElement(vs,t('vertex'),{k:format(float(x),'.9g')for k,x in zip(['x','y','z'],v)})
 for f in m.faces:ET.SubElement(ts,t('triangle'),{k:str(int(x))for k,x in zip(['v1','v2','v3'],f)})
 ET.SubElement(ET.SubElement(root,t('build')),t('item'),{'objectid':'1'})
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED)as z:
  z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
  z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model"/></Relationships>');z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
 with zipfile.ZipFile(path)as z:assert z.testzip()is None;ET.fromstring(z.read('3D/3dmodel.model'))

def export(s,name):
 a=s.to_mesh();m=trimesh.Trimesh(np.asarray(a.vert_properties)[:,:3],np.asarray(a.tri_verts),process=True)
 assert m.is_watertight and m.is_winding_consistent and len(s.decompose())==1
 assert np.all(np.bincount(m.edges_unique_inverse)==2)
 m.export(OUT/(name+'.stl'));three(m,OUT/(name+'.3mf'));return m
# Existing bracket: X -55..30; Y +/-27; base thickness5.
# Test receiver raises base to Z3. Lateral and vertical running clearance .35/.45.
r=box(118,60.6,3,1,0,0)
for y in (-1,1):
 r+=box(89,2.5,8.45,-13.5,y*28.6,0)
 r+=box(89,4.5,2,-13.5,y*27.6,8.45)
r+=box(2.5,60.6,10.45,-56.6,0,0)
# Lateral spring cantilever: root +X, release by pushing out toward +Y.
# A relief slot isolates the leaf from the receiver floor and side wall.
r-=box(33,8,11,45,29.6,0)
r+=box(4,8,8.45,62,29.6,0)
r+=box(29,1.2,8.45,47,29.6,0)
# Catch face behind bracket front edge; diagonal nose guides insertion.
section=md.CrossSection([np.array([[30.4,25.5],[32.4,25.5],[36.4,29],[30.4,29]])])
r+=section.extrude(8.45)
r+=box(5,4,3,33,31.2,5.45)
# Floor bores allow printed pins through anchor + bracket + receiver.
for x in (-20,20):r-=cyl(3.4,3.4,x,12,-.2)
receiver=export(r,'slide_receiver_test_PETG')
# Pin: print head on bed. 11mm stack plus one mm axial release allowance.
# Split shaft bends inward through 3.4mm hole; hooks open below receiver.
pin=cyl(6,2)+cyl(3,11.4,z=1.9)
pin+=md.Manifold.cylinder(1.0,1.5,1.9,circular_segments=96).translate((0,0,12.6))
pin+=md.Manifold.cylinder(.8,1.9,1.5,circular_segments=96).translate((0,0,13.6))
pin-=box(.8,8,9,0,0,6)
pm=export(pin,'anchor_snap_pin_PETG_print_two')
# Verify assembled bracket and anchor have no static intersection with receiver.
bracket=box(85,54,5,-12.5,0,3)
assert (r^bracket).volume()<.01
report={'units':'mm','receiver_extents_mm':receiver.extents.tolist(),'bracket_width_mm':54,'bracket_thickness_mm':5,'side_clearance_mm':.35,'vertical_clearance_mm':.45,'rail_overlap_mm':1.65,'latch_deflection_estimate_mm':2,'leaf_length_mm':29,'leaf_thickness_mm':1.2,'pin_shaft_mm':3,'pin_max_hook_mm':3.8,'physical_fit_confirmed':False,'slicer_validation_completed':False,'receiver_connected_solids':1,'pin_connected_solids':1,'watertight':True,'intended_mount':'receiver integral to future lamp; existing bracket inserted later; two removable printed anchor pins','warning':'Mechanical trial only. Leaf strength, pin insertion and retention require physical testing.'}
(OUT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
