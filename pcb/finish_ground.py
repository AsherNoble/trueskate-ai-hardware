#!/usr/bin/env python3
"""Deliberate quiet-ground stitching after signal routing; never routes motor nets.

Choose widely cleared points on a 0.25 mm grid where the already-filled top and
bottom logic-GND areas overlap. Connect distinct copper islands with a spanning
forest, locking and recording every via. KiCad DRC remains the authority.
"""
import json
import math
from pathlib import Path
import pcbnew as k

ROOT=Path(__file__).resolve().parent
b=k.LoadBoard(str(ROOT/'trueskate-main-v1.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
# Four congested ground contacts use solid copper instead of a single stranded
# thermal spoke. This is a geometry correction, not a waived thermal violation.
for ref,number in [('J2','2'),('J2','15'),('J1','1'),('JP5','2')]:
    p=next(p for p in fps[ref].Pads() if p.GetNumber()==number)
    assert p.GetNetname()=='GND';p.SetLocalZoneConnection(k.ZONE_CONNECTION_FULL)
def xy(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def mm(p):return k.ToMM(p.x),k.ToMM(p.y)
# Two deliberate, short quiet-ground links bypass the signal/3V3 fences. They
# were selected from the native copper geometry and checked independently;
# neither carries an axis power return. No autorouter is used for these links.
chosen=[];links=[]
for layer,points in [(k.B_Cu,[(51.25,51),(51.25,53.5),(52.25,54.5),(56,54.5)]),
                     (k.F_Cu,[(87.25,50),(94.25,50)])]:
    for x,y in [points[0],points[-1]]:
        v=k.PCB_VIA(b);v.SetPosition(xy(x,y));v.SetWidth(k.FromMM(.7));v.SetDrill(k.FromMM(.3))
        v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetViaType(k.VIATYPE_THROUGH)
        v.SetNet(b.GetNetsByName()['GND']);v.SetLocked(True);b.Add(v)
        chosen.append(dict(x=x,y=y,diameter=.7,drill=.3,reason='deliberate ground-link endpoint'))
    for a,z in zip(points,points[1:]):
        t=k.PCB_TRACK(b);t.SetStart(xy(*a));t.SetEnd(xy(*z));t.SetWidth(k.FromMM(.4))
        t.SetLayer(layer);t.SetNet(b.GetNetsByName()['GND']);t.SetLocked(True);b.Add(t)
        links.append(dict(net='GND',layer=b.GetLayerName(layer),width=.4,start=a,end=z))
k.ZONE_FILLER(b).Fill(b.Zones())
zones={z.GetLayer():z for z in b.Zones() if z.GetNetname()=='GND'}
polys={l:z.GetFilledPolysList(l) for l,z in zones.items()}
assert set(polys)=={k.F_Cu,k.B_Cu}
holes=[];pads=[];segments=[]
for fp in b.GetFootprints():
    for p in fp.Pads():
        x,y=mm(p.GetPosition());size=mm(p.GetSize());drill=mm(p.GetDrillSize())
        holes.append((x,y,max(drill)/2))
        if p.GetNetname()!='GND':
            r=max(size)/2 if p.GetShape()==k.PAD_SHAPE_CIRCLE else math.hypot(*size)/2
            pads.append((x,y,r))
for t in b.GetTracks():
    if isinstance(t,k.PCB_VIA):
        x,y=mm(t.GetPosition());holes.append((x,y,k.ToMM(t.GetDrillValue())/2))
        if t.GetNetname()!='GND':pads.append((x,y,k.ToMM(t.GetWidth(k.F_Cu))/2))
    elif t.GetNetname()!='GND':segments.append((*mm(t.GetStart()),*mm(t.GetEnd()),k.ToMM(t.GetWidth())/2))
def clearance(x,y):
    best=20.0
    for px,py,r in holes:
        d=math.hypot(x-px,y-py)-r-.15-.45
        if d<0:return -1
        best=min(best,d)
    for px,py,r in pads:
        d=math.hypot(x-px,y-py)-r-.35-.25
        if d<0:return -1
        best=min(best,d)
    for ax,ay,zx,zy,r in segments:
        if x<min(ax,zx)-2 or x>max(ax,zx)+2 or y<min(ay,zy)-2 or y>max(ay,zy)+2:continue
        dx,dy=zx-ax,zy-ay
        f=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy))) if dx or dy else 0
        d=math.hypot(x-ax-f*dx,y-ay-f*dy)-r-.35-.25
        if d<0:return -1
        best=min(best,d)
    return best
candidates={}
for iy in range(177,336):
    for ix in range(113,628):
        x,y=ix/4,iy/4
        p=xy(x,y)
        if not all(poly.Contains(p) for poly in polys.values()):continue
        margin=clearance(x,y)
        if margin<0:continue
        a=next(i for i in range(polys[k.F_Cu].OutlineCount()) if polys[k.F_Cu].Contains(p,i))
        z=next(i for i in range(polys[k.B_Cu].OutlineCount()) if polys[k.B_Cu].Contains(p,i))
        key=(a,z)
        if key not in candidates or margin>candidates[key][0]:candidates[key]=(margin,x,y)
parent={('F',i):('F',i) for i in range(polys[k.F_Cu].OutlineCount())}
parent.update({('B',i):('B',i) for i in range(polys[k.B_Cu].OutlineCount())})
def find(p):
    if parent[p]!=p:parent[p]=find(parent[p])
    return parent[p]
for (a,z),(margin,x,y) in sorted(candidates.items(),key=lambda item:-item[1][0]):
    pa,pz=find(('F',a)),find(('B',z))
    if pa==pz:continue
    if any(math.hypot(x-v['x'],y-v['y'])<1 for v in chosen):continue
    parent[pa]=pz
    chosen.append(dict(x=x,y=y,diameter=.7,drill=.3,clearance_margin=round(margin,3),reason='interplane stitch'))
    v=k.PCB_VIA(b);v.SetPosition(xy(x,y));v.SetWidth(k.FromMM(.7));v.SetDrill(k.FromMM(.3))
    v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetViaType(k.VIATYPE_THROUGH)
    v.SetNet(b.GetNetsByName()['GND']);v.SetLocked(True);b.Add(v)
k.ZONE_FILLER(b).Fill(b.Zones())
assert all(t.GetNetname()=='GND' for t in b.GetTracks() if isinstance(t,k.PCB_VIA) and t.IsLocked())
k.SaveBoard(str(ROOT/'trueskate-main-v1.kicad_pcb'),b,True)
(ROOT/'ground-stitching.json').write_text(json.dumps(chosen,indent=2)+'\n')
(ROOT/'ground-links.json').write_text(json.dumps(links,indent=2)+'\n')
print(f'Placed {len(chosen)} locked logic-GND stitching vias at independently cleared grid positions.')
print('Motor returns and existing manual traces were not changed. Run strict DRC next.')
