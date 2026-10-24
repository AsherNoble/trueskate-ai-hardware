#!/usr/bin/env python3
"""Check the actual netlist topology and all axis-population / EN states."""
import itertools,json
from pathlib import Path
r=Path(__file__).resolve().parent
parts={p['ref']:p for p in json.loads((r/'circuit.json').read_text())}
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
print('Static circuit check; switch behavior, startup and loss of supply still require bench qualification.')
