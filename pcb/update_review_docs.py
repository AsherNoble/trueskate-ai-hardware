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
old=list(csv.DictReader(io.StringIO(subprocess.check_output(['git','show','f5fce90:pcb/bom-review.csv'],cwd=r,text=True))))
new=list(csv.DictReader((p/'bom-review.csv').open()))
o={x['Reference']:x for x in old};n={x['Reference']:x for x in new}
out='# BOM diff from f5fce90\n\n| Change | Reference(s) | Details |\n|---|---|---|\n'
for ref in sorted(o.keys()|n.keys()):
 if ref not in n:out+=f'| Removed | {ref} | {o[ref]["Value"]} |\n'
 elif ref not in o:out+=f'| Added | {ref} | {n[ref]["Value"]}; {n[ref]["Assembly"]} |\n'
 elif any(o[ref][key]!=n[ref][key] for key in ['Value','Assembly','LCSC']):out+=f'| Changed | {ref} | {o[ref]["Value"]} → {n[ref]["Value"]}; {n[ref]["Assembly"]} |\n'
out+='\nF1 changes to one Keystone3557-2 complete standard-ATO holder (C352820); both fuse contacts are included in that single part. No fuse amperage is specified. Six bulk capacitors and six ceramics move outside the GKO+0.5mm Mini courtyard; their quantities and MPNs do not change. CS pull-ups move behind the Minis to free the encoder lanes. Resistors are specified as 10k, 5% or better. No Teensy pin changes.\n'
(p/'bom-diff.md').write_text(out)
