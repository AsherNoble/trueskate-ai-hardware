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

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT.parent/'docs/pcb'
groups=[
(['12V_IN'],'J5 positive to F1 input, before the fuse. Original outer-layer input route; correct polarity required.'),
(['12V_FUSED'],'F1 output to all Mini VIN contacts and local capacitors. Original outer-layer bus and feeds; 1 oz copper.'),
(['3V3'],'Teensy regulator to encoders, CS pull-ups, kill buffers and /OE pull-up. USB powers the Teensy.'),
(['GND'],'Stitched top/bottom GND fills join supply negative, logic, Minis and capacitor returns. No isolation.'),
(['SPI_SCK'],'Teensy 13 to all encoders. SH contact assignment is provisional; see README verification table.'),
(['SPI_MOSI'],'Teensy 11 to all encoders. Host-to-encoder data.'),
(['SPI_MISO'],'Encoders to Teensy 12. Only the selected encoder may drive this shared line.'),
([f'A{i}_PWM{p}' for i in range(1,7) for p in range(1,4)],'Three logic PWM instructions per axis from Teensy to Mini. Existing pin map retained.'),
([f'A{i}_EN_CMD' for i in range(1,7)],'Teensy EN command to a buffer input; 10k input pull-down holds an undriven command low.'),
(['EN_DISABLE'],'J6 NC loop shorts this net to GND to permit commands. Open loop lets R1 pull it high and disable all buffers.'),
([f'A{i}_EN' for i in range(1,7)],'Buffered enable to Mini pin9. Open kill loop makes buffer high impedance; local 10k pulls EN low.'),
([f'A{i}_CS' for i in range(1,7)],'Individual active-low encoder select with 10k pull-up. Fit with its encoder; deselect all before SPI.'),
([f'A{i}_PH{p}' for i in range(1,7) for p in range(1,4)],'Mini P3/P2/P1 to male motor header1/2/3. Never move phase cables with 12V live.')
]
actual={n for p in json.loads((ROOT/'design/data/circuit.json').read_text()) for n in p['nets'] if n}
covered=[n for ns,_ in groups for n in ns]
assert len(covered)==len(set(covered)) and set(covered)==actual
axes=json.loads((ROOT/'design/data/design.json').read_text())['axes']
title='TrueSkate v1 - every net, in plain English'
intro=('Identical labels are one electrical net. Shared copper remains continuous with any axis unpopulated. '
       'The two shared kill buffers and their bias/bypass parts remain fitted. Plug-in modules perform motor control.')
labels=['12V_IN','12V_FUSED','3V3','GND','SPI_SCK','SPI_MOSI','SPI_MISO',
        'A<n>_PWM<p>','A<n>_EN_CMD','EN_DISABLE','A<n>_EN','A<n>_CS','A<n>_PH<p>']
footer=('SH pin-to-net order is UNVERIFIED: see README and check the actual AS5048A board with a multimeter. '
        'Opening kill disables EN but does not disconnect 12V; reclosing permits the current command without a latch. '
        'Human review, mechanical fit, startup and noise tests remain required before manufacture.')
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
pdf=ROOT/'review/drawings/net-guide-review.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=32,leftMargin=32,topMargin=25,bottomMargin=25,
                      title=title,author='TrueSkate hardware review')
doc.build(story)
assert len(PdfReader(pdf).pages)==1,'Net guide must remain one page'
print(f'Wrote one-page net guide; all {len(actual)} real net names covered exactly once by the families.')
