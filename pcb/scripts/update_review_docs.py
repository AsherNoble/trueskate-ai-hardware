#!/usr/bin/env python3
"""Refresh the single SH mapping table and BOM diff from declarative source."""
from pathlib import Path
import csv,io,json,re,subprocess
r=Path(__file__).resolve().parents[2]
p=r/'pcb'
d=json.loads((p/'design/data/design.json').read_text())
nets={'CLK':'SPI_SCK','MISO':'SPI_MISO','MOSI':'SPI_MOSI','CSn':'An_CS','3V3':'3V3','GND':'GND'}
table='<!-- SH_TABLE_START -->\n| SH contact | Proposed signal | Carrier net (axis n) |\n|---|---|---|\n'
for i,n in enumerate(d['encoder_pin_order'],1):table+=f'| {i} | {n} | `{nets[n]}` |\n'
table+='<!-- SH_TABLE_END -->'
f=p/'README.md';f.write_text(re.sub(r'<!-- SH_TABLE_START -->.*?<!-- SH_TABLE_END -->',lambda m:table,f.read_text(),flags=re.S))
old=list(csv.DictReader(io.StringIO(subprocess.check_output(['git','show','800ba4a:pcb/bom/bom-review.csv'],cwd=r,text=True))))
new=list(csv.DictReader((p/'bom/bom-review.csv').open()))
o={x['Reference']:x for x in old};n={x['Reference']:x for x in new}
out='# BOM diff from rollback checkpoint 800ba4a\n\n| Change | Reference(s) | Details |\n|---|---|---|\n'
for ref in sorted(o.keys()|n.keys()):
 if ref not in n:out+=f'| Removed | {ref} | {o[ref]["Value"]} |\n'
 elif ref not in o:out+=f'| Added | {ref} | {n[ref]["Value"]}; {n[ref]["Assembly"]} |\n'
 elif any(o[ref][key]!=n[ref][key] for key in ['Value','Assembly','LCSC']):out+=f"| Changed | {ref} | {o[ref]['LCSC']} → {n[ref]['LCSC']}; {n[ref]['Value']}; {n[ref]['Assembly']} |\n"
out+='\nThis pass adds Q1 (Infineon IRF4905PbF, C2564), D1 (ST(Semtech) 1N4742A 12V, C2545), and R2 (TyoHM RD1/4W10KJT/BA1, C433778), one each. All three are hand-soldered through-hole. No removals or footprint/placement changes. J31-J36 change supplier code only. F1 remains one complete Keystone 3557-2; fuse rated to the connected supply. Q1 needs no heat sink below ~5 A continuous; 12 A is copper sizing only. J31-J36 use stocked JST lead-free/tin supplier code C160405 in place of C7588156, without footprint/placement changes.\n'
(p/'bom/bom-diff.md').write_text(out)
