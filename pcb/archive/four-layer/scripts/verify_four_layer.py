#!/usr/bin/env python3
"""Audit native stack, placement and filled L2 beneath every SPI/CS/EN trace."""
import json,math
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parent;b=k.LoadBoard(str(ROOT/'trueskate-main-v1.kicad_pcb'))
def mm(p):return [round(k.ToMM(p.x),6),round(k.ToMM(p.y),6)]
def xy(x,y):return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
actual={f.GetReference():dict(fpid=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),position=mm(f.GetPosition()),angle=f.GetOrientationDegrees(),pads=[dict(number=p.GetNumber(),net=p.GetNetname(),position=mm(p.GetPosition()),size=mm(p.GetSize()),drill=mm(p.GetDrillSize()),shape=int(p.GetShape())) for p in f.Pads()])for f in b.GetFootprints()}
assert actual==json.loads((ROOT/'four-layer-placement-baseline.json').read_text()),'Footprint/placement change'
assert b.GetCopperLayerCount()==4
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):continue
 assert t.GetLayer()!=k.In1_Cu,'L2 must contain no traces'
 if t.GetNetname() in ('12V_IN','12V_FUSED'):assert t.GetLayer()==k.In2_Cu
 else:assert t.GetLayer() in (k.F_Cu,k.B_Cu)
l2=[z for z in b.Zones()if z.GetLayer()==k.In1_Cu]
assert len(l2)==1 and l2[0].GetNetname()=='GND'
plane=l2[0].GetFilledPolysList(k.In1_Cu);assert plane.OutlineCount()==1,plane.OutlineCount()
protected={'SPI_SCK','SPI_MOSI','SPI_MISO','EN_DISABLE'}|{f'A{i}_{s}'for i in range(1,7)for s in ('CS','EN','EN_CMD')}
# Non-ground through-hole contacts need insulating antipads even on a solid
# ground plane. Exempt only each protected net's own terminal/transition holes.
terminals={}
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetNetname() in protected and p.GetAttribute()==k.PAD_ATTRIB_PTH:
   # Use the real pad bounding box, enlarged by zone clearance; circle/rect.
   q=p.GetBoundingBox();terminals.setdefault(p.GetNetname(),[]).append((k.ToMM(q.GetX())-.3,k.ToMM(q.GetY())-.3,k.ToMM(q.GetRight())+.3,k.ToMM(q.GetBottom())+.3))
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA) and t.GetNetname() in protected:
  x,y=mm(t.GetPosition());r=k.ToMM(t.GetWidth(k.In1_Cu))/2+.3
  terminals.setdefault(t.GetNetname(),[]).append((x-r,y-r,x+r,y+r))
violations=[];samples=0;terminal_samples=0;segments=0
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA) or t.GetNetname()not in protected:continue
 segments+=1;a,z=mm(t.GetStart()),mm(t.GetEnd());dx,dy=z[0]-a[0],z[1]-a[1];length=math.hypot(dx,dy)
 if not length:continue
 half=k.ToMM(t.GetWidth())/2;n=math.ceil(length/.025)
 for i in range(n+1):
  u=i/n;cx,cy=a[0]+u*dx,a[1]+u*dy
  for offset in (-half,0,half):
   x,y=cx-dy/length*offset,cy+dx/length*offset;samples+=1
   if plane.Contains(xy(x,y),-1,0,True):continue
   if any(x0-1e-5<=x<=x1+1e-5 and y0-1e-5<=y<=y1+1e-5 for x0,y0,x1,y1 in terminals.get(t.GetNetname(),[])):
    terminal_samples+=1;continue
   violations.append(dict(net=t.GetNetname(),layer=t.GetLayerName(),xy=[round(x,4),round(y,4)],uuid=t.m_Uuid.AsString()))
report=dict(stackup=json.loads((ROOT/'stackup.json').read_text())['name'],footprints_preserved=len(actual),l2_connected_ground_regions=plane.OutlineCount(),l2_trace_count=0,protected_signal_segments=segments,coverage_sample_pitch_mm=.025,trace_width_sampled_at=['left edge','centre','right edge'],samples=samples,own_terminal_antipad_samples=terminal_samples,unreferenced_samples=violations,scope='No intentional L2 splits; mandatory non-GND PTH/via antipads at own terminals are excepted. L4 is adjacent to L3 power, not directly to L2.')
(ROOT/'four-layer-review.json').write_text(json.dumps(report,indent=2)+'\n')
assert not violations,(len(violations),violations[:12])
print(f'PASS: 4 layers, {len(actual)} unchanged footprints/placements, all routed 12V on L3, zero L2 traces.')
print(f'PASS: one connected L2 GND plane; {segments} SPI/CS/EN segments checked across width at 0.025mm pitch; only own terminal antipads excepted.')
