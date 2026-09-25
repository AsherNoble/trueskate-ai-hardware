#!/usr/bin/env python3
"""Independent generated-board checks; use KiCad's bundled Python.

This validates selected data/geometry invariants, not analog operation or routing.
"""
import json
from pathlib import Path
import pcbnew as k

root=Path(__file__).resolve().parent
board=k.LoadBoard(str(root/"trueskate-main-v1.kicad_pcb"))
parts=json.loads((root/"circuit.json").read_text())
fps={f.GetReference():f for f in board.GetFootprints()}
def pad(ref,num):
    return next(p for p in fps[ref].Pads() if p.GetNumber()==str(num))
def pos(ref,num):
    p=pad(ref,num).GetPosition()
    return round(k.ToMM(p.x),4),round(k.ToMM(p.y),4)
def net(ref,num): return pad(ref,num).GetNetname()
for part in parts:
    assert part["ref"] in fps
    for number,name in zip(part["pins"],part["nets"]):
        assert net(part["ref"],number)==(name or ""),(part["ref"],number,name)
    if part["assembly"]=="JLCPCB": assert part["lcsc"].startswith("C")

# Independent anchors from PJRC's top-view pinout, USB at left, VIN row above.
assert pos("J2",1)==(44,60) and net("J2",1)=="VIN_OR"
assert pos("J1",1)==(44,75.24) and net("J1",1)=="GND"
assert pos("J1",24)==(102.42,75.24)
assert net("J1",2)=="A4_PWM2"  # Teensy 0
assert net("J2",16)=="WRIST_TX_ENABLE"  # Teensy 41
assert net("J2",22)=="WRIST_TX"  # Teensy 35
assert net("J2",23)=="WRIST_RX"  # Teensy 34
for i in range(1,7):
    assert net(f"J{10+i}",2)==""  # Never join the Mini's regulator output.
    assert net(f"J{10+i}",9)==f"A{i}_EN"
    assert net(f"J{40+i}",1)=="12V_PROTECTED"
    assert net(f"J{40+i}",2)==f"PGND{i}"
    assert abs(pos(f"C{10+i}",2)[0]-pos(f"C{10+i}",1)[0])==5
    assert net(f"J{30+i}",5)=="3V3"  # Provisional cable order, not confirmation.
    assert net(f"J{30+i}",6)=="GND"
assert fps["R8"].IsDNP()
assert net("U5",5)=="BUCK_5V" and net("U6",5)=="3V3"
assert net("U2",11)=="WRIST_TX_ALLOWED"
assert net("U2",12)=="WRIST_TX_ENABLE" and net("U2",13)=="KILL_OK"
assert board.GetCopperLayerCount()==2
assert pos("NT1",1)==(18,22)  # Ground junction stays near the input, not at the far edge.
assert len(list(board.Zones()))==1
assert next(iter(board.Zones())).GetNetname()=="GND"  # Never merge PGND branches with a blanket pour.
print(f"PASS: {len(parts)} parts match generated net data; socket orientation and selected safety invariants hold.")
tracks=list(board.GetTracks())
via_count=sum(isinstance(t,k.PCB_VIA) for t in tracks)
print(f"Board has {len(tracks)-via_count} deliberate track segments, {via_count} vias and one local buck-ground zone; final routing is NOT complete.")
