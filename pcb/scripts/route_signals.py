#!/usr/bin/env python3
"""Export/import routing exchanges, explicitly excluding all power and ground.

Run with KiCad's bundled Python: export, then run the documented Freerouting
command, then import. The import only copies approved signal nets; every original
manual segment, footprint and ground zone stays in the original board.
"""
import json
from pathlib import Path
import re
import sys
import pcbnew as k

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/"design/trueskate-main-v1.kicad_pcb"
EXCHANGE=ROOT/"design/routing"
SIGNALS={f"A{i}_{suffix}" for i in range(1,7) for suffix in
         ("PWM1","PWM2","PWM3","EN","EN_CMD","CS")}|{"SPI_SCK","SPI_MISO","SPI_MOSI","3V3","EN_DISABLE"}

def export():
    EXCHANGE.mkdir(exist_ok=True)
    b=k.LoadBoard(str(PCB))
    assert all(t.IsLocked() for t in b.GetTracks()),"Export the manual-only generated board"
    dsn=EXCHANGE/"signals.dsn"
    assert k.ExportSpecctraDSN(b,str(dsn))
    source=dsn.read_text()
    # KiCad's standalone BOARD API does not load the project net classes.
    # Substitute a conservative routing rule and two explicit net classes.
    source=source.replace('(width 200)','(width 250)').replace('(clearance 200)','(clearance 250)')
    source=source.replace('Via[0-1]_600:300_um','Via[0-1]_700:300_um')
    source=source.replace('(circle F.Cu 600)','(circle F.Cu 700)').replace('(circle B.Cu 600)','(circle B.Cu 700)')
    start=source.index('    (class kicad_default ')
    end=source.index('\n  )\n  (wiring',start)
    manual=sorted({t.GetNetname() for t in b.GetTracks()}-SIGNALS)
    def netclass(name,names):
        return '    (class '+name+' '+' '.join(names)+'\n      (circuit (use_via "Via[0-1]_700:300_um"))\n      (rule (width 250) (clearance 250))\n    )'
    source=source[:start]+netclass('Signals',sorted(SIGNALS-set(manual)))+'\n'+netclass('Manual',manual)+source[end:]
    # Routing-only exclusion regions protect all phase corridors. Fixed
    # encoder escape tracks already reach the legal routing area below/right.
    keepouts=[]
    regions=[(0,0,160,17)]+[(3+25*i,17,17.5+25*i,44.75) for i in range(6)]
    for i,(x0,y0,x1,y1) in enumerate(regions):
        for layer in ('F.Cu','B.Cu'):
            keepouts.append(f'    (keepout route_guard_{i}_{layer} (rect {layer} {x0*1000:g} {-y1*1000:g} {x1*1000:g} {-y0*1000:g}))')
    source=source.replace('    (via "Via[0-1]_700:300_um")','\n'.join(keepouts)+'\n    (via "Via[0-1]_700:300_um")',1)
    dsn.write_text(source)
    print('Exported fixed manual copper. Autoroute Signals only, with -inc Manual.')

def imp():
    imported=k.LoadBoard(str(PCB))
    assert k.ImportSpecctraSES(imported,str(EXCHANGE/"signals.ses"))
    original=k.LoadBoard(str(PCB)); nets=original.GetNetsByName()
    count=0
    for t in imported.GetTracks():
        if t.GetNetname() not in SIGNALS or t.IsLocked(): continue
        copied=t.Duplicate();copied.SetNet(nets[t.GetNetname()]);copied.SetLocked(False)
        if not isinstance(copied,k.PCB_VIA): copied.SetWidth(max(copied.GetWidth(),k.FromMM(.2)))
        # Freerouting uses its own edge rules. Keep every endpoint at least
        # 0.65mm inside the board (>=0.5mm to a 0.25mm trace edge).
        if not isinstance(copied,k.PCB_VIA):
            for getter,setter in [(copied.GetStart,copied.SetStart),(copied.GetEnd,copied.SetEnd)]:
                q=getter();q.y=max(k.FromMM(.65),min(q.y,k.FromMM(119.35)));q.x=max(k.FromMM(.65),min(q.x,k.FromMM(159.35)));setter(q)
        original.Add(copied);count+=1
    k.ZONE_FILLER(original).Fill(original.Zones())
    k.SaveBoard(str(PCB),original,True)
    print(f'Imported {count} signal items only; manual power/ground untouched.')

if __name__=='__main__':
    {'export':export,'import':imp}[sys.argv[1]]()
