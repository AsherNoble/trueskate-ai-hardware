#!/usr/bin/env python3
"""JLC upload BOM/CPL for the six SMT encoders only; native board is read-only.

Main: ordinary Python. --collect-native: KiCad Python. No uploads/orders.
"""
from pathlib import Path
import csv,json,sys,subprocess,hashlib,math,os
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'design/trueskate-main-v1.kicad_pcb'
OUT=ROOT/'manufacturing';CHECKS=OUT/'validation';STEM='trueskate-main-v1'
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
KPY='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
REFERENCES={f'J{i}'for i in range(31,37)}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def collect():
 import pcbnew as k
 b=k.LoadBoard(str(PCB));rows=[]
 for f in b.GetFootprints():
  if f.GetReference()not in REFERENCES:continue
  assert f.GetAttributes() & k.FP_SMD and not f.IsFlipped()
  rows.append(dict(ref=f.GetReference(),x_mm=k.ToMM(f.GetPosition().x),y_mm=k.ToMM(f.GetPosition().y),rotation_deg=f.GetOrientationDegrees()%360,footprint=str(f.GetFPID().GetLibItemName()),value=f.GetValue(),pads=[dict(number=p.GetNumber(),net=p.GetNetname(),x_mm=k.ToMM(p.GetPosition().x),y_mm=k.ToMM(p.GetPosition().y))for p in f.Pads()]))
 print(json.dumps(sorted(rows,key=lambda r:r['ref'])))
def export_jst():
 before=digest(PCB);CHECKS.mkdir(exist_ok=True)
 decisions=json.loads((ROOT/'sources/prototype-decisions.json').read_text());selection=decisions['assembly']
 assert selection.get('mode')=='bare-pcb' or set(selection['references'])==REFERENCES
 with (ROOT/'bom/bom-review.csv').open(newline='')as f:parts=[p for p in csv.DictReader(f)if p['Reference']in REFERENCES]
 assert {p['Reference']for p in parts}==REFERENCES and len(parts)==6
 assert all(p['LCSC']==selection['lcsc']and p['Quantity']=='1'for p in parts)
 native=json.loads(subprocess.check_output([KPY,str(Path(__file__).resolve()),'--collect-native'],text=True))
 (CHECKS/'assembly-native.json').write_text(json.dumps(native,indent=2)+'\n')
 raw=CHECKS/'native-positions.csv'
 subprocess.run([CLI,'pcb','export','pos','--side','front','--format','csv','--units','mm','--smd-only','--exclude-dnp','--output',str(raw),str(PCB)],check=True)
 with raw.open(newline='')as f:positions=list(csv.DictReader(f))
 assert {p['Ref']for p in positions}==REFERENCES and len(positions)==6
 byref={r['ref']:r for r in native};placements=[]
 for row in sorted(positions,key=lambda p:p['Ref']):
  n=byref[row['Ref']];x,y,angle=float(row['PosX']),float(row['PosY']),float(row['Rot'])%360
  assert abs(x-n['x_mm'])<1e-6 and abs(y+n['y_mm'])<1e-6,'CPL must share the absolute Gerber/Excellon origin'
  assert abs(angle-n['rotation_deg'])<1e-6 and row['Side'].lower()=='top'
  assert {p['number']for p in n['pads']}=={'1','2','3','4','5','6','MP'}
  assert n['value']=='SM06B-SRSS-TB'
  bank='upper'if n['ref']in('J32','J33','J35')else 'lower'
  assert angle==(180 if bank=='upper'else 0)
  assert abs(n['y_mm']-(3.3 if bank=='upper'else 136.7))<1e-6
  pin1=next(p for p in n['pads']if p['number']=='1')
  placements.append(dict(designator=n['ref'],mid_x_mm=x,mid_y_mm=y,rotation_deg=angle,layer='Top',bank=bank,opening='outward / carrier -Y'if bank=='upper'else 'outward / carrier +Y',pin1_gerber_mm=[pin1['x_mm'],-pin1['y_mm']]))
 bom=OUT/(STEM+'-JLCPCB-BOM.csv');cpl=OUT/(STEM+'-JLCPCB-CPL.csv')
 with bom.open('w',newline='')as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['Comment','Designator','Footprint','LCSC Part #'])
  w.writerow([selection['mpn'],','.join(sorted(REFERENCES)),'JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal',selection['lcsc']])
 with cpl.open('w',newline='')as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['Designator','Mid X','Mid Y','Rotation','Layer'])
  for p in placements:w.writerow([p['designator'],f"{p['mid_x_mm']:.4f}",f"{p['mid_y_mm']:.4f}",f"{p['rotation_deg']:g}",p['layer']])
 # Independent CSV readback and count checks.
 with bom.open(newline='')as f:out_bom=list(csv.DictReader(f))
 with cpl.open(newline='')as f:out_cpl=list(csv.DictReader(f))
 assert len(out_bom)==1 and set(out_bom[0]['Designator'].split(','))==REFERENCES
 assert {p['Designator']for p in out_cpl}==REFERENCES and len(out_cpl)==6
 assert all(p['Layer']=='Top'for p in out_cpl)
 assert digest(PCB)==before,'Assembly export must not modify the board'
 report=dict(source_pcb_sha256=before,assembly_references=sorted(REFERENCES),parts_per_board=6,grouped_bom_rows=1,cpl_rows=6,manufacturer=selection['manufacturer'],mpn=selection['mpn'],lcsc=selection['lcsc'],supplier_code_note='C160405 replaces out-of-stock C7588156; same six-pin side-entry JST SH connector, lead-free/tin version; no footprint/placement changes',coordinate_reference='Absolute Gerber/Excellon origin; X right, Y up (native KiCad Y negated); mm; CCW-positive degrees',rotation_reference='Native KiCad placement, no undocumented rotation offset; 0deg mouth toward carrier +Y, 180deg toward -Y',physical_openings_verified='Upper J32/J33/J35 and lower J31/J34/J36 all face outward',placements=placements,files_sha256={bom.name:digest(bom),cpl.name:digest(cpl)},sources=['https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad','https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly','https://jlcpcb.com/partdetail/C160405'],uploaded=False,order_placed=False)
 (CHECKS/'assembly-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 manifest=OUT/'manifest.json'
 if manifest.exists():
  data=json.loads(manifest.read_text());assert data['source_pcb_sha256']==before
  data['assembly']=report;manifest.write_text(json.dumps(data,indent=2)+'\n')
 subprocess.run([sys.executable,str(ROOT/'scripts/compare_assembly.py')],check=True)
 print('Created',bom);print('Created',cpl);print('Assembly: six JST connectors only; native board unchanged.')
def main():
 decisions=json.loads((ROOT/'sources/prototype-decisions.json').read_text())
 if decisions['assembly'].get('mode')!='bare-pcb':return export_jst()
 before=digest(PCB)
 for suffix in ['BOM','CPL']:
  path=OUT/(STEM+'-JLCPCB-'+suffix+'.csv')
  if path.exists():path.unlink()
 with (ROOT/'bom/bom-review.csv').open(newline='')as f:parts=list(csv.DictReader(f))
 assert not any(p['Assembly']=='JLCPCB'for p in parts)
 import shutil
 shutil.copyfile(ROOT/'bom/bom-review.csv',OUT/(STEM+'-hand-assembly-BOM.csv'))
 report=dict(source_pcb_sha256=before,mode='bare-pcb',assembly_references=[],parts_per_board=0,instruction='PCB assembly OFF; all carrier parts including JSTs hand soldered',hand_assembly_bom=STEM+'-hand-assembly-BOM.csv',uploaded=False,order_placed=False)
 (CHECKS/'assembly-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 manifest=OUT/'manifest.json';data=json.loads(manifest.read_text());data['assembly']=report;manifest.write_text(json.dumps(data,indent=2)+'\n')
 subprocess.run([sys.executable,str(ROOT/'scripts/compare_assembly.py')],check=True)
 assert digest(PCB)==before
 print('Bare PCB selected: zero factory parts; hand-assembly BOM exported. No default PCBA BOM/CPL.')
if __name__=='__main__':collect()if '--collect-native'in sys.argv else main()
