#!/usr/bin/env python3
"""Edge connector carrier source; deliberate power routing, no manufacturing exports.

The previous full-feature draft is preserved by local checkpoint 36e9dca.
Run with KiCad's bundled Python. Signal routing is a separate step.
"""
import csv
import re
import math
import json
import os
from pathlib import Path
import uuid
import pcbnew as k
from kicad_source import write_schematic, write_project
from layout_3plus3 import WIDTH, HEIGHT, BANKS, SD_SERVICE, axis_point, place

ROOT=Path(__file__).resolve().parents[1]
SHARE=Path(os.environ.get("KICAD_SHARE","/Applications/KiCad/KiCad.app/Contents/SharedSupport"))
D=json.loads((ROOT/"design/data/design.json").read_text())
G=json.loads((ROOT/"sources/mini-geometry.json").read_text())
PROJECT="trueskate-main-v1"
NAMESPACE=uuid.UUID("0155f481-079d-43c3-a259-e57f78864d1c")
def uid(s): return str(uuid.uuid5(NAMESPACE,s))
def xy(x,y): return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
def layers(*ids):
    result=k.LSET()
    for layer in ids: result.AddLayer(layer)
    return result
parts,pages=[],{}
def page(name,title,notes): pages[name]=dict(title=title,notes=notes,parts=[])
def add(ref,value,fp,pins,nets,pg,sch,pcb,price=0,note="",lcsc="",assembly="Hand"):
    assert len(pins)==len(nets) and ref not in {p["ref"] for p in parts}
    p=dict(ref=ref,value=value,fp=fp,pins=[str(n) for n in pins],nets=nets,page=pg,
           sch=sch,pcb=pcb,price=price,note=note,lcsc=lcsc,assembly=assembly)
    if ref.startswith("R"):p["note"]+="; 10k, 5% or better"
    parts.append(p);pages[pg]["parts"].append(p)

RFP="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
CFP="Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
page("controller","01 / USB-powered Teensy sockets",[
    "USB is the ONLY Teensy power source. VIN socket contact is deliberately unconnected.",
    "Pin map unchanged. EN commands pass through hardware kill buffers on the power sheet.",
    "Teensy 3.3V powers encoders and buffers. Mini regulator outputs remain isolated."])
pin_nets={}
for i,a in enumerate(D["axes"],1):
    for n,pin in enumerate(a["pwm"],1): pin_nets[pin]=f"A{i}_PWM{n}"
    pin_nets[a["enable"]]=f"A{i}_EN_CMD";pin_nets[a["cs"]]=f"A{i}_CS"
pin_nets.update({11:"SPI_MOSI",12:"SPI_MISO",13:"SPI_SCK"})
lower=["GND"]+[str(n) for n in range(13)]+["3V3"]+[str(n) for n in range(24,33)]
upper=["VIN","GND","3V3"]+[str(n) for n in range(23,12,-1)]+["GND"]+[str(n) for n in range(41,32,-1)]
for ref,names,sch,x in [("J1",lower,(65,85),155.24),("J2",upper,(190,85),140)]:
    nets=[pin_nets.get(int(n)) if n.isdigit() else {"GND":"GND","3V3":"3V3","VIN":None}[n] for n in names]
    add(ref,"Teensy 4.1 FEMALE 1x24","Connector_PinSocket_2.54mm:PinSocket_1x24_P2.54mm_Vertical",
        list(range(1,25)),nets,"controller",sch,(x,118.03,180),1.5,"Physical pin legend: "+",".join(names))

for i,a in enumerate(D["axes"],1):
    pg=f"axis{i}";x=5+25*(i-1)
    page(pg,f"{i+1:02} / A{i}: {a['name']}",[
        "Entire axis population optional. No shared connection depends on a fitted axis component.",
        "Mini v1.0 exact 15-hole footprint, NOT mirrored. Buffered EN with local 10k pull-down.",
        "SH order UNVERIFIED: VERIFY WITH MULTIMETER AGAINST AS5048A BOARD. See README table.",
        "Pin labels derive from design.json encoder_pin_order. CS has an individual 10k pull-up."])
    add(f"J{10+i}","Mini v1.0 / 15-hole socket","TrueSkate:SimpleFOC_Mini_v1.0",
        list(range(1,11))+["P1","P2","P3","GND","VIN"],
        ["GND",None,f"A{i}_PWM1","GND",f"A{i}_PWM2",None,
         f"A{i}_PWM3",None,f"A{i}_EN",None,f"A{i}_PH3",f"A{i}_PH2",f"A{i}_PH1","GND","12V_FUSED"],
        pg,(70,65),(x+21,23,270),.7,
        "Optional axis; female 2x5 + female 1x3 + two >=3A single receptacles; matched mating height")
    add(f"J{20+i}","MOTOR PHASES male 1x3","Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        [1,2,3],[f"A{i}_PH{n}" for n in (1,2,3)],pg,(190,45),(x+6.58,3,270),.1,"Optional axis; outward cable clearance at front edge")
    encmap={"CLK":"SPI_SCK","MISO":"SPI_MISO","MOSI":"SPI_MOSI","CSn":f"A{i}_CS","3V3":"3V3","GND":"GND"}
    add(f"J{30+i}","SM06B-SRSS-TB","Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal",
        list(range(1,7)),[encmap[n] for n in D['encoder_pin_order']],pg,(190,90),(x+18,3.3,180),.9,
        "Optional axis; side entry opens toward front (-Y); SH harness pin order UNVERIFIED",lcsc="C160405",assembly="Hand")
    add(f"R{20+i}","10k EN pull-down",RFP,[1,2],[f"A{i}_EN","GND"],pg,(70,120),(x+2,51,270),.05,"Optional axis; fit with Mini")
    add(f"R{30+i}","10k CS pull-up",RFP,[1,2],[f"A{i}_CS","3V3"],pg,(190,185),(x+14.6,61,0),.05,"Optional axis; fit with encoder")
    add(f"C{10+i}","1000uF 35V EEUFR1V102B","Capacitor_THT:CP_Radial_D12.5mm_P5.00mm",
        [1,2],["12V_FUSED","GND"],pg,(70,155),(x+12.5,51.5,0),0,
        "Optional axis; owned Panasonic diameter12.5mm height20mm pitch5mm",lcsc="C128476",assembly="Hand / owned")
    add(f"C{20+i}","100nF 50V ceramic",CFP,[1,2],["12V_FUSED","GND"],pg,(190,155),(x+5,47,270),.13,
        "Optional axis; Vishay K104K10X7RF5UH5",lcsc="C2979769")
page("power","08 / Power and hardware kill",[
    "12V motor rail only. 12mm shared bus; 2mm per-axis feeds; 1oz copper. Thermal evaluation stopped.",
    "NC switch across J6: closed permits EN commands, open tri-states every EN output.",
    "R1 pulls /OE high on open loop. Local R21-R26 pull EN low independently of firmware.",
    "Reclosing switch restores commanded state; no restart latch. Kill does NOT isolate 12V.",
    "U1/U2 SN74HC125N PDIP14, 3.3V, no Ioff. Unused inputs tied; unused outputs NC."])
add("J5","12V INPUT + / -","TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
    [1,2],["12V_IN","GND"],"power",(60,55),(12,115,0),2,"Phoenix1715721 17.5A nominal; verify wire size and applicable rating")
add("F1","Keystone 3557-2 ATO holder","TrueSkate:Keystone_3557-2_ATO",
    [1,2],["12V_IN","12V_PREPOL"],"power",(190,55),(30,112.5,0),1.68,"One complete holder includes both contacts for one standard ATO fuse; fuse purchased separately",lcsc="C352820")
add("J6","NC KILL SWITCH","Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    [1,2],["EN_DISABLE","GND"],"power",(60,85),(61,117,90),.1,"Open loop disables every Mini; closed loop permits firmware EN")
add("R1","10k /OE pull-up",RFP,[1,2],["EN_DISABLE","3V3"],"power",(190,85),(60,110,0),.05)
for chip in (1,2):
    a=1 if chip==1 else 4;xx=76 if chip==1 else 103
    add(f"U{chip}","SN74HC125N","Package_DIP:DIP-14_W7.62mm",list(range(1,15)),
        ["EN_DISABLE",f"A{a}_EN_CMD",f"A{a}_EN","EN_DISABLE",f"A{a+1}_EN_CMD",f"A{a+1}_EN","GND",
         f"A{a+2}_EN",f"A{a+2}_EN_CMD","EN_DISABLE",None,"GND","3V3","3V3"],
        "power",(60 if chip==1 else 190,135),(xx,89,0),1,"Shared mandatory kill buffer; pins1/4/10=/OE,13 disabled; TI SCLS104F; TI DIP-14 C2890; powered-off EN not guaranteed",lcsc="C2890")
    parts[-1]['pin_names']=['/1OE','1A','1Y','/2OE','2A','2Y','GND','3Y','3A','/3OE','4Y','4A','/4OE','VCC']
    add(f"C{chip}","100nF buffer bypass",CFP,[1,2],["3V3","GND"],"power",(60 if chip==1 else 190,175),(xx+7.62,85,180),.13)
    for n in range(3):
        i=a+n
        add(f"R{40+i}","10k EN command pull-down",RFP,[1,2],[f"A{i}_EN_CMD","GND"],"controller",(65 if chip==1 else 190,145+n*25),(xx-13,88+n*8,0),.05,"Shared buffer input bias; may omit with corresponding axis")

page('protection','09 / Fused reverse-polarity protection',[
    'F1 -> Q1 drain; Q1 source -> protected 12V_FUSED bus. P-MOS body diode points input to load.',
    'D1 cathode (band/pad1) to source; anode to gate. R2 10k from gate to GND.',
    'IRF4905PbF: -55V, 20mOhm max at VGS=-10V, -74A case rating. TO-220 pin1 G,2 D/tab,3 S.',
    'V1 operates at a few amps, current-limited. No heat sink below ~5A continuous; 12A copper sizing only.',
    'Single MOSFET is reverse-input protection, not reverse-current or load-disconnect protection.'])
add('Q1','IRF4905PBF','Package_TO_SOT_THT:TO-220-3_Vertical',[1,2,3],
    ['POL_GATE','12V_PREPOL','12V_FUSED'],'protection',(70,60),(126,24,90),.62,
    'Infineon TO-220AB; G,D(tab),S; -55V; 20mOhm max at -10V; 74A case rating; no heat sink below ~5A continuous; 12A copper sizing only',lcsc='C2564')
parts[-1]['pin_names']=['G','D / tab','S']
add('R2','10k gate pull-down',RFP,[1,2],['POL_GATE','GND'],'protection',(70,110),(122,32,270),.01,
    'TyoHM RD1/4W10KJT/BA1; 0.25W,5%; gate bias',lcsc='C433778')
add('D1','1N4742A 12V','Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal',[1,2],
    ['12V_FUSED','POL_GATE'],'protection',(190,110),(120,9,0),.03,
    'ST(Semtech); DO-41 12V 1W; band/cathode pad1 to source, anode pad2 to gate',lcsc='C2545')
parts[-1]['pin_names']=['K / source','A / gate']

def line(fp,a,z,layer,width=.15):
    s=k.PCB_SHAPE(fp);s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(xy(*a));s.SetEnd(xy(*z))
    s.SetLayer(layer);s.SetWidth(k.FromMM(width));fp.Add(s)
def pth(fp,num,x,y,size=1.8,drill=1):
    p=k.PAD(fp);p.SetNumber(str(num));p.SetAttribute(k.PAD_ATTRIB_PTH)
    p.SetShape(k.PAD_SHAPE_RECT if str(num)=="1" else k.PAD_SHAPE_CIRCLE)
    p.SetSize(xy(size,size));p.SetDrillSize(xy(drill,drill));p.SetPosition(xy(x,y))
    p.SetLayerSet(layers(k.F_Cu,k.B_Cu,k.F_Mask,k.B_Mask));fp.Add(p)
def save_fp(fp):
    path=ROOT/'design/TrueSkate.pretty'/(str(fp.GetFPID().GetLibItemName())+'.kicad_mod')
    # The verified Mini library is authoritative across placement-only revisions.
    if path.exists() and fp.GetFPID().GetLibItemName()=='SimpleFOC_Mini_v1.0':return
    previous=path.read_text() if path.exists() else None
    k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(ROOT/'design/TrueSkate.pretty'),fp)
    # Preserve identical libraries rather than rewriting randomly assigned UUIDs.
    normalize=lambda s:re.sub(r'\(uuid "[^"]+"\)','(uuid "")',s)
    if previous is not None and normalize(previous)==normalize(path.read_text()):path.write_text(previous)
def custom():
    (ROOT/"design/TrueSkate.pretty").mkdir(exist_ok=True)
    mini=k.FOOTPRINT(None);mini.SetFPID(k.LIB_ID("TrueSkate","SimpleFOC_Mini_v1.0"));mini.SetReference("REF**")
    mini.SetAttributes(k.FP_THROUGH_HOLE)
    mini.SetLibDescription("SimpleFOCMini tag v1.0; 15 drill-derived contacts; origin H1.9; component-side up, NOT mirrored")
    for name,prefix in [("control",""),("phase","P"),("power","")]:
        for p in G["connectors"][name]:
            pth(mini,prefix+p["pin"],p["x_mm"],p["y_mm"],2.4 if name=="power" else 1.8,p["drill_mm"])
    for path in G["outline_paths"]:
        for a,z in zip(path,path[1:]):line(mini,a,z,k.F_Fab,.1)
    outline=k.SHAPE_POLY_SET();outline.NewOutline()
    for x,y in G['outline_polygon'][:-1]:outline.Append(k.FromMM(x),k.FromMM(y))
    outline.Inflate(k.FromMM(.5),k.CORNER_STRATEGY_ROUND_ALL_CORNERS,k.FromMM(.001),True)
    assert outline.OutlineCount()==1
    chain=outline.COutline(0)
    pts=[(k.ToMM(chain.CPoint(i).x),k.ToMM(chain.CPoint(i).y)) for i in range(chain.PointCount())]
    # Collapse sub-micron offset artifacts before KiCad rotates the courtyard.
    # RDP retains the source-derived curved outline within 1 micron.
    def simplify(seq):
        a,z=seq[0],seq[-1];dx,dy=z[0]-a[0],z[1]-a[1];dd=dx*dx+dy*dy
        def dist(p):
            u=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/dd)) if dd else 0
            return math.hypot(p[0]-a[0]-u*dx,p[1]-a[1]-u*dy)
        if len(seq)<3:return seq
        error,i=max((dist(p),i) for i,p in enumerate(seq[1:-1],1))
        return simplify(seq[:i+1])[:-1]+simplify(seq[i:]) if error>.001 else [a,z]
    mid=len(pts)//2
    pts=simplify(pts[:mid+1])[:-1]+simplify(pts[mid:]+[pts[0]])[:-1]
    for a,z in zip(pts,pts[1:]+pts[:1]):line(mini,a,z,k.F_CrtYd,.05)
    (ROOT/'sources/mini-courtyard.json').write_text(json.dumps(dict(margin_mm=.5,arc_error_mm=.001,points_mm=pts),indent=2)+'\n')
    for a,z in [((-1.3,-1.3),(11.5,-1.3)),((11.5,-1.3),(11.5,3.9)),((11.5,3.9),(-1.3,3.9)),((-1.3,3.9),(-1.3,-1.3))]:line(mini,a,z,k.F_SilkS)
    for label,x,y in [("GND",17.399,1.8),("VIN",17.399,10.8)]:
        t=k.PCB_TEXT(mini);t.SetText(label);t.SetPosition(xy(x,y));t.SetLayer(k.F_SilkS)
        t.SetTextSize(xy(1,1));t.SetTextThickness(k.FromMM(.15));mini.Add(t)
    for name,offset in [("PinSocket_2x05_P2.54mm_Vertical",(10.16,-2.54,0)),("PinSocket_1x03_P2.54mm_Vertical",(8.636,-17.653,0))]:
        m=k.FP_3DMODEL();m.m_Filename="${KICAD10_3DMODEL_DIR}/Connector_PinSocket_2.54mm.3dshapes/"+name+".step"
        m.m_Offset.Set(*offset);m.m_Rotation.z=90;mini.Add3DModel(m)
    save_fp(mini)
    fuse=k.FOOTPRINT(None);fuse.SetFPID(k.LIB_ID('TrueSkate','Keystone_3557-2_ATO'));fuse.SetReference('REF**')
    fuse.SetAttributes(k.FP_THROUGH_HOLE)
    fuse.SetLibDescription('Keystone3557-2: one complete ATO holder; manufacturer drawing3557-2 revD / catalog p47; 13.47x3.40mm hole centres, >=1.60mm drills')
    for n,x in [('1',0),('2',13.47)]:
        for y in (0,3.40):pth(fuse,n,x,y,3,1.65)
    for layer,margin,width in [(k.F_Fab,0,.1),(k.F_CrtYd,.5,.05)]:
        x0,y0,x1,y1=-3.17-margin,-1.665-margin,16.64+margin,5.065+margin
        for a,z in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:line(fuse,a,z,layer,width)
    save_fp(fuse)

def edge_libraries():
    # Project-local variants retain full fabrication/model geometry. Silk body
    # graphics move to Fab to avoid socket/module-pad and edge interference.
    for p in parts:
        lib,name=p['fp'].split(':',1)
        folder=ROOT/'design/TrueSkate.pretty' if lib=='TrueSkate' else SHARE/'footprints'/(lib+'.pretty')
        f=k.FootprintLoad(str(folder),name)
        if p['ref']=='Q1':
            # Max lead rectangle 1.01 x .61 mm (1.18 mm diagonal): allow a 1.4 mm finished hole.
            for pad in f.Pads():pad.SetDrillSize(xy(1.4,1.4));pad.SetSize(xy(2.2,2.2))
        for g in f.GraphicalItems():
            if g.GetLayer()==k.F_SilkS:g.SetLayer(k.F_Fab)
        if lib!='TrueSkate':name='Edge_'+name
        f.SetFPID(k.LIB_ID('TrueSkate',name));save_fp(f);p['fp']='TrueSkate:'+name

def board():
    b=k.BOARD();b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(k.FromMM(1.6))
    # Standard green solder mask: 1:1 openings and >= 0.10 mm webs.
    b.GetDesignSettings().m_SolderMaskMinWidth=k.FromMM(.1)
    def nc_name(p,number):
        index=p['pins'].index(number)
        label=p['note'].split('Physical pin legend: ')[-1].split(',')[index] if p['ref'] in ('J1','J2') else p.get("pin_names",p["pins"])[index]
        return f"unconnected-({p['ref']}{'-'+label if label!=number else ''}-Pad{number})"
    nets={}
    names={n or nc_name(p,number) for p in parts for number,n in zip(p['pins'],p['nets'])}
    for name in sorted(names): nets[name]=k.NETINFO_ITEM(b,name);b.Add(nets[name])
    fps={}
    for p in parts:
        lib,name=p["fp"].split(":",1);folder=ROOT/"design/TrueSkate.pretty" if lib=="TrueSkate" else SHARE/"footprints"/(lib+".pretty")
        f=k.FootprintLoad(str(folder),name);assert f is not None,p["fp"]
        f.SetFPID(k.LIB_ID(lib,name));f.SetReference(p["ref"]);f.SetValue(p["value"])
        f.SetPosition(xy(*p["pcb"][:2]));f.SetOrientationDegrees(p["pcb"][2]);f.Reference().SetVisible(False);f.Value().SetVisible(False)
        path=k.KIID_PATH()
        for label in ("root","sheet-"+p["page"],p["ref"]): path.push_back(k.KIID(uid(label)))
        f.SetPath(path)
        for pad in f.Pads():
            name=dict(zip(p["pins"],p["nets"])).get(pad.GetNumber())
            if pad.GetNumber() in p["pins"]: pad.SetNet(nets[name or nc_name(p,pad.GetNumber())])
        b.Add(f);fps[p["ref"]]=f
    for n,(x,y) in enumerate([(4,4),(WIDTH-4,4),(WIDTH-4,HEIGHT-4),(4,HEIGHT-4)],1):
        f=k.FootprintLoad(str(SHARE/"footprints/MountingHole.pretty"),"MountingHole_3.2mm_M3")
        f.SetAttributes(k.FP_BOARD_ONLY|k.FP_EXCLUDE_FROM_BOM|k.FP_EXCLUDE_FROM_POS_FILES)
        f.SetReference(f"H{n}");f.Reference().SetVisible(False);f.SetPosition(xy(x,y));f.Value().SetVisible(False);b.Add(f)
    for a,z in [((0,0),(WIDTH,0)),((WIDTH,0),(WIDTH,HEIGHT)),((WIDTH,HEIGHT),(0,HEIGHT)),((0,HEIGHT),(0,0))]: line(b,a,z,k.Edge_Cuts,.05)
    def text(label,x,y,size=1,layer=k.F_SilkS):
        t=k.PCB_TEXT(b);t.SetText(label);t.SetPosition(xy(x,y));t.SetLayer(layer)
        size=max(size,1.0) if layer==k.F_SilkS else size
        t.SetTextSize(xy(size,size));t.SetTextThickness(k.FromMM(.15));b.Add(t)
    text("NC KILL",143,102);text("12V + / -",141,62);text("F1 / ATO",136,19)
    text("USB",8,70)
    for bank,axes in BANKS.items():
        for i in axes:
            x,y=axis_point(i,13,8)
            text(f"A{i}",x,y,1.5)
            for label,lx in [(f"M{i}",5),(f"ENC{i}",20)]:
                xx,yy=axis_point(i,lx,7);text(label,xx,yy)
    sx0,sy0,sx1,sy1=SD_SERVICE
    for a,z in [((sx0,sy0),(sx1,sy0)),((sx1,sy0),(sx1,sy1)),((sx1,sy1),(sx0,sy1)),((sx0,sy1),(sx0,sy0))]:line(b,a,z,k.Dwgs_User,.15)
    text("SD CARD SERVICE / KEEP CLEAR",72,70,.8,k.Dwgs_User)
    def pad(ref,n): return next(p for p in fps[ref].Pads() if p.GetNumber()==str(n))
    def pos(p): return k.ToMM(p.GetPosition().x),k.ToMM(p.GetPosition().y)
    def track(name,points,width,layer):
        for a,z in zip(points,points[1:]):
            if a==z: continue
            t=k.PCB_TRACK(b);t.SetStart(xy(*a));t.SetEnd(xy(*z));t.SetNet(nets[name])
            t.SetWidth(k.FromMM(width));t.SetLayer(layer);t.SetLocked(True);b.Add(t)
    def route(ref,n,ref2,n2,width=1,layer=k.F_Cu,bends=()):
        a,z=pad(ref,n),pad(ref2,n2);assert a.GetNetname()==z.GetNetname()
        track(a.GetNetname(),[pos(a),*bends,pos(z)],width,layer)
    # Rotated, never mirrored axis geometry; phases and encoder escapes stay separated.
    for i in range(1,7):
        ap=lambda x,y:axis_point(i,x,y)
        for ph in (1,2,3):
            a=pos(pad(f"J{10+i}",f"P{4-ph}"));end=pos(pad(f"J{20+i}",ph))
            lane=1.4-(ph-1)*1.4
            phase_y={1:16.556,2:19.096,3:21.636}[ph]
            track(f"A{i}_PH{ph}",[a,ap(lane,phase_y),ap(lane,12-2*ph),ap(6.58-2.54*(ph-1),12-2*ph),end],1,k.F_Cu)
        for pin in range(1,7):
            p=pad(f'J{30+i}',pin);start=pos(p)
            # Local pin X is 20.5-(pin-1); fanout reaches the inboard side.
            startx=20.5-(pin-1);lane=16.8-.8*(pin-1);endx=lane+5.5
            track(p.GetNetname(),[start,ap(startx,6.5),ap(lane,6.5+startx-lane),ap(lane,24.5),ap(endx,30),ap(endx,35)],.25 if pin<=4 else .3,k.F_Cu)
        mini,bulk,cer=f"J{10+i}",f"C{10+i}",f"C{20+i}"
        route(mini,'VIN',bulk,1,2,k.F_Cu,[ap(12.237,41.5)])
        route(mini,'VIN',cer,1,.6,k.F_Cu,[ap(12.237,37)])
        track('12V_FUSED',[ap(12.5,53),pos(pad(bulk,1))],2,k.F_Cu)
    # Both bank backbones and the common right-hand feed retain 12 mm copper.
    track('12V_FUSED',[(20.5,53),(112,53),(112,87),(21.5,87)],12,k.F_Cu)
    for p in fps['F1'].Pads():
        pp=pos(p)
        if p.GetNumber()=='2':track('12V_PREPOL',[pp,(pp[0],21.46),(131,21.46)],6,k.F_Cu)
        if p.GetNumber()=='1':track('12V_IN',[pp,(pp[0],56),pos(pad('J5',1))],6,k.F_Cu)
    # Opposite-side escapes keep G/D/S separated at 2.54 mm pitch, then flare.
    track('12V_PREPOL',[pos(pad('Q1',2)),(131,21.46)],2,k.F_Cu)
    track('12V_FUSED',[pos(pad('Q1',3)),(121.5,18.92)],2,k.F_Cu)
    track('12V_FUSED',[(121.5,18.92),(112,18.92)],6,k.F_Cu)
    track('12V_FUSED',[(112,18.92),(112,53)],12,k.F_Cu)
    track('POL_GATE',[pos(pad('Q1',1)),(126,28),pos(pad('R2',1))],.3,k.F_Cu)
    track('POL_GATE',[pos(pad('D1',2)),(145,9),(145,34),(124,34),pos(pad('R2',1))],.3,k.B_Cu)
    track('12V_FUSED',[pos(pad('D1',1)),(120,15.5),(121.5,18.92)],.6,k.F_Cu)
    # Parallel top/bottom short lead necks, joined to the broad top routes by four vias each.
    track('12V_PREPOL',[pos(pad('Q1',2)),(131,21.46),(132.5,21.46)],2,k.B_Cu)
    track('12V_PREPOL',[(131,21.46),(132.5,21.46)],6,k.B_Cu)
    track('12V_FUSED',[pos(pad('Q1',3)),(121.5,18.92)],2,k.B_Cu)
    track('12V_FUSED',[(121.5,18.92),(120,18.92)],6,k.B_Cu)
    power_vias=[]
    for name,points in [('12V_PREPOL',[(131,21.46),(132.5,21.46),(131,22.96),(132.5,22.96)]),('12V_FUSED',[(120,18.92),(121.5,18.92),(120,17.42),(121.5,17.42)])]:
        for x,y in points:
            v=k.PCB_VIA(b);v.SetPosition(xy(x,y));v.SetWidth(k.FromMM(1.2));v.SetDrill(k.FromMM(.6));v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetViaType(k.VIATYPE_THROUGH);v.SetNet(nets[name]);v.SetLocked(True);b.Add(v)
            power_vias.append(dict(net=name,x=x,y=y,diameter_mm=1.2,drill_mm=.6))
    (ROOT/'design/data/power-vias.json').write_text(json.dumps(power_vias,indent=2)+'\n')
    for layer in (k.F_Cu,k.B_Cu):
        z=k.ZONE(b);z.SetLayer(layer);z.SetNet(nets["GND"]);z.SetLocalClearance(k.FromMM(.3))
        z.SetIslandRemovalMode(k.ISLAND_REMOVAL_MODE_ALWAYS);z.SetMinThickness(k.FromMM(.25));z.SetPadConnection(k.ZONE_CONNECTION_FULL)
        outline=z.Outline();outline.NewOutline()
        for x,y in [(1,1),(WIDTH-1,1),(WIDTH-1,HEIGHT-1),(1,HEIGHT-1)]:outline.Append(int(k.FromMM(x)),int(k.FromMM(y)))
        b.Add(z)
    k.ZONE_FILLER(b).Fill(b.Zones())
    k.SaveBoard(str(ROOT/'design'/(PROJECT+".kicad_pcb")),b,True)
    pcbpath=ROOT/'design'/(PROJECT+".kicad_pcb")
    source=pcbpath.read_text()
    stack='(stackup (layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01)) (layer "F.Cu" (type "copper") (thickness 0.035)) (layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02)) (layer "B.Cu" (type "copper") (thickness 0.035)) (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01)) (layer "B.SilkS" (type "Bottom Silk Screen")) (copper_finish "HASL lead-free") (dielectric_constraints no))'
    pcbpath.write_text(source.replace('(setup','(setup '+stack,1))
    (ROOT/"design/data/manual-routes.json").write_text(json.dumps([
        dict(net=t.GetNetname(),layer=t.GetLayerName(),width=k.ToMM(t.GetWidth(k.F_Cu) if isinstance(t,k.PCB_VIA) else t.GetWidth()),
             start=[k.ToMM(t.GetStart().x),k.ToMM(t.GetStart().y)],end=[k.ToMM(t.GetEnd().x),k.ToMM(t.GetEnd().y)])
        for t in b.GetTracks() if not isinstance(t,k.PCB_VIA)],indent=2)+"\n")
def bom():
    (ROOT/"design/data/circuit.json").write_text(json.dumps(parts,indent=2)+"\n")
    with (ROOT/"bom/bom-review.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(["Reference","Quantity","Value","Footprint","LCSC","Assembly","Estimated USD each","Notes"])
        for p in parts: w.writerow([p["ref"],1,p["value"],p["fp"],p["lcsc"],p["assembly"],p["price"],p["note"]])
        w.writerow(["J11-J16 VIN/GND",12,"Single machine-pin receptacle","Included in SimpleFOC_Mini_v1.0","","Hand",.5,">=3 A/contact; body/tail fits 1.101 mm finished hole; compatible pin and matching seated height; MPN pending mechanical selection"])
if __name__=="__main__":
    place(parts);custom();edge_libraries();write_project(ROOT/'design',PROJECT,parts);write_schematic(ROOT/'design',PROJECT,parts,pages,uid);bom();board()
    print(f"Generated {len(parts)}-item carrier. Signal routing follows separately.")
    print("Review only: no manufacturing exports.")
