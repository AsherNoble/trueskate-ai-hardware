"""DC sheet-network estimate only; no thermal qualification. Requires numpy scipy shapely pyamg."""
import json,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point
from shapely import contains_xy,union_all
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import cg
from scipy.ndimage import label
import pyamg
ROOT=Path(__file__).resolve().parents[1]/'sources/copper-evaluation'
D=json.loads((ROOT/'filled-planes.json').read_text());h=float(sys.argv[1]);results={}
rho=1.724e-8*(1+.00393*20);th=.0152e-3;rs=rho/th
for net in ['12V_IN','12V_FUSED','GND']:
 z=next(z for z in D['zones'] if z['net']==net)
 geom=union_all([Polygon(c).buffer(0) for c in z['contours']])
 def pp(ref,pin):return [p for p in D['pads'] if p['ref']==ref and p['pin']==pin]
 if net=='12V_IN': ports=[pp('J5','1'),pp('F1','1')]
 elif net=='12V_FUSED':ports=[pp('F1','2')]+[pp('J'+str(11+i),'VIN') for i in range(6)]
 else:ports=[pp('J5','2')]+[pp('J'+str(11+i),'GND') for i in range(6)]
 # Ideal soldered contacts are equipotential disks; drill/barrel resistance separate.
 for port in ports:
  for p in port:geom=geom.union(Point(p['xy']).buffer(min(p['size'])/2))
 minx,miny,maxx,maxy=geom.bounds
 x=np.arange(minx+h/2,maxx,h);y=np.arange(miny+h/2,maxy,h);xx,yy=np.meshgrid(x,y)
 mask=contains_xy(geom,xx,yy);labs,n=label(mask);counts=np.bincount(labs.ravel());counts[0]=0;mask=labs==counts.argmax()
 ids=np.full(mask.shape,-1,dtype=int);ids[mask]=np.arange(mask.sum())
 portids=[]
 for port in ports:
  pm=np.zeros(mask.shape,dtype=bool)
  for p in port:pm|=(xx-p['xy'][0])**2+(yy-p['xy'][1])**2<(min(p['size'])/2)**2
  portids.append(ids[pm&mask])
 # Contract each port into a single graph node (ideal soldered-pad boundary).
 remap=np.arange(mask.sum())
 for pi in portids: remap[pi]=pi[0]
 _,remap=np.unique(remap,return_inverse=True);ids[mask]=remap[ids[mask]]
 portnodes=[remap[p[0]] for p in portids];N=remap.max()+1
 aa=[];bb=[]
 for a,b in [(ids[:,:-1],ids[:,1:]),(ids[:-1,:],ids[1:,:])]:
  valid=(a>=0)&(b>=0)&(a!=b);aa.append(a[valid]);bb.append(b[valid])
 a=np.concatenate(aa);b=np.concatenate(bb);weights=np.ones(len(a))/rs
 A=coo_matrix((np.r_[weights,weights,-weights,-weights],(np.r_[a,b,a,b],np.r_[a,b,b,a])),shape=(N,N)).tocsr()
 fixed=portnodes[0];free=np.arange(N)!=fixed;Ar=A[free][:,free];M=pyamg.smoothed_aggregation_solver(Ar).aspreconditioner()
 R=[]
 for pn in portnodes[1:]:
  rhs=np.zeros(N);rhs[pn]=1
  v,info=cg(Ar,rhs[free],M=M,rtol=1e-9,maxiter=500)
  assert info==0,info
  full=np.zeros(N);full[free]=v;R.append(full[portnodes[1:]].tolist())
 print(net,N,'nodes',flush=True)
 results[net]={'transfer_ohm':np.array(R).T.tolist(),'area_mm2':geom.area,'ports':[[p['ref']+':'+p['pin'] for p in port] for port in ports]}
result={'mesh_mm':h,'temperature_c':40,'sheet_resistance_ohm':rs,'inner_thickness_um':15.2,'planes':results}
(ROOT/('plane-dc-'+str(h)+'.json')).write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
