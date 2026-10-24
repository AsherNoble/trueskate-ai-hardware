"""Measure power-pad exit arcs, not thermal capacities. Requires shapely."""
import json
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely import union_all
ROOT=Path(__file__).resolve().parents[1]/'sources/copper-evaluation'
data=json.loads((ROOT/'filled-planes.json').read_text());rows=[]
for p in data['pads']:
 if not (p['ref'] in ['J5','F1'] or (p['ref'] in ['J11','J12','J13','J14','J15','J16'] and p['pin'] in ['VIN','GND'])):continue
 zone=next(z for z in data['zones'] if z['net']==p['net'])
 geometry=union_all([Polygon(c).buffer(0) for c in zone['contours']])
 radius=min(p['size'])/2+.01
 arc=Point(p['xy']).buffer(radius,quad_segs=1024).exterior.intersection(geometry).length
 rows.append(dict(p,exit_radius_mm=radius,available_exit_arc_mm=arc))
assert len(rows)==18
(ROOT/'terminal-exits.json').write_text(json.dumps(rows,indent=2))
