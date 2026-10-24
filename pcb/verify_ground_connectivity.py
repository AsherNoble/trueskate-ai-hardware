#!/usr/bin/env python3
"""Independent 2D copper-region union and cross-layer GND connectivity check."""
import json,hashlib
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely import union_all
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'ground-geometry-review.json').read_text())
assert D['pcb_sha256']==hashlib.sha256((ROOT/'trueskate-main-v1.kicad_pcb').read_bytes()).hexdigest()
regions={};parent={}
for layer,contours in D['layers'].items():
 shapes=[Polygon(c).buffer(0)for c in contours]
 shapes += [LineString([t['start'],t['end']]).buffer(t['width']/2,quad_segs=32) for t in D['tracks']if t['layer']==layer]
 shapes += [Point(c['position']).buffer(c['radius'],quad_segs=32) for c in D['contacts']]
 merged=union_all(shapes).buffer(0)
 regions[layer]=list(merged.geoms)if merged.geom_type=='MultiPolygon'else [merged]
 for i in range(len(regions[layer])):parent[(layer,i)]=(layer,i)
def find(n):
 if parent[n]!=n:parent[n]=find(parent[n])
 return parent[n]
for c in D['contacts']:
 nodes=[];p=Point(c['position'])
 for layer,parts in regions.items():
  ids=[i for i,g in enumerate(parts)if g.covers(p)]
  assert len(ids)==1,(c['ref'],layer,ids)
  nodes.append((layer,ids[0]))
 a,z=map(find,nodes);parent[a]=z
components={find(n)for n in parent}
report=dict(pcb_sha256=D['pcb_sha256'],ground_regions_per_layer={n:len(p)for n,p in regions.items()},through_ground_contacts=len(D['contacts']),connected_ground_networks=len(components),floating_ground_regions=0 if len(components)==1 else None,ground_copper_area_mm2={n:round(sum(p.area for p in parts),3)for n,parts in regions.items()},method='Union filled zones, real pad outlines, GND tracks and via annuli per side, then join regions at every through-ground contact; plated holes treated as solid contact nodes.')
(ROOT/'ground-connectivity-review.json').write_text(json.dumps(report,indent=2)+'\n')
assert len(components)==1,report
print('PASS: every retained GND copper region belongs to one cross-layer network; no floating islands.',report['ground_regions_per_layer'])
