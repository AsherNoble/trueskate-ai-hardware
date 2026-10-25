#!/usr/bin/env python3
"""Measure actual SPI/EN reference gaps; report limitations without hiding them in DRC."""
import json,hashlib
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'review/checks/ground-geometry-review.json').read_text())
assert d['pcb_sha256']==hashlib.sha256((ROOT/'design/trueskate-main-v1.kicad_pcb').read_bytes()).hexdigest()
planes={layer:unary_union([Polygon(p).buffer(0)for p in polys])for layer,polys in d['layers'].items()}
for layer in planes:
 planes[layer]=unary_union([planes[layer]]+[LineString([t['start'],t['end']]).buffer(t['width']/2)for t in d['tracks']if t['layer']==layer])
critical=lambda n:n.startswith('SPI_') or n.endswith('_CS') or '_EN' in n or n=='EN_DISABLE'
rows=[]
for net in sorted({t['net']for t in d['signals']if critical(t['net'])}):
 transitions=unary_union([Point(t['position']).buffer(t['radius'])for t in d['signal_transitions']if t['net']==net])
 lengths={'F.Cu':0.,'B.Cu':0.};gaps=[]
 for t in d['signals']:
  if t['net']!=net:continue
  line=LineString([t['start'],t['end']]);lengths[t['layer']]+=line.length
  opposite='B.Cu'if t['layer']=='F.Cu'else 'F.Cu'
  span=line.difference(transitions)
  missing=span.difference(planes[opposite].buffer(.002))
  # Centreline length is an audit diagnostic, not impedance qualification.
  if missing.length>.005:
   pieces=list(missing.geoms)if hasattr(missing,'geoms')else [missing]
   paths=[list(g.coords)for g in pieces if g.geom_type=='LineString']
   gaps.append(dict(layer=t['layer'],start=t['start'],end=t['end'],unreferenced_length_mm=round(missing.length,4),gap_paths_mm=paths))
 rows.append(dict(net=net,length_mm={k:round(v,3)for k,v in lengths.items()},opposite_ground_gap_mm=round(sum(g['unreferenced_length_mm']for g in gaps),3),gaps=gaps))
report=dict(pcb_sha256=d['pcb_sha256'],method='Exact filled-polygon centreline coverage; excludes only own PTH/via radius plus 0.3 mm transition. Not impedance or EMC qualification.',all_critical_on_top=all(r['length_mm']['B.Cu']==0 for r in rows),all_spans_over_opposite_ground=not any(r['gaps']for r in rows),nets=rows)
report['prototype_status']='accepted for v1'
report['spi_clock_policy']='1-4MHz; lower if encoder reads glitch; documentation only, firmware unchanged'
report['bottom_ground_under_every_spi_en_trace']=report['all_critical_on_top']and report['all_spans_over_opposite_ground']
(ROOT/'review/checks/return-path-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('Bottom GND beneath every SPI/CS/EN span:',report['bottom_ground_under_every_spi_en_trace'])
print('Critical bottom trace length:',round(sum(r['length_mm']['B.Cu']for r in rows),3),'mm; uncovered opposite-ground centreline:',round(sum(r['opposite_ground_gap_mm']for r in rows),3),'mm')

# Exact gap segments plotted over signal routes, one view per signal layer.
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 330 175" width="1650" height="875">','<rect width="330" height="175" fill="white"/>']
for i,layer in enumerate(['F.Cu','B.Cu']):
 ox=8+165*i;oy=18
 svg.append(f'<text x="{ox}" y="10" font-family="sans-serif" font-size="4">{layer}: grey signals; red = gap in opposite GND</text>')
 svg.append(f'<rect x="{ox}" y="{oy}" width="150" height="140" fill="#fafafa" stroke="#333" stroke-width=".25"/>')
 for t in d['signals']:
  if t['layer']!=layer or not critical(t['net']):continue
  a,z=t['start'],t['end'];svg.append(f'<path d="M{ox+a[0]},{oy+a[1]} L{ox+z[0]},{oy+z[1]}" stroke="#9caaae" stroke-width=".25" fill="none"/>')
 for row in rows:
  for gap in row['gaps']:
   if gap['layer']!=layer:continue
   for points in gap['gap_paths_mm']:
    path='M'+' L'.join(f'{ox+x},{oy+y}'for x,y in points)
    svg.append(f'<path d="{path}" stroke="#cf362d" stroke-width=".65" fill="none"/>')
svg.append('<text x="8" y="168" font-family="sans-serif" font-size="3.4">Accepted for v1. Top view on both panels. Own PTH/via transitions excluded; measured centreline documentation.</text></svg>')
(ROOT/'renders/copper/return-path-gaps.svg').write_text(''.join(svg))

# Physical crossings are distinct from logical pin-row mismatch counts.
crossings=[]
for t in d['signals']:
 a,z=t['start'],t['end']
 if (a[1]<=70<z[1])or(z[1]<=70<a[1]):
  x=a[0]+(z[0]-a[0])*(70-a[1])/(z[1]-a[1])
  crossings.append(dict(net=t['net'],layer=t['layer'],x_mm=round(x,4),under_teensy=.7<=x<=61.66))
out=dict(definition='Physical crossings of Y=70 mm; includes all routed signal nets, buffers and shared supplies. Not equivalent to the 14 pin-row mismatch estimate.',crossings=crossings,unique_nets=len({t['net']for t in crossings}),events=len(crossings),top_under_teensy_events=sum(t['layer']=='F.Cu'and t['under_teensy']for t in crossings),bottom_under_teensy_events=sum(t['layer']=='B.Cu'and t['under_teensy']for t in crossings))
(ROOT/'review/checks/bank-crossings.json').write_text(json.dumps(out,indent=2)+'\n')
