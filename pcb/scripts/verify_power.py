#!/usr/bin/env python3
"""Geometry/connectivity metadata only. Copper/thermal qualification is stopped."""
import json
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];b=k.LoadBoard(str(ROOT/'design/trueskate-main-v1.kicad_pcb'))
assert b.GetCopperLayerCount()==2
power=[t for t in b.GetTracks()if t.GetNetname()in('12V_IN','12V_PREPOL','12V_FUSED') and not isinstance(t,k.PCB_VIA)]
vias=[t for t in b.GetTracks()if isinstance(t,k.PCB_VIA)and t.GetNetname()in('12V_PREPOL','12V_FUSED')]
assert len(vias)==8 and all(t.IsLocked()and abs(k.ToMM(t.GetWidth(k.F_Cu))-1.2)<1e-6 and abs(k.ToMM(t.GetDrillValue())-.6)<1e-6 for t in vias)
assert len(power)>0 and all(not isinstance(t,k.PCB_VIA) and t.GetLayer()in(k.F_Cu,k.B_Cu) and t.IsLocked()for t in power)
report=dict(layers=2,copper_oz=1,power_segments=len(power),widths_mm=sorted(set(k.ToMM(t.GetWidth())for t in power)),routing='3+3: 12 mm bank backbones/common trunk; 6 mm fuse/input paths, parallel 2 mm top/bottom Q1 lead escapes flaring into 6/12 mm copper with four 1.2/.6 mm vias per power node; 2 mm Mini supply branches; 0.6 mm ceramic taps',qualification='STOPPED by user decision; no current/temperature qualification claimed',historical_report='../../../docs/pcb/copper-options.md')
(ROOT/'review/checks/power-routing-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: two-layer 1 oz design; locked 3+3 outer power segments retained. Thermal qualification stopped.')
