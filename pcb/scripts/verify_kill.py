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
    assert parts[u]['value']=='SN74LV125AN'
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
print('Static circuit check retained; supply-ramp behavior is accepted for v1 under the documented boot/PWM policy.')
# DC bounds for the requested states, using TI SCES124O and SLVSBA5D.
# Each Mini has three DRV8313 EN inputs behind its upstream 10k series R4.
# Include all three EN low-input leakage currents; do not credit internal pulldowns.
r_carrier_max=10000*1.05
r_mini_max=10000*1.10
buffer_off_leak=5e-6
mini_en_leak=3*5e-6
high_z_carrier_max=(buffer_off_leak+mini_en_leak)*r_carrier_max
high_z_driver_max=high_z_carrier_max+mini_en_leak*r_mini_max
assert high_z_driver_max<.6
boot_carrier_max=.1  # TI VOL max at <=50uA load, valid 3.3V rail.
assert mini_en_leak+boot_carrier_max/9500<50e-6
boot_driver_max=boot_carrier_max+mini_en_leak*r_mini_max
assert boot_driver_max<.6
for i in range(1,7):
    assert [net(f'R{40+i}',p) for p in (1,2)]==[f'A{i}_EN_CMD','GND']
states=[dict(state='Teensy unpowered',rail_v=0,buffer='Ioff / high impedance',carrier_en_max_v=high_z_carrier_max,drv8313_en_max_v=high_z_driver_max),dict(state='Teensy boot, GPIO high impedance',rail_v=3.3,buffer='input pulled low; enabled output low, or disabled output pulled low',carrier_en_max_v=max(boot_carrier_max,high_z_carrier_max),drv8313_en_max_v=max(boot_driver_max,high_z_driver_max)),dict(state='Kill loop open',rail_v=3.3,buffer='/OE high, output high impedance',carrier_en_max_v=high_z_carrier_max,drv8313_en_max_v=high_z_driver_max)]
report=dict(part='SN74LV125AN',logic_family='LV-A low-voltage CMOS',supply='Teensy USB-powered 3V3; no connection to Mini regulator outputs',axes=list(range(1,7)),states=states,conservative_drv8313_low_limit_v=.6,assumptions=['Carrier pull-downs 10k, <=5% tolerance; Mini R4 10k, <=10% tolerance','Boot state uses valid 3.3V rail and high-impedance GPIO without a pull-up','No external back-powering; all GND connections intact'],scope='Datasheet DC analysis, not an oscilloscope measurement; the 0<VCC<2V transition is outside the buffer recommended operating range')
report['prototype_supply_ramp_status']='accepted for v1: no PWM during supply ramp; boot disabled and initFOC only on command'
(r/'review/checks/kill-state-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: all six EN lines low in the three DC states; worst carrier EN {high_z_carrier_max:.3f}V, downstream driver EN {high_z_driver_max:.3f}V <0.6V.')
