"""Publish native Studio exports with two display colors and shared PLA settings."""
from pathlib import Path
import sys,zipfile,json,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]/'src'))
from finalize import validate

def publish(project_dir,slice_dir):
 p=Path(project_dir)/'TriLamp_Soft_Spiral_Desert_Tan_P2S.3mf';validate(p)
 shutil.copy2(p,ROOT/'studio'/p.name)
 with zipfile.ZipFile(p) as z:d={n:z.read(n) for n in z.namelist()}
 s=json.loads(d['Metadata/project_settings.config']);s['filament_colour']=['#6F8491']
 if 'filament_multi_colour' in s:s['filament_multi_colour']=['#6F8491']
 d['Metadata/project_settings.config']=json.dumps(s,indent=2).encode()
 with zipfile.ZipFile(ROOT/'studio/TriLamp_Soft_Spiral_Grey_Blue_PLA_P2S.3mf','w',zipfile.ZIP_DEFLATED) as z:
  for n,b in d.items():z.writestr(n,b)
 r=json.loads((Path(slice_dir)/'result.json').read_text());assert r['return_code']==0
 (ROOT/'slice-validation.json').write_text(json.dumps(r,indent=2))
 print('Slice warning:',r['sliced_plates'][0]['warning_message'])
 print('Seconds:',r['sliced_plates'][0]['total_predication'])
 print('Material:',r['sliced_plates'][0]['filaments'])

if __name__=='__main__':publish(sys.argv[1],sys.argv[2])
