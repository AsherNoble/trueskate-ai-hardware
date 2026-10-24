#!/usr/bin/env python3
"""Measure actual footprint clearances and audit encoder lanes on native copper."""
import json,math
from pathlib import Path
import pcbnew as k
from extract_mini import outline_polygon
ROOT=Path(__file__).resolve().parent
b=k.LoadBoard(str(ROOT/'trueskate-main-v1.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
def mm(p):return k.ToMM(p.x),k.ToMM(p.y)
def ptseg(p,a,z):
    dx,dy=z[0]-a[0],z[1]-a[1];d=dx*dx+dy*dy
    f=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/d)) if d else 0
    return math.hypot(p[0]-a[0]-f*dx,p[1]-a[1]-f*dy)
def segs(poly):return list(zip(poly,poly[1:]+poly[:1]))
def distance(poly1,poly2):
    return min([ptseg(p,a,z) for p in poly1 for a,z in segs(poly2)]+[ptseg(p,a,z) for p in poly2 for a,z in segs(poly1)])
def point_inside(p,poly):
    c=False
    for a,z in segs(poly):
        if (a[1]>p[1])!=(z[1]>p[1]) and p[0]<(z[0]-a[0])*(p[1]-a[1])/(z[1]-a[1])+a[0]:c=not c
    return c
source,maxgap=outline_polygon();source=source[:-1]
lib=k.FootprintLoad(str(ROOT/'TrueSkate.pretty'),'SimpleFOC_Mini_v1.0')
courtyard=[mm(g.GetStart()) for g in lib.GraphicalItems() if g.GetLayer()==k.F_CrtYd]
assert len(courtyard)>20
# The generated line order is not guaranteed after a library save: stitch endpoints.
lines=[(mm(g.GetStart()),mm(g.GetEnd())) for g in lib.GraphicalItems() if g.GetLayer()==k.F_CrtYd]
ordered=[lines.pop(0)[0]]
# For closed polygon containment, use the source-derived saved offset sequence and
# independently compare all native segment endpoints against it.
expected=json.loads((ROOT/'sources/mini-courtyard.json').read_text())['points_mm']
assert len(courtyard)==len(expected) and max(min(math.dist(p,q) for q in expected) for p in courtyard)<.000003
courtyard=[tuple(p) for p in expected]
assert all(point_inside(p,courtyard) for p in source)
margin=min(ptseg(p,a,z) for p in source for a,z in segs(courtyard))
assert .498<=margin<=.502,margin
rows=[]
for i in range(1,7):
    f=fps[f'J{10+i}'];ox,oy=mm(f.GetPosition());ang=math.radians(f.GetOrientationDegrees());c,s=math.cos(ang),math.sin(ang)
    def world(poly):return [(ox+c*x+s*y,oy-s*x+c*y) for x,y in poly]
    board=world(source);court=world(courtyard)
    for ref,shape in [(f'C{10+i}','circle'),(f'C{20+i}','rectangle')]:
        cf=fps[ref];pads=list(cf.Pads());cx=sum(mm(p.GetPosition())[0] for p in pads)/2;cy=sum(mm(p.GetPosition())[1] for p in pads)/2
        if shape=='circle':
            gap=min(ptseg((cx,cy),a,z) for a,z in segs(board))-6.25
            cgap=min(ptseg((cx,cy),a,z) for a,z in segs(court))-6.25
        else:
            # Conservative native C_Disc 5x2.5mm body, rotated with footprint.
            aa=math.radians(cf.GetOrientationDegrees());cc,ss=math.cos(aa),math.sin(aa)
            body=[(cx+cc*x+ss*y,cy-ss*x+cc*y) for x,y in [(-2.5,-1.25),(2.5,-1.25),(2.5,1.25),(-2.5,1.25)]]
            gap=distance(board,body);cgap=distance(court,body)
            assert not any(point_inside(p,court) for p in body)
        assert cgap>.5,(ref,cgap)
        rows.append(dict(reference=ref,body_to_mini_outline_mm=round(gap,4),body_to_mini_courtyard_mm=round(cgap,4)))
# Standard ATO holder: two pads per electrical terminal, one complete part.
f=fps['F1'];positions={}
for p in f.Pads():positions.setdefault(p.GetNumber(),[]).append(tuple(round(v,3) for v in mm(p.GetPosition())))
assert positions=={'1':[(30.0,112.5),(30.0,115.9)],'2':[(43.47,112.5),(43.47,115.9)]},positions
assert all(abs(k.ToMM(p.GetDrillSize().x)-1.65)<1e-6 for p in f.Pads())
# No encoder signal or supply segment may enter a phase-side corridor above
# the back of a Mini. Exact segment clipping detects crossings, not just endpoints.
encoder={f'A{i}_CS' for i in range(1,7)}|{'SPI_SCK','SPI_MISO','SPI_MOSI','3V3'}
violations=[]
for t in b.GetTracks():
    if t.GetNetname() not in encoder:continue
    a,z=mm(t.GetStart()),mm(t.GetEnd())
    for i in range(1,7):
        x0=5+25*(i-1)
        # Half-column boundary; y>44.75 is the shared rear distribution area.
        lo,hi=0.,1.
        for start,delta,mn,mx in [(a[0],z[0]-a[0],x0-2,x0+12.5),(a[1],z[1]-a[1],0,44.75)]:
            if abs(delta)<1e-9:
                if not mn<start<mx:lo,hi=1,0;break
            else:
                p,q=(mn-start)/delta,(mx-start)/delta
                lo=max(lo,min(p,q));hi=min(hi,max(p,q))
        if lo<hi-1e-7:violations.append(dict(axis=i,net=t.GetNetname(),start=a,end=z))
assert not violations,violations[:10]
report=dict(board_mm=[160,120],mini_courtyard_offset_mm=.5,measured_minimum_offset_mm=round(margin,6),gko_max_endpoint_closure_mm=round(maxgap,6),capacitor_clearances=rows,min_body_to_outline_mm=min(p['body_to_mini_outline_mm'] for p in rows),min_body_to_courtyard_mm=min(p['body_to_mini_courtyard_mm'] for p in rows),encoder_lane_exceptions=violations,keystone_parts_per_fuse=1)
(ROOT/'layout-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(f"PASS: outline +0.5mm courtyard; minimum capacitor/body gap {report['min_body_to_outline_mm']:.4f}mm to board, {report['min_body_to_courtyard_mm']:.4f}mm to courtyard.")
print('PASS: all six encoder columns use the right half; Keystone3557-2 has four holes / one complete holder.')
