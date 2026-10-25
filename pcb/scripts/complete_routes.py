#!/usr/bin/env python3
"""Local clearance-aware completion of DRC opens; frozen results replay with --apply.
Collect/apply: KiCad Python. Search: Python with numpy and shapely. DRC is mandatory.
"""
from pathlib import Path
import json,sys,math
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'design/trueskate-main-v1.kicad_pcb'
DATA=ROOT/'design/routing/signal-completions.json';SCRATCH=Path('/private/tmp/3plus3-routing-geometry.json')
if '--collect' in sys.argv or '--apply' in sys.argv:
 import pcbnew as k
 b=k.LoadBoard(str(PCB));mm=lambda p:[k.ToMM(p.x),k.ToMM(p.y)]
 xy=lambda p:k.VECTOR2I(k.FromMM(p[0]),k.FromMM(p[1]))
 if '--collect' in sys.argv:
  out=dict(pads=[],holes=[],tracks=[])
  for f in b.GetFootprints():
   for p in f.Pads():
    for layer in (k.F_Cu,k.B_Cu):
     if not p.IsOnLayer(layer):continue
     poly=p.GetEffectivePolygon(layer)
     for i in range(poly.OutlineCount()):out['pads'].append(dict(net=p.GetNetname(),layer=0 if layer==k.F_Cu else 1,points=[mm(poly.COutline(i).CPoint(j))for j in range(poly.COutline(i).PointCount())]))
    if max(mm(p.GetDrillSize()))>0:out['holes'].append(dict(net=p.GetNetname(),position=mm(p.GetPosition()),radius=max(mm(p.GetDrillSize()))/2))
  for t in b.GetTracks():
   if isinstance(t,k.PCB_VIA):
    out['holes'].append(dict(net=t.GetNetname(),position=mm(t.GetPosition()),radius=k.ToMM(t.GetDrillValue())/2))
    for layer in (0,1):out['tracks'].append(dict(net=t.GetNetname(),layer=layer,start=mm(t.GetPosition()),end=mm(t.GetPosition()),width=k.ToMM(t.GetWidth(k.F_Cu))))
   else:out['tracks'].append(dict(net=t.GetNetname(),layer=0 if t.GetLayer()==k.F_Cu else 1,start=mm(t.GetStart()),end=mm(t.GetEnd()),width=k.ToMM(t.GetWidth())))
  SCRATCH.write_text(json.dumps(out));sys.exit()
 nets=b.GetNetsByName()
 for route in json.loads(DATA.read_text()):
  for seg in route['segments']:
   if seg['layer']=='via':
    t=k.PCB_VIA(b);t.SetPosition(xy(seg['start']));t.SetWidth(k.FromMM(.7));t.SetDrill(k.FromMM(.3));t.SetLayerPair(k.F_Cu,k.B_Cu);t.SetViaType(k.VIATYPE_THROUGH)
   else:
    t=k.PCB_TRACK(b);t.SetStart(xy(seg['start']));t.SetEnd(xy(seg['end']));t.SetWidth(k.FromMM(.25));t.SetLayer(k.F_Cu if seg['layer']==0 else k.B_Cu)
   t.SetNet(nets[route['net']]);b.Add(t)
 k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(PCB),b,True);print('Applied',len(json.loads(DATA.read_text())),'completion routes');sys.exit()
import heapq,re
import numpy as np
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
from shapely import intersects_xy
from layout_3plus3 import WIDTH,HEIGHT,axis_point
geo=json.loads(SCRATCH.read_text());drc=json.loads(Path(sys.argv[1]).read_text())
step=.25;nx=int(WIDTH/step)+1;ny=int(HEIGHT/step)+1;N=nx*ny
xx,yy=np.meshgrid(np.arange(nx)*step,np.arange(ny)*step)
records=[];guards=[]
for axis in range(1,7):
 a,z=axis_point(axis,-2,0),axis_point(axis,12.5,34.75)
 guards.append(box(min(a[0],z[0]),min(a[1],z[1]),max(a[0],z[0]),max(a[1],z[1])))
for open_ in drc['unconnected_items']:
 items=open_['items'];net=re.search(r'\[([^]]+)\]',items[0]['description']).group(1)
 if net=='GND':continue
 points=[[i['pos']['x'],i['pos']['y']]for i in items]
 layers=[0 if 'F.Cu' in i['description'] else 1 if 'B.Cu' in i['description'] else -1 for i in items]
 print('Routing',net,points,flush=True)
 obs=[[],[]];viaobs=[]
 for p in geo['pads']:
  if p['net']==net:continue
  shape=Polygon(p['points']).buffer(0);obs[p['layer']].append(shape.buffer(.405));viaobs.append(shape.buffer(.63))
 for t in geo['tracks']:
  if t['net']==net:continue
  shape=Point(t['start'])if t['start']==t['end']else LineString([t['start'],t['end']])
  obs[t['layer']].append(shape.buffer(t['width']/2+.405));viaobs.append(shape.buffer(t['width']/2+.63))
 for h in geo['holes']:
  shape=Point(h['position'])
  viaobs.append(shape.buffer(h['radius']+.15+.45+.08))
  if h['net']!=net:
   for l in (0,1):obs[l].append(shape.buffer(h['radius']+.45+.125+.08))
 for l in (0,1):obs[l]+=guards
 blocked=np.array([intersects_xy(unary_union(o),xx,yy)for o in obs]);vblocked=intersects_xy(unary_union(viaobs+guards),xx,yy)
 border=(xx<.75)|(xx>WIDTH-.75)|(yy<.75)|(yy>HEIGHT-.75)
 blocked|=border;vblocked|=border
 starts=[];goals=set()
 for j,(p,l)in enumerate(zip(points,layers)):
  x,y=int(round(p[0]/step)),int(round(p[1]/step))
  for ll in ((0,1)if l==-1 else (l,)):
   if blocked[ll,y,x]:continue
   index=ll*N+y*nx+x
   if j==0:starts.append(index)
   else:goals.add(index)
 if not starts or not goals:raise RuntimeError((net,'terminal blocked',starts,goals))
 gx,gy=round(points[1][0]/step),round(points[1][1]/step)
 def heuristic(x,y):
  dx,dy=abs(x-gx),abs(y-gy);return max(dx,dy)+.41421356*min(dx,dy)
 distance=np.full(2*N,np.inf);parent=np.full(2*N,-1,dtype=np.int32);heap=[]
 for n in starts:distance[n]=0;heapq.heappush(heap,(heuristic(n%nx,(n%N)//nx),0,n))
 moves=[(-1,0,1),(1,0,1),(0,-1,1),(0,1,1),(-1,-1,2**.5),(1,-1,2**.5),(-1,1,2**.5),(1,1,2**.5)]
 found=None
 while heap:
  _,cost,n=heapq.heappop(heap)
  if cost>distance[n]+1e-8:continue
  if n in goals:found=n;break
  l=n//N;y=(n%N)//nx;x=n%nx
  for dx,dy,w in moves:
   ax,ay=x+dx,y+dy
   if ax<0 or ay<0 or ax>=nx or ay>=ny or blocked[l,ay,ax]:continue
   if dx and dy and (blocked[l,y,ax] or blocked[l,ay,x]):continue
   m=l*N+ay*nx+ax;new=cost+w*(1 if l==0 else 1.8)
   if new<distance[m]:distance[m]=new;parent[m]=n;heapq.heappush(heap,(new+heuristic(ax,ay),new,m))
  if not vblocked[y,x] and not blocked[1-l,y,x]:
   m=(1-l)*N+y*nx+x;new=cost+16
   if new<distance[m]:distance[m]=new;parent[m]=n;heapq.heappush(heap,(new+heuristic(x,y),new,m))
 if found is None:raise RuntimeError((net,'no path'))
 path=[]
 while found!=-1:path.append(found);found=int(parent[found])
 path.reverse();nodes=[(n%nx*step,(n%N)//nx*step,n//N)for n in path]
 nodes=[(*points[0],nodes[0][2])]+nodes+[(*points[1],nodes[-1][2])]
 # Keep corners and layer transitions only.
 simple=[nodes[0]]
 for j in range(1,len(nodes)-1):
  a,p,z=simple[-1],nodes[j],nodes[j+1]
  if a[2]==p[2]==z[2] and abs((p[0]-a[0])*(z[1]-p[1])-(p[1]-a[1])*(z[0]-p[0]))<1e-8:continue
  simple.append(p)
 simple.append(nodes[-1]);segments=[]
 for a,z in zip(simple,simple[1:]):
  if a==z:continue
  if a[2]!=z[2]:
   segments.append(dict(layer='via',start=list(a[:2]),end=list(a[:2])))
   geo['holes'].append(dict(net=net,position=list(a[:2]),radius=.15))
   for l in(0,1):geo['tracks'].append(dict(net=net,layer=l,start=list(a[:2]),end=list(a[:2]),width=.7))
  else:
   segments.append(dict(layer=a[2],start=list(a[:2]),end=list(z[:2])))
   geo['tracks'].append(dict(net=net,layer=a[2],start=list(a[:2]),end=list(z[:2]),width=.25))
 records.append(dict(net=net,segments=segments));DATA.write_text(json.dumps(records,indent=2)+'\n')
 print('Completed:',len(segments),'segments',flush=True)
