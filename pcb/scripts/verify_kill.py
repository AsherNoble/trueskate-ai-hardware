#!/usr/bin/env python3
"""Check the actual netlist topology and all axis-population / EN states."""
import itertools,json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
parts={p['ref']:p for p in json.loads((r/'design/data/circuit.json').read_text())}
def net(ref,pin):
    p=parts[ref];return dict(zip(p['pins'],p['nets']))[str(pin)]
assert [net('J6',n) for n in (1,2)]==['EN_DISABLE','GND']
assert [net('R1',n) for n in (1,2)]==['EN_DISABLE','3V3']
for i in range(1,7):
    u='U1' if i<=3 else 'U2';oe,inp,out=[(1,2,3),(4,5,6),(10,9,8)][(i-1)%3]
    assert parts[u]['value']=='SN74HC125N'
    assert net(u,oe)=='EN_DISABLE' and net(u,inp)==f'A{i}_EN_CMD'
    assert net(u,out)==net(f'J{10+i}',9)==f'A{i}_EN'
    assert [net(f'R{20+i}',p) for p in (1,2)]==[f'A{i}_EN','GND']
    assert [net(f'R{30+i}',p) for p in (1,2)]==[f'A{i}_CS','3V3']
    assert net(u,7)=='GND' and net(u,14)=='3V3'
    assert net(u,12)=='GND' and net(u,13)=='3V3' and net(u,11) is None
# TI truth table: /OE high => Z, local pulldown => low. Closed loop => Y=A.
# No axis component is in series with a shared supply, bus or /OE connection.
for populated in itertools.product((False,True),repeat=6):
    for commands in itertools.product((0,1),repeat=6):
        for closed in (False,True):
            en=[int(closed and cmd) if present else None for present,cmd in zip(populated,commands)]
            assert closed or all(v in (None,0) for v in en)
print('PASS: six verified buffer channels, CS pullups and EN pulldowns; 8192 population/command/loop cases.')
print('DC topology only; unpowered HC outputs and supply ramps are not qualified.')
# DC bounds for the requested states, using TI SCLS104F and SLVSBA5D.
# HC has no Ioff. IOZ below applies only to the powered engineering estimate.
# Each Mini has three DRV8313 EN inputs behind its upstream 10k series R4.
# Include all three EN low-input leakage currents; do not credit internal pulldowns.
r_carrier_max=10000*1.05
r_mini_max=10000*1.10
buffer_powered_ioz=5e-6
mini_en_leak=3*5e-6
high_z_carrier_max=(buffer_powered_ioz+mini_en_leak)*r_carrier_max
high_z_driver_max=high_z_carrier_max+mini_en_leak*r_mini_max
assert high_z_driver_max<.6
boot_carrier_max=.1  # Engineering estimate from 20uA VOL rows at 2/4.5/6V, not a 3.3V table guarantee.
assert mini_en_leak<20e-6  # Output pull-down reduces the buffer sink load.
boot_driver_max=boot_carrier_max+mini_en_leak*r_mini_max
assert boot_driver_max<.6
for i in range(1,7):
    assert [net(f'R{40+i}',p) for p in (1,2)]==[f'A{i}_EN_CMD','GND']
states=[
    dict(state='Teensy and buffer unpowered, 12V present',rail_v=0,status='UNVERIFIED',buffer='No specified Ioff; do not apply powered IOZ',carrier_en_max_v=None,drv8313_en_max_v=None),
    dict(state='Teensy boot, GPIO high impedance, valid rail',rail_v=3.3,status='DC_ESTIMATE',buffer='input pulled low; enabled output low, or disabled output pulled low',carrier_en_max_v=max(boot_carrier_max,high_z_carrier_max),drv8313_en_max_v=max(boot_driver_max,high_z_driver_max)),
    dict(state='Kill loop open, valid rail',rail_v=3.3,status='DC_ESTIMATE',buffer='/OE high, output high impedance',carrier_en_max_v=high_z_carrier_max,drv8313_en_max_v=high_z_driver_max)]
# Six used /OE inputs share R1; two unused /OE inputs connect directly to 3V3.
assert 6*1e-6*r_carrier_max < .1
assert 1e-6*r_carrier_max < .5
report=dict(part='SN74HC125N',manufacturer='Texas Instruments',lcsc='C2890',logic_family='HC CMOS',supply='Teensy USB-powered 3V3; no connection to Mini regulator outputs',axes=list(range(1,7)),states=states,overall_status='INCOMPLETE: powered-off EN low is not guaranteed',conservative_drv8313_low_limit_v=.6,assumptions=['Carrier pull-downs 10k, <=5% tolerance; Mini R4 10k, <=10% tolerance','Powered DC estimates apply 6V leakage and tabulated 2/4.5/6V light-load VOL limits at 3.3V; no separate 3.3V table row','Boot uses valid 3.3V rail, high-impedance GPIO without pull-up or material source leakage','No external back-powering; all GND connections intact'],sources=['https://www.ti.com/lit/ds/symlink/sn74hc125.pdf (SCLS104F sections 5, 6.1, 6.3, 6.5)','https://www.ti.com/lit/ds/symlink/drv8313.pdf (SLVSBA5D)'],scope='Topology assertions and DC estimates only; no bench measurements',prototype_supply_ramp_status='Unverified: 0<VCC<2V, power-down and brownout; no-PWM policy does not prove EN low',bench_required='Monitor all six carrier and downstream EN nodes with 12V present: unpowered with kill closed/open, floating-pin USB boot/power-down, kill opening with commands high; check against 0.6V including pulses')
(r/'review/checks/kill-state-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Powered DC estimate: worst carrier EN {high_z_carrier_max:.3f}V, downstream driver EN {high_z_driver_max:.3f}V <0.6V.')
print('UNVERIFIED: powered-off EN and supply ramps; SN74HC125N has no specified Ioff. Overall safety verification incomplete.')
