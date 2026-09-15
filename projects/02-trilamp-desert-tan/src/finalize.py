"""Publish an unmodified native Studio export after validating desktop invariants.

Input is the unsliced export generated with --export-3mf into
/tmp/trilamp-shade-project. The separately sliced copy stays in /tmp.
"""
from pathlib import Path
import json,shutil,zipfile,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/tmp/trilamp-shade-project/TriLamp_Shade_Only_P2S.3mf')

def validate(path):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  s=json.loads(z.read('Metadata/project_settings.config'))
  # Desktop PresetBundle::load_config_file_config requires these arrays to match.
  assert len(s['filament_self_index'])==len(s['filament_extruder_variant'])==3
  assert s['filament_self_index']==['1','1','1']
  assert s['filament_colour']==['#E8DBB7'] and s['filament_type']==['PLA']
  assert s['spiral_mode']=='0'
  ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
  model=E.fromstring(z.read('3D/3dmodel.model'))
  assert len(model.findall('m:build/m:item',ns))==1
  r=E.fromstring(z.read('Metadata/layer_config_ranges.xml'))
  assert len(r.findall('object'))==1
  assert r.find('.//option[@opt_key="fuzzy_skin"]').text=='external'
  assert not any(n.endswith('.gcode') for n in z.namelist())

if __name__=='__main__':
 validate(SOURCE)
 for name in ['TriLamp_Shade_Only_P2S.3mf','TriLamp_Desert_Tan_P2S.3mf']:
  shutil.copy2(SOURCE,ROOT/'studio'/name)
 r=json.loads(Path('/tmp/trilamp-shade-only/result.json').read_text())
 assert r['return_code']==0
 (ROOT/'shade-only-validation.json').write_text(json.dumps(r,indent=2))
