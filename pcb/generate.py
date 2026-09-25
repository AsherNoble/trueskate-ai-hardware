#!/usr/bin/env python3
"""Generate a review-stage KiCad project. Never emit fabrication files.

Run using KiCad's bundled Python (pcbnew). Circuit/placement data below are
the editable source of truth. Mini power uses approved short screw-terminal
wire pairs. Fabrication remains blocked by hardware identification checks.
"""
import csv
import json
import math
import os
from pathlib import Path
import uuid

import pcbnew as k

ROOT = Path(__file__).resolve().parent
SHARE = Path(os.environ.get("KICAD_SHARE", "/Applications/KiCad/KiCad.app/Contents/SharedSupport"))
D = json.loads((ROOT / "design.json").read_text())
G = json.loads((ROOT / "sources/mini-geometry.json").read_text())
PROJECT = "trueskate-main-v1"
NAMESPACE = uuid.UUID("0155f481-079d-43c3-a259-e57f78864d1c")
def uid(s): return str(uuid.uuid5(NAMESPACE, s))
def q(s): return json.dumps(str(s))
def xy(x, y): return k.VECTOR2I(k.FromMM(x), k.FromMM(y))
def layers(*ids):
    result=k.LSET()
    for layer in ids: result.AddLayer(layer)
    return result
def eff(size=1.0, extra=""): return f'(effects (font (size {size} {size})) {extra})'

parts = []
pages = {}
def page(name, title, notes):
    pages[name] = {"title": title, "notes": notes, "parts": []}

def add(ref, value, fp, pins, nets, page_name, sch, pcb, lcsc="", price=0,
        assembly="JLCPCB", types=None, note=""):
    assert ref not in [p["ref"] for p in parts]
    assert len(pins) == len(nets)
    part = dict(ref=ref, value=value, fp=fp, pins=[str(x) for x in pins],
                nets=nets, page=page_name, sch=sch, pcb=pcb, lcsc=lcsc,
                price=price, assembly=assembly, types=types or ["passive"]*len(pins), note=note)
    parts.append(part)
    pages[page_name]["parts"].append(part)
    return part

RFP="Resistor_SMD:R_0603_1608Metric"
CFP="Capacitor_SMD:C_0603_1608Metric"
HEADER="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
SH="Connector_JST:JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical"
def resistor(ref,value,a,b,page_name,sch,pcb,lcsc="C25804"):
    return add(ref,value,RFP,[1,2],[a,b],page_name,sch,pcb,lcsc,.01)
def cap(ref,value,a,b,page_name,sch,pcb,fp=CFP,lcsc="C14663"):
    return add(ref,value,fp,[1,2],[a,b],page_name,sch,pcb,lcsc,.015)

page("controller", "01 / Socketed Teensy and signal allocation", [
    "All pin numbers are Teensy numbers. Socket contact names are physical pad IDs.",
    "18 PWM outputs use edge alignment at one common frequency: initially 25 kHz.",
    "USB/VIN link MUST be cut on Teensy before simultaneous board and USB power.",
    "J3 is a wire from Teensy VUSB, not a connection to its USB-host 5V pad.",
    "This is a review draft. Existing firmware still uses the old one-axis wiring."])
pin_nets={}
for i,a in enumerate(D["axes"],1):
    for phase,p in enumerate(a["pwm"],1): pin_nets[p]=f"A{i}_PWM{phase}"
    pin_nets[a["enable"]]=f"A{i}_EN_REQ"
    pin_nets[a["cs"]]=f"A{i}_CS"
pin_nets.update({11:"SPI_MOSI",12:"SPI_MISO",13:"SPI_SCK",34:"WRIST_RX",35:"WRIST_TX",
                41:"WRIST_TX_ENABLE",18:"LINK_SDA",19:"LINK_SCL",10:"KILL_OK"})
left=["GND"]+[str(x) for x in range(13)]+["3V3"]+[str(x) for x in range(24,33)]
right=["VIN","GND","3V3"]+[str(x) for x in range(23,12,-1)]+["GND"]+[str(x) for x in range(41,32,-1)]
# PJRC top-view card, USB to the LEFT: VIN row is ABOVE the GND/pin-0 row.
for ref,pins,sx,by in [("J1",left,60,75.24),("J2",right,175,60)]:
    nets=[pin_nets.get(int(p)) if p.isdigit() else {"VIN":"VIN_OR","3V3":"3V3","GND":"GND"}[p] for p in pins]
    add(ref,"Teensy 4.1 FEMALE 1x24", "Connector_PinSocket_2.54mm:PinSocket_1x24_P2.54mm_Vertical",
        list(range(1,25)),nets,"controller",(sx,85),(44,by,90),price=1.5,assembly="Hand",note="24x 2.54 mm; physical pin legend: "+",".join(pins))
add("J3","VUSB from isolated Teensy pad", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    [1,2],["VUSB","GND"],"controller",(60,150),(42,31,0),price=.15,assembly="Hand")
# A socket is electrically passive. These markers model the module's actual
# 3.3V regulator output and its SPI/enable outputs for ERC; see ERC scope notes.
page("safety", "02 / Normally-closed hardware kill", [
    "Close NC loop to request permission; open loop/broken cable forces all EN low.",
    "U1/U2 AND each EN request with KILL_OK. Pulldowns keep requests off at boot.",
    "U3 has a Schmitt input: its two switching thresholds reject slow/noisy edges.",
    "NON-LATCHING: restoring the switch can restart a motor if its request is high.",
    "Servo supply is also removed by Q2. This is not a safety-rated stop circuit."])
add("J4","NC KILL SWITCH", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",[1,2],
    ["KILL_SEND","KILL_RAW"],"safety",(55,40),(12,60,0),price=.15,assembly="Hand")
resistor("R1","1k", "3V3","KILL_SEND","safety",(130,40),(20,58,0),"C21190")
resistor("R2","10k", "KILL_RAW","GND","safety",(205,40),(20,64,0))
cap("C1","1nF 50V", "KILL_RAW","GND","safety",(55,70),(24,64,0),lcsc="C1588")
add("U3","SN74LVC1G17DBVR", "Package_TO_SOT_SMD:SOT-23-5",[1,2,3,4,5],
    [None,"KILL_RAW","GND","KILL_OK","3V3"],"safety",(130,70),(28,62,0),"C7836",.15,
    types=["no_connect","input","power_in","output","power_in"])
cap("C2","100nF 50V","3V3","GND","safety",(205,70),(31,65,0))
for bank in range(2):
    nets=[]
    # Physical 74LVC08 pin order, including the reversed pin sequence for gates 3/4.
    gate=[]
    for g in range(4):
        n=bank*3+g+1
        gate.append([f"A{n}_EN_REQ","KILL_OK",f"A{n}_EN"] if g<3 else
                    (["WRIST_TX_ENABLE","KILL_OK","WRIST_TX_ALLOWED"] if bank==1 else ["GND","GND",None]))
    nets=gate[0]+gate[1]+["GND"]+[gate[2][2],gate[2][0],gate[2][1],gate[3][2],gate[3][0],gate[3][1],"3V3"]
    types=["input","input","output","input","input","output","power_in","output","input","input","output","input","input","power_in"]
    add(f"U{bank+1}","SN74LVC08APWR", "Package_SO:TSSOP-14_4.4x5mm_P0.65mm",range(1,15),nets,
        "safety",(70+bank*115,120),(28+bank*11,71,0),"C465737",.3759,types=types)
    cap(f"C{3+bank}","100nF 50V","3V3","GND","safety",(70+bank*115,165),(28+bank*11,76,0))

for i,a in enumerate(D["axes"],1):
    pg=f"axis{i}"
    page(pg, f"{i+2:02} / Axis {i}: {a['name']}", [
        "Female sockets at exact upstream v1.0 coordinates; verify against your physical Mini.",
        "Mini pin 2 is its own regulator OUTPUT. NEVER connect it to Teensy 3.3V.",
        "Mini ground pins 1/4 left open: ground reference comes through the paired power wires.",
        "Mini power: approved short screw-terminal wire pair, 12V plus dedicated motor return.",
        "Encoder contact order verified on bench: 1 CLK, 2 MISO, 3 MOSI, 4 CSn, 5 VDD, 6 GND.",
        "Before plugging any encoder in: meter socket contact 5 for 3.3V and contact 6 for ground."])
    col=(i-1)%3; row=(i-1)//3
    x=35+col*43; y=36 if row==0 else 92
    # Combined socket footprint preserves non-grid phase header offset.
    pins=list(range(1,11))+["P1","P2","P3"]
    nets=[None,None,f"A{i}_PWM1",None,f"A{i}_PWM2",None,f"A{i}_PWM3",None,f"A{i}_EN",None,
          f"A{i}_PH3",f"A{i}_PH2",f"A{i}_PH1"]
    add(f"J{10+i}","Mini v1.0 FEMALE sockets", "TrueSkate:Mini_v1_Sockets",pins,nets,pg,(70,65),(x,y,180 if row==0 else 0),
        price=.7,assembly="Hand",note="Socket set: 2x5 plus 1x3; geometry approval pending")
    add(f"J{20+i}","MOTOR PHASES male 1x3",HEADER,[1,2,3],[f"A{i}_PH1",f"A{i}_PH2",f"A{i}_PH3"],
        pg,(185,45),(x+6.604 if row==0 else x-6.604,10 if row==0 else 116,270 if row==0 else 90),price=.1,assembly="Hand")
    # Contact order VERIFIED on the working bench breakout (pin 1 = square pad,
    # traces straight from socket to header): 1 CLK, 2 MISO, 3 MOSI, 4 CSn,
    # 5 VDD 3.3V, 6 GND. Note CSn is contact 4, not contact 1.
    add(f"J{30+i}","ENCODER JST-SH 6p",SH,range(1,7),
        ["SPI_SCK_CABLE","SPI_MISO","SPI_MOSI_CABLE",f"A{i}_CS_CABLE","3V3","GND"],
        pg,(185,92),(80+col*21,48+row*37,0),"C160392",.349,
        note="CLK MISO MOSI CSn VDD GND verified on bench; footprint contact-1 orientation still to confirm on the fab drawing")
    resistor(f"R{10+i}","10k EN boot pulldown",f"A{i}_EN_REQ","GND",pg,(65,123),(x-18,y+5,0))
    resistor(f"R{20+i}","10k EN output pulldown",f"A{i}_EN",f"PGND{i}",pg,(175,123),(x-18,y+9,0))
    resistor(f"R{30+i}","10k CS idle pullup",f"A{i}_CS","3V3",pg,(65,150),(78+col*21,54+row*25,0))
    resistor(f"R{40+i}","33R CS source damping",f"A{i}_CS",f"A{i}_CS_CABLE",pg,(175,150),(82+col*21,54+row*25,0),"C23140")
    add(f"C{10+i}","EEUFR1V102B 1000uF 35V", "Capacitor_THT:CP_Radial_D12.5mm_P5.00mm",
        [1,2],["12V_PROTECTED",f"PGND{i}"],pg,(65,178),(x+21 if row==0 else x+18,20 if row==0 else 104,0),"C128476",0,assembly="Hand / owned")
    cap(f"C{20+i}","100nF 50V", "12V_PROTECTED",f"PGND{i}",pg,(175,178),(x+23 if row==0 else x+20,28 if row==0 else 112,0))
    add(f"J{40+i}","MINI POWER: +12V / GND", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1-2-3.81_1x02_P3.81mm_Horizontal",[1,2],
        ["12V_PROTECTED",f"PGND{i}"],pg,(65,210),(x+21 if row==0 else x+18,36 if row==0 else 94,0),price=.8,assembly="Hand",
        note="User approved short paired wires; main-board terminal independent of Mini pad pitch")

page("power", "09 / Power entry and 5V supply", [
    "Input: regulated 12V ONLY. Initial design envelope 5A total, validate fuse/inrush/temperature.",
    "Q1 is reversed relative to a normal switch: body diode starts forward input, blocks reversal.",
    "D1/D2 OR the two 5V sources. CUT Teensy VUSB-VIN link or the PC can be back-powered.",
    "Buck layout needs a very short VIN/CIN/GND loop and a compact SW/inductor connection.",
    "Input and local buck/axis copper are hand-routed; main distribution remains unfinished."])
add("J5","12V INPUT 5.08mm >=10A", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
    [1,2],["12V_IN","GND"],"power",(45,40),(8,10,0),price=1,assembly="Hand")
add("F1","5A time-delay fuse / VERIFY", "Fuse:Fuseholder_Cylinder-5x20mm_Schurter_0031_8201_Horizontal_Open",
    [1,2],["12V_IN","12V_FUSED"],"power",(120,40),(8,43,90),price=1.8,assembly="Hand")
add("Q1","FQP47P06 reverse-polarity", "Package_TO_SOT_THT:TO-220-3_Vertical",[1,2,3],
    ["REV_GATE","12V_FUSED","12V_PROTECTED"],"power",(205,40),(20,28,0),price=1.5,assembly="Hand")
resistor("R3","100k", "REV_GATE","GND","power",(45,70),(22,38,0),"C25803")
add("D3","1N4742A 12V gate clamp", "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",[1,2],
    ["12V_PROTECTED","REV_GATE"],"power",(120,70),(20,43,0),price=.1,assembly="Hand",note="1=K, 2=A")
add("U4","AP63205WU-7 fixed 5V", "Package_TO_SOT_SMD:TSOT-23-6",range(1,7),
    ["BUCK_5V","12V_PROTECTED","12V_PROTECTED","GND","BUCK_SW","BUCK_BST"],
    "power",(205,82),(16,90,0),"C2071056",.4337,
    types=["input","input","power_in","power_in","power_out","passive"])
add("L1","4.7uH / Isat >=3.5A VERIFY", "Inductor_SMD:L_Bourns_SRN6045TA",[1,2],
    ["BUCK_SW","BUCK_5V"],"power",(45,108),(24,88,0),"C2044594",.6,note="Bourns SRN6045TA-4R7M; verify stock")
cap("C5","10uF 50V X7R", "12V_PROTECTED","GND","power",(120,108),(10,87,0),
    "Capacitor_SMD:C_1210_3225Metric",lcsc="C432929")
cap("C6","100nF bootstrap", "BUCK_BST","BUCK_SW","power",(205,125),(18,86,0))
for j in range(2):
    cap(f"C{7+j}","22uF 25V X5R", "BUCK_5V","GND","power",(45+j*75,143),(31,85+j*5,0),
        "Capacitor_SMD:C_1206_3216Metric",lcsc="C12891")
for ref,src,sch,pos in [("D1","BUCK_5V",(45,178),(40,85,0)),("D2","VUSB",(145,178),(40,91,0))]:
    add(ref,"SS14 Schottky", "Diode_SMD:D_SMA",[1,2],["VIN_OR",src],"power",sch,pos,"C2480",.06,
        note="1=K cathode (stripe), 2=A anode")

page("wrist", "10 / STS3215 12V half-duplex interface", [
    "Serial8: RX34, TX35. Pin41 HIGH enables transmit; LOW releases shared data wire.",
    "5V AHCT transmit buffer accepts 3.3V logic. LVC receiver accepts 5V at its input.",
    "Q3 defaults transmit OFF; U2 also forces transmit OFF during kill. R8 is DNP.",
    "Feetech connector footprint is PROVISIONAL PH 2.0mm; verify your actual cable.",
    "Q2 cuts servo 12V when KILL_OK is low. Logic ground stays connected."])
add("J6","WRIST: GND / 12V / DATA", "Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical",[1,2,3],
    ["WRIST_GND","WRIST_12V","WRIST_DATA"],"wrist",(45,40),(145,64,0),price=.3,assembly="Hand",note="Confirm Feetech cable housing before release")
add("U5","SN74AHCT1G125DBVR TX", "Package_TO_SOT_SMD:SOT-23-5",[1,2,3,4,5],
    ["WRIST_TX_OE_N","WRIST_TX","GND","WRIST_TX_5V","BUCK_5V"],"wrist",(125,45),(135,63,0),"C7484",.12,
    types=["input","input","power_in","tri_state","power_in"])
add("U6","SN74LVC1G125DBVR RX", "Package_TO_SOT_SMD:SOT-23-5",[1,2,3,4,5],
    ["GND","WRIST_DATA","GND","WRIST_RX","3V3"],"wrist",(215,45),(135,71,0),"C23654",.0992,
    types=["input","input","power_in","tri_state","power_in"])
add("Q3","MMBT3904 transmit enable", "Package_TO_SOT_SMD:SOT-23",[1,2,3],
    ["TX_BASE","GND","WRIST_TX_OE_N"],"wrist",(45,86),(129,64,0),"C20526",.02)
resistor("R4","10k", "WRIST_TX_ALLOWED","TX_BASE","wrist",(125,86),(124,62,0))
resistor("R58","10k TX boot pulldown", "WRIST_TX_ENABLE","GND","safety",(70,195),(124,74,0))
resistor("R59","100k bus off-state bias", "WRIST_DATA","GND","wrist",(125,216),(129,74,0),"C25803")
resistor("R60","10k UART idle pullup", "WRIST_TX","3V3","wrist",(215,216),(125,69,0))
resistor("R5","100k", "TX_BASE","GND","wrist",(215,86),(124,66,0),"C25803")
resistor("R6","10k", "WRIST_TX_OE_N","BUCK_5V","wrist",(45,117),(132,59,0))
resistor("R7","100R bus series", "WRIST_TX_5V","WRIST_DATA","wrist",(125,117),(140,62,0),"C22775")
resistor("R8","2.2k bus idle pullup / DNP", "WRIST_DATA","BUCK_5V","wrist",(215,117),(140,72,0),"C4190")["note"]="DO NOT POPULATE pending servo bus bias and powered-off injection test."
add("Q2","FQP47P06 servo power switch", "Package_TO_SOT_THT:TO-220-3_Vertical",[1,2,3],
    ["SERVO_GATE","WRIST_12V","12V_PROTECTED"],"wrist",(45,154),(145,84,0),price=1.5,assembly="Hand")
add("Q4","MMBT3904 kill power control", "Package_TO_SOT_SMD:SOT-23",[1,2,3],
    ["SERVO_BASE","GND","SERVO_GATE_SINK"],"wrist",(125,154),(136,83,0),"C20526",.02)
resistor("R9","10k gate sink", "SERVO_GATE","SERVO_GATE_SINK","wrist",(215,154),(140,87,0))
resistor("R51","100k gate off", "SERVO_GATE","12V_PROTECTED","wrist",(45,183),(147,89,0),"C25803")
resistor("R52","10k", "KILL_OK","SERVO_BASE","wrist",(125,183),(131,83,0))
resistor("R53","100k", "SERVO_BASE","GND","wrist",(215,183),(131,87,0),"C25803")
page("io", "11 / Ground star, expansion and decoupling", [
    "NT1 is a copper net-tie: all grounds meet only at this planned power-entry star.",
    "PGND1..6 are separate motor return branches. Do not join through Mini control sockets.",
    "Touch returns have their own branch plus one ferrite bead each, away from motor current.",
    "I2C expansion is 3.3V only; 4.7k pullups. No daughterboard motor power on this connector.",
    "Star is beside input; buck return is routed. Motor, wrist and touch branches remain open."])
add("NT1","GROUND STAR / dedicated copper", "TrueSkate:GroundStar",range(1,10),
    ["GND"]+[f"PGND{i}" for i in range(1,7)]+["WRIST_GND","TOUCH_GND"],"io",(55,55),(10,75,0),assembly="PCB copper")
add("J7","FUTURE I2C / 3V3 ONLY", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",[1,2,3,4],
    ["GND","3V3","LINK_SDA","LINK_SCL"],"io",(145,42),(106,56,90),price=.15,assembly="Hand")
resistor("R54","4.7k", "LINK_SDA","3V3","io",(225,42),(108,51,0),"C23162")
resistor("R55","4.7k", "LINK_SCL","3V3","io",(225,65),(112,51,0),"C23162")
for i in range(2):
    add(f"FB{i+1}","BLM21PG221SN1D ferrite", "Inductor_SMD:L_0805_2012Metric",[1,2],
        ["TOUCH_GND",f"TIP{i+1}"],"io",(60+i*115,100),(15+i*10,107,0),"C85840",.04)
    add(f"J{8+i}",f"FINGERTIP {i+1} GND", "Connector_Wire:SolderWire-1sqmm_1x01_D1.4mm_OD2.7mm",[1],
        [f"TIP{i+1}"],"io",(60+i*115,130),(15+i*10,114,0),assembly="Hand",note="Solder terminal; strain-relieve wire")
for i,(source,dest) in enumerate([("SPI_SCK","SPI_SCK_CABLE"),("SPI_MOSI","SPI_MOSI_CABLE")]):
    resistor(f"R{56+i}","33R source damping",source,dest,"io",(60+i*115,160),(67+i*4,42,0),"C23140")
for i,(net,pos) in enumerate([("BUCK_5V",(136,58,0)),("3V3",(135,77,0)),("3V3",(80,42,0)),("3V3",(101,42,0)),("3V3",(122,42,0)),("3V3",(86,79,0)),("3V3",(107,79,0)),("3V3",(128,79,0))]):
    cap(f"C{31+i}","100nF 50V",net,"GND","io",(45+(i%4)*65,183+(i//4)*17),pos)

# Test pads are electrically real and help commission without probing JST pins.
page("test", "12 / Test points and release holds", [
    "REVIEW DRAFT: physical module fit and encoder cable pinout unresolved.",
    "Partial power routing and local buck ground only; no assembly file or Gerbers released.",
    "Do not treat ERC success as proof of correct connectors, thermal design or firmware.",
    "See docs/pcb/design-notes.md and verification.md before considering manufacture."])
for i,net in enumerate(["GND","12V_PROTECTED","BUCK_5V","VIN_OR","3V3","SPI_SCK_CABLE","SPI_MOSI_CABLE","SPI_MISO","KILL_OK"]):
    add(f"TP{i+1}",net,"TestPoint:TestPoint_Pad_D1.5mm",[1],[net],"test",(50+(i%3)*85,55+(i//3)*30),
        (107+(i%3)*6,63+(i//3)*5,0),assembly="PCB copper")

page("indicators", "13 / Rail and driver-enable indicators", [
    "Red LEDs show rail presence and hardware-gated enables, not actual motor motion.",
    "Series resistors limit LED current. Enable LEDs use small current to avoid loading EN.",
    "An extinguished LED is NOT proof of a discharged or safe circuit; use a meter."])
for n,net in enumerate(["12V_PROTECTED","BUCK_5V","3V3"]+[f"A{i}_EN" for i in range(1,7)]):
    if n<3:
        pos=(20+n*6,7);return_net="GND"
    else:
        i=n-2; col=(i-1)%3
        pos=(24+col*43,44) if i<=3 else (30+col*43,87)
        return_net=f"PGND{i}"
    sx=45+(n%3)*95;sy=48+(n//3)*60
    anode=f"LED{n+1}_A"
    resistor(f"R{61+n}","4.7k LED limit",net,anode,"indicators",(sx,sy),(pos[0],pos[1]+(4 if n<6 else -4),0),"C23162")
    add(f"D{11+n}","KT-0603R red indicator","LED_SMD:LED_0603_1608Metric",[1,2],[return_net,anode],
        "indicators",(sx,sy+24),(*pos,0),"C2286",.025,note="1=cathode, 2=anode; low-current brightness to verify")

# Placement adjustments keep tall parts out of the socketed-module envelopes.
# Low SMD logic fits below the Teensy in the >=8.5 mm socket clearance.
PLACEMENT={
    "R61":(23,11,0),"R64":(30,48,0),"D19":(114,87,0),"R69":(113,82,0),
    "J3":(40,54,90),"J5":(12,14,0),"F1":(8,23.5,270),"Q1":(19,49,0),"R3":(18,54,0),"D3":(22,55,0),
    "U1":(60,67,0),"U2":(76,67,0),"C3":(60,72,0),"C4":(76,72,0),
    "U4":(24,63,0),"C5":(19.3,64,270),"C6":(26,59,270),"L1":(30.5,63,0),
    "C7":(36.5,59.5,0),"C8":(36.5,66.5,0),"D1":(32,72,0),"D2":(32,79,0),
    "J4":(8,70,0),"R1":(14,67,0),"R2":(14,73,0),"C1":(18,73,0),
    "U3":(23,73,0),"C2":(23,78,0),"NT1":(18,22,0),
    "FB1":(10,109,0),"FB2":(16,109,0),"J8":(11,115,0),"J9":(17,115,0),
    "J7":(108,56,90),"R54":(110,51,0),"R55":(114,51,0),
}
for i in range(1,7):
    PLACEMENT[f"R{10+i}"]=(50 if i<=3 else 92,64+((i-1)%3)*4,0)
    PLACEMENT[f"R{20+i}"]=(50+((i-1)%3)*7,80+((i-1)//3)*4,0)
    if i>=4:
        x=35+((i-1)%3)*43
        PLACEMENT[f"C{10+i}"]=(x+18,107,0)
        PLACEMENT[f"C{20+i}"]=(x+20,116,0)
        PLACEMENT[f"J{40+i}"]=(x+18,94,0)
for p in parts:
    if p["ref"] in PLACEMENT: p["pcb"]=PLACEMENT[p["ref"]]
    if p["ref"]=="C5": p["price"]=.2802
    if p["ref"] in ("C7","C8"): p["price"]=.1747
    if p["ref"]=="L1": p.update(value="SRN6045TA-4R7M 4.7uH",price=.3411,note="4.5A rated / 6.8A saturation; 680 in LCSC listing")
    if p["ref"]=="U3": p["price"]=.1696
    if p["ref"]=="R8": p.update(assembly="DNP / do not populate",price=0)

def draw_line(fp,a,b,layer,width=.15):
    s=k.PCB_SHAPE(fp); s.SetShape(k.SHAPE_T_SEGMENT); s.SetStart(xy(*a)); s.SetEnd(xy(*b))
    s.SetLayer(layer); s.SetWidth(k.FromMM(width)); fp.Add(s)
def make_custom():
    folder=ROOT/"TrueSkate.pretty"; folder.mkdir(exist_ok=True)
    fp=k.FOOTPRINT(None); fp.SetFPID(k.LIB_ID("TrueSkate","Mini_v1_Sockets"))
    fp.SetReference("REF**"); fp.SetValue("Mini v1.0 socket set")
    for name,prefix in [("control",""),("phase","P")]:
        for pad in G["connectors"][name]:
            p=k.PAD(fp);p.SetNumber(prefix+pad["pin"]);p.SetAttribute(k.PAD_ATTRIB_PTH)
            p.SetShape(k.PAD_SHAPE_RECT if pad["pin"]=="1" else k.PAD_SHAPE_CIRCLE)
            p.SetSize(xy(1.8,1.8));p.SetDrillSize(xy(1,1));p.SetPosition(xy(pad["x_mm"],pad["y_mm"]))
            p.SetLayerSet(layers(k.F_Cu,k.B_Cu,k.F_Mask,k.B_Mask));fp.Add(p)
    for a,b in [((-15,-3),(12,-3)),((12,-3),(12,21)),((12,21),(-15,21)),((-15,21),(-15,-3))]:
        draw_line(fp,a,b,k.F_CrtYd,.05)
        draw_line(fp,a,b,k.F_Fab,.1)
    for a,b in [((-11.5,-1.3),(1.3,-1.3)),((1.3,-1.3),(1.3,3.9)),((1.3,3.9),(-11.5,3.9)),((-11.5,3.9),(-11.5,-1.3))]:
        draw_line(fp,a,b,k.F_SilkS)
    fp.Reference().SetPosition(xy(-5,-4));fp.Value().SetVisible(False)
    # Socket bodies only; do not invent an installed Mini or its component heights.
    for model_name,offset,angle in [
        ("PinSocket_2x05_P2.54mm_Vertical",(0,-2.54,0),90),
        ("PinSocket_1x03_P2.54mm_Vertical",(-1.524,-17.653,0),90),
    ]:
        model=k.FP_3DMODEL()
        model.m_Filename="${KICAD10_3DMODEL_DIR}/Connector_PinSocket_2.54mm.3dshapes/"+model_name+".step"
        model.m_Offset.Set(*offset);model.m_Rotation.z=angle;fp.Add3DModel(model)
    k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(folder),fp)
    star=k.FOOTPRINT(None);star.SetFPID(k.LIB_ID("TrueSkate","GroundStar"));star.SetReference("REF**")
    star.AddNetTiePadGroup("1,2,3,4,5,6,7,8,9")
    for n in range(9):
        p=k.PAD(star);p.SetNumber(str(n+1));p.SetAttribute(k.PAD_ATTRIB_SMD);p.SetShape(k.PAD_SHAPE_RECT)
        p.SetSize(xy(2,2));p.SetPosition(xy((n%3)*3,(n//3)*3));p.SetLayerSet(layers(k.F_Cu));star.Add(p)
    star.Reference().SetPosition(xy(3,-3));star.Value().SetVisible(False)
    for row in range(3): draw_line(star,(0,row*3),(6,row*3),k.F_Cu,2)
    for col in range(3): draw_line(star,(col*3,0),(col*3,6),k.F_Cu,2)
    k.PCB_IO_MGR.FindPlugin(k.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(folder),star)

def board():
    b=k.BOARD(); b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(k.FromMM(1.6))
    nets={}
    for name in sorted({n for p in parts for n in p["nets"] if n}):
        net=k.NETINFO_ITEM(b,name);b.Add(net);nets[name]=net
    for p in parts:
        lib,name=p["fp"].split(":",1)
        directory=ROOT/"TrueSkate.pretty" if lib=="TrueSkate" else SHARE/"footprints"/(lib+".pretty")
        fp=k.FootprintLoad(str(directory),name)
        if fp is None: raise RuntimeError(p["fp"])
        fp.SetFPID(k.LIB_ID(lib,name));fp.SetReference(p["ref"]);fp.SetValue(p["value"])
        if p["ref"]=="R8": fp.SetDNP(True)
        fp.SetPosition(xy(*p["pcb"][:2]));fp.SetOrientationDegrees(p["pcb"][2]);fp.Value().SetVisible(False)
        fp.Reference().SetVisible(False)
        # Link symbols to board via hierarchical UUID path.
        path=k.KIID_PATH();path.push_back(k.KIID(uid("root")));path.push_back(k.KIID(uid("sheet-"+p["page"])));path.push_back(k.KIID(uid(p["ref"])))
        fp.SetPath(path)
        pinmap=dict(zip(p["pins"],p["nets"]))
        for pad in fp.Pads():
            net=pinmap.get(pad.GetNumber())
            if net: pad.SetNet(nets[net])
        for model in fp.Models():
            model.m_Filename=model.m_Filename.replace("${KICAD10_3DMODEL_DIR}",str(SHARE/"3dmodels"))
        b.Add(fp)
    for x,y in [(5,5),(155,5),(155,115),(5,115)]:
        f=k.FootprintLoad(str(SHARE/"footprints/MountingHole.pretty"),"MountingHole_3.2mm_M3")
        f.SetReference(f"H{1+[(5,5),(155,5),(155,115),(5,115)].index((x,y))}")
        f.SetPosition(xy(x,y));f.Value().SetVisible(False);b.Add(f)
    for a,c in [((0,0),(160,0)),((160,0),(160,120)),((160,120),(0,120)),((0,120),(0,0))]:
        s=k.PCB_SHAPE();s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(xy(*a));s.SetEnd(xy(*c));s.SetLayer(k.Edge_Cuts);s.SetWidth(k.FromMM(.05));b.Add(s)
    for text_,x,y,size in [("TrueSkate MAIN v1 / REVIEW ONLY",85,4,1.2),
                          ("USB",42,68,1),("POWER OFF BEFORE CHANGING MOTOR WIRES",93,118.5,.8)]:
        t=k.PCB_TEXT(b);t.SetText(text_);t.SetPosition(xy(x,y));t.SetTextSize(xy(size,size));t.SetTextThickness(k.FromMM(.15));t.SetLayer(k.F_SilkS);b.Add(t)
    for i,a in enumerate(D["axes"],1):
        t=k.PCB_TEXT(b);t.SetText(f"A{i}");t.SetPosition(xy((32 if i<=3 else 23)+((i-1)%3)*43,43 if i<=3 else 86));t.SetTextSize(xy(1.1,1.1));t.SetTextThickness(k.FromMM(.15));t.SetLayer(k.F_SilkS);b.Add(t)
    # Documentation layer only: a 1:1 print check, never manufacturing copper.
    for a,z in [((55,125),(105,125)),((55,123),(55,127)),((105,123),(105,127))]:
        line=k.PCB_SHAPE();line.SetShape(k.SHAPE_T_SEGMENT);line.SetStart(xy(*a));line.SetEnd(xy(*z))
        line.SetLayer(k.Dwgs_User);line.SetWidth(k.FromMM(.2));b.Add(line)
    fit_labels=[("TOP VIEW / COMPONENT SIDE / NOT MIRRORED",80,-7,1.5),
                ("PRINT AT 100% / ACTUAL SIZE - DO NOT FIT TO PAGE",80,-3,1.2),
                ("50 mm between tick centres - measure before checking pins",80,130,1.1),
                ("160 x 120 mm carrier / PAPER FIT ONLY / NOT FOR FABRICATION",80,134,1.1),
                ("Teensy: USB LEFT",74,62.5,1.2)]
    for i in range(1,7):
        fit_labels.append((f"A{i} MINI",35+((i-1)%3)*43,25 if i<=3 else 101,1.2))
    for label,x,y,size in fit_labels:
        t=k.PCB_TEXT(b);t.SetText(label);t.SetPosition(xy(x,y));t.SetTextSize(xy(size,size))
        t.SetTextThickness(k.FromMM(.15));t.SetLayer(k.Dwgs_User);b.Add(t)
    # Deliberate, reproducible local power routing. No autorouter is used.
    # Trunks and ground-star returns must still be designed; never hide opens.
    fps={f.GetReference():f for f in b.GetFootprints()}
    def pad(ref,number):
        return next(p for p in fps[ref].Pads() if p.GetNumber()==str(number))
    def point(p): return (k.ToMM(p.GetPosition().x),k.ToMM(p.GetPosition().y))
    def via(name,x,y,diameter=.65,drill=.3):
        v=k.PCB_VIA(b);v.SetPosition(xy(x,y));v.SetWidth(k.FromMM(diameter));v.SetDrill(k.FromMM(drill))
        v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(nets[name]);b.Add(v)
        return v
    def route(a,z,width=1.0,bends=(),layer=k.F_Cu):
        assert a.GetNetname()==z.GetNetname()
        pts=[point(a),*bends,point(z)]
        for start,end in zip(pts,pts[1:]):
            if start==end: continue
            track=k.PCB_TRACK(b);track.SetStart(xy(*start));track.SetEnd(xy(*end))
            track.SetWidth(k.FromMM(width));track.SetLayer(layer);track.SetNet(a.GetNet());b.Add(track)
    for i in range(1,7):
        for phase in range(1,4):
            route(pad(f"J{10+i}",f"P{4-phase}"),pad(f"J{20+i}",phase),1.0)
        bulk=f"C{10+i}";term=f"J{40+i}";ceramic=f"C{20+i}"
        route(pad(bulk,1),pad(term,1),1.2)
        x1,y1=point(pad(bulk,2));x2,y2=point(pad(term,2))
        mid=(y1+y2)/2
        route(pad(bulk,2),pad(term,2),1.2,[(x1,mid),(x2,mid+abs(x1-x2)*(1 if y2>y1 else -1))])
        for n in (1,2):
            cx,cy=point(pad(ceramic,n));bx,by=point(pad(bulk,n))
            route(pad(bulk,n),pad(ceramic,n),.4,[(bx,cy)])
    # Manually selected input/fuse/reverse-polarity paths. The fuse is symmetric;
    # orient contact 1 toward the input to avoid a long unfused loop.
    route(pad("J5",1),pad("F1",1),1.5,[(12,19.5),(8,23.5)])
    route(pad("J5",2),pad("NT1",1),1.5,[(18,14.92)])
    route(pad("F1",2),pad("Q1",2),1.5,[(10,44),(19,44),(21.54,46.54)])
    route(pad("Q1",1),pad("R3",1),.3,[(17.175,50.825)])
    route(pad("Q1",1),pad("D3",2),.3,[(19,46),(32.16,46)],layer=k.B_Cu)
    route(pad("Q1",3),pad("D3",1),.5,[(24.08,52.92)])
    # Buck converter: manually controlled local loops, compact switching node,
    # and separate thin output-sense branch. No generic signal autorouting here.
    route(pad("C5",1),pad("U4",3),.6,[(21.4375,63.95)])
    route(pad("U4",2),pad("U4",3),.3)
    route(pad("C5",2),pad("U4",4),.6,[(20.825,67),(25.1375,67)])
    route(pad("U4",5),pad("L1",1),.6)
    route(pad("U4",6),pad("C6",1),.25,[(25.1375,58.225)])
    route(pad("U4",5),pad("C6",2),.25,[(26.5,63),(26.5,60.275)])
    route(pad("L1",2),pad("C7",1),.8,[(35.025,60.55)])
    route(pad("L1",2),pad("C8",1),.8,[(35.025,65.45)])
    route(pad("C7",2),pad("C8",2),.8)
    route(pad("C8",2),pad("U4",4),.6,[(37.975,68.5),(25.1375,68.5)])
    route(pad("U4",1),pad("C7",1),.25,[(21.5,62.05),(21.5,57),(35.025,57)])
    buck_feed=via("12V_PROTECTED",19.3,61,1,.5)
    route(pad("Q1",3),buck_feed,.8,[(24.08,54),(19.3,58.78)],layer=k.B_Cu)
    route(buck_feed,pad("C5",1),.8)
    # Local converter ground island, NOT a blanket motor-ground plane. Its only
    # supply-return connection is the deliberate GND branch back to NT1.
    for ref,pin,x,y in [("C5",2,17.8,65.1),("C5",2,17.8,65.9),
                        ("U4",4,25.1375,65.3),("C7",2,38.8,60.2),("C8",2,38.8,65.8)]:
        route(pad(ref,pin),via("GND",x,y),.4)
    ground_entry=via("GND",15.5,22,1,.5)
    ground_local=via("GND",17.5,60,1,.5)
    route(pad("NT1",1),ground_entry,1)
    route(ground_entry,ground_local,1,[(15.5,58)],layer=k.B_Cu)
    route(ground_local,pad("C5",2),.4,[(16,61.5),(16,65.475)])
    gate_ground=via("GND",18.825,55.2)
    route(pad("R3",2),gate_ground,.3)
    route(gate_ground,ground_local,.3,[(17.5,56.525)],layer=k.B_Cu)
    zone=k.ZONE(b);zone.SetLayer(k.B_Cu);zone.SetNet(nets["GND"])
    zone.SetLocalClearance(k.FromMM(.2));zone.SetMinThickness(k.FromMM(.2))
    zone.SetPadConnection(k.ZONE_CONNECTION_FULL)
    outline=zone.Outline();outline.NewOutline()
    for x,y in [(16,59.3),(39.5,59.3),(39.5,70),(16,70)]: outline.Append(int(k.FromMM(x)),int(k.FromMM(y)))
    b.Add(zone);k.ZONE_FILLER(b).Fill(b.Zones())
    k.SaveBoard(str(ROOT/(PROJECT+".kicad_pcb")),b)

def symbol_def(p):
    name=p["ref"];n=len(p["pins"]); rows=math.ceil(n/2)
    height=max(5.08,(rows+1)*2.54)
    s=f'(symbol "TrueSkate:{name}" (pin_names (offset 0.508)) (in_bom yes) (on_board yes) '
    for key,val,y in [("Reference",name,-height/2-2.54),("Value",p["value"],height/2+2.54),("Footprint",p["fp"],0)]:
        s+=f'(property {q(key)} {q(val)} (at 0 {y} 0) {eff(.9,"(hide yes)" if key=="Footprint" else "")}) '
    s+=f'(symbol "{name}_0_1" (rectangle (start -10.16 {height/2}) (end 10.16 {-height/2}) (stroke (width .254) (type default)) (fill (type background)))) '
    s+=f'(symbol "{name}_1_1" '
    for i,(num,typ) in enumerate(zip(p["pins"],p["types"])):
        right=i>=rows;index=i-rows if right else i
        y=(rows-1)*1.27-index*2.54;x=15.24 if right else -15.24
        pinname=(p["note"].split("physical pin legend: ")[-1].split(",")[i]
                 if p["ref"] in ("J1","J2") else num)
        s+=f'(pin {typ} line (at {x} {y} {180 if right else 0}) (length 5.08) (name {q(pinname)} {eff(.9)}) (number {q(num)} {eff(.9)})) '
    return s+'))',height

def schematic():
    lib=['(kicad_symbol_lib (version 20250114) (generator "trueskate" )']
    for p in parts: lib.append(symbol_def(p)[0].replace('"TrueSkate:'+p["ref"]+'"','"'+p["ref"]+'"',1))
    (ROOT/"TrueSkate.kicad_sym").write_text("\n".join(lib)+")\n")
    for pg,data in pages.items():
        header=f'(kicad_sch (version 20250114) (generator "trueskate") (uuid {uid(pg)}) (paper "A3") (title_block (title {q(data["title"])}) (rev "v1 DRAFT")) '
        flagdef='(symbol "power:PWR_FLAG" (power) (pin_names (offset 0)) (in_bom no) (on_board no) (property "Reference" "#FLG" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) (property "Value" "PWR_FLAG" (at 0 3.81 0) (effects (font (size 1.27 1.27)))) (symbol "PWR_FLAG_0_1" (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.27 1.905) (xy 0 2.54) (xy 1.27 1.905) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))) (symbol "PWR_FLAG_1_1" (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 0 0)))) (number "1" (effects (font (size 0 0)))))))'
        s=header+'(lib_symbols '+" ".join(symbol_def(p)[0] for p in data["parts"])+(flagdef if pg=="power" else "")+')\n'
        for p in data["parts"]:
            x,y=[round(v/1.27)*1.27 for v in p["sch"]];n=len(p["pins"]);rows=math.ceil(n/2);height=symbol_def(p)[1]
            dnp="yes" if p["ref"]=="R8" else "no"
            s+=f'(symbol (lib_id "TrueSkate:{p["ref"]}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp {dnp}) (uuid {uid(p["ref"])}) '
            for key,val,py,hidden in [("Reference",p["ref"],y-height/2-2.54,False),("Value",p["value"],y+height/2+2.54,False),("Footprint",p["fp"],y,True),("LCSC",p["lcsc"],y,True)]:
                s+=f'(property {q(key)} {q(val)} (at {x} {py} 0) {eff(.85,"(hide yes)" if hidden else "")}) '
            for pin in p["pins"]: s+=f'(pin {q(pin)} (uuid {uid(p["ref"]+"-"+pin)})) '
            s+=f'(instances (project "{PROJECT}" (path "/{uid("root")}/{uid("sheet-"+pg)}" (reference {q(p["ref"])}) (unit 1)))))\n'
            for i,net in enumerate(p["nets"]):
                right=i>=rows;index=i-rows if right else i
                px=x+(15.24 if right else -15.24);py=y-((rows-1)*1.27-index*2.54)
                if net:
                    end=px+(3.81 if right else -3.81)
                    s+=f'(wire (pts (xy {px} {py}) (xy {end} {py})) (stroke (width 0) (type default)) (uuid {uid(p["ref"]+"-w"+str(i))}))\n'
                    s+=f'(global_label {q(net)} (shape bidirectional) (at {end} {py} {0 if right else 180}) {eff(.85,"(justify left)" if right else "(justify right)")} (uuid {uid(p["ref"]+"-l"+str(i))}))\n'
                else:
                    s+=f'(no_connect (at {px} {py}) (uuid {uid(p["ref"]+"-nc"+str(i))}))\n'
        # Notes near the top, in their own area; some pages use all available height.
        for i,t in enumerate(data["notes"]):
            s+=f'(text {q(t)} (at 15 {15+i*3.3} 0) {eff(1.1,"(justify left)")} (uuid {uid(pg+"note"+str(i))}))\n'
        if pg=="power":
            for i,net in enumerate(["GND","3V3","12V_PROTECTED","VIN_OR","BUCK_5V"]):
                x=304.8;y=50.8+i*25.4;ref=f"#FLG0{i+1}"
                s+=f'(symbol (lib_id "power:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {uid(ref)}) (property "Reference" {q(ref)} (at {x} {y} 0) {eff(1,"(hide yes)")}) (property "Value" "PWR_FLAG" (at {x} {y-3.81} 0) {eff(1)}) (pin "1" (uuid {uid(ref+"pin")})) (instances (project "{PROJECT}" (path "/{uid("root")}/{uid("sheet-power")}" (reference {q(ref)}) (unit 1))))) '
                s+=f'(global_label {q(net)} (shape input) (at {x} {y} 0) {eff(1,"(justify left)")} (uuid {uid(ref+"label")})) '
            for n,note in enumerate(["Flags declare power through passive components.",
                                     "They do not add physical parts or prove safe wiring.",
                                     "Sources: PSU, Teensy regulator, protected 12V,",
                                     "diode-selected VIN and regulated buck 5V."]):
                s+=f'(text {q(note)} (at 280 {170+n*4} 0) {eff(1.1,"(justify left)")} (uuid {uid("flag-note-"+str(n))})) '
        s+=')\n'
        if pg=="power":
            library=ROOT/"TrueSkate.kicad_sym"
            library.write_text(library.read_text()[:-2]+flagdef.replace('"power:PWR_FLAG"','"PWR_FLAG"',1)+")\n")
            s=s.replace('"power:PWR_FLAG"','"TrueSkate:PWR_FLAG"')
        (ROOT/(pg+".kicad_sch")).write_text(s)
    s=f'(kicad_sch (version 20250114) (generator "trueskate") (uuid {uid("root")}) (paper "A3") (title_block (title "TrueSkate main control PCB") (rev "v1 DRAFT")) (lib_symbols) '
    for i,(pg,data) in enumerate(pages.items()):
        x=15+(i%3)*130;y=45+(i//3)*50
        s+=f'(sheet (at {x} {y}) (size 115 35) (stroke (width .254) (type default)) (fill (color 0 0 0 0)) (uuid {uid("sheet-"+pg)}) '
        s+=f'(property "Sheetname" {q(data["title"])} (at {x} {y-1.27} 0) {eff(1,"(justify left bottom)")}) '
        s+=f'(property "Sheetfile" "{pg}.kicad_sch" (at {x} {y+36.27} 0) {eff(1,"(justify left top)")}) '
        s+=f'(instances (project "{PROJECT}" (path "/{uid("root")}" (page "{i+2}"))))) '
    for i,t in enumerate(["REVIEW DRAFT - NOT FOR FABRICATION", "Six edge-aligned FOC axes / Teensy 4.1 / 12V wrist / two-layer carrier", "Global labels join identically named wires across pages. Rectangles show physical connector or component pins.", "Power wires approved. Pending: physical module fit, encoder cable verification, component qualification and routing."]):
        s+=f'(text {q(t)} (at 15 {15+i*5} 0) {eff(1.3,"(justify left)")} (uuid {uid("root-note"+str(i))})) '
    s+=f'(sheet_instances (path "/" (page "1"))))\n'
    (ROOT/(PROJECT+".kicad_sch")).write_text(s)

def project_files():
    rules={"min_clearance":.2,"min_track_width":.2,"min_via_diameter":.6,"min_through_hole_diameter":.3,
           "min_via_annular_width":.15,"min_copper_edge_clearance":.5,"min_hole_clearance":.25}
    project={"meta":{"filename":PROJECT+".kicad_pro","version":1},"board":{"design_settings":{"rules":rules}},
             "net_settings":{"classes":[{"name":"Default","clearance":.2,"track_width":.25,"via_diameter":.65,"via_drill":.3,
                                          "microvia_diameter":.3,"microvia_drill":.1,"diff_pair_width":.25,"diff_pair_gap":.2,"diff_pair_via_gap":.25}]}}
    (ROOT/(PROJECT+".kicad_pro")).write_text(json.dumps(project,indent=2)+"\n")
    (ROOT/"sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "TrueSkate") (type "KiCad") (uri "${KIPRJMOD}/TrueSkate.kicad_sym") (options "") (descr "Project symbols; explicit physical pins")))\n')
    libs=sorted({p["fp"].split(":")[0] for p in parts}|{"MountingHole"})
    s='(fp_lib_table (version 7) '
    for name in libs:
        uri="${KIPRJMOD}/TrueSkate.pretty" if name=="TrueSkate" else "${KICAD10_FOOTPRINT_DIR}/"+name+".pretty"
        s+=f'(lib (name {q(name)}) (type "KiCad") (uri {q(uri)}) (options "") (descr "")) '
    (ROOT/"fp-lib-table").write_text(s+")\n")
    with (ROOT/"bom-review.csv").open("w",newline="") as f:
        w=csv.writer(f);w.writerow(["Reference","Value","Footprint","LCSC","Assembly","Estimated USD each","Qualification / notes"])
        for p in parts: w.writerow([p["ref"],p["value"],p["fp"],p["lcsc"],p["assembly"],p["price"],p["note"] or "Review candidate; see sourcing.md"])
    (ROOT/"circuit.json").write_text(json.dumps(parts,indent=2)+"\n")
    groups={}
    for p in parts:
        key=(p["lcsc"],p["fp"],p["assembly"],p["price"])
        if not key[0]: key=(*key,p["value"])
        groups.setdefault(key,[]).append(p)
    lines=["# Review bill of materials", "", "NOT an assembly-order BOM. See [sourcing.md](sourcing.md) for qualifications and exclusions.", "", "All costs are USD budget allowances, not a supplier quote. DNP means do not populate.", "", "| References | Qty | Description | LCSC | Assembly | Extended USD |", "|---|---:|---|---|---|---:|"]
    totals={}
    for group in groups.values():
        p=group[0];extended=sum(g["price"] for g in group)
        totals[p["assembly"]]=totals.get(p["assembly"],0)+extended
        code=f'[{p["lcsc"]}](https://www.lcsc.com/product-detail/{p["lcsc"]}.html)' if p["lcsc"] else "Not selected / no purchase for copper"
        lines.append(f'| {", ".join(g["ref"] for g in group)} | {len(group)} | {p["value"]} | {code} | {p["assembly"]} | {extended:.2f} |')
    lines.extend(["",f"Component allowance total: **USD {sum(totals.values()):.2f}**.", ""])
    for assembly,total in totals.items(): lines.append(f"- {assembly}: USD {total:.2f}")
    lines.extend(["", "Excludes Teensy, six Minis, six motor/encoder assemblies, wrist servo, owned bulk capacitors, PCB fabrication, assembly setup/placement, minimum-order quantities, fuse cartridge, wire, switch, mounting hardware, freight and tax.", "", "Zero cost for the owned capacitors means no incremental purchase, not a free retail part.", ""])
    docs=ROOT.parent/"docs/pcb";docs.mkdir(parents=True,exist_ok=True)
    (docs/"bom.md").write_text("\n".join(lines))

if __name__=="__main__":
    make_custom();project_files();schematic();board()
    print(f"Generated {len(parts)} component review draft, {len(pages)+1} schematic pages.")
    print("REVIEW ONLY. Mini power uses the approved screw-terminal wire pair.")
