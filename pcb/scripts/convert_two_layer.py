#!/usr/bin/env python3
"""Restore outer power routing from 62ef1ea's conversion log; use 2 x 1oz copper."""
import json,re,tempfile
from collections import defaultdict
from pathlib import Path
import json as _guard_json
_guard_root=Path(__file__).resolve().parents[1]
if _guard_json.loads((_guard_root/'design/data/design.json').read_text())['board_mm']!=[160,120]:
 raise SystemExit('Historical layout-specific tool; use rebuild.py for the current 3+3 carrier.')
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'design/trueskate-main-v1.kicad_pcb'
source=PCB.read_text()
def strip_inner(m):
 block=m.group(0)
 return '' if re.search(r'\(layer "In[12]\.Cu"\)',block) else block
clean=re.sub(r'\n\t\(zone\n.*?\n\t\)',strip_inner,source,flags=re.S)
with tempfile.NamedTemporaryFile(suffix='.kicad_pcb',mode='w') as temp:
 temp.write(clean);temp.flush();b=k.LoadBoard(temp.name)
def mm(p):return [round(k.ToMM(p.x),6),round(k.ToMM(p.y),6)]
assert b.GetCopperLayerCount() in [2,4]
original=json.loads((ROOT/'design/data/original-power-routes.json').read_text())['moved_outer_power_segments']
def sig(net,a,z,w):return net,tuple(sorted([tuple(a),tuple(z)])),round(w,6)
lookup=defaultdict(list)
for row in original:lookup[sig(row['net'],row['start'],row['end'],row['width'])].append(row['layer'])
count=0
for t in b.GetTracks():
 if t.GetNetname() in ('12V_IN','12V_FUSED'):
  key=sig(t.GetNetname(),mm(t.GetStart()),mm(t.GetEnd()),k.ToMM(t.GetWidth()))
  t.SetLayer({'F.Cu':k.F_Cu,'B.Cu':k.B_Cu}[lookup[key].pop()]);count+=1
assert count==len(original) and not any(lookup.values())
if b.GetCopperLayerCount()==4:
 b.SetCopperLayerCount(2)
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetAttribute()==k.PAD_ATTRIB_PTH:
    layers=p.GetLayerSet();layers.RemoveLayer(k.In1_Cu);layers.RemoveLayer(k.In2_Cu);p.SetLayerSet(layers)
else:assert b.GetCopperLayerCount()==2
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):t.SetRemoveUnconnected(False)
for z in b.Zones():
 assert z.GetNetname()=='GND'
 z.SetIslandRemovalMode(k.ISLAND_REMOVAL_MODE_ALWAYS)
 z.SetMinThickness(k.FromMM(.2))
 o=z.Outline();o.RemoveAllContours();o.NewOutline()
 for x,y in [(0,0),(160,0),(160,120),(0,120)]:o.Append(k.FromMM(x),k.FromMM(y))
k.SaveBoard(str(PCB),b,True)
# Fill in a fresh process after removing SWIG-owned zone objects.
s=PCB.read_text();start=s.index('(stackup');depth=0
for i in range(start,len(s)):
 if s[i]=='(':depth+=1
 elif s[i]==')':
  depth-=1
  if depth==0:end=i+1;break
stack='''(stackup
(layer "F.SilkS" (type "Top Silk Screen"))
(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
(layer "F.Cu" (type "copper") (thickness 0.035))
(layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
(layer "B.Cu" (type "copper") (thickness 0.035))
(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
(layer "B.SilkS" (type "Bottom Silk Screen"))
(copper_finish "HASL lead-free") (dielectric_constraints no))'''
PCB.write_text(s[:start]+stack+s[end:])
print('Two-layer 1 oz board; original outer-layer power routes restored; full-board GND zones, disconnected islands removed.')
