#!/usr/bin/env python3
"""Independent carrier allocation and scope checks; no hardware is touched."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
d=json.loads((ROOT/"design.json").read_text())
pwm={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,18,19,22,23,24,25,28,29,33,36,37}
expected=[([4,5,6],16,26),([2,22,23],17,27),([7,36,29],20,32),
          ([24,0,25],21,38),([3,33,37],30,39),([8,9,28],31,40)]
used=[]
for a,(pins,en,cs) in zip(d['axes'],expected):
    assert (a['pwm'],a['enable'],a['cs'])==(pins,en,cs)
    assert set(pins)<=pwm and en not in pwm and cs not in pwm
    used+=pins+[en,cs]
assert len(d['axes'])==6
assert d['spi0']==dict(mosi=11,miso=12,sck=13)
used += list(d['spi0'].values())
assert len(used)==len(set(used))==33
assert set(range(42))-set(used)==set(d['unused_pins'])
assert d['encoder_pin_order']==['CLK','MISO','MOSI','CSn','3V3','GND']
assert d['board_mm']==[160,120] and d['layers']==2
ini=(ROOT.parent/'firmware/platformio.ini').read_text()
assert 'lib_archive = no' in ini
assert '-D SIMPLEFOC_TEENSY4_FORCE_CENTER_ALIGNED_3PWM' not in ini
parts=json.loads((ROOT/'circuit.json').read_text())
assert len(parts)==53
assert not any(p['assembly']=='JLCPCB' for p in parts)
assert not any(p['ref'].startswith(('U','Q','D')) for p in parts)
settings=json.loads((ROOT/'trueskate-main-v1.kicad_pro').read_text())['board']['design_settings']
for key,value in dict(min_clearance=.2,min_track_width=.2,min_via_diameter=.7,
                      min_via_annular_width=.2,min_hole_clearance=.45,
                      min_hole_to_hole=.45,min_copper_edge_clearance=.5,
                      min_silk_clearance=.15,min_text_height=1,min_text_thickness=.15).items():
    assert settings['rules'][key]>=value,(key,settings['rules'][key])
assert not settings.get('drc_exclusions')
assert all(value!='ignore'for value in settings['rule_severities'].values())
print('PASS: unchanged six-axis map; 18 PWM; 12 plain-digital EN/CS; SPI0; 9 spare contacts.')
print('PASS: USB-only passive carrier scope; 53 schematic references; no factory assembly.')
print('PASS: conservative two-layer rules persisted; no DRC exclusions or ignored checks.')
print('Static checks only. Six-axis electrical operation still requires bench testing.')
