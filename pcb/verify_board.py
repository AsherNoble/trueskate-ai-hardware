#!/usr/bin/env python3
"""Independent netlist, THT, geometry and immutable-manual-routing checks.

Run after KiCad XML netlist export. Uses KiCad's bundled Python. Strict DRC/ERC
are separate: these checks do not establish physical current or signal margins.
"""
import collections
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as k
root=Path(__file__).resolve().parent
b=k.LoadBoard(str(root/'trueskate-main-v1.kicad_pcb'))
parts=json.loads((root/'circuit.json').read_text())
fps={f.GetReference():f for f in b.GetFootprints()}
def pad(ref,n): return next(p for p in fps[ref].Pads() if p.GetNumber()==str(n))
def rawnet(ref,n): return pad(ref,n).GetNetname()
def net(ref,n):
    name=rawnet(ref,n)
    return '' if name.startswith('unconnected-') else name
def pos(ref,n):
    p=pad(ref,n).GetPosition();return round(k.ToMM(p.x),4),round(k.ToMM(p.y),4)

# Compare independently parsed KiCad schematic netlist with actual PCB pads.
xml=ET.parse(root/'netlist-review.xml')
sch={}
for n in xml.findall('./nets/net'):
    for node in n.findall('node'): sch[(node.attrib['ref'],node.attrib['pin'])]=n.attrib['name']
board={}
for p in parts:
    f=fps[p['ref']]
    assert f.GetAttributes() & k.FP_THROUGH_HOLE,(p['ref'],'not through-hole')
    for number,name in zip(p['pins'],p['nets']):
        actual=rawnet(p['ref'],number)
        assert actual==name if name else actual.startswith('unconnected-'),(p['ref'],number,actual,name)
        board[(p['ref'],number)]=actual
    assert all(x.GetAttribute()==k.PAD_ATTRIB_PTH for x in f.Pads() if x.GetNumber()),p['ref']
assert board==sch,'PCB/schematic net mismatch'
unused=collections.Counter(n for n in board.values() if n.startswith('unconnected-'))
assert len(unused)==34 and all(count==1 for count in unused.values())
assert not any(t.GetNetname().startswith('unconnected-') for t in b.GetTracks())

# PJRC top-view anchors, USB at left. Deliberately unused VIN and former v2 pins.
assert pos('J2',1)==(44,60) and net('J2',1)==''
assert pos('J1',1)==(44,75.24) and net('J1',1)=='GND'
assert pos('J1',24)==(102.42,75.24)
assert net('J1',2)=='A4_PWM2'
for pin in (16,22,23): assert net('J2',pin)==''  # Teensy 41,35,34.
geometry=json.loads((root/'sources/mini-geometry.json').read_text())
for i in range(1,7):
    mini=f'J{10+i}';origin=pos(mini,9);sign=-1 if i<=3 else 1
    for group,prefix in [('control',''),('phase','P'),('power','')]:
        for point in geometry['connectors'][group]:
            x,y=pos(mini,prefix+point['pin'])
            assert abs(x-origin[0]-sign*point['x_mm'])<.0001
            assert abs(y-origin[1]-sign*point['y_mm'])<.0001
    for unused_contact in (2,6,8,10): assert net(mini,unused_contact)==''
    assert net(mini,9)==net(f'R{20+i}',1)==f'A{i}_EN'
    assert net(f'R{20+i}',2)==net(mini,'GND')==f'PGND{i}'
    assert net(mini,'VIN')=='12V_FUSED'
    assert [net(f'J{30+i}',p) for p in range(1,7)]==['SPI_SCK','SPI_MISO','SPI_MOSI',f'A{i}_CS','3V3','GND']
    assert net(f'JP{i}',1)==net(mini,1)==net(mini,4)==f'CGND{i}'
    assert net(f'JP{i}',2)=='GND'
    for phase in (1,2,3): assert net(f'J{20+i}',phase)==net(mini,f'P{4-phase}')==f'A{i}_PH{phase}'
    assert abs(pos(f'C{10+i}',2)[1]-pos(f'C{10+i}',1)[1])==5
    assert f'J{40+i}' not in fps
assert pos('NT1',1)==(22,69)
assert len(list(b.Zones()))==2 and all(z.GetNetname()=='GND' for z in b.Zones())
assert b.GetCopperLayerCount()==2 and len(fps)==51
assert k.ToMM(b.GetDesignSettings().m_SolderMaskMinWidth)>=.1

def signature(t):
    points=sorted([(round(k.ToMM(t.GetStart().x),6),round(k.ToMM(t.GetStart().y),6)),
                   (round(k.ToMM(t.GetEnd().x),6),round(k.ToMM(t.GetEnd().y),6))])
    return t.GetNetname(),t.GetLayerName(),round(k.ToMM(t.GetWidth(k.F_Cu) if isinstance(t,k.PCB_VIA) else t.GetWidth()),6),tuple(points)
expected=collections.Counter((t['net'],t['layer'],round(t['width'],6),tuple(sorted(map(tuple,[t['start'],t['end']]))))
                            for t in json.loads((root/'manual-routes.json').read_text()))
actual=collections.Counter(signature(t) for t in b.GetTracks() if t.IsLocked() and not isinstance(t,k.PCB_VIA))
links=collections.Counter((t['net'],t['layer'],round(t['width'],6),tuple(sorted(map(tuple,[t['start'],t['end']]))))
                          for t in json.loads((root/'ground-links.json').read_text()))
assert actual==expected+links,'Manual power/ground routing was altered'
stitches=json.loads((root/'ground-stitching.json').read_text())
ground_vias=[t for t in b.GetTracks() if t.IsLocked() and isinstance(t,k.PCB_VIA)]
assert {(round(k.ToMM(t.GetPosition().x),3),round(k.ToMM(t.GetPosition().y),3)) for t in ground_vias}=={(v['x'],v['y']) for v in stitches}
assert all(t.GetNetname()=='GND' for t in ground_vias)
from route_signals import SIGNALS
assert all(t.IsLocked() or t.GetNetname() in SIGNALS for t in b.GetTracks()),'Unapproved automatic net'
tracks=list(b.GetTracks());vias=sum(isinstance(t,k.PCB_VIA) for t in tracks)
print(f'PASS: {len(board)-len(unused)} connected pads + {len(unused)} isolated NC contacts agree with KiCad netlist; all 47 references THT.')
print('PASS: verified Mini geometry, encoder order, USB-only VIN isolation, 6 EN pulldowns, 6 open bridges.')
print(f'PASS: {sum(expected.values())} manual copper segments unchanged; {len(tracks)-vias} total segments, {vias} vias.')
print(f'PASS: {sum(links.values())} deliberate quiet-GND link segments and {len(stitches)} locked GND vias.')
for name in ('SPI_SCK','SPI_MOSI','SPI_MISO'):
    ts=[t for t in tracks if t.GetNetname()==name]
    length=sum(k.ToMM(t.GetLength()) for t in ts if not isinstance(t,k.PCB_VIA))
    coords=[(k.ToMM(p.x),k.ToMM(p.y)) for t in ts for p in (t.GetStart(),t.GetEnd())]
    assert all(37<=x<=145 and 44<=y<=83.8 for x,y in coords),(name,'left the quiet logic region')
    print(f'{name}: {length:.1f} mm total branched copper, within central logic region (not one cable length).')
