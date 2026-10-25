#!/usr/bin/env python3
"""Readable assembly silk, outside socketed modules; all dimensions in millimetres."""
from pathlib import Path
import json,math,subprocess,sys,hashlib
import pcbnew as k
from layout_3plus3 import BANKS,axis_point
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'design/trueskate-main-v1.kicad_pcb'
clean=Path('/private/tmp')/('trueskate-silk-'+hashlib.sha256(str(PCB).encode()).hexdigest()[:12]+'.kicad_pcb')
if '--clean' in sys.argv:
 b=k.LoadBoard(str(PCB))
 for item in list(b.GetDrawings()):
  if item.GetLayer()==k.F_SilkS or (isinstance(item,k.PCB_TEXT) and 'USB ONLY' in item.GetText()):b.Remove(item)
 k.SaveBoard(str(clean),b,True)
 sys.exit(0)
# Object removal changes SWIG wrapper ownership; isolate cleanup in its own process.
subprocess.run([sys.executable,str(Path(__file__).resolve()),'--clean'],check=True,stdout=subprocess.DEVNULL)
b=k.LoadBoard(str(clean));fps={f.GetReference():f for f in b.GetFootprints()}
xy=lambda p:k.VECTOR2I(k.FromMM(p[0]),k.FromMM(p[1]))
mm=lambda p:[k.ToMM(p.x),k.ToMM(p.y)]
for f in b.GetFootprints():
 f.Reference().SetVisible(False);f.Value().SetVisible(False)
 for g in f.GraphicalItems():
  if g.GetLayer()==k.F_SilkS:g.SetLayer(k.F_Fab)
texts=[];markers=[]
def text(label,x,y,size=1,angle=0):
 t=k.PCB_TEXT(b);t.SetText(label);t.SetPosition(xy((x,y)));t.SetLayer(k.F_SilkS);t.SetTextSize(xy((size,size)));t.SetTextThickness(k.FromMM(.15));t.SetTextAngle(k.EDA_ANGLE(angle,k.DEGREES_T));b.Add(t);texts.append(t);return t
def line(a,z):
 s=k.PCB_SHAPE(b);s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(xy(a));s.SetEnd(xy(z));s.SetLayer(k.F_SilkS);s.SetWidth(k.FromMM(.15));b.Add(s)
def poly(points):
 for a,z in zip(points,points[1:]+points[:1]):line(a,z)
def marker(ref,point,direction=(0,-1)):
 x,y=point;dx,dy=direction;px,py=-dy,dx
 poly([(x+dx*.5,y+dy*.5),(x-dx*.4+px*.4,y-dy*.4+py*.4),(x-dx*.4-px*.4,y-dy*.4-py*.4)])
 markers.append(dict(reference=ref,point=point))
# Title below the Teensy, right of its body. Number box is blank white ink.
text('TSAI-FOC6 v1 · 2026-10',78,80.6,1.2)
text('Asher Noble · CC BY-NC',78,82.6)
text('github.com/AsherNoble/trueskate-ai-hardware',78,84.6)
white=k.PCB_SHAPE(b);white.SetShape(k.SHAPE_T_RECT);white.SetStart(xy((82.575,73.575)));white.SetEnd(xy((97.425,79.425)));white.SetWidth(k.FromMM(.15));white.SetFilled(True);white.SetLayer(k.F_SilkS);b.Add(white)
text('Populate A1-A3 first',79,60)
# Exact source silhouette + .35 mm visibility allowance; no text inside modules.
geo=json.loads((ROOT/'sources/mini-geometry.json').read_text())
outline=k.SHAPE_POLY_SET();outline.NewOutline()
for x,y in geo['outline_polygon'][:-1]:outline.Append(k.FromMM(x),k.FromMM(y))
outline.Inflate(k.FromMM(.35),k.CORNER_STRATEGY_ROUND_ALL_CORNERS,k.FromMM(.005),True)
chain=outline.COutline(0);local=[mm(chain.CPoint(i))for i in range(chain.PointCount())]
for axis in range(1,7):
 f=fps[f'J{10+axis}'];ox,oy=mm(f.GetPosition());a=math.radians(f.GetOrientationDegrees())
 world=lambda p:(ox+math.cos(a)*p[0]+math.sin(a)*p[1],oy-math.sin(a)*p[0]+math.cos(a)*p[1])
 poly([world(p)for p in local])
 ap=lambda x,y:axis_point(axis,x,y)
 # Source PCB: U1 centre (4108,3085.5), pad1 (4091.366,3096.783), H1.9 (4089.5,3046).
 # This orientation icon uses the same transformed pin1 corner, in the visible gutter.
 poly([ap(26.8,21),ap(29.2,21),ap(29.2,25),ap(26.8,25)])
 for yy in (21.6,22.4,23.2,24):
  for x0,x1 in ((26.3,26.8),(29.2,29.7)):line(ap(x0,yy),ap(x1,yy))
 cx,cy=ap(27.25,21.55)
 dot=k.PCB_SHAPE(b);dot.SetShape(k.SHAPE_T_CIRCLE);dot.SetCenter(xy((cx,cy)));dot.SetEnd(xy((cx+.15,cy)));dot.SetWidth(k.FromMM(.15));dot.SetLayer(k.F_SilkS);b.Add(dot)
 for label,x,y,size in [(f'A{axis}',28,28.5,1.5),(f'M{axis}',5,6.9,1),(f'ENC{axis}',18,7,1),('+',8,43.5,1.5)]:
  xx,yy=ap(x,y);text(label,xx,yy,size)
 labels=['TODO']+[f'{n} {name}'for n,name in enumerate(json.loads((ROOT/'design/data/design.json').read_text())['encoder_pin_order'],1)]
 for n,label in enumerate(labels):
  xx,yy=ap(28,9.5+1.5*n);text(label,xx,yy)
 sign=-1 if axis in BANKS['upper']else 1
 marker(f'J{10+axis}:control1',ap(24.8,23.16),(sign,0))
 marker(f'J{10+axis}:phase1',ap(-.5,21.636),(-sign,0))
 marker(f'J{20+axis}',ap(9.5,3),(sign,0))
 marker(f'J{30+axis}',ap(24,5.3),(sign,0))
# Teensy outline has .35 mm allowance; rotate the requested USB text to point left.
poly([(.35,60.76),(62.01,60.76),(62.01,79.24),(.35,79.24)])
text('USB →',8.5,81.5,1,180)
marker('J1',(1.97,80.7),(0,-1));marker('J2',(1.97,59.3),(0,1))
text('1',3.8,80.7);text('1',3.8,59.3)
# Input labels line up with the actual rotated terminal pins.
text('+12 V',135.5,56);text('GND',136,50.92)
marker('J5',(137,59),(1,0))
text('F1 ATO · rate to supply',147,34,1,90)
text('KILL (NC) · open = motors off',143,113,1,90)
marker('J6',(143.5,95),(1,0))
text('Q1 PMOS',125,13);text('G',129.3,25.5)
# Export text bounds for an independent overlap audit.
record=[]
for t in texts:
 rect=t.GetBoundingBox();pos=rect.GetPosition();size=rect.GetSize()
 record.append(dict(text=t.GetText(),height_mm=k.ToMM(t.GetTextSize().y),stroke_mm=k.ToMM(t.GetTextThickness()),box_mm=[*mm(pos),k.ToMM(pos.x+size.x),k.ToMM(pos.y+size.y)]))
# A writing box must also be free of physical holes, even when vias are tented.
write_box=(82.5,73.5,97.5,79.5)
holes=[]
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetDrillSize().x:holes.append((*mm(p.GetPosition()),k.ToMM(p.GetDrillSize().x)/2))
for t in b.GetTracks():
 if isinstance(t,k.PCB_VIA):holes.append((*mm(t.GetPosition()),k.ToMM(t.GetDrillValue())/2))
for x,y,r in holes:
 distance=math.hypot(max(write_box[0]-x,x-write_box[2],0),max(write_box[1]-y,y-write_box[3],0))
 assert distance>r,(x,y,'hole intersects writing box')
k.SaveBoard(str(PCB),b,True)
(ROOT/'review/checks/silkscreen-review.json').write_text(json.dumps(dict(texts=record,pin1_markers=markers,mini_outline_offset_mm=.35,white_box_outer_mm=[15,6],white_box_rect_mm=write_box,white_box_clear_of_holes=True,chip_marker_source='tag v1.0 EasyEDA PCB U1 pad1 orientation, projected to visible gutter'),indent=2)+'\n')
print('Applied',len(texts),'labels and',len(markers),'pin1 markers; all text >=1 mm / .15 mm stroke.')
