#!/usr/bin/env python3
"""All-through-hole carrier source; deliberate power routing, no manufacturing exports.

The previous full-feature draft is preserved by local checkpoint 36e9dca.
Run with KiCad's bundled Python. Signal routing is a separate step.
"""
import csv
import json
import os
from pathlib import Path
import uuid
import pcbnew as k
from kicad_source import write_schematic, write_project

ROOT=Path(__file__).resolve().parent
SHARE=Path(os.environ.get("KICAD_SHARE","/Applications/KiCad/KiCad.app/Contents/SharedSupport"))
D=json.loads((ROOT/"design.json").read_text())
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
    parts.append(p);pages[pg]["parts"].append(p)

page("controller","01 / USB-powered Teensy sockets",[
    "USB is the ONLY Teensy power source. VIN socket contact is deliberately unconnected.",
    "All six axes use edge-aligned PWM. Existing firmware needs the new EN/CS assignments.",
    "Teensy 3.3V powers encoders. Mini regulator outputs are NOT connected to this rail.",
    "Mini fit, encoder pin 1 and 160 x 120 mm base fit confirmed by the user."])
pin_nets={}
for i,a in enumerate(D["axes"],1):
    for n,pin in enumerate(a["pwm"],1): pin_nets[pin]=f"A{i}_PWM{n}"
    pin_nets[a["enable"]]=f"A{i}_EN";pin_nets[a["cs"]]=f"A{i}_CS"
pin_nets.update({11:"SPI_MOSI",12:"SPI_MISO",13:"SPI_SCK"})
lower=["GND"]+[str(n) for n in range(13)]+["3V3"]+[str(n) for n in range(24,33)]
upper=["VIN","GND","3V3"]+[str(n) for n in range(23,12,-1)]+["GND"]+[str(n) for n in range(41,32,-1)]
for ref,names,sch,y in [("J1",lower,(65,85),75.24),("J2",upper,(190,85),60)]:
    nets=[pin_nets.get(int(n)) if n.isdigit() else {"GND":"GND","3V3":"3V3","VIN":None}[n] for n in names]
    add(ref,"Teensy 4.1 FEMALE 1x24","Connector_PinSocket_2.54mm:PinSocket_1x24_P2.54mm_Vertical",
        list(range(1,25)),nets,"controller",sch,(44,y,90),1.5,"Physical pin legend: "+",".join(names))

for i,a in enumerate(D["axes"],1):
    pg=f"axis{i}";col=(i-1)%3;top=i<=3;x=35+43*col;y=30 if top else 92
    page(pg,f"{i+1:02} / A{i}: {a['name']}",[
        "Mini footprint fit confirmed on the 1:1 template. Female control and phase sockets.",
        "EN goes directly to Teensy; 10k to this Mini's power ground holds EN low at reset.",
        "JP control-ground bridge defaults OPEN; module already references its power-return wire.",
        "Breakout socket: 1 CLK, 2 MISO, 3 MOSI, 4 CSn, 5 3.3V, 6 GND. Pin 1 is marked.",
        "Mini 3.3V output, nRESET, nSLEEP and nFAULT contacts intentionally unconnected."])
    add(f"J{10+i}","Mini v1.0 FEMALE sockets","TrueSkate:Mini_v1_Sockets",
        list(range(1,11))+["P1","P2","P3"],
        [f"CGND{i}",None,f"A{i}_PWM1",f"CGND{i}",f"A{i}_PWM2",None,
         f"A{i}_PWM3",None,f"A{i}_EN",None,f"A{i}_PH3",f"A{i}_PH2",f"A{i}_PH1"],
        pg,(70,65),(x,y,180 if top else 0),.7,"User-verified 2x5 and 1x3 female socket geometry")
    add(f"J{20+i}","MOTOR PHASES male 1x3","Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        [1,2,3],[f"A{i}_PH{n}" for n in (1,2,3)],pg,(190,45),
        (x+6.604 if top else x-6.604,7 if top else 116,270 if top else 90),.1)
    add(f"J{30+i}","ENCODER breakout FEMALE 1x6","Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Vertical",
        list(range(1,7)),["SPI_SCK","SPI_MISO","SPI_MOSI",f"A{i}_CS","3V3","GND"],
        pg,(190,90),(43+43*col,47 if top else 79,90),.5,"Pin 1 = square pad = CLK; verified by user")
    add(f"R{20+i}","10k EN pull-down","Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
        [1,2],[f"A{i}_EN",f"PGND{i}"],pg,(70,120),
        (34+43*col,36,0) if top else (61+43*col,79,0),.05,"10k, 1/4 W, 5% or better")
    add(f"JP{i}","CONTROL GND / OPEN","TrueSkate:GroundBridge_THT",[1,2],[f"CGND{i}","GND"],
        pg,(190,120),(25+43*col,36,0) if top else (35.5+43*col,82,0),0,
        "Leave open; optional soldered wire bridge after noise review",assembly="PCB / optional wire")
    bx,by=(x+21,16) if top else (x+18,109.5)
    add(f"C{10+i}","1000uF 35V EEUFR1V102B","Capacitor_THT:CP_Radial_D12.5mm_P5.00mm",
        [1,2],["12V_FUSED",f"PGND{i}"],pg,(70,155),(bx,by,0),0,
        "Owned Panasonic; diameter 12.5mm, height 20mm, pitch 5mm",lcsc="C128476",assembly="Hand / owned")
    add(f"C{20+i}","100nF 50V ceramic","Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
        [1,2],["12V_FUSED",f"PGND{i}"],pg,(190,155),
        (x+21,24.2,0) if top else (x+18,101.5,0),.13,
        "Vishay K104K10X7RF5UH5; 5mm pitch; body 3.6 x 2.3mm max; hand solder",lcsc="C2979769")
    add(f"J{40+i}","MINI POWER +12V / GND","TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1-2-3.81_1x02_P3.81mm_Horizontal",
        [1,2],["12V_FUSED",f"PGND{i}"],pg,(70,190),
        (x+21,30,0) if top else (x+18,94,0),2.5,"Phoenix Contact 1727010; approved short paired wires to Mini")
page("power","08 / Fused 12V and ground star",[
    "12V is motor power only: no connection to Teensy VIN, VUSB or 3.3V.",
    "Through-hole fuse holder; candidate 3.15A time-delay cartridge, qualify load/inrush.",
    "Correct input polarity required. Reverse-polarity protection moved to the v2 backlog.",
    "NT1 is PCB copper: six separate motor returns and logic ground meet at this junction.",
    "No hardware kill on v1. Disconnect 12V to remove motor power."])
add("J5","12V INPUT + / -","TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
    [1,2],["12V_IN","GND"],"power",(65,55),(7,69,0),2,"Phoenix Contact 1715721; 5.08mm pitch")
add("F1","5x20 fuse holder / fuse TBD","Fuse:Fuseholder_Cylinder-5x20mm_Schurter_0031_8201_Horizontal_Open",
    [1,2],["12V_IN","12V_FUSED"],"power",(190,55),(8,50,90),1.8,"Schurter 0031.8201; cartridge separately purchased",lcsc="C3204125")
add("NT1","GROUND STAR / PCB COPPER","TrueSkate:GroundStar",list(range(1,8)),
    ["GND"]+[f"PGND{i}" for i in range(1,7)],"power",(65,105),(22,69,0),assembly="PCB copper")

def line(fp,a,z,layer,width=.15):
    s=k.PCB_SHAPE(fp);s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(xy(*a));s.SetEnd(xy(*z))
    s.SetLayer(layer);s.SetWidth(k.FromMM(width));fp.Add(s)
def pth(fp,num,x,y,size=1.8,drill=1):
    p=k.PAD(fp);p.SetNumber(str(num));p.SetAttribute(k.PAD_ATTRIB_PTH)
    p.SetShape(k.PAD_SHAPE_RECT if str(num)=="1" else k.PAD_SHAPE_CIRCLE)
    p.SetSize(xy(size,size));p.SetDrillSize(xy(drill,drill));p.SetPosition(xy(x,y))
    p.SetLayerSet(layers(k.F_Cu,k.B_Cu,k.F_Mask,k.B_Mask));fp.Add(p)
def save_fp(fp): k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(ROOT/"TrueSkate.pretty"),fp)
def custom():
    (ROOT/"TrueSkate.pretty").mkdir(exist_ok=True)
    mini=k.FOOTPRINT(None);mini.SetFPID(k.LIB_ID("TrueSkate","Mini_v1_Sockets"));mini.SetReference("REF**")
    mini.SetAttributes(k.FP_THROUGH_HOLE)
    for name,prefix in [("control",""),("phase","P")]:
        for p in G["connectors"][name]: pth(mini,prefix+p["pin"],p["x_mm"],p["y_mm"])
    for a,z in [((-15,-3),(12,-3)),((12,-3),(12,21)),((12,21),(-15,21)),((-15,21),(-15,-3))]:
        line(mini,a,z,k.F_CrtYd,.05);line(mini,a,z,k.F_Fab,.1)
    for a,z in [((-11.5,-1.3),(1.3,-1.3)),((1.3,-1.3),(1.3,3.9)),((1.3,3.9),(-11.5,3.9)),((-11.5,3.9),(-11.5,-1.3))]: line(mini,a,z,k.F_SilkS)
    for name,offset in [("PinSocket_2x05_P2.54mm_Vertical",(0,-2.54,0)),("PinSocket_1x03_P2.54mm_Vertical",(-1.524,-17.653,0))]:
        m=k.FP_3DMODEL();m.m_Filename="${KICAD10_3DMODEL_DIR}/Connector_PinSocket_2.54mm.3dshapes/"+name+".step"
        m.m_Offset.Set(*offset);m.m_Rotation.z=90;mini.Add3DModel(m)
    save_fp(mini)
    star=k.FOOTPRINT(None);star.SetFPID(k.LIB_ID("TrueSkate","GroundStar"));star.SetReference("REF**")
    star.SetAttributes(k.FP_THROUGH_HOLE);star.AddNetTiePadGroup("1,2,3,4,5,6,7")
    for n,y in [(1,0),(2,-9),(3,-6),(4,-3),(5,9),(6,6),(7,3)]: pth(star,n,0,y,2,1)
    for layer in (k.F_Cu,k.B_Cu): line(star,(0,-9),(0,9),layer,2)
    for a,z in [((-1.5,-10.5),(1.5,-10.5)),((1.5,-10.5),(1.5,10.5)),((1.5,10.5),(-1.5,10.5)),((-1.5,10.5),(-1.5,-10.5))]: line(star,a,z,k.F_CrtYd,.05)
    save_fp(star)
    bridge=k.FOOTPRINT(None);bridge.SetFPID(k.LIB_ID("TrueSkate","GroundBridge_THT"));bridge.SetReference("REF**")
    bridge.SetAttributes(k.FP_THROUGH_HOLE);pth(bridge,1,0,0);pth(bridge,2,3,0)
    for a,z in [((-1.3,-1.3),(4.3,-1.3)),((4.3,-1.3),(4.3,1.3)),((4.3,1.3),(-1.3,1.3)),((-1.3,1.3),(-1.3,-1.3))]: line(bridge,a,z,k.F_CrtYd,.05)
    save_fp(bridge)

def board():
    b=k.BOARD();b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(k.FromMM(1.6))
    # Standard green 1 oz solder mask: 1:1 openings and >= 0.10 mm webs.
    b.GetDesignSettings().m_SolderMaskMinWidth=k.FromMM(.1)
    def nc_name(p,number):
        index=p['pins'].index(number)
        label=p['note'].split('Physical pin legend: ')[-1].split(',')[index] if p['ref'] in ('J1','J2') else number
        return f"unconnected-({p['ref']}{'-'+label if label!=number else ''}-Pad{number})"
    nets={}
    names={n or nc_name(p,number) for p in parts for number,n in zip(p['pins'],p['nets'])}
    for name in sorted(names): nets[name]=k.NETINFO_ITEM(b,name);b.Add(nets[name])
    fps={}
    for p in parts:
        lib,name=p["fp"].split(":",1);folder=ROOT/"TrueSkate.pretty" if lib=="TrueSkate" else SHARE/"footprints"/(lib+".pretty")
        f=k.FootprintLoad(str(folder),name);assert f is not None,p["fp"]
        f.SetFPID(k.LIB_ID(lib,name));f.SetReference(p["ref"]);f.SetValue(p["value"])
        f.SetPosition(xy(*p["pcb"][:2]));f.SetOrientationDegrees(p["pcb"][2]);f.Reference().SetVisible(False);f.Value().SetVisible(False)
        path=k.KIID_PATH()
        for label in ("root","sheet-"+p["page"],p["ref"]): path.push_back(k.KIID(uid(label)))
        f.SetPath(path)
        for pad in f.Pads():
            name=dict(zip(p["pins"],p["nets"])).get(pad.GetNumber())
            if pad.GetNumber(): pad.SetNet(nets[name or nc_name(p,pad.GetNumber())])
        b.Add(f);fps[p["ref"]]=f
    for n,(x,y) in enumerate([(5,5),(155,5),(155,115),(5,115)],1):
        f=k.FootprintLoad(str(SHARE/"footprints/MountingHole.pretty"),"MountingHole_3.2mm_M3")
        f.SetAttributes(k.FP_BOARD_ONLY|k.FP_EXCLUDE_FROM_BOM|k.FP_EXCLUDE_FROM_POS_FILES)
        f.SetReference(f"H{n}");f.SetPosition(xy(x,y));f.Value().SetVisible(False);b.Add(f)
    for a,z in [((0,0),(160,0)),((160,0),(160,120)),((160,120),(0,120)),((0,120),(0,0))]: line(b,a,z,k.Edge_Cuts,.05)
    def text(label,x,y,size=1,layer=k.F_SilkS):
        t=k.PCB_TEXT(b);t.SetText(label);t.SetPosition(xy(x,y));t.SetLayer(layer)
        size=max(size,1.0) if layer==k.F_SilkS else size
        t.SetTextSize(xy(size,size));t.SetTextThickness(k.FromMM(.15));b.Add(t)
    text("TrueSkate v1 / USB-POWERED CARRIER",83,1.2,1)
    text("USB ONLY",35,67);text("NO VIN",43,56.5,.8)
    text("12V +  -",10,78);text("F1 / 5x20",8,21);text("STAR",22,56,.9)
    text("POWER OFF BEFORE MOVING MOTOR WIRES",87,118.5,.8)
    for i in range(1,7):
        c=(i-1)%3;x=35+43*c;top=i<=3
        text(f"A{i}",x-5 if top else x-17,32 if top else 96,1.2)
        text(f"ENC{i}: 1 CLK",49+43*c,44 if top else 82.1)
        text(f"JP{i} OPEN",26.5+43*c if top else 37+43*c,33.5 if top else 84.5)
        text(f"R{20+i} 10k",37.8+43*c if top else 64.8+43*c,33.5 if top else 82)
        text("+12  GND",58+43*c,38.5 if top else 89)
        text("1  2  3",44+43*c if top else 31+43*c,4.5 if top else 113.4,.65)
    for a,z in [((55,125),(105,125)),((55,123),(55,127)),((105,123),(105,127))]: line(b,a,z,k.Dwgs_User,.2)
    for label,x,y in [("TOP VIEW / PRINT 100% / NOT MIRRORED",80,-5),("50 mm between ticks - check print scale",80,130)]: text(label,x,y,1.1,k.Dwgs_User)
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
    # All motor phases, 12V feeds and power returns are deliberately drawn and locked.
    for i in range(1,7):
        for ph in (1,2,3): route(f"J{10+i}",f"P{4-ph}",f"J{20+i}",ph,1)
        bulk,term,cer=f"C{10+i}",f"J{40+i}",f"C{20+i}"
        route(bulk,1,term,1,1.5)
        bx,by=pos(pad(bulk,2));tx,ty=pos(pad(term,2));mid=(by+ty)/2
        route(bulk,2,term,2,1.5,bends=[(bx,mid),(tx,mid+abs(bx-tx)*(1 if ty>by else -1))])
        for n in (1,2):
            cx,cy=pos(pad(cer,n));tx,ty=pos(pad(term,n))
            route(cer,n,term,n,.6,bends=[(cx,(cy+ty)/2),(tx,(cy+ty)/2)])
        rx,ry=pos(pad(f"R{20+i}",2));tx,ty=pos(pad(term,2))
        route(f"R{20+i}",2,term,2,.4,k.F_Cu,[(rx,ry+3),(tx,ry+3)] if i<=3 else [(rx-3,ry+3),(rx-8.62,ry+3),(rx-8.62,97),(tx,97)])
        route(f"J{10+i}",1,f"J{10+i}",4,.3)
        mx,my=pos(pad(f"J{10+i}",1));jx,jy=pos(pad(f"JP{i}",1))
        route(f"J{10+i}",1,f"JP{i}",1,.3,k.F_Cu,[(jx,my)] if i<=3 else [(mx,84)])
        if i<=3:
            jx,jy=pos(pad(f"JP{i}",2))
            track("GND",[(jx,jy),(jx,45.5)],.5,k.F_Cu)
    route("J5",1,"F1",1,3,bends=[(7,51)])
    route("J5",2,"NT1",1,3)
    track("12V_FUSED",[pos(pad("F1",2)),(17.5,18),(17.5,112.8),(139,112.8)],3,k.B_Cu)
    track("12V_FUSED",[pos(pad("F1",2)),(17.5,18),(17.5,3.5),(142,3.5)],3,k.F_Cu)
    for i in range(1,7):
        x,y=pos(pad(f"C{10+i}",1));track("12V_FUSED",[(x,3.5 if i<=3 else 112.8),(x,y)],2,k.F_Cu if i<=3 else k.B_Cu)
    for i in range(1,4):
        sx,sy=pos(pad("NT1",i+1));tx,ty=pos(pad(f"J{40+i}",2));rail=37+2*i;fan=28+2*i
        track(f"PGND{i}",[(sx,sy),(fan,sy-(fan-sx)),(fan,rail),(tx,rail),(tx,ty)],1.5,k.B_Cu)
    for i in range(4,7):
        sx,sy=pos(pad("NT1",i+1));tx,ty=pos(pad(f"J{40+i}",2));rail=97-2*i;fan=22+2*i
        track(f"PGND{i}",[(sx,sy),(fan,sy+(fan-sx)),(fan,rail),(tx,rail),(tx,ty)],1.5,k.B_Cu)
    track("GND",[pos(pad("NT1",1)),(29,69)],1.5,k.F_Cu)
    # Encoder supply is deliberately routed, separate from the motor-power rails.
    route("J2",3,"J1",15,.4,k.F_Cu,[(49.08,64),(79.56,64)])
    track("3V3",[(49.08,60),(49.08,54),(53.16,52),(139.16,52)],.4,k.F_Cu)
    track("3V3",[(53.16,77),(139.16,77)],.4,k.F_Cu)
    track("3V3",[(79.56,75.24),(79.56,77)],.4,k.F_Cu)
    for i in range(1,7):
        px,py=pos(pad(f"J{30+i}",5))
        track("3V3",[(px,py),(px,52 if i<=3 else 77)],.4,k.F_Cu)
    for layer in (k.F_Cu,k.B_Cu):
        z=k.ZONE(b);z.SetLayer(layer);z.SetNet(nets["GND"]);z.SetLocalClearance(k.FromMM(.3))
        z.SetMinThickness(k.FromMM(.25));z.SetPadConnection(k.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(k.FromMM(.3));z.SetThermalReliefSpokeWidth(k.FromMM(.4))
        outline=z.Outline();outline.NewOutline()
        # The front plane wraps around the control sockets so signal fences do
        # not isolate encoder/Teensy grounds. It does not join any PGND branch.
        # Outer motor phase headers and shared 12 V trunks remain outside it.
        # The back plane stays between the separately routed motor returns.
        left,top,bottom=(27,20,102) if layer==k.F_Cu else (28,44,84)
        for x,y in [(left,top),(157,top),(157,bottom),(left,bottom)]: outline.Append(int(k.FromMM(x)),int(k.FromMM(y)))
        b.Add(z)
    k.ZONE_FILLER(b).Fill(b.Zones())
    k.SaveBoard(str(ROOT/(PROJECT+".kicad_pcb")),b,True)
    (ROOT/"manual-routes.json").write_text(json.dumps([
        dict(net=t.GetNetname(),layer=t.GetLayerName(),width=k.ToMM(t.GetWidth(k.F_Cu) if isinstance(t,k.PCB_VIA) else t.GetWidth()),
             start=[k.ToMM(t.GetStart().x),k.ToMM(t.GetStart().y)],end=[k.ToMM(t.GetEnd().x),k.ToMM(t.GetEnd().y)])
        for t in b.GetTracks()],indent=2)+"\n")
def bom():
    (ROOT/"circuit.json").write_text(json.dumps(parts,indent=2)+"\n")
    with (ROOT/"bom-review.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(["Reference","Value","Footprint","LCSC","Assembly","Estimated USD each","Notes"])
        for p in parts: w.writerow([p["ref"],p["value"],p["fp"],p["lcsc"],p["assembly"],p["price"],p["note"]])
if __name__=="__main__":
    custom();write_project(ROOT,PROJECT,parts);write_schematic(ROOT,PROJECT,parts,pages,uid);bom();board()
    print(f"Generated {len(parts)}-item through-hole carrier. Signal routing follows separately.")
    print("Review only: no manufacturing exports.")
