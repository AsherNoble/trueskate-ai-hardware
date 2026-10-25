#!/usr/bin/env python3
"""Reset stitch records for a freshly rebuilt 3+3 board; fill before adding stitches."""
import json
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'design/trueskate-main-v1.kicad_pcb'
b=k.LoadBoard(str(PCB))
assert not any(isinstance(t,k.PCB_VIA) and t.GetNetname()=='GND' for t in b.GetTracks())
for name in ['ground-stitching','ground-links','ground-link-plan']:
 (ROOT/f'design/data/{name}.json').write_text('[]\n')
for z in b.Zones():z.SetIslandRemovalMode(k.ISLAND_REMOVAL_MODE_ALWAYS)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(PCB),b,True)
