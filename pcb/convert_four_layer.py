#!/usr/bin/env python3
"""Convert the frozen routed carrier to dedicated inner planes; preserve placement."""
import json,re,hashlib
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parent;PCB=ROOT/'trueskate-main-v1.kicad_pcb'
b=k.LoadBoard(str(PCB));assert b.GetCopperLayerCount()==2,'Run after the two-layer routing import'
def mm(p):return [round(k.ToMM(p.x),6),round(k.ToMM(p.y),6)]
def footprints(board):
 return {f.GetReference():dict(fpid=str(f.GetFPID().GetLibNickname())+":"+str(f.GetFPID().GetLibItemName()),position=mm(f.GetPosition()),angle=f.GetOrientationDegrees(),pads=[dict(number=p.GetNumber(),net=p.GetNetname(),position=mm(p.GetPosition()),size=mm(p.GetSize()),drill=mm(p.GetDrillSize()),shape=int(p.GetShape())) for p in f.Pads()])for f in board.GetFootprints()}
before=footprints(b)
nets=b.GetNetsByName()
b.SetCopperLayerCount(4)
# Plated through-hole contacts must reach both new inner copper layers.
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetAttribute()==k.PAD_ATTRIB_PTH:
   ls=p.GetLayerSet();ls.AddLayer(k.In1_Cu);ls.AddLayer(k.In2_Cu);p.SetLayerSet(ls)
# Move all 12V tracks to L3 and reinforce them with two isolated, directly connected L3 areas.
removed=[]
for t in list(b.GetTracks()):
 if t.GetNetname() in ('12V_IN','12V_FUSED'):
  removed.append(dict(net=t.GetNetname(),layer=t.GetLayerName(),start=mm(t.GetStart()),end=mm(t.GetEnd()),width=k.ToMM(t.GetWidth())))
  t.SetLayer(k.In2_Cu)
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):t.SetRemoveUnconnected(True)
def zone(net,layer,points,priority=0):
 z=k.ZONE(b);z.SetLayer(layer);z.SetNet(nets[net]);z.SetLocalClearance(k.FromMM(.2 if layer==k.In1_Cu else .3))
 z.SetMinThickness(k.FromMM(.16 if layer==k.In1_Cu else .2));z.SetPadConnection(k.ZONE_CONNECTION_FULL);z.SetAssignedPriority(priority)
 o=z.Outline();o.NewOutline()
 for x,y in points:o.Append(k.FromMM(x),k.FromMM(y))
 b.Add(z)
rect=[(1,1),(159,1),(159,119),(1,119)]
zone('GND',k.In1_Cu,rect)
zone('12V_FUSED',k.In2_Cu,rect)
zone('12V_IN',k.In2_Cu,[(1,94),(37,94),(37,119),(1,119)],1)
assert footprints(b)==before
k.SaveBoard(str(PCB),b,True)
# Write the explicit, documented JLC standard physical stack.
s=PCB.read_text();start=s.index('(stackup');level=0;end=None
for i in range(start,len(s)):
 if s[i]=='(':level+=1
 elif s[i]==')':
  level-=1
  if level==0:end=i+1;break
stack=json.loads((ROOT/'stackup.json').read_text())
rows=['(layer "F.SilkS" (type "Top Silk Screen"))','(layer "F.Mask" (type "Top Solder Mask") (thickness 0.013))']
for row in stack['layers']:
 if row['type']=='copper':rows.append(f'(layer "{row["name"]}" (type "copper") (thickness {row["thickness_mm"]}))')
 else:rows.append(f'(layer "{row["name"]}" (type "{row["type"]}") (thickness {row["thickness_mm"]}) (material "{row["material"]}") (epsilon_r {row["dk"]}) (loss_tangent 0.02))')
rows+=['(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.013))','(layer "B.SilkS" (type "Bottom Silk Screen"))','(copper_finish "HASL lead-free")','(dielectric_constraints yes)']
PCB.write_text(s[:start]+'(stackup\n'+'\n'.join(rows)+')'+s[end:])
(ROOT/'four-layer-placement-baseline.json').write_text(json.dumps(before,indent=2)+'\n')
(ROOT/'four-layer-conversion.json').write_text(json.dumps(dict(footprints_preserved=len(before),moved_outer_power_segments=removed,stackup=stack['name']),indent=2)+'\n')
print(f'Converted to 4 layers; preserved {len(before)} footprint placements/pad geometries; moved {len(removed)} power tracks to L3 and added power planes.')
