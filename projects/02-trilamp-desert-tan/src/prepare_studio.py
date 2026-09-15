#!/usr/bin/env python3
"""Package meshes with locally installed Bambu P2S/PLA Matte presets."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as E
import trimesh
ROOT=Path(__file__).resolve().parents[1]
PROFILES=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
E.register_namespace('',NS)

def resolve(kind,name):
 d=json.loads((PROFILES/kind/(name+'.json')).read_text());out={}
 if d.get('inherits'):out.update(resolve(kind,d['inherits']))
 for inc in d.get('include',[]):out.update(resolve(kind,inc))
 out.update(d)
 for k in ['inherits','include']:out.pop(k,None)
 return out

def settings():
 s={}
 for kind,name in [('machine','Bambu Lab P2S 0.4 nozzle'),('process','0.20mm Standard @BBL P2S'),('filament','Bambu PLA Matte @BBL P2S')]:
  d=resolve(kind,name)
  for k in ['type','name','from','setting_id','instantiation','description','compatible_printers','filament_id']:d.pop(k,None)
  s.update(d)
 s.update(printer_settings_id='Bambu Lab P2S 0.4 nozzle',print_settings_id='TriLamp Desert Tan 0.20mm',
  filament_settings_id=['Bambu PLA Matte @BBL P2S'],filament_ids=['GFA01'],filament_colour=['#E8DBB7'],
  filament_self_index=['1','1','1'],filament_type=['PLA'],filament_vendor=['Bambu Lab'],filament_is_support=['0'],
  layer_height='0.2',initial_layer_print_height='0.2',spiral_mode='0',wall_loops='3',
  wall_generator='arachne',outer_wall_line_width='0.42',inner_wall_line_width='0.45',
  sparse_infill_density='15%',top_shell_layers='5',bottom_shell_layers='5',
  fuzzy_skin='none',fuzzy_skin_thickness='0.12',fuzzy_skin_point_distance='0.4',
  brim_type='outer_only',brim_width='4',brim_object_gap='0.15',enable_support='0',
  enable_prime_tower='0',curr_bed_type='Textured PEI Plate',seam_position='back',
  outer_wall_speed=['35']*3,inner_wall_speed=['60']*3,bridge_speed=['25']*3,
  outer_wall_acceleration=['1000']*3,initial_layer_speed=['25']*3,
  first_x_layer_fan_speed=['1'],additional_cooling_fan_speed=['0'],reduce_crossing_wall='1')
 return s

def package(filename,names,positions,fuzz=True,title=None,description=None,plate_ids=None):
 model=E.Element(f'{{{NS}}}model',unit='millimeter')
 E.SubElement(model,f'{{{NS}}}metadata',name='Application').text='BambuStudio-02.08.02.61'
 E.SubElement(model,f'{{{NS}}}metadata',name='BambuStudio:3mfVersion').text='1'
 E.SubElement(model,f'{{{NS}}}metadata',name='Title').text=title or 'TriLamp Desert Tan — tall vertical rounds replacement shade'
 E.SubElement(model,f'{{{NS}}}metadata',name='Description').text=description or 'Personal adaptation of TriLamp by XYZilla, MakerWorld model 772090. Original mounting geometry retained. Perforated replacement shade.'
 resources=E.SubElement(model,f'{{{NS}}}resources');build=E.SubElement(model,f'{{{NS}}}build')
 cfg=E.Element('config')
 plate_ids=plate_ids or [1]*len(names)
 assert len(plate_ids)==len(names)
 plates={}
 for pid in sorted(set(plate_ids)):
  plate=E.SubElement(cfg,'plate');plates[pid]=plate
  E.SubElement(plate,'metadata',key='plater_id',value=str(pid))
  E.SubElement(plate,'metadata',key='plater_name',value=('Shade and cap' if pid==1 else 'Original tall stand') if len(set(plate_ids))>1 else (title or 'TriLamp'))
 ranges=E.Element('objects')
 for i,(name,(x,y)) in enumerate(zip(names,positions),1):
  m=trimesh.load_mesh(ROOT/'models'/f'{name}.stl')
  obj=E.SubElement(resources,f'{{{NS}}}object',id=str(i),type='model',name=name)
  mesh=E.SubElement(obj,f'{{{NS}}}mesh');vs=E.SubElement(mesh,f'{{{NS}}}vertices');ts=E.SubElement(mesh,f'{{{NS}}}triangles')
  for v in m.vertices:E.SubElement(vs,f'{{{NS}}}vertex',**{k:f'{a:.6f}' for k,a in zip(('x','y','z'),v)})
  for f in m.faces:E.SubElement(ts,f'{{{NS}}}triangle',**{k:str(a) for k,a in zip(('v1','v2','v3'),f)})
  E.SubElement(build,f'{{{NS}}}item',objectid=str(i),transform=f'1 0 0 0 1 0 0 0 1 {x} {y} 0',printable='1')
  o=E.SubElement(cfg,'object',id=str(i))
  E.SubElement(o,'metadata',key='name',value=name)
  E.SubElement(o,'metadata',key='extruder',value='1')
  E.SubElement(o,'metadata',face_count=str(len(m.faces)))
  part=E.SubElement(o,'part',id=str(i),subtype='normal_part')
  E.SubElement(part,'metadata',key='name',value=name)
  E.SubElement(part,'metadata',key='matrix',value='1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
  plate=plates[plate_ids[i-1]]
  instance=E.SubElement(plate,'model_instance')
  for k,v in [('object_id',str(i)),('instance_id','0'),('identify_id',str(i))]:E.SubElement(instance,'metadata',key=k,value=v)
  if fuzz and name in ('shade','cap'):
   o=E.SubElement(ranges,'object',id=str(i))
   r=E.SubElement(o,'range',min_z='14' if name=='shade' else '0',max_z='203' if name=='shade' else '1.8')
   for k,v in [('layer_height','0.2'),('fuzzy_skin','external'),('fuzzy_skin_thickness','0.12'),('fuzzy_skin_point_distance','0.4')]:E.SubElement(r,'option',opt_key=k).text=v
 payload={'3D/3dmodel.model':E.tostring(model,encoding='utf-8',xml_declaration=True),
 'Metadata/model_settings.config':E.tostring(cfg,encoding='utf-8',xml_declaration=True),
 'Metadata/project_settings.config':json.dumps(settings(),indent=2),
 '[Content_Types].xml':'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>',
 '_rels/.rels':'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'}
 if fuzz:payload['Metadata/layer_config_ranges.xml']=E.tostring(ranges,encoding='utf-8',xml_declaration=True)
 with zipfile.ZipFile(ROOT/'studio'/filename,'w',zipfile.ZIP_DEFLATED) as z:
  for n,b in payload.items():z.writestr(n,b)
 print(ROOT/'studio'/filename)

if __name__=='__main__':
 package('TriLamp_Shade_Only_P2S.3mf',['shade'],[(128,128)])
 package('TriLamp_Fit_Checks_P2S.3mf',['mount_fit','cap_fit_ring','cap'],[(60,65),(160,65),(110,165)],fuzz=False)
