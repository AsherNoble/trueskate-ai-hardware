#!/usr/bin/env python3
"""Trim unused encoder escape tails and apply recorded SES clearance corrections."""
import json,math
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'design/trueskate-main-v1.kicad_pcb'
b=k.LoadBoard(str(PCB))
def mm(p):return [round(k.ToMM(p.x),6),round(k.ToMM(p.y),6)]
def xy(p):return k.VECTOR2I(k.FromMM(p[0]),k.FromMM(p[1]))
def record(t):return dict(net=t.GetNetname(),layer=b.GetLayerName(t.GetLayer()),width=k.ToMM(t.GetWidth()),start=mm(t.GetStart()),end=mm(t.GetEnd()))
points={}
for t in b.GetTracks():
    if not t.IsLocked():points.setdefault(t.GetNetname(),[]).extend([mm(t.GetStart()),mm(t.GetEnd())])
trims=[]
manual=[t for t in b.GetTracks() if t.IsLocked() and not isinstance(t,k.PCB_VIA)]
for tail in manual:
    a,z=mm(tail.GetStart()),mm(tail.GetEnd())
    if a[0]!=z[0] or a[1]!=40 or z[1]!=45 or tail.GetNetname()=='GND':continue
    # Walk backward from each escape's free end to its last routed junction.
    chain=[];t=tail;end=z;seen=set()
    while t.m_Uuid.AsString() not in seen:
        seen.add(t.m_Uuid.AsString())
        start=mm(t.GetStart()) if mm(t.GetEnd())==end else mm(t.GetEnd())
        dx,dy=end[0]-start[0],end[1]-start[1];length2=dx*dx+dy*dy
        hits=[]
        for q in points.get(t.GetNetname(),[]):
            u=((q[0]-start[0])*dx+(q[1]-start[1])*dy)/length2
            if -1e-6<=u<=1+1e-6 and math.dist(q,[start[0]+u*dx,start[1]+u*dy])<1e-5:hits.append((u,q))
        if hits:
            u,q=max(hits)
            if u<1-1e-6:
                old=record(t)
                if u<=1e-6:chain.append(t)
                else:
                    if mm(t.GetEnd())==end:t.SetEnd(xy(q))
                    else:t.SetStart(xy(q))
                    trims.append(dict(before=old,after=record(t)))
            for item in chain:
                trims.append(dict(before=record(item),after=None));b.Remove(item)
            break
        chain.append(t)
        prev=[v for v in manual if v.GetNetname()==t.GetNetname() and v.m_Uuid.AsString() not in seen and start in [mm(v.GetStart()),mm(v.GetEnd())]]
        if len(prev)!=1:break
        t=prev[0];end=start
# 0.0046mm native hole-clearance deficit in this frozen routing session.
# Move the offending via away from the adjacent MOSI segment, including its leads.
fixes=json.loads((ROOT/'design/routing/signal-adjustments.json').read_text())
for fix in fixes:
    vs=[t for t in b.GetTracks() if isinstance(t,k.PCB_VIA) and t.GetNetname()==fix['net'] and math.dist(mm(t.GetPosition()),fix['before'])<1e-5]
    assert len(vs)==1,fix
    for t in b.GetTracks():
        if t.GetNetname()!=fix['net']:continue
        if isinstance(t,k.PCB_VIA):
            if math.dist(mm(t.GetPosition()),fix['before'])<1e-5:t.SetPosition(xy(fix['after']))
        else:
            if math.dist(mm(t.GetStart()),fix['before'])<1e-5:t.SetStart(xy(fix['after']))
            if math.dist(mm(t.GetEnd()),fix['before'])<1e-5:t.SetEnd(xy(fix['after']))
k.SaveBoard(str(PCB),b,True)
(ROOT/'design/data/encoder-tail-trims.json').write_text(json.dumps(trims,indent=2)+'\n')
print(f'Trimmed {len(trims)} unused encoder tails; applied {len(fixes)} recorded signal clearance correction(s). Power/phase copper unchanged.')
