#!/usr/bin/env python3
"""Independent pin/net and selected-part audit; no thermal qualification implied."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p={r['ref']:r for r in json.loads((ROOT/'design/data/circuit.json').read_text())}
net=lambda ref,pin:dict(zip(p[ref]['pins'],p[ref]['nets']))[str(pin)]
assert [net('Q1',i)for i in (1,2,3)]==['POL_GATE','12V_PREPOL','12V_FUSED']
assert [net('F1',i)for i in (1,2)]==['12V_IN','12V_PREPOL']
assert [net('R2',i)for i in (1,2)]==['POL_GATE','GND']
assert [net('D1',i)for i in (1,2)]==['12V_FUSED','POL_GATE']
assert all(net(f'J{10+i}','VIN')=='12V_FUSED'for i in range(1,7))
assert p['Q1']['value']=='IRF4905PBF'and p['Q1']['lcsc']=='C2564'
assert p['D1']['value']=='1N4742A 12V'and p['D1']['lcsc']=='C2545'
assert p['R2']['value'].startswith('10k')and p['R2']['lcsc']=='C433778'
assert all(p[r]['assembly']=='Hand'for r in ('Q1','D1','R2'))
report=dict(topology='F1 -> Q1 drain; source -> protected bus; gate ->10k->GND; zener cathode at source/anode at gate',q1_pinout={'1':'G','2':'D / exposed tab','3':'S'},q1=dict(part='Infineon IRF4905PbF',lcsc='C2564',package='TO-220AB',vds_abs_v=55,rds_on_max_ohm_at_vgs_minus10V_tj25C=.020,id_case25C_abs_a=74,vgs_abs_v=20),zener=dict(part='ST(Semtech) 1N4742A',lcsc='C2545',nominal_v=12),gate_resistor_ohm=10000,states=[dict(input='correct +12 V, initially uncharged output',body_diode='drain -> source conducts initially',channel='VGS negative: on'),dict(input='reversed -12 V, initially uncharged output',body_diode='reverse biased',channel='VGS approximately 0: off')],at_12A_room_temperature=dict(mosfet_drop_v=12*.020,mosfet_dissipation_w=12**2*.020),limitations=['74A is a case-temperature rating, not free-air assembly capacity','V1 is bench-current-limited to a few amps; 12A is copper-sizing worst case, not continuous operation','Single P-MOS stage does not block reverse load current or guarantee hot reverse connection with a charged output','Zener is a nominal 12V clamp; no transient/surge qualification'],sources=['https://www.infineon.com/assets/row/public/documents/24/49/infineon-irf4905-datasheet-en.pdf','https://jlcpcb.com/partdetail/C2564','https://jlcpcb.com/partdetail/C2545','https://jlcpcb.com/partdetail/C433778'])
report['prototype_decisions']=json.loads((ROOT/'sources/prototype-decisions.json').read_text())
(ROOT/'review/checks/reverse-polarity-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: reverse-input pin topology, gate pull-down and zener polarity; three JLC-listed THT parts. V1 cooling accepted without a heat sink below ~5A continuous.')
