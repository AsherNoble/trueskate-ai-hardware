#!/usr/bin/env python3
"""Independent text bounds vs all socketed-module bodies. KiCad checks pad/edge clearance."""
from pathlib import Path
import json,math
from shapely.geometry import Polygon,box
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'review/checks/silkscreen-review.json').read_text());fps=json.loads((ROOT/'design/data/placement-baseline.json').read_text());geo=json.loads((ROOT/'sources/mini-geometry.json').read_text())
modules={'Teensy':box(.7,61.11,61.66,78.89)}
for i in range(1,7):
 f=fps[f'J{10+i}'];ox,oy=f['position'];a=math.radians(f['angle'])
 modules[f'J{10+i}']=Polygon([(ox+math.cos(a)*x+math.sin(a)*y,oy-math.sin(a)*x+math.cos(a)*y)for x,y in geo['outline_polygon']]).buffer(0)
for t in d['texts']:
 assert t['height_mm']>=1 and t['stroke_mm']>=.15,t
 assert 'USB ONLY'not in t['text']
 bounds=box(*t['box_mm'])
 for ref,body in modules.items():assert not bounds.intersects(body),(t['text'],ref,t['box_mm'])
required=['TSAI-FOC6 v1 · 2026-10','Asher Noble · CC BY-NC','github.com/AsherNoble/trueskate-ai-hardware','USB →','F1 ATO · rate to supply','KILL (NC) · open = motors off','Populate A1-A3 first']
assert set(required)<={t['text']for t in d['texts']}
assert len(d['pin1_markers'])==28
for i in range(1,7):assert {f'A{i}',f'M{i}',f'ENC{i}'}<={t['text']for t in d['texts']}
assert sum(t['text']=='TODO'for t in d['texts'])==6
print('PASS: all silk text >=1mm/.15mm, required strings present, 28 pin1 markers, no text under socketed modules.')
