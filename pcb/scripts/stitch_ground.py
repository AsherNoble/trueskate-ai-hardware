#!/usr/bin/env python3
"""Add clearance-checked GND stitching at the edge and along every SPI/CS route.

Run on the restored two-layer board after filling. At least one connected ground fill
must touch each added via; the via joins and restores the opposite-side fill. Disconnected zone islands are removed on final fill.
"""
import json,math
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'design/trueskate-main-v1.kicad_pcb'
b=k.LoadBoard(str(PCB));assert b.GetCopperLayerCount()==2
xy=lambda x,y:k.VECTOR2I(k.FromMM(x),k.FromMM(y))
mm=lambda p:(k.ToMM(p.x),k.ToMM(p.y))
for z in b.Zones():z.SetIslandRemovalMode(k.ISLAND_REMOVAL_MODE_ALWAYS)
k.ZONE_FILLER(b).Fill(b.Zones())
polys=[z.GetFilledPolysList(z.GetLayer()) for z in b.Zones()]
assert len(polys)==2
holes=[];pads=[];segments=[];original=[];ground_ends=[]
for f in b.GetFootprints():
 for p in f.Pads():
  x,y=mm(p.GetPosition());size=mm(p.GetSize());drill=mm(p.GetDrillSize())
  if max(drill)>0:holes.append((x,y,max(drill)/2))
  if p.GetNetname()!='GND':pads.append((x,y,max(size)/2 if p.GetShape()==k.PAD_SHAPE_CIRCLE else math.hypot(*size)/2))
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):
  x,y=mm(t.GetPosition());holes.append((x,y,k.ToMM(t.GetDrillValue())/2))
  if t.GetNetname()=='GND':original.append((x,y))
  else:pads.append((x,y,k.ToMM(t.GetWidth(k.F_Cu))/2))
 elif t.GetNetname()!='GND':segments.append((*mm(t.GetStart()),*mm(t.GetEnd()),k.ToMM(t.GetWidth())/2))
 else:ground_ends.extend([mm(t.GetStart()),mm(t.GetEnd())])
def allowed(x,y):
 if not(1.25<=x<=158.75 and 1.25<=y<=118.75):return False
 if any(.00001<math.dist((x,y),p)<.65 for p in ground_ends):return False
 for px,py,r in holes:
  if math.hypot(x-px,y-py)<r+.15+.46:return False
 for px,py,r in pads:
  if math.hypot(x-px,y-py)<r+.35+.31:return False
 for ax,ay,zx,zy,r in segments:
  if x<min(ax,zx)-r-.7 or x>max(ax,zx)+r+.7 or y<min(ay,zy)-r-.7 or y>max(ay,zy)+r+.7:continue
  dx,dy=zx-ax,zy-ay
  f=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy))) if dx or dy else 0
  if math.hypot(x-ax-f*dx,y-ay-f*dy)<r+.35+.31:return False
 return any(poly.Contains(xy(x,y)) for poly in polys)
cache={}
def valid(p):
 if p not in cache:cache[p]=allowed(*p)
 return cache[p]
added=[];existing=original[:];targets=[]
spi={'SPI_SCK','SPI_MISO','SPI_MOSI'}|{f'A{i}_CS' for i in range(1,7)}
for side in ['front','back','left','right']:
 length=160 if side in ['front','back'] else 120
 for n in range(2,length,8):
  p={'front':(n,2),'back':(n,118),'left':(2,n),'right':(158,n)}[side]
  targets.append(dict(kind='edge',group=side,point=p))
# Sample EVERY segment, including all six column branches and the rear fanout.
for t in b.GetTracks():
 if t.GetNetname() not in spi:continue
 a,z=mm(t.GetStart()),mm(t.GetEnd());n=max(1,math.ceil(math.dist(a,z)/3))
 for i in range(n+1):targets.append(dict(kind='SPI',group=t.GetNetname(),point=(a[0]+(z[0]-a[0])*i/n,a[1]+(z[1]-a[1])*i/n)))
# Greedily cover targets; conservative obstacle shapes are checked on both sides.
for target in targets:
 p=target['point'];limit=4.5 if target['kind']=='SPI' else 5
 if existing and min(math.dist(p,v) for v in existing)<=limit:continue
 candidates=[]
 for ix in range(-20,21):
  for iy in range(-20,21):
   q=(round(p[0]*2)/2+ix*.5,round(p[1]*2)/2+iy*.5)
   distance=math.dist(p,q)
   if distance>10:continue
   if target['kind']=='edge' and min(q[0],160-q[0],q[1],120-q[1])>4:continue
   candidates.append((distance,q))
 for distance,q in sorted(candidates):
  if any(math.dist(q,v)<1.0 for v in existing) or not valid(q):continue
  added.append(dict(x=q[0],y=q[1],diameter=.7,drill=.3,reason=target['kind']+' stitch near '+target['group']))
  existing.append(q);break
for row in added:
 v=k.PCB_VIA(b);v.SetPosition(xy(row['x'],row['y']));v.SetWidth(k.FromMM(.7));v.SetDrill(k.FromMM(.3));v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetViaType(k.VIATYPE_THROUGH);v.SetNet(b.GetNetsByName()['GND']);v.SetLocked(True);b.Add(v)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(PCB),b,True)
previous=json.loads((ROOT/'design/data/ground-stitching.json').read_text());known={(r['x'],r['y']) for r in previous}
assert known==set(original)
(ROOT/'design/data/ground-stitching.json').write_text(json.dumps(previous+added,indent=2)+'\n')
for target in targets:target['nearest_stitch_mm']=round(min(math.dist(target['point'],q) for q in existing),3)
report=dict(original_vias=len(original),added_vias=len(added),total_vias=len(existing),via_diameter_mm=.7,via_drill_mm=.3,edge_target_pitch_mm=8,spi_sample_pitch_max_mm=3,targets=targets,max_spi_distance_mm=max(t['nearest_stitch_mm'] for t in targets if t['kind']=='SPI'),max_edge_target_distance_mm=max(t['nearest_stitch_mm'] for t in targets if t['kind']=='edge'),island_removal='ALWAYS on both GND zones')
(ROOT/'review/checks/two-layer-ground-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('Added',len(added),'stitches; total',len(existing),'SPI max distance',report['max_spi_distance_mm'],'edge max distance',report['max_edge_target_distance_mm'],flush=True)
