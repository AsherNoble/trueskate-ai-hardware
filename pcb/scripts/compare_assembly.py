#!/usr/bin/env python3
"""Create three assembly comparison packages; never represent unresolved parts as orderable."""
from pathlib import Path
import csv,json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'manufacturing/assembly-options'
def write_csv(path,headers,rows):
 with path.open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(headers);w.writerows(rows)
def main():
 source=ROOT/'manufacturing';board=ROOT/'design/trueskate-main-v1.kicad_pcb';before=hashlib.sha256(board.read_bytes()).hexdigest()
 with (ROOT/'bom/bom-review.csv').open(newline='')as f:parts=list(csv.DictReader(f))
 native=json.loads((ROOT/'design/data/placement-baseline.json').read_text())
 policy=json.loads((ROOT/'sources/prototype-decisions.json').read_text())
 for name in ['bare-pcb','jst-only','full-carrier-planning']:(OUT/name).mkdir(parents=True,exist_ok=True)
 for name in ['bare-pcb','jst-only']:
  (OUT/name/'README.md').write_text('Use the shared ../../trueskate-main-v1-2layer-1oz-JLCPCB.zip. '+('Select PCB assembly OFF; no BOM/CPL is needed.\n'if name=='bare-pcb'else 'ALTERNATIVE ONLY; current choice is bare PCB. For a future JST-only order select top-side assembly and upload BOM.csv and CPL.csv. Six JST connectors per board; all remaining parts hand assembled.\n'))
 # Previously validated JST-only CSVs are retained for comparison, not the selected order.
 rows=[];placements=[];used=set()
 for part in parts:
  ref=part['Reference']
  if ref not in native:continue # aggregate power sockets are expanded from each Mini below
  fp=native[ref];pads=fp['pads']
  groups=[(ref,pads,part['Value'])]
  if ref in {f'J{i}'for i in range(11,17)}:
   groups=[(ref+'_CTRL',[p for p in pads if p['number'].isdigit()],'Female 2x5 2.54mm; matched Mini socket height'),(ref+'_PHASE',[p for p in pads if p['number'] in ['P1','P2','P3']],'Female 1x3 2.54mm; matched Mini socket height')]+[(ref+'_'+n,[p for p in pads if p['number']==n],'Single machine-pin receptacle >=3A; matched height; 0.64mm square mating pin') for n in ['VIN','GND']]
  for physical,contacts,desc in groups:
   assert physical not in used;used.add(physical)
   stocked=ref in {f'J{i}'for i in range(31,37)}
   code=policy['assembly']['lcsc']if stocked else ''
   status='Selected: stocked JST'if stocked else 'UNRESOLVED: exact stocked compatible part not verified; do not order'
   rows.append([physical,ref,1,5,desc,fp['fpid'],code,status,part['LCSC'] if not stocked else code])
   # Pad centroid is an audit coordinate, not a validated component body centroid.
   x=sum(p['position'][0]for p in contacts)/len(contacts);y=sum(p['position'][1]for p in contacts)/len(contacts)
   placements.append([physical,ref,f'{x:.4f}',f'{-y:.4f}',f"{fp['angle']%360:g}",'Top',','.join(p['number'] for p in contacts),'Pad centroid only; body centroid and JLC zero-angle NOT validated'])
 assert len(rows)==79 and len(placements)==79 and len(used)==79
 write_csv(OUT/'full-carrier-planning/BOM-NOT-FOR-UPLOAD.csv',['Physical reference','PCB reference','Qty per board','Qty for 5','Required part','Existing footprint','Selected stocked LCSC','Status','Existing or candidate code (not stock approval)'],rows)
 write_csv(OUT/'full-carrier-planning/PLACEMENTS-NOT-FOR-UPLOAD.csv',['Physical reference','PCB reference','Pad centroid X mm','Pad centroid Y mm','Native rotation CCW deg','Layer','Native pad numbers','Qualification'],placements)
 (OUT/'full-carrier-planning/README.md').write_text('''# Full carrier: planning files, not an orderable assembly package

Stocked-JLC-only policy; no sourcing or consignment. PCB unchanged.

79 physical parts per carrier (395 for five), excluding plug-in Teensy and Mini modules, loose fuse, cables, encoders, motors and external switch. The six Mini footprint references each expand into four physical socket parts: CTRL, PHASE, VIN and GND. This avoids counting a custom 15-hole footprint as one purchasable connector. The existing aggregate 12-receptacle BOM row is not counted twice.

BOM-NOT-FOR-UPLOAD.csv is a complete assembly scope, not a JLC upload BOM. Blank selected LCSC cells are deliberately unresolved. Existing/candidate codes are research leads, not approved stocked substitutions. PLACEMENTS-NOT-FOR-UPLOAD.csv maps every physical part to native pads for review; pad centroids are NOT validated component body centroids or JLC zero-angle placements.

The exact SN74LV125AN PDIP-14 listing C1548088 has zero stock (live search saved in sources/jlc-assembly/SN74LV125AN-search.txt). The Mini socket/receptacle combination has no selected stocked MPN or validated common seating height. The exact bulk capacitor C128476 has zero stock for the 30 required parts. These prevent a truthful full-carrier stocked-only quote/package on the unchanged board. Do not silently substitute SMD buffers, a different logic family, ordinary sockets for machine-pin receptacles, or a different mechanical seating height.

Consequently a full-carrier price is unavailable, rather than zero. No sourcing request, consignment, board change, upload or purchase was performed. JST-only and bare-PCB packages remain usable.
''')
 write_csv(OUT/'cost-comparison.csv',['Variant','Boards','Factory parts per board','Factory parts for 5','PCB USD for 5','Known component subtotal USD for 5','Assembly fees USD','Total USD','Readiness'],[['Bare PCB',5,0,0,'15.80',0,0,'15.80 before shipping/tax','PCB quote recorded 2026-10-25'],['JST only',5,6,30,'15.80','19.836 (30 x 0.6612; excludes attrition)','JLC quote required','','Upload BOM/CPL; parts plus base PCB 35.636 before fees/shipping/tax'],['Full carrier',5,79,395,'15.80','','Unavailable','','BLOCKED under stocked-only policy; planning files only']])
 report=dict(source_pcb_sha256=before,selected_option='bare-pcb',policy='For alternative factory assembly: stocked JLC library parts only; no sourcing/consignment',full_physical_parts_per_board=79,full_package_orderable=False,full_quote_available=False,full_blockers=['SN74LV125AN PDIP-14 C1548088 has zero stock','No stocked matched Mini socket/receptacle set selected','Exact bulk capacitor stock insufficient for 30'],board_changed=False,files={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(OUT.rglob('*'))if p.is_file()and p.name!='validation.json'})
 (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
 assert hashlib.sha256(board.read_bytes()).hexdigest()==before
 print('Assembly comparison: bare and JST upload packages; 79-part full scope explicitly blocked under stocked-only policy.')
if __name__=='__main__':main()
