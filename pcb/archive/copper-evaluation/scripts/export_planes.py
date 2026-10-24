import pcbnew as k,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
b=k.LoadBoard(str(root/'trueskate-main-v1.kicad_pcb'))
def xy(p):return [k.ToMM(p.x),k.ToMM(p.y)]
out={'zones':[],'pads':[]}
for z in b.Zones():
 if z.GetLayer() not in [k.In1_Cu,k.In2_Cu]:continue
 p=z.GetFilledPolysList(z.GetLayer())
 contours=[]
 for i in range(p.OutlineCount()):
  c=p.COutline(i);contours.append([xy(c.CPoint(j)) for j in range(c.PointCount())])
 out['zones'].append({'net':z.GetNetname(),'layer':b.GetLayerName(z.GetLayer()),'contours':contours})
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetNetname() not in ['12V_IN','12V_FUSED','GND']:continue
  out['pads'].append({'ref':f.GetReference(),'pin':p.GetNumber(),'net':p.GetNetname(),'xy':xy(p.GetPosition()),'size':xy(p.GetSize()),'drill':xy(p.GetDrillSize())})
(root/'sources/copper-evaluation/filled-planes.json').write_text(json.dumps(out))
print([(z['net'],[len(c) for c in z['contours']]) for z in out['zones']])
print([p for p in out['pads'] if p['ref'] in ['J5','F1','J11']])
