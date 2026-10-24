#!/usr/bin/env python3
"""Corrected-current screening and DC estimates; NOT full thermal qualification.

Run with KiCad Python after analysis/export_planes.py and analysis/plane_dc.py.
The DC model deliberately omits parallel outer GND copper. A thermal signoff
cannot be inferred from this electrical model or a uniform-strip IPC fit.
"""
import hashlib,json,math,re
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parent;PCB=ROOT/'trueskate-main-v1.kicad_pcb'
SOURCES=ROOT/'sources/copper-evaluation'
digest=hashlib.sha256(PCB.read_bytes()).hexdigest();b=k.LoadBoard(str(PCB))
provenance=json.loads((SOURCES/'provenance.json').read_text())
assert digest==provenance['pcb_sha256'],'Re-export copper and rerun the DC solver after any PCB change'
phases={}
for t in b.GetTracks():
 if not re.fullmatch(r'A[1-6]_PH[1-3]',t.GetNetname()):continue
 assert not isinstance(t,k.PCB_VIA) and t.GetLayer()==k.F_Cu
 d=phases.setdefault(t.GetNetname(),dict(widths_mm=[],length_mm=0))
 d['widths_mm'].append(k.ToMM(t.GetWidth()));d['length_mm']+=k.ToMM(t.GetLength())
assert len(phases)==18
for d in phases.values():
 d['widths_mm']=sorted(set(d['widths_mm']));d['length_mm']=round(d['length_mm'],4)
assert all(d['widths_mm']==[1.0]for d in phases.values())
rho=1.724e-8*(1+.00393*20)
def barrel(d):return rho*.0016/(math.pi*d*.001*18e-6)
# Two input-terminal barrels at 12 A; F1 worst-case one conducting leg on each side;
# two Mini power barrels at 2.5 A. Full 1.6mm traversal, no solder credit.
barrel_drop=24*barrel(1.3)+24*barrel(1.65)+5*barrel(1.101)
def mesh_report(h):
 d=json.loads((SOURCES/('plane-dc-'+str(h)+'.json')).read_text());p=d['planes']
 R=[[p['12V_FUSED']['transfer_ohm'][i][j]+p['GND']['transfer_ohm'][i][j] for j in range(6)] for i in range(6)]
 ri=p['12V_IN']['transfer_ohm'][0][0];axes=[]
 for i in range(6):
  load=[0.]*6;remaining=12.
  for j in sorted(range(6),key=lambda j:R[i][j],reverse=True):
   load[j]=min(2.5,remaining);remaining-=load[j]
  assert abs(sum(load)-12)<1e-9 and load[i]==2.5
  plane=12*ri+sum(R[i][j]*load[j] for j in range(6))
  axes.append(dict(axis=i+1,worst_loads_a=load,plane_loop_drop_v=plane,equal_2a_each_plane_drop_v=12*ri+2*sum(R[i])))
 return dict(mesh_mm=h,axes=axes)
meshes=[mesh_report(.25),mesh_report(.125)]
worst=max(a['plane_loop_drop_v'] for m in meshes for a in m['axes'])
rows=[]
for order,outer,inner_um in [(1,35,15.2),(2,35,30),(3,70,61)]:
 rise=215.3*2.5**2*(1/.0254)**-1.15*(outer/1000/.0254)**-1
 # Only DC copper resistivity is scaled. This is not a thermal rerun.
 plane=worst*15.2/inner_um
 rows.append(dict(order=order,outer_um=outer,inner_um=inner_um,isolated_phase_fit_rise_c=rise,isolated_phase_screen='PASS',plane_loop_estimate_v=plane,barrel_allowance_v=barrel_drop,receptacle_contact_allowance_v=.05,copper_plus_receptacles_estimate_v=plane+barrel_drop+.05,thermal_status='UNRESOLVED: no complete per-neck/assembly thermal qualification',overall_status='NOT QUALIFIED',dc_status='below 0.3V under stated model assumptions, excluding F1/fuse and input-terminal contact resistance'))
report=dict(checkpoint='62ef1ea',pcb_sha256=digest,criteria=dict(shared_a=12,phase_a=2.5,per_mini_a=2.5,maximum_rise_c=20,maximum_copper_drop_v=.3,aggregate_load='sum axis currents <=12A, each <=2.5A; never six simultaneous 2.5A rail loads'),supersedes='Previous 12A-per-phase rejection is withdrawn.',phase_paths=phases,ordered_results=rows,selected_option=None,mesh_results=meshes,mesh_max_worst_drop_change_v=abs(max(a['plane_loop_drop_v'] for a in meshes[0]['axes'])-max(a['plane_loop_drop_v'] for a in meshes[1]['axes'])),dc_model=dict(temperature_c=40,rho_ohm_m=rho,source='actual filled L2/L3 copper; grounded graph Laplacian and equipotential solder-pad ports',limits=['Not a thermal model','L2 only for GND; outer GND copper omitted','Uniform nominal finished copper thickness; etch tolerances not bounded','Square-cell boundaries and ideal soldered pads approximate constrictions','18um barrel plating is an assumption based on JLC published average, not a guaranteed minimum','Full 1.6mm barrel allowance; F1 barrel allowance assumes all current in one leg per side; no solder conductivity credited','Input terminal wire-contact resistance not specified; reported separately as remaining allowance'],barrel_allowance_v=barrel_drop,receptacle_ohm_each=.01,input_terminal_total_contact_resistance_budget_ohm=(.3-worst-barrel_drop-.05)/12),fuse_holder=dict(resistance_ohm=.005,scope='total holder resistance, not per contact',basis='USER ASSUMPTION; not a Keystone datasheet value',drop_at_12a_v=.06,power_at_12a_w=.72,excluded_from_copper_budget=True),fuse=dict(source='https://media.digikey.com/pdf/Data%20Sheets/Littelfuse%20PDFs/257%20Series.pdf',typical_drop_at_rated_current_mv={'15A':102,'20A':98,'25A':92,'30A':84},note='Examples, not a fuse selection. Typical rated-current figures are not guaranteed maxima or measured drops at 12A. Fuse remains rated to connected supply.'),price=dict(option=1,quantity=5,usd=42.4,status='candidate quote only; no passing option selected',excludes=['shipping','tax','assembly']),layout_modified=False,remaining=['Complete per-neck IPC-2152 thermal assessment of shared input/fuse escapes and GND return','Nearby phase-trace thermal interaction and module/holder heat','Connector/contact temperature rise at requested currents'])
assert hashlib.sha256(PCB.read_bytes()).hexdigest()==digest
(ROOT/'copper-options-review.json').write_text(json.dumps(report,indent=2)+'\n')
for r in rows:print('Option',r['order'],': isolated phase %.3fC; modeled copper + receptacles %.4fV; overall NOT QUALIFIED'%(r['isolated_phase_fit_rise_c'],r['copper_plus_receptacles_estimate_v']))
print('No native PCB change. No complete thermal pass claimed.')
