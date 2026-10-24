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
    assert f.GetAttributes() & (k.FP_SMD if p['assembly']=='JLCPCB' else k.FP_THROUGH_HOLE),(p['ref'],'assembly mismatch')
    for number,name in zip(p['pins'],p['nets']):
        actual=rawnet(p['ref'],number)
        assert actual==name if name else actual.startswith('unconnected-'),(p['ref'],number,actual,name)
        board[(p['ref'],number)]=actual
    assert all(x.GetAttribute()==(k.PAD_ATTRIB_SMD if p['assembly']=='JLCPCB' else k.PAD_ATTRIB_PTH) for x in f.Pads() if x.GetNumber()),p['ref']
assert board==sch,'PCB/schematic net mismatch'
unused=collections.Counter(n for n in board.values() if n.startswith('unconnected-'))
assert len(unused)==36 and all(count==1 for count in unused.values())
assert not any(t.GetNetname().startswith('unconnected-') for t in b.GetTracks())

# Independent interface checks; placement fit is also checked by strict DRC.
assert net('J2',1)=='' and net('J1',1)=='GND'
assert net('J1',2)=='A4_PWM2'
assert pos('J2',1)==(140,118.03) and pos('J1',24)==(155.24,59.61)
for i in range(1,7):
    mini=f'J{10+i}'
    assert net(mini,9)==net(f'R{20+i}',1)==f'A{i}_EN'
    assert net(f'R{20+i}',2)==net(mini,'GND')=='GND'
    assert net(mini,'VIN')=='12V_FUSED'
    assert net(f'R{30+i}',1)==f'A{i}_CS' and net(f'R{30+i}',2)=='3V3'
    assert net(mini,1)==net(mini,4)=='GND'
    assert fps[f'J{30+i}'].GetOrientationDegrees()==180
    assert abs(pos(f'J{30+i}',1)[1]-5.3)<1e-5
    for phase in (1,2,3):assert net(f'J{20+i}',phase)==net(mini,f'P{4-phase}')==f'A{i}_PH{phase}'
    assert f'J{40+i}' not in fps
assert len(list(b.Zones()))==2 and all(z.GetNetname()=='GND' for z in b.Zones())
assert b.GetCopperLayerCount()==2 and len(fps)==62
assert k.ToMM(b.GetDesignSettings().m_SolderMaskMinWidth)>=.1

def signature(t):
    points=sorted([(round(k.ToMM(t.GetStart().x),6),round(k.ToMM(t.GetStart().y),6)),
                   (round(k.ToMM(t.GetEnd().x),6),round(k.ToMM(t.GetEnd().y),6))])
    return t.GetNetname(),t.GetLayerName(),round(k.ToMM(t.GetWidth(k.F_Cu) if isinstance(t,k.PCB_VIA) else t.GetWidth()),6),tuple(points)
expected=collections.Counter((t['net'],t['layer'],round(t['width'],6),tuple(sorted(map(tuple,[t['start'],t['end']]))))
                            for t in json.loads((root/'manual-routes.json').read_text()))
for trim in json.loads((root/'encoder-tail-trims.json').read_text()):
    for key,delta in [('before',-1),('after',1)]:
        t=trim[key]
        if t is None:continue
        expected[(t['net'],t['layer'],round(t['width'],6),tuple(sorted(map(tuple,[t['start'],t['end']]))))]+=delta
expected=+expected
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
print(f'PASS: schematic/PCB agree for {len(board)} contacts, including {len(unused)} isolated NC contacts.')
print('PASS: six SMD outward-facing JST connectors; all other fitted parts THT; unchanged Teensy map.')
print(f'PASS: {sum(expected.values())} locked manual segments and {len(stitches)} ground stitches retained.')
