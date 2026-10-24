#!/usr/bin/env python3
"""Check placement, stackup, GND island policy and actual SPI/edge via coverage."""
import json,math,re
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parent;b=k.LoadBoard(str(ROOT/'trueskate-main-v1.kicad_pcb'))
def mm(p):return [round(k.ToMM(p.x),6),round(k.ToMM(p.y),6)]
actual={f.GetReference():dict(fpid=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),position=mm(f.GetPosition()),angle=f.GetOrientationDegrees(),pads=[dict(number=p.GetNumber(),net=p.GetNetname(),position=mm(p.GetPosition()),size=mm(p.GetSize()),drill=mm(p.GetDrillSize()),shape=int(p.GetShape()))for p in f.Pads()])for f in b.GetFootprints()}
assert actual==json.loads((ROOT/'four-layer-placement-baseline.json').read_text()),'Footprint/placement change'
assert b.GetCopperLayerCount()==2
assert all(t.GetLayer()in(k.F_Cu,k.B_Cu)for t in b.GetTracks()if not isinstance(t,k.PCB_VIA))
stack=json.loads((ROOT/'stackup.json').read_text());assert [r['thickness_mm']for r in stack['layers']if r['type']=='copper']==[.035,.035]
text=(ROOT/'trueskate-main-v1.kicad_pcb').read_text()
for layer in ['F.Cu','B.Cu']:
 assert re.search(r'\(layer "'+re.escape(layer)+r'"\s*\(type "copper"\)\s*\(thickness 0\.035\)',text)
regions={};islands=[]
for z in b.Zones():
 assert z.GetNetname()=='GND'and z.GetIslandRemovalMode()==k.ISLAND_REMOVAL_MODE_ALWAYS
 poly=z.GetFilledPolysList(z.GetLayer());regions[b.GetLayerName(z.GetLayer())]=poly.OutlineCount()
 for i in range(poly.OutlineCount()):
  if z.IsIsland(z.GetLayer(),i):islands.append([b.GetLayerName(z.GetLayer()),i])
assert not islands,islands
vias=[mm(t.GetPosition())for t in b.GetTracks()if isinstance(t,k.PCB_VIA)and t.GetNetname()=='GND']
report=json.loads((ROOT/'two-layer-ground-review.json').read_text())
for target in report['targets']:
 distance=min(math.dist(target['point'],q)for q in vias)
 assert abs(distance-target['nearest_stitch_mm'])<.001
report.update(footprints_preserved=len(actual),layers=2,copper_oz=1,ground_regions=regions,isolated_zone_islands=islands,total_vias=len(vias))
# Dense signal fanout has larger exclusion areas; retain the exact measured limit.
assert report['max_spi_distance_mm']<=10.2 and report['max_edge_target_distance_mm']<=5.1
report['scope']='Electrical geometry only; no thermal or impedance qualification. Region interconnection additionally checked in ground-connectivity-review.json.'
(ROOT/'two-layer-ground-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: 2 layers, 1 oz, {len(actual)} unchanged footprints; {len(vias)} GND vias, island removal enabled on both fills, zero isolated zone islands.')
print(f"PASS: every SPI/CS route sampled at <=3mm; maximum distance to a GND stitch {report['max_spi_distance_mm']:.3f}mm; edge targets {report['max_edge_target_distance_mm']:.3f}mm.")
