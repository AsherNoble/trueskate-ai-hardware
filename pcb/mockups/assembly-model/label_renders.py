"""Add a title and cable legend to the actual Blender renders using Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent
FONT='/System/Library/Fonts/Helvetica.ttc'
title=ImageFont.truetype(FONT,44);sub=ImageFont.truetype(FONT,26)
small=ImageFont.truetype(FONT,23)
for source,dest,view in [('assembly-perspective.png','assembled-overview.png','Perspective view'),('assembly-top.png','assembled-top-overview.png','Top view')]:
    raw=Image.open(ROOT/source).convert('RGB')
    out=Image.new('RGB',(raw.width,raw.height+230),'#f5f7f8')
    out.paste(raw,(0,130));d=ImageDraw.Draw(out)
    d.text((48,26),'TrueSkate carrier — assembled model',font=title,fill='#1e3139')
    d.text((50,83),f'{view}  /  160 × 120 mm PCB  /  six drivers, one motor connected',font=sub,fill='#53636b')
    y=raw.height+160
    for x,color,label in [(50,'#df782c','3 motor phases'),(430,'#2899b3','Encoder harness'),(850,'#cb4035','12 V power pairs'),(1290,'#30383d','USB to Teensy')]:
        d.line((x,y+13,x+42,y+13),fill=color,width=9)
        d.text((x+58,y),label,font=sub,fill='#253943')
    d.text((50,y+39),'Simplified solid geometry. PCB contact positions from KiCad; module bodies and cable routing are representative.',font=small,fill='#62747d')
    out.save(ROOT/dest)
    print(ROOT/dest)
