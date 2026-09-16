"""Build the complete local lamp set from a separately downloaded original 3MF."""
from pathlib import Path
import argparse,json,shutil,subprocess,sys,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_STUDIO='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('source',type=Path,help='Original TriLamp-AllVariants 3MF obtained from XYZilla')
 p.add_argument('--studio',default=DEFAULT_STUDIO,help='Bambu Studio executable')
 a=p.parse_args();source=a.source.expanduser().resolve()
 if not source.is_file():p.error(f'Source file missing: {source}')
 if not Path(a.studio).is_file():p.error(f'Bambu Studio executable missing: {a.studio}')
 for d in ['models','studio','previews']:(ROOT/d).mkdir(exist_ok=True)
 for name in ['generate.py','complete_set.py']:
  subprocess.run([sys.executable,str(ROOT/'src'/name),str(source)],check=True)
 names=['TriLamp_Organic_Lantern_Desert_Tan_P2S.3mf','TriLamp_Organic_Lantern_Cap_P2S.3mf','TriLamp_Original_Tall_Stands_P2S.3mf','TriLamp_Organic_Lantern_Full_Set_P2S.3mf']
 with tempfile.TemporaryDirectory(prefix='trilamp-build-') as tmp:
  work=Path(tmp)
  for i,name in enumerate(names):
   out=work/f'export-{i}';out.mkdir()
   with (out/'log.txt').open('w') as log:
    result=subprocess.run([a.studio,'--debug','1','--datadir',str(work/'data'),'--export-3mf',name,'--outputdir',str(out),str(ROOT/'studio'/name)],stdout=log,stderr=subprocess.STDOUT)
   if result.returncode:
    raise RuntimeError((out/'log.txt').read_text())
   shutil.copy2(out/name,ROOT/'studio'/name)
  out=work/'slice';out.mkdir()
  with (out/'log.txt').open('w') as log:
   result=subprocess.run([a.studio,'--debug','1','--datadir',str(work/'data'),'--slice','0','--export-3mf','check.3mf','--outputdir',str(out),str(ROOT/'studio'/names[-1])],stdout=log,stderr=subprocess.STDOUT)
  report=json.loads((out/'result.json').read_text()) if (out/'result.json').exists() else {}
  if result.returncode or report.get('return_code')!=0:raise RuntimeError((out/'log.txt').read_text())
  (ROOT/'full-set-slice-validation.json').write_text(json.dumps(report,indent=2))
  for plate in report['sliced_plates']:
   if plate.get('warning_message'):print('Slicer warning:',plate['warning_message'])
 with zipfile.ZipFile(ROOT/'studio'/names[0]) as z:d={n:z.read(n) for n in z.namelist()}
 s=json.loads(d['Metadata/project_settings.config']);s['filament_colour']=['#6F8491']
 if 'filament_multi_colour' in s:s['filament_multi_colour']=['#6F8491']
 d['Metadata/project_settings.config']=json.dumps(s,indent=2).encode()
 gray='TriLamp_Organic_Lantern_Grey_Blue_PLA_P2S.3mf'
 with zipfile.ZipFile(ROOT/'studio'/gray,'w',zipfile.ZIP_DEFLATED) as z:
  for name,content in d.items():z.writestr(name,content)
 print('Complete local files:',ROOT/'studio')
 print('Original stand meshes and source-derived shade/full-set files remain local; obtain permission before public redistribution.')

if __name__=='__main__':main()
