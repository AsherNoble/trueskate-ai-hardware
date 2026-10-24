#!/usr/bin/env python3
"""Render populated current carrier using native models and simplified plug-in bodies.
Run using KiCad bundled Python. Does not modify electrical design.
"""
import json,math,hashlib,subprocess,os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pcbnew as k
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent
PCB=ROOT/'trueskate-main-v1.kicad_pcb'
source_hash=hashlib.sha256(PCB.read_bytes()).hexdigest()
b=k.LoadBoard(str(PCB));fps={f.GetReference():f for f in b.GetFootprints()}
shapes=['#VRML V2.0 utf8\n']
black=(.035,.04,.045);silver=(.65,.68,.72);gold=(.72,.51,.16);blue=(.025,.14,.32);green=(.025,.27,.14);white=(.85,.86,.83)
def mat(c):return 'appearance Appearance { material Material { diffuseColor %s specularColor .2 .2 .2 shininess .3 } }'%(' '.join(map(str,c)))
def coords(p):return p[0]/2.54,-p[1]/2.54,p[2]/2.54
def box(p,size,c):
 shapes.append('Transform { translation %s children [ Shape { %s geometry Box { size %s } } ] }\n'%(' '.join(map(str,coords(p))),mat(c),' '.join(str(v/2.54)for v in size)))
def cyl(p,r,h,c):
 shapes.append('Transform { translation %s rotation 1 0 0 1.57079632679 children [ Shape { %s geometry Cylinder { radius %s height %s } } ] }\n'%(' '.join(map(str,coords(p))),mat(c),r/2.54,h/2.54))
def prism(poly,z,h,color):
 # Triangulate caps explicitly: KiCad's VRML importer does not reliably render
 # large concave IndexedFaceSet faces. Keep source vertices and omit duplicates.
 clean=[]
 for p in poly:
  if not clean or math.dist(p,clean[-1])>1e-7:clean.append(p)
 if math.dist(clean[0],clean[-1])<1e-7:clean.pop()
 poly=clean
 if sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(poly,poly[1:]+poly[:1]))>0:poly.reverse()
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 ids=list(range(len(poly)));tri=[]
 while len(ids)>3:
  for j in range(len(ids)):
   ia,ib,ic=ids[j-1],ids[j],ids[(j+1)%len(ids)];a,b,c=poly[ia],poly[ib],poly[ic]
   if cross(a,b,c)>=-1e-12:continue
   if any(cross(a,b,poly[q])<-1e-10 and cross(b,c,poly[q])<-1e-10 and cross(c,a,poly[q])<-1e-10 for q in ids if q not in (ia,ib,ic)):continue
   tri.append([ia,ib,ic]);ids.pop(j);break
  else:raise RuntimeError('Cannot triangulate Mini outline')
 tri.append(ids)
 pts=[coords((x,y,zz))for zz in (z,z+h)for x,y in poly];n=len(poly)
 faces=[list(reversed(t))for t in tri]+[[i+n for i in t]for t in tri]+[[i,(i+1)%n,(i+1)%n+n,i+n]for i in range(n)]
 shapes.append('Shape { %s geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ %s ] } coordIndex [ %s ] } }\n'%(mat(color),','.join(' '.join(map(str,p))for p in pts),','.join(' '.join(map(str,f))+',-1'for f in faces)))
def mm(p):return k.ToMM(p.x),k.ToMM(p.y)
def transform(f,x,y):
 ox,oy=mm(f.GetPosition());a=math.radians(f.GetOrientationDegrees());return ox+math.cos(a)*x+math.sin(a)*y,oy-math.sin(a)*x+math.cos(a)*y
geo=json.loads((ROOT/'sources/mini-geometry.json').read_text())
# Socket seating is illustrative: standard sockets ~8.5mm above carrier top.
# Mini local coordinates follow the verified carrier (top view, not mirrored).
for i in range(1,7):
 f=fps[f'J{10+i}'];poly=[transform(f,*p)for p in geo['outline_polygon'][:-1]]
 prism(poly,9.0,1.6,blue)
 for pad in f.Pads():
  x,y=mm(pad.GetPosition());box((x,y,8.2),(.64,.64,5.0),gold)
  cyl((x,y,10.66),.85,.12,silver)
  if pad.GetNumber() in ('VIN','GND'):
   cyl((x,y,3.9),1.05,7.8,gold);cyl((x,y,7.9),.65,.15,black)
 # Representative module components, not a manufacturer-qualified component model.
 x,y=transform(f,6,8.2);box((x,y,11.35),(6,7,.95),black)
 for dx in (-3.6,3.6):
  for q in range(6):box((x+dx,y-2.5+q,10.95),(.7,.45,.25),silver)
 x,y=transform(f,15,13);cyl((x,y,13.2),2.8,5.2,black);cyl((x,y,15.84),2.65,.12,silver)
 x,y=transform(f,14,3);box((x,y,11.1),(3,4,1),black)
 for q in range(5):
  x,y=transform(f,3+q*2.3,13.4);box((x,y,10.95),(1.1,.65,.55),(.55,.43,.27))
# Teensy 4.1 body oriented with the actual two socket rows and USB facing Y=120.
xs=[mm(p.GetPosition())[0]for ref in ('J1','J2')for p in fps[ref].Pads()]
xc=(min(xs)+max(xs))/2
box((xc,89.55,9.8),(17.78,60.96,1.6),green)
for ref in ('J1','J2'):
 for pad in fps[ref].Pads():
  x,y=mm(pad.GetPosition());box((x,y,8.4),(.64,.64,4),gold);cyl((x,y,10.65),.85,.12,silver)
box((xc,88,11.4),(9,9,1.6),black)
box((xc,65,11.6),(12,10,2),silver)
box((xc,65,12.64),(10,7,.1),black)
box((xc,117.2,12),(7.5,5.6,2.8),silver)
box((xc,120.02,12),(5.8,.12,1.6),black)
box((xc-4,109,11.1),(2.8,4,1),black)
for q in range(8):box((xc+4.5,77+q*3,10.95),(1,.6,.55),(.55,.43,.27))
# One complete Keystone 3557-2 holder plus illustrative unmarked ATO fuse.
f=fps['F1'];ox,oy=mm(f.GetPosition());cx,cy=ox+6.735,oy+1.7
box((cx,cy,1.0),(19.81,6.73,2),black)
for dx in (-6.735,6.735):
 box((cx+dx,cy,4.3),(3.6,5.7,5.4),silver)
 box((cx+dx,cy,6.9),(2.5,1.6,1.0),black)
 box((cx+dx,cy,7.7),(1.0,.8,6),silver)
box((cx,cy,12.2),(19.1,5.1,9.2),(.65,.68,.7))
box((cx,cy,17),(19.1,5.1,.6),black)
model=OUT/'populated-components.wrl';model.write_text(''.join(shapes))
f=k.FOOTPRINT(b);f.SetReference('ASSEMBLY_VISUAL_ONLY');f.SetPosition(k.VECTOR2I(0,0));f.Reference().SetVisible(False);f.Value().SetVisible(False)
m=k.FP_3DMODEL();m.m_Filename=str(model);f.Add3DModel(m);b.Add(f)
# Resolve standard model variables explicitly in this disposable review copy.
share='/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels'
for fp in b.GetFootprints():
 for md in fp.Models():md.m_Filename=md.m_Filename.replace('${KICAD10_3DMODEL_DIR}',share)
review=OUT/'populated-review.kicad_pcb';k.SaveBoard(str(review),b,True)
cli='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
def render(spec):
 name,rot=spec
 cmd=[cli,'pcb','render','--width','2000','--height','1600','--quality','high','--background','opaque','--side','top','--output',str(OUT/(name+'.png'))]
 if rot:cmd+=['--rotate',rot,'--perspective','--zoom','.72']
 cmd.append(str(review));result=subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(OUT/(name+'.log')).write_bytes(result.stdout)
with ThreadPoolExecutor(max_workers=3)as ex:list(ex.map(render,[('populated-top',None),('populated-perspective','-35,0,25'),('populated-rear','-35,0,155')]))
assert hashlib.sha256(PCB.read_bytes()).hexdigest()==source_hash
(OUT/'provenance.json').write_text(json.dumps(dict(source_pcb_sha256=source_hash,geometry='current native carrier; exact tagged Mini outline/contact placement',simplifications=['Mini component bodies and locations illustrative','Teensy component bodies illustrative; socket rows native','module seating heights illustrative','holder and unmarked fuse simplified envelopes','no external cables']),indent=2)+'\n')
print('Rendered 3 populated views. Source PCB unchanged.')
