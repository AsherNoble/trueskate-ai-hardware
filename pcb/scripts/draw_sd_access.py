#!/usr/bin/env python3
"""Dimensioned top-view SD service envelope from actual placement and Mini geometry."""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
fps=json.loads((ROOT/'design/data/placement-baseline.json').read_text())
geo=json.loads((ROOT/'sources/mini-geometry.json').read_text())
layout=json.loads((ROOT/'review/checks/layout-review.json').read_text())
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-6 -12 162 176" width="1296" height="1408">','<rect x="-6" y="-12" width="162" height="176" fill="white"/>','<style>text{font-family:sans-serif;font-size:2.8px}.dim{stroke:#c73528;stroke-width:.3;fill:none}</style>']
svg.append('<text x="0" y="-6" style="font-size:4px">150 × 140 mm carrier — SD access, top view</text><rect x="0" y="0" width="150" height="140" fill="#f4f7f2" stroke="#333" stroke-width=".4"/>')
for i in range(1,7):
 f=fps[f'J{10+i}'];a=math.radians(f['angle']);ox,oy=f['position']
 poly=[(ox+math.cos(a)*x+math.sin(a)*y,oy-math.sin(a)*x+math.cos(a)*y)for x,y in geo['outline_polygon']]
 points=' '.join(f'{x:.4f},{y:.4f}'for x,y in poly)
 svg.append(f'<polygon points="{points}" fill="#b4c9e1" stroke="#375f92" stroke-width=".3"/>')
 c=fps[f'C{10+i}'];pads=c['pads'];x=sum(t['position'][0]for t in pads)/2;y=sum(t['position'][1]for t in pads)/2
 svg.append(f'<circle cx="{x}" cy="{y}" r="6.25" fill="#e1e8ed" stroke="#425f76" stroke-width=".3"/><text x="{x}" y="{y+1}" text-anchor="middle">C{10+i}</text>')
 svg.append(f'<text x="{sum(x for x,y in poly)/len(poly):.3f}" y="{20 if oy<70 else 120}" text-anchor="middle">A{i}</text>')
for ref in ('H1','H2','H3','H4'):
 x,y=fps[ref]['position'];svg.append(f'<circle cx="{x}" cy="{y}" r="1.6" fill="white" stroke="#666" stroke-width=".25"/>')
svg.append('<rect x=".7" y="61.11" width="60.96" height="17.78" fill="#b0d8ba" stroke="#286440" stroke-width=".35"/><text x="26" y="72" text-anchor="middle">Teensy 4.1</text><text x="1" y="59">USB flush at X=0</text>')
x0,y0,x1,y1=layout['sd_service']['rect_mm'];svg.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="#ffd5cf" stroke="#c73528" stroke-width=".4"/><text x="71.66" y="69" text-anchor="middle">SD service</text><text x="71.66" y="73" text-anchor="middle">KEEP CLEAR</text>')
svg.append('<path class="dim" d="M61.66,79 L61.66,86 M81.66,77.5 L81.66,86 M61.66,84 L81.66,84 M61.66,84 l1,-.7 M61.66,84 l1,.7 M81.66,84 l-1,-.7 M81.66,84 l-1,.7"/><text x="71.66" y="89" text-anchor="middle" fill="#ad3025">20 mm removal depth</text>')
svg.append('<path class="dim" d="M81.66,62.5 L91,62.5 M81.66,77.5 L91,77.5 M89,62.5 L89,77.5 M89,62.5 l-.7,1 M89,62.5 l.7,1 M89,77.5 l-.7,-1 M89,77.5 l.7,-1"/><text x="93" y="71" fill="#ad3025">15 mm</text>')
svg.append('<text x="0" y="148">Service envelope: X 61.66–81.66, Y 62.50–77.50 mm. Other courtyards ≥14.5 mm away.</text><text x="0" y="154">Design allowance; socket revision, seated protrusion and fingertip access need physical checking.</text><text x="0" y="160">Minis/capacitor bodies shown; drawing omits routing and small parts. Native DRC checks all parts.</text></svg>')
(ROOT/'review/drawings/sd-access.svg').write_text(''.join(svg))
print('Wrote dimensioned SD access illustration.')
