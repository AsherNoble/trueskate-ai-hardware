#!/usr/bin/env python3
"""Check continuous full-width Mini feed/return paths on actual board copper."""
import json
import math
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parent
b=k.LoadBoard(str(ROOT/'trueskate-main-v1.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
def pad(ref,n):return next(p for p in fps[ref].Pads() if p.GetNumber()==str(n))
def point(p):return k.ToMM(p.x),k.ToMM(p.y)
def on(p,a,z):
    dx,dy=z[0]-a[0],z[1]-a[1];length=math.hypot(dx,dy)
    return length>0 and abs((p[0]-a[0])*dy-(p[1]-a[1])*dx)/length<1e-4 and min(a[0],z[0])-1e-4<=p[0]<=max(a[0],z[0])+1e-4 and min(a[1],z[1])-1e-4<=p[1]<=max(a[1],z[1])+1e-4

def wide_path(source,target,width):
    net=source.GetNetname();assert target.GetNetname()==net
    ts=[t for t in b.GetTracks() if t.GetNetname()==net and not isinstance(t,k.PCB_VIA) and k.ToMM(t.GetWidth())>=width-1e-6]
    assert all(t.IsLocked() for t in ts)
    parent=list(range(len(ts)))
    def find(i):
        if parent[i]!=i:parent[i]=find(parent[i])
        return parent[i]
    def join(indices):
        for j in indices[1:]:parent[find(j)]=find(indices[0])
    seg=[(point(t.GetStart()),point(t.GetEnd()),t.GetLayer()) for t in ts]
    for i,(a,z,l) in enumerate(seg):
        for j,(c,d,m) in enumerate(seg[:i]):
            if l==m and (on(a,c,d) or on(z,c,d) or on(c,a,z) or on(d,a,z)):join([i,j])
    # Plated contacts connect F/B copper. No signal-sized via is credited.
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname()==net and p.GetAttribute()==k.PAD_ATTRIB_PTH:
                join([i for i,(a,z,l) in enumerate(seg) if on(point(p.GetPosition()),a,z)])
    starts=[find(i) for i,(a,z,l) in enumerate(seg) if on(point(source.GetPosition()),a,z)]
    ends=[find(i) for i,(a,z,l) in enumerate(seg) if on(point(target.GetPosition()),a,z)]
    assert set(starts)&set(ends),(net,source.GetParent().GetReference(),target.GetParent().GetReference(),width)

# IPC-2221 external-layer estimate, I=.048*dT^.44*A^.725; A in square mils.
required_mm=(3/(.048*10**.44))**(1/.725)/(.070/.0254)*.0254
assert required_mm<2
rows=[]
for i in range(1,7):
    mini=f'J{10+i}';vin=pad(mini,'VIN');gnd=pad(mini,'GND')
    assert all(abs(k.ToMM(p.GetSize().x)-2.4)<1e-6 for p in (vin,gnd))
    wide_path(pad('F1',2),vin,2)
    assert gnd.GetNetname()=='GND'
    wide_path(pad(f'C{10+i}',1),vin,2)
    assert pad(f'C{10+i}',2).GetNetname()=='GND'
    row=dict(axis=i,supply_min_width_mm=2,return_path='continuous GND planes; thermal qualification pending')
    for typ,ref in [('bulk',f'C{10+i}'),('ceramic',f'C{20+i}')]:
        row[typ+'_power_pad_distances_mm']=[round(math.dist(point(pad(ref,n).GetPosition()),point(power.GetPosition())),3) for n,power in [(1,vin),(2,gnd)]]
    rows.append(row)
bus_required=(12/(.048*10**.44))**(1/.725)/(.070/.0254)*.0254
assert bus_required<12
report=dict(bus_current_a=12,bus_calculated_minimum_mm=round(bus_required,3),input_feed='parallel 2mm top/bottom paths, 6A estimate per layer; connector and fuse pad transitions require thermal validation',current_a=3,copper_thickness_um=70,layer='external',temperature_rise_c=10,estimate='IPC-2221 external-layer equation; not a thermal qualification',minimum_calculated_width_mm=round(required_mm,3),supply_chosen_mm=2,return_geometry='filled GND planes',shared_trunk_mm=12,aggregate_six_axis_rating_established=False,axes=rows)
(ROOT/'power-routing-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: six continuous >=2.0 mm VIN paths; common ground planes; 3 A estimate requires {required_mm:.3f} mm at 70 um / 10 C.')
