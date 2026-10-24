#!/usr/bin/env python3
"""Strict validation and human-review exports ONLY; never manufacturing files.

Uses installed macOS KiCad 10 CLI and Python. Run using Python 3.11 with
reportlab/pypdf. --checks-only skips PDF/PNG rendering.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
PY='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
PCB=ROOT/'trueskate-main-v1.kicad_pcb'
SCH=ROOT/'trueskate-main-v1.kicad_sch'
def run(args):
    env=os.environ.copy()
    share='/Applications/KiCad/KiCad.app/Contents/SharedSupport'
    env.setdefault('KICAD10_FOOTPRINT_DIR',share+'/footprints')
    env.setdefault('KICAD10_3DMODEL_DIR',share+'/3dmodels')
    result=subprocess.run([str(a)for a in args],cwd=ROOT,text=True,
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)
    print(result.stdout,flush=True)
    result.check_returncode()
    return result.stdout
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checks-only',action='store_true')
    args=parser.parse_args()
    run([CLI,'sch','erc','--severity-all','--exit-code-violations','--format','json',
         '--output',ROOT/'erc-review.json',SCH])
    run([CLI,'pcb','drc','--severity-all','--all-track-errors','--schematic-parity',
         '--refill-zones','--save-board','--exit-code-violations','--format','json',
         '--output',ROOT/'drc-review.json',PCB])
    drc=json.loads((ROOT/'drc-review.json').read_text())
    assert not any(drc[name]for name in ['violations','unconnected_items','schematic_parity','ignored_checks'])
    run([CLI,'sch','export','netlist','--format','kicadxml','--output',ROOT/'netlist-review.xml',SCH])
    audit=run([sys.executable,ROOT/'audit.py'])
    board_audit=run([PY,ROOT/'verify_board.py'])
    ground_audit=run([sys.executable,ROOT/'verify_kill.py'])
    mini_audit=run([sys.executable,ROOT/'verify_mini.py','--checks-only'])
    power_audit=run([PY,ROOT/'verify_power.py'])
    layout_audit=run([PY,ROOT/'verify_layout.py'])
    layer_audit=run([PY,ROOT/'verify_four_layer.py'])
    if not args.checks_only:
        run([CLI,'sch','export','pdf','--output',ROOT/'schematic-review.pdf',SCH])
        run([PY,ROOT/'export-fit.py'])
        run([sys.executable,ROOT/'net_guide.py'])
        for name,layer in [('l2-ground-review','In1.Cu'),('l3-power-review','In2.Cu')]:
            run([CLI,'pcb','export','svg','--mode-single','--layers',layer+',Edge.Cuts',
                 '--page-size-mode','2','--exclude-drawing-sheet','--output',ROOT/(name+'.svg'),PCB])
        jobs=[]
        for name,side,rotate in [('top','top',None),('bottom','bottom',None),('3d','top','-35,0,25')]:
            cmd=[CLI,'pcb','render','--width','1800','--height','1400','--quality','high',
                 '--background','opaque','--side',side,'--output',ROOT/(name+'-review.png')]
            if rotate:cmd+=['--rotate',rotate,'--perspective','--zoom','0.78']
            jobs.append(cmd+[PCB])
        with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,jobs))
    files=[PCB,ROOT/'trueskate-main-v1.kicad_pro',ROOT/'trueskate-main-v1.kicad_dru',SCH,ROOT/'routing/signals.ses',
           ROOT/'circuit.json',ROOT/'bom-review.csv',ROOT/'erc-review.json',ROOT/'drc-review.json',
           ROOT/'TrueSkate.pretty/SimpleFOC_Mini_v1.0.kicad_mod',ROOT/'mini-fit-report.json',
           ROOT/'power-routing-review.json',ROOT/'layout-review.json',ROOT/'four-layer-review.json',ROOT/'stackup.json',ROOT/'kill-state-review.json',ROOT/'mini-drill-overlay.png',ROOT/'ground-link-plan.json']
    if not args.checks_only:
        files += [ROOT/name for name in ['schematic-review.pdf','mechanical-fit-review.pdf',
                    'net-guide-review.pdf','top-review.png','bottom-review.png','3d-review.png','l2-ground-review.svg','l3-power-review.svg']]
    status=dict(kicad_version=drc['kicad_version'],checked_at=drc['date'],
                erc='PASS',drc='PASS: no violations, opens, parity issues, exclusions or ignored checks',
                human_review_required=True,manufacturing_exports_generated=False,
                requirements_not_fully_satisfied=['SH harness mapping needs physical verification', '0<VCC<2V supply-ramp behavior is outside the buffer DC guarantees', 'New mounting-hole and socket/cable fit checks pending'],
                files_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},
                independent_checks=(audit+board_audit+ground_audit+mini_audit+power_audit+layout_audit+layer_audit).strip())
    (ROOT/'review-status.json').write_text(json.dumps(status,indent=2)+'\n')
    print('Review checks passed. STOP: human review before any manufacturing export.',flush=True)
if __name__=='__main__':main()
