#!/usr/bin/env python3
"""Geometry/connectivity metadata only. Copper/thermal qualification is stopped."""
import json
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parent;b=k.LoadBoard(str(ROOT/'trueskate-main-v1.kicad_pcb'))
assert b.GetCopperLayerCount()==2
power=[t for t in b.GetTracks()if t.GetNetname()in('12V_IN','12V_FUSED')]
assert len(power)==51 and all(not isinstance(t,k.PCB_VIA) and t.GetLayer()in(k.F_Cu,k.B_Cu) and t.IsLocked()for t in power)
report=dict(layers=2,copper_oz=1,power_segments=len(power),widths_mm=sorted(set(k.ToMM(t.GetWidth())for t in power)),routing='Original outer-layer input, fuse, bus and Mini feeds restored from 62ef1ea conversion log',qualification='STOPPED by user decision; no current/temperature qualification claimed',historical_report='../docs/pcb/copper-options.md')
(ROOT/'power-routing-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: two-layer 1 oz design; 51 original locked outer power segments retained. Thermal qualification stopped.')
