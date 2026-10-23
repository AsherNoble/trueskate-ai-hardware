#!/usr/bin/env python3
"""One-page beginner net guide; checks that every real carrier net is covered."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
DOCS=ROOT.parent/'docs/pcb'
groups=[
    (['12V_IN'],'J5 positive to F1 input. Raw motor-supply power, before the fuse. Wrong polarity can damage this board.'),
    (['12V_FUSED'],'F1 output to all six Mini VIN pads and both capacitors per axis. The fuse interrupts sustained excess input current; it does not regulate motor current.'),
    (['3V3'],'Teensy 3.3 V output to encoder contact 5. USB powers the Teensy; neither the carrier VIN contact nor any Mini regulator output feeds this net.'),
    (['GND'],'Zero-volt reference for Teensy, encoders and bridge GND pads. Joins supply negative and all motor returns at copper junction NT1. USB and motor supply are not electrically isolated.'),
    ([f'PGND{i}' for i in range(1,7)],'One separate motor-power return per axis: Mini GND power pad, its capacitor negatives and EN pull-down. The six returns meet GND only at NT1 on the bare carrier.'),
    ([f'CGND{i}' for i in range(1,7)],'Mini control contacts 1 and 4 to that axis\'s optional bridge pad. Leave JP1-JP6 OPEN. The installed Mini already joins these contacts internally to its own power return; closing a bridge adds a parallel path through logic ground.'),
    (['SPI_SCK'],'Teensy pin 13 to encoder contact 1 on all six sockets. Clock pulses tell encoders when to shift each data bit.'),
    (['SPI_MOSI'],'Teensy pin 11 to encoder contact 3. Commands go out from the Teensy to all encoders.'),
    (['SPI_MISO'],'Encoder contact 2 to Teensy pin 12. Only the selected encoder may send angle data back.'),
    ([f'A{i}_PWM{p}' for i in range(1,7) for p in range(1,4)],'Three low-power pulse-width-modulation instructions per axis, Teensy to Mini control contacts 3/5/7. All axes use edge-aligned PWM at one common frequency (intended 25 kHz). These are NOT motor-phase power.'),
    ([f'A{i}_EN' for i in range(1,7)],'Teensy to Mini control contact 9. High enables that driver. R21-R26 each connect EN through 10k ohms to its own PGND, holding it low when the Teensy is not driving. This cannot override a stuck-high output and is not a hardware kill.'),
    ([f'A{i}_CS' for i in range(1,7)],'Teensy to encoder contact 4. Chip select is active low: choose one encoder at a time. Firmware must establish all selects high before SPI transfers.'),
    ([f'A{i}_PH{p}' for i in range(1,7) for p in range(1,4)],'Three switched motor-power outputs per axis: Mini OUT1/2/3 (socket P3/P2/P1) to male phase-header contacts 1/2/3. Never move these cables with 12 V live.')
]
actual={n for p in json.loads((ROOT/'circuit.json').read_text()) for n in p['nets'] if n}
covered=[n for ns,_ in groups for n in ns]
assert len(covered)==len(set(covered)) and set(covered)==actual
axes=json.loads((ROOT/'design.json').read_text())['axes']
title='TrueSkate v1 - every net, in plain English'
intro=('A net is one named electrical connection: all its pads and copper are joined. '
       'This guide covers all 67 nets; n means axis 1-6, p means channel 1-3. '
       'The carrier is wiring, sockets, capacitors, resistors and a fuse holder; the plugged-in modules do the control.')
labels=['12V_IN','12V_FUSED','3V3','GND','PGND1 ... PGND6','CGND1 ... CGND6',
        'SPI_SCK','SPI_MOSI','SPI_MISO','A<n>_PWM<p> (18 nets)','A<n>_EN (6 nets)',
        'A<n>_CS (6 nets)','A<n>_PH<p> (18 nets)']
footer=('No-connect contacts are NOT nets: Teensy VIN and unused digital contacts; Mini 2 (its regulator output), '
        '6 (reset), 8 (sleep), 10 (fault). Encoder square pad/marked pin 1 is CLK; order is CLK, MISO, MOSI, CSn, 3V3, GND. '
        'V1 has no polarity protection, hardware kill or guaranteed capacitor discharge. Disconnect 12 V and measure residual voltage before moving wires. '
        'Human review before ordering; this is not a manufacturing release.')
md='# '+title+'\n\n'+intro+'\n\n| Net or repeated family | What it connects and why |\n|---|---|\n'
for label,(_,desc) in zip(labels,groups): md+='| `'+label+'` | '+desc+' |\n'
md+='\nNames expand literally: for example `A2_PWM3` and `A6_PH1`. This covers every name, not just a sample.\n\n'
md+='| Axis | Movement | Teensy PWM1/2/3 | Teensy EN | Teensy CS |\n|---|---|---|---|---|\n'
for i,a in enumerate(axes,1):md+=f"| A{i} | {a['name'].replace('_',' ')} | {' / '.join(map(str,a['pwm']))} | {a['enable']} | {a['cs']} |\n"
md+='\n'+footer+'\n'
(DOCS/'nets.md').write_text(md)
body=ParagraphStyle('body',fontName='Helvetica',fontSize=8.7,leading=11.1,textColor=colors.HexColor('#172634'),spaceAfter=3)
head=ParagraphStyle('head',parent=body,fontName='Helvetica-Bold',fontSize=16,leading=19,spaceAfter=7)
small=ParagraphStyle('small',parent=body,fontSize=8,leading=10)
cell=ParagraphStyle('cell',parent=body,fontSize=8.3,leading=10.5,spaceAfter=0)
net=ParagraphStyle('net',parent=cell,fontName='Courier-Bold',fontSize=8.0)
story=[Paragraph(title,head),Paragraph(escape(intro),body),Spacer(1,5)]
rows=[[Paragraph('NET / FAMILY',cell),Paragraph('CONNECTION AND PURPOSE',cell)]]
for label,(_,desc) in zip(labels,groups): rows.append([Paragraph(escape(label),net),Paragraph(escape(desc),cell)])
t=Table(rows,colWidths=[136,395],hAlign='LEFT')
t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef5')),
                      ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#829bb3')),
                      ('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d9e1e8')),
                      ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
                      ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
story+=[t,Spacer(1,7),Paragraph('TEENSY PIN NUMBERS (not socket contact numbers)',small)]
mapping=[['AXIS / MOVEMENT','PWM1 / PWM2 / PWM3','EN','CSn']]
for i,a in enumerate(axes,1):mapping.append([f"A{i} / {a['name'].replace('_',' ')}",' / '.join(map(str,a['pwm'])),str(a['enable']),str(a['cs'])])
t=Table(mapping,colWidths=[236,155,70,70],hAlign='LEFT')
t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),8.2),
                      ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef5')),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
story += [t,Spacer(1,7),Paragraph(escape(footer),small)]
pdf=ROOT/'net-guide-review.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=32,leftMargin=32,topMargin=25,bottomMargin=25,
                      title=title,author='TrueSkate hardware review')
doc.build(story)
assert len(PdfReader(pdf).pages)==1,'Net guide must remain one page'
print(f'Wrote one-page net guide; all {len(actual)} real net names covered exactly once by the families.')
