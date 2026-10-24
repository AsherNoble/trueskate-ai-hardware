#!/usr/bin/env python3
"""Read-only native copper export for independent ground-connectivity audit."""
import json,hashlib
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parent;PCB=ROOT/'trueskate-main-v1.kicad_pcb';b=k.LoadBoard(str(PCB))
def mm(p):return [k.ToMM(p.x),k.ToMM(p.y)]
def contours(poly):return [[mm(poly.COutline(i).CPoint(j))for j in range(poly.COutline(i).PointCount())]for i in range(poly.OutlineCount())]
out=dict(pcb_sha256=hashlib.sha256(PCB.read_bytes()).hexdigest(),layers={'F.Cu':[],'B.Cu':[]},tracks=[],contacts=[])
for z in b.Zones():out['layers'][b.GetLayerName(z.GetLayer())]+=contours(z.GetFilledPolysList(z.GetLayer()))
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetNetname()!='GND':continue
  for layer in (k.F_Cu,k.B_Cu):
   if p.IsOnLayer(layer):out['layers'][b.GetLayerName(layer)]+=contours(p.GetEffectivePolygon(layer))
  if p.GetAttribute()==k.PAD_ATTRIB_PTH:out['contacts'].append(dict(ref=f.GetReference()+':'+p.GetNumber(),position=mm(p.GetPosition()),radius=min(mm(p.GetSize()))/2))
for t in b.GetTracks():
 if t.GetNetname()!='GND':continue
 if isinstance(t,k.PCB_VIA):out['contacts'].append(dict(ref=t.m_Uuid.AsString(),position=mm(t.GetPosition()),radius=k.ToMM(t.GetWidth(k.F_Cu))/2))
 else:out['tracks'].append(dict(layer=b.GetLayerName(t.GetLayer()),start=mm(t.GetStart()),end=mm(t.GetEnd()),width=k.ToMM(t.GetWidth())))
(ROOT/'ground-geometry-review.json').write_text(json.dumps(out)+'\n')
