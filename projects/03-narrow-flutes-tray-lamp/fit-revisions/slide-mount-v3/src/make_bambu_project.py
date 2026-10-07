from pathlib import Path
import zipfile,json,xml.etree.ElementTree as ET
import numpy as np,trimesh
root=Path(__file__).resolve().parents[1]
out=root/'models/olive_body_slide_mount_PETG_Bambu_project.3mf'
src=root/'models/olive_body_slide_mount_PETG.3mf'
cfg=json.loads((root/'docs/official-bambu-profile-snapshot.json').read_text())
for k in ['type','name','inherits','include','from','setting_id','instantiation','description','compatible_printers','filament_id']:
 cfg.pop(k,None)
# Select the standard extruder variant, and one filament, from current official preset arrays.
for k,v in list(cfg.items()):
 if isinstance(v,list) and len(v)==3 and k not in ['printable_area','bed_exclude_area','wrapping_exclude_area']:
  cfg[k]=v[:1]
 elif isinstance(v,list) and len(v)==6 and k.startswith('machine_max_'):
  cfg[k]=v[:2]
cfg.update(printer_settings_id='Bambu Lab P2S 0.4 nozzle',print_settings_id='Lamp PETG 0.20mm localized supports',filament_settings_id=['Generic PETG @BBL P2S'],filament_ids=['GFG99'],filament_colour=['#78824B'],filament_type=['PETG'],nozzle_diameter=['0.4'],printer_model='Bambu Lab P2S',printer_variant='0.4',layer_height='0.2',initial_layer_print_height='0.2',wall_loops='3',top_shell_layers='5',bottom_shell_layers='4',sparse_infill_density='15%',sparse_infill_pattern='gyroid',enable_support='1',support_type='normal(manual)',support_style='grid',support_on_build_plate_only='1',support_top_z_distance='0.2',support_bottom_z_distance='0.2',support_object_xy_distance='0.35',support_interface_top_layers='2',support_interface_spacing='0.3',support_base_pattern_spacing='2.5',support_filament='0',support_interface_filament='0',support_remove_small_overhang='0',bridge_no_support='0',brim_type='outer_only',brim_width='2',brim_object_gap='0.1',skirt_loops='0',enable_prime_tower='0',timelapse_type='0',curr_bed_type='Textured PEI Plate',seam_position='back',outer_wall_speed=['60'],inner_wall_speed=['100'],initial_layer_speed=['25'],initial_layer_infill_speed=['35'],bridge_speed=['25'],support_speed=['60'],support_interface_speed=['40'])
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
def t(s):return '{'+ns+'}'+s
with zipfile.ZipFile(src) as z:
 members={n:z.read(n) for n in z.namelist()}
m=ET.fromstring(members['3D/3dmodel.model'])
for e in m.findall(t('metadata')):m.remove(e)
for name,value in [('Application','BambuStudio-2.0.0.0'),('BambuStudio:3mfVersion','1'),('BambuStudio:FdmSupportsPaintingVersion','0'),('Title','Lamp V3 PETG — localized receiver support'),('Designer','Jacob Steenwyk / Codex'),('Description','Prepared programmatically for Bambu Studio; import and slicing not yet tested.')]:
 ET.SubElement(m,t('metadata'),{'name':name}).text=value
mesh=m.find('.//'+t('mesh'));verts=np.array([[float(e.get(k))for k in ('x','y','z')]for e in mesh.find(t('vertices'))]);tri=mesh.find(t('triangles'));faces=np.array([[int(e.get(k))for k in ('v1','v2','v3')]for e in tri]);mt=trimesh.Trimesh(verts,faces,process=False)
# Whole unsplit triangle support paint: enforcer state 1 => hex 4; blocker state 2 => hex 8.
# Paint only horizontal downward-facing surfaces at the raised receiver bottom Z=2.
points=verts[faces];cent=points.mean(axis=1)
force=(mt.face_normals[:,2]<-.99)&np.all(np.isclose(points[:,:,2],2,atol=1e-4),axis=1)&(cent[:,0]>=-58.001)&(cent[:,0]<=64.001)&(np.abs(cent[:,1])<=33.601)
assert force.sum()>0
for i,e in enumerate(tri):e.set('paint_supports','4' if force[i] else '8')
res=m.find(t('resources'));assembly=ET.SubElement(res,t('object'),{'id':'2','type':'model','name':'Olive lamp V3'});components=ET.SubElement(assembly,t('components'));ET.SubElement(components,t('component'),{'objectid':'1','transform':'1 0 0 0 1 0 0 0 1 0 0 0'})
build=m.find(t('build'));build.clear();ET.SubElement(build,t('item'),{'objectid':'2','transform':'1 0 0 0 1 0 0 0 1 128 128 0','printable':'1'})
modelcfg=ET.Element('config');obj=ET.SubElement(modelcfg,'object',{'id':'2'})
def md(parent,key,value):ET.SubElement(parent,'metadata',{'key':key,'value':str(value)})
md(obj,'name','Olive lamp V3 — PETG');md(obj,'extruder','1');part=ET.SubElement(obj,'part',{'id':'1','subtype':'normal_part'});md(part,'name','olive_body_slide_mount_PETG');md(part,'matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1');md(part,'extruder','1')
plate=ET.SubElement(modelcfg,'plate');md(plate,'plater_id','1');md(plate,'plater_name','Lamp body');md(plate,'locked','false');md(plate,'bed_type','Textured PEI Plate');instance=ET.SubElement(plate,'model_instance');md(instance,'object_id','2');md(instance,'instance_id','0');md(instance,'identify_id','1')
members['3D/3dmodel.model']=ET.tostring(m,encoding='utf-8',xml_declaration=True)
members['Metadata/model_settings.config']=ET.tostring(modelcfg,encoding='utf-8',xml_declaration=True)
members['Metadata/project_settings.config']=json.dumps(cfg,indent=2).encode()
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for name,data in members.items():z.writestr(name,data)
with zipfile.ZipFile(out)as z:
 assert z.testzip()is None
 check=ET.fromstring(z.read('3D/3dmodel.model'));v=np.array([[float(e.get(k))for k in ('x','y','z')]for e in check.findall('.//'+t('vertex'))]);f=np.array([[int(e.get(k))for k in ('v1','v2','v3')]for e in check.findall('.//'+t('triangle'))]);assert np.array_equal(f,faces)and np.array_equal(v,verts)
 assert mt.is_watertight
 loaded=json.loads(z.read('Metadata/project_settings.config'));assert loaded['enable_support']=='1'and loaded['support_type']=='normal(manual)'
 bounds=mt.bounds+np.array([128,128,0]);assert bounds[0,:2].min()>2.1 and bounds[1,:2].max()<253.9
report={'file':out.name,'mesh_unchanged':True,'watertight':True,'support_enforcer_facets':int(force.sum()),'support_enforcer_area_mm2':float(mt.area_faces[force].sum()),'support_z_mm':2,'settings_count':len(cfg),'bed_bounds_mm':bounds.tolist(),'brim_width_mm':2,'nozzle_mm':.4,'filament':'Generic PETG; awaiting exact filament confirmation','import_tested':False,'sliced':False,'source':'https://github.com/bambulab/BambuStudio','paint_encoding':'TriangleSelector serialize: ENFORCER=1 => 4; BLOCKER=2 => 8'}
(root/'docs/bambu-project-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
