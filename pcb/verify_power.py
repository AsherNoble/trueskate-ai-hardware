#!/usr/bin/env python3
"""Audit the dedicated L3 power areas and retained wide feeds on native copper."""
import json,math
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parent;b=k.LoadBoard(str(ROOT/'trueskate-main-v1.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
def pad(ref,n):return next(p for p in fps[ref].Pads()if p.GetNumber()==str(n))
def point(p):return k.ToMM(p.x),k.ToMM(p.y)
assert b.GetCopperLayerCount()==4
power=[t for t in b.GetTracks()if t.GetNetname()in('12V_IN','12V_FUSED')]
assert power and all(not isinstance(t,k.PCB_VIA) and t.GetLayer()==k.In2_Cu and t.IsLocked()for t in power)
areas={z.GetNetname():z for z in b.Zones()if z.GetLayer()==k.In2_Cu}
assert set(areas)=={'12V_IN','12V_FUSED'}
for net,z in areas.items():
 assert z.GetPadConnection()==k.ZONE_CONNECTION_FULL
 poly=z.GetFilledPolysList(k.In2_Cu);assert poly.OutlineCount()==1
 # Direct connections at multiple points around each powered plated contact.
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()!=net:continue
   x,y=point(p.GetPosition());r=k.ToMM(p.GetSize().x)/2+.05
   assert any(poly.Contains(k.VECTOR2I(k.FromMM(x+r*math.cos(a)),k.FromMM(y+r*math.sin(a))),-1,0,True)for a in [j*math.pi/4 for j in range(8)]),(f.GetReference(),p.GetNumber())
rows=[]
for i in range(1,7):
 vin,gnd=pad(f'J{10+i}','VIN'),pad(f'J{10+i}','GND')
 assert all(abs(k.ToMM(p.GetSize().x)-2.4)<1e-6 for p in(vin,gnd))
 assert vin.GetNetname()=='12V_FUSED'and gnd.GetNetname()=='GND'
 row=dict(axis=i,supply='direct L3 fused-plane connection; existing 2mm branch retained',return_path='dedicated L2 GND plus outer GND fills')
 for typ,ref in [('bulk',f'C{10+i}'),('ceramic',f'C{20+i}')]:row[typ+'_power_pad_distances_mm']=[round(math.dist(point(pad(ref,n).GetPosition()),point(power.GetPosition())),3)for n,power in[(1,vin),(2,gnd)]]
 rows.append(row)
# Published JLC 2oz inner finished copper is 61um, not the nominal 70um foil.
thickness=.061
def width(current):return (current/(.024*10**.44))**(1/.725)/(thickness/.0254)*.0254
report=dict(bus_current_target_a=12,axis_current_target_a=3,stackup='JLC041622-3313',outer_copper_um=70,inner_copper_um=61,layer='In2.Cu',power_zones={n:dict(connected_regions=z.GetFilledPolysList(k.In2_Cu).OutlineCount(),connection='solid, no thermal spokes')for n,z in areas.items()},input_area_mm=[36,25],fused_area='board-wide plane with input-net clearance and mandatory hole antipads',original_trunk_mm=12,original_branches_mm=2,ipc2221_internal_reference=dict(temperature_rise_c=10,uniform_12a_strip_width_mm=round(width(12),3),uniform_3a_strip_width_mm=round(width(3),3)),sizing_note='The original tracks alone are insufficient as internal uniform strips; broad L3 planes carry current in parallel. The strip equation is a reference, not a plane thermal simulation or proof of connector/pad current rating.',axes=rows)
(ROOT/'power-routing-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: all 12V routing on L3; separate single-region input/fused power areas; all supply contacts connect directly without thermal spokes.')
print(f'12A target retained with broad 61um inner planes; IPC-2221 uniform-strip reference is {width(12):.3f}mm (12A), {width(3):.3f}mm (3A), at 10C rise.')
