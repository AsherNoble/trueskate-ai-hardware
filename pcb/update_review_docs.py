#!/usr/bin/env python3
"""Refresh the single SH mapping table and BOM diff from declarative source."""
from pathlib import Path
import csv,io,json,re,subprocess
r=Path(__file__).resolve().parent.parent
p=r/'pcb'
d=json.loads((p/'design.json').read_text())
nets={'CLK':'SPI_SCK','MISO':'SPI_MISO','MOSI':'SPI_MOSI','CSn':'An_CS','3V3':'3V3','GND':'GND'}
table='<!-- SH_TABLE_START -->\n| SH contact | Proposed signal | Carrier net (axis n) |\n|---|---|---|\n'
for i,n in enumerate(d['encoder_pin_order'],1):table+=f'| {i} | {n} | `{nets[n]}` |\n'
table+='<!-- SH_TABLE_END -->'
f=p/'README.md';f.write_text(re.sub(r'<!-- SH_TABLE_START -->.*?<!-- SH_TABLE_END -->',lambda m:table,f.read_text(),flags=re.S))
old=list(csv.DictReader(io.StringIO(subprocess.check_output(['git','show','1d2f9e6:pcb/bom-review.csv'],cwd=r,text=True))))
new=list(csv.DictReader((p/'bom-review.csv').open()))
o={x['Reference']:x for x in old};n={x['Reference']:x for x in new}
out='# BOM diff from 1d2f9e6\n\n| Change | Reference(s) | Details |\n|---|---|---|\n'
for ref in sorted(o.keys()|n.keys()):
 if ref not in n:out+=f'| Removed | {ref} | {o[ref]["Value"]} |\n'
 elif ref not in o:out+=f'| Added | {ref} | {n[ref]["Value"]}; {n[ref]["Assembly"]} |\n'
 elif any(o[ref][key]!=n[ref][key] for key in ['Value','Assembly','LCSC']):out+=f'| Changed | {ref} | {o[ref]["Value"]} → {n[ref]["Value"]}; {n[ref]["Assembly"]} |\n'
out+='\nSix SH connectors replace six 1×6 adapter sockets. Added six CS pull-ups, six buffer-input pull-downs, two PDIP buffers, two bypass capacitors, one kill pull-up and one NC-loop header. Removed six optional ground bridges and the copper star. F1 changes from 5×20 holder to ATO holder; fuse rating remains TBD after load/inrush qualification. Twelve single machine-pin receptacles remain. J41–J46 were already removed in the baseline. Bare PCB copper changes from 1 oz to 2 oz. External NC switch and verified six-wire harnesses must be procured separately.\n'
(p/'bom-diff.md').write_text(out)
