"""Exterior arrows on the assembled view, plus complete per-reference soldering map."""
from pathlib import Path
import csv,json,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
FONT='/System/Library/Fonts/Helvetica.ttc'
def font(n):return ImageFont.truetype(FONT,n)
INK='#203b48';MUTED='#58707a';LINE='#3b6375';PAPER='#f5f7f8'
fps={f['ref']:f for f in json.loads((ROOT/'board-geometry.json').read_text())['footprints']}
def centre(ref,numbers=None):
    ps=[p for p in fps[ref]['pads'] if numbers is None or p['number'] in numbers]
    return tuple(sum(p['xy'][i] for p in ps)/len(ps) for i in (0,1))
def arrow(d,points,color=LINE,width=3):
    d.line(points,fill='white',width=width+3,joint='curve')
    d.line(points,fill=color,width=width,joint='curve')
    a,b=points[-2:];ang=math.atan2(b[1]-a[1],b[0]-a[0]);r=11
    d.polygon([b,(b[0]-r*math.cos(ang-.42),b[1]-r*math.sin(ang-.42)),(b[0]-r*math.cos(ang+.42),b[1]-r*math.sin(ang+.42))],fill=color)

# General assembly: each soldered component family, all reference ranges.
out=Image.new('RGB',(2600,1660),PAPER);d=ImageDraw.Draw(out)
d.text((50,30),'Carrier components — what gets soldered to the PCB',font=font(43),fill=INK)
d.text((52,90),'Plug-in modules removed to expose the soldered parts. The detailed map labels each individual reference.',font=font(27),fill=MUTED)
raw=Image.open(ROOT/'carrier-soldered-perspective.png').convert('RGB')
scale=.9;ox,oy=490,180
out.paste(raw.resize((1620,1215),Image.Resampling.LANCZOS),(ox,oy));d=ImageDraw.Draw(out)
proj=json.loads((ROOT/'callout-projections.json').read_text())
spec={
 'fuse':('Fuse holder','F1  ·  5 × 20 mm cartridge holder','Cartridge fits into the clips.'),
 'input':('12 V input terminal','J5  ·  1 × two-way screw terminal','5.08 mm pin spacing'),
 'teensy':('Teensy female sockets','J1, J2  ·  2 × 24-way sockets','Under the removable Teensy'),
 'mini_control':('Mini control sockets','J11–J16  ·  6 × female 2×5','Under each removable Mini'),
 'mini_phase':('Mini phase sockets','J11–J16  ·  6 × female 1×3','Second socket in each Mini set'),
 'motor_header':('Motor phase headers','J21–J26  ·  6 × male 1×3','External motor wires plug here.'),
 'bulk':('Large electrolytic capacitors','C11–C16  ·  6 × 1000 µF / 35 V','Polarised; blue cylindrical bodies'),
 'ceramic':('Small ceramic capacitors','C21–C26  ·  6 × 100 nF / 50 V','Beside each large capacitor'),
 'power':('Driver power terminals','J41–J46  ·  6 × two-way terminals','Short wire pairs feed the Minis.'),
 'encoder':('Encoder female sockets','J31–J36  ·  6 × female 1×6','Under the removable JST adapters'),
 'resistor':('Enable pull-down resistors','R21–R26  ·  6 × 10 kΩ','Axial through-hole resistors'),
}
for side,keys in [('left',['fuse','input','mini_control','teensy','mini_phase','motor_header']),('right',['bulk','ceramic','power','encoder','resistor'])]:
    keys.sort(key=lambda k:sum(p[1] for p in proj[k])/len(proj[k]))
    for i,key in enumerate(keys):
        y=340+i*(175 if side=='left' else 200)
        x=40 if side=='left' else 2150
        start=(455 if side=='left' else 2130,y+28)
        elbow=475 if side=='left' else 2118
        for p in proj[key]:arrow(d,[start,(elbow,start[1]),(ox+p[0]*scale,oy+p[1]*scale)])
        title,refs,detail=spec[key]
        d.text((x,y),title,font=font(27),fill=INK)
        d.text((x,y+38),refs,font=font(23),fill=INK)
        d.text((x,y+72),detail,font=font(22),fill=MUTED)
d.text((52,1460),'52 physical carrier parts: 46 references, with two separate sockets in each J11–J16 set.',font=font(30),fill=INK)
d.text((52,1510),'The Teensy, six Minis and JST adapter boards plug into these sockets. Their own onboard parts are not added to the carrier.',font=font(25),fill=MUTED)
d.text((52,1552),'JP1–JP6 are optional wire-bridge pads, left open. NT1 is the copper ground star. Neither requires a soldered component.',font=font(25),fill=MUTED)
out.save(ROOT/'carrier-components-labelled.png')

# Detailed map: eight exterior callouts per axis, then four controller/power parts.
raw=Image.open(ROOT/'carrier-soldered-top.png').convert('RGB')
refproj=json.loads((ROOT/'carrier-projections.json').read_text())
u=raw.width/180
def boardpixel(x,y):return (raw.width/2+(x-80)*u,raw.height/2+(y-60)*u)
sheet=Image.new('RGB',(2760,2050),PAPER);d=ImageDraw.Draw(sheet)
d.text((42,25),'Soldered-component map — every reference',font=font(46),fill=INK)
d.text((44,86),'Plug-in modules removed to expose the sockets. Arrows point to the actual rendered component positions.',font=font(28),fill=MUTED)
covered=set()
for i in range(1,7):
    col=(i-1)%3;row=(i-1)//3;top=i<=3
    bx,by=20+col*915,150+row*650
    d.rounded_rectangle((bx,by,bx+895,by+630),radius=14,fill='white',outline='#d6dfe3',width=2)
    d.text((bx+24,by+15),f'AXIS {i}',font=font(31),fill=INK)
    x0=(19 if top else 16)+43*col;y0=1 if top else 76
    x1=(69 if top else 73)+43*col;y1=54 if top else 120
    p0=boardpixel(x0,y0);p1=boardpixel(x1,y1)
    mm=7.5;w=round((x1-x0)*mm);h=round((y1-y0)*mm)
    px,py=bx+18,by+100
    crop=raw.crop((*p0,*p1)).resize((w,h),Image.Resampling.LANCZOS)
    sheet.paste(crop,(px,py));d=ImageDraw.Draw(sheet)
    j=f'J{10+i}'
    entries=[(j+' control','Female 2×5 socket',centre(j,[str(n) for n in range(1,11)]),j),
      (j+' phases','Female 1×3 socket',centre(j,['P1','P2','P3']),j),
      (f'J{20+i}','Male 1×3 motor header',centre(f'J{20+i}'),f'J{20+i}'),
      (f'J{30+i}','Female 1×6 encoder socket',centre(f'J{30+i}'),f'J{30+i}'),
      (f'R{20+i}','10 kΩ resistor',centre(f'R{20+i}'),f'R{20+i}'),
      (f'C{10+i}','1000 µF / 35 V capacitor',centre(f'C{10+i}'),f'C{10+i}'),
      (f'C{20+i}','100 nF / 50 V capacitor',centre(f'C{20+i}'),f'C{20+i}'),
      (f'J{40+i}','Two-way power terminal',centre(f'J{40+i}'),f'J{40+i}')]
    entries.sort(key=lambda e:e[2][1])
    for n,(ref,desc,p,key) in enumerate(entries):
        covered.add(key);ly=by+77+n*65;lx=bx+526
        target=(px+(p[0]-x0)*mm,py+(p[1]-y0)*mm)
        arrow(d,[(lx-16,ly+20),(bx+485,ly+20),target],width=2)
        d.text((lx,ly),ref,font=font(24),fill=INK)
        d.text((lx,ly+30),desc,font=font(20),fill=MUTED)
    d.text((bx+24,by+580),'Two separate female sockets share the Mini reference.',font=font(20),fill=MUTED)

# Shared parts, shown in two focused crops for legible arrows.
by=1470
d.text((42,by),'SHARED CONTROLLER AND POWER PARTS',font=font(30),fill=INK)
for b,x0,y0,x1,y1,refs in [(40,0,20,18,77,['F1','J5']),(1350,40,56,108,79,['J2','J1'])]:
    mm=5 if b==40 else 8
    p0=boardpixel(x0,y0);p1=boardpixel(x1,y1)
    crop=raw.crop((*p0,*p1)).resize((round((x1-x0)*mm),round((y1-y0)*mm)),Image.Resampling.LANCZOS)
    px,py=b+40,by+65
    sheet.paste(crop,(px,py));d=ImageDraw.Draw(sheet)
    for n,ref in enumerate(refs):
        covered.add(ref);p=centre(ref);target=(px+(p[0]-x0)*mm,py+(p[1]-y0)*mm)
        lx=b+(290 if b==40 else 660);ly=by+90+n*135
        arrow(d,[(lx-20,ly+20),(lx-50,ly+20),target],width=3)
        desc={'F1':'5×20 mm fuse holder (cartridge fits into clips)','J5':'Two-way 12 V input terminal; 5.08 mm pitch','J1':'Female 1×24 Teensy socket — lower row','J2':'Female 1×24 Teensy socket — upper row'}[ref]
        d.text((lx,ly),ref,font=font(28),fill=INK);d.text((lx,ly+40),desc,font=font(22),fill=MUTED)
d.text((42,1900),'46 references / 52 physical soldered parts. Fuse cartridge, plug-in modules, wires and mounting screws are additional.',font=font(27),fill=INK)
d.text((42,1945),'JP1–JP6: optional wire bridges, left open. NT1: existing PCB copper. These are not missing components.',font=font(26),fill=MUTED)
bom=list(csv.DictReader((ROOT.parents[1]/'bom-review.csv').open()))
expected={r['Reference'] for r in bom if r['Assembly'].startswith('Hand')}
assert covered==expected,(expected-covered,covered-expected)
sheet.save(ROOT/'soldered-components-map.png')
print('Coverage verified:',len(covered),'references; 52 physical carrier parts')
