#!/usr/bin/env python3
"""Replay the reviewed ground-via geometry rather than reseeding a heuristic."""
from pathlib import Path
import json
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'design/trueskate-main-v1.kicad_pcb'
b=k.LoadBoard(str(PCB));rows=json.loads((ROOT/'design/data/ground-stitching.json').read_text())
assert not any(isinstance(t,k.PCB_VIA)and t.GetNetname()=='GND'for t in b.GetTracks())
for row in rows:
 v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I(k.FromMM(row['x']),k.FromMM(row['y'])));v.SetWidth(k.FromMM(row['diameter']));v.SetDrill(k.FromMM(row['drill']));v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetViaType(k.VIATYPE_THROUGH);v.SetNet(b.GetNetsByName()['GND']);v.SetLocked(True);b.Add(v)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(PCB),b,True)
print('Replayed',len(rows),'reviewed GND stitches.')
