#!/usr/bin/env python3
"""Check explicitly proposed quiet-GND joins against real native copper shapes."""
from pathlib import Path
import math
import json
import pcbnew as k
root=Path(__file__).resolve().parents[1]
b=k.LoadBoard(str(root/'design/trueskate-main-v1.kicad_pcb'))
def xy(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def mm(p):return k.ToMM(p.x),k.ToMM(p.y)
obstacles={k.F_Cu:[],k.B_Cu:[]};holes=[]
for fp in b.GetFootprints():
 for p in fp.Pads():
  holes.append((fp.GetReference()+'.'+p.GetNumber(),*mm(p.GetPosition()),max(mm(p.GetDrillSize()))/2))
  if p.GetNetname()!='GND':
   for l in obstacles:obstacles[l].append((fp.GetReference()+'.'+p.GetNumber(),p.GetEffectivePolygon(l)))
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):holes.append((t.GetNetname(),*mm(t.GetPosition()),k.ToMM(t.GetDrillValue())/2))
 if t.GetNetname()!='GND':
  for l in obstacles:
   if t.IsOnLayer(l):obstacles[l].append((t.GetNetname()+str(mm(t.GetStart()))+str(mm(t.GetEnd())),t.GetEffectiveShape(l)))
plan=json.loads((root/'design/data/ground-link-plan.json').read_text())
bridges=[({'F.Cu':k.F_Cu,'B.Cu':k.B_Cu}[p['layer']],p['points']) for p in plan['routes']]
for layer,points in bridges:
 print('BRIDGE',b.GetLayerName(layer),points)
 for a,z in zip(points,points[1:]):
  s=k.SHAPE_SEGMENT(xy(*a),xy(*z),k.FromMM(.4))
  blockers=[n for n,o in obstacles[layer]if o.Collide(s,k.FromMM(.2))]
  assert not blockers,(a,z,blockers)
for point in plan['vias']:
 c=k.SHAPE_CIRCLE(xy(*point),k.FromMM(.35))
 for l,shapes in obstacles.items():
  blockers=[n for n,s in shapes if s.Collide(c,k.FromMM(.25))]
  assert not blockers,(point,b.GetLayerName(l),blockers)
 blockers=[n for n,x,y,r in holes if math.hypot(point[0]-x,point[1]-y)<r+.15+.45 and math.hypot(point[0]-x,point[1]-y)>.001]
 assert not blockers,(point,'holes',blockers)
print('PASS: all deliberate quiet-GND links independently clear of other copper and via holes.')
