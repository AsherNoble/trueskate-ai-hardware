#!/usr/bin/env python3
"""Strict validation and human-review exports ONLY; never manufacturing files.

Uses installed macOS KiCad 10 CLI and Python. Run using Python 3.11 with
reportlab, pypdf, Pillow and shapely. --checks-only skips PDF/PNG rendering.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
PY='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
PCB=ROOT/'design/trueskate-main-v1.kicad_pcb'
SCH=ROOT/'design/trueskate-main-v1.kicad_sch'
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
    decisions=json.loads((ROOT/'sources/prototype-decisions.json').read_text())
    run([CLI,'sch','erc','--severity-all','--exit-code-violations','--format','json',
         '--output',ROOT/'review/checks/erc-review.json',SCH])
    run([CLI,'pcb','drc','--severity-all','--all-track-errors','--schematic-parity',
         '--refill-zones','--save-board','--exit-code-violations','--format','json',
         '--output',ROOT/'review/checks/drc-review.json',PCB])
    drc=json.loads((ROOT/'review/checks/drc-review.json').read_text())
    assert not any(drc[name]for name in ['violations','unconnected_items','schematic_parity','ignored_checks'])
    run([CLI,'sch','export','netlist','--format','kicadxml','--output',ROOT/'review/checks/netlist-review.xml',SCH])
    audit=run([sys.executable,ROOT/'scripts/audit.py'])
    board_audit=run([PY,ROOT/'scripts/verify_board.py'])
    ground_audit=run([sys.executable,ROOT/'scripts/verify_kill.py'])
    mini_audit=run([sys.executable,ROOT/'scripts/verify_mini.py','--checks-only'])
    power_audit=run([PY,ROOT/'scripts/verify_power.py'])
    protection_audit=run([sys.executable,ROOT/'scripts/verify_protection.py'])
    silk_audit=run([sys.executable,ROOT/'scripts/verify_silkscreen.py'])
    layout_audit=run([PY,ROOT/'scripts/verify_layout.py'])
    layer_audit=run([PY,ROOT/'scripts/verify_two_layer.py'])
    run([PY,ROOT/'scripts/export_ground_geometry.py'])
    connectivity_audit=run([sys.executable,ROOT/'scripts/verify_ground_connectivity.py'])
    return_audit=run([sys.executable,ROOT/'scripts/audit_return_paths.py'])
    if not args.checks_only:
        run([CLI,'sch','export','pdf','--output',ROOT/'review/drawings/schematic-review.pdf',SCH])
        run([PY,ROOT/'scripts/export-fit.py'])
        run([sys.executable,ROOT/'scripts/net_guide.py'])
        run([sys.executable,ROOT/'scripts/draw_sd_access.py'])
        for name,layer in [('top-copper-review','F.Cu'),('bottom-copper-review','B.Cu')]:
            run([CLI,'pcb','export','svg','--mode-single','--layers',layer+',Edge.Cuts',
                 '--page-size-mode','2','--exclude-drawing-sheet','--output',ROOT/'renders/copper'/(name+'.svg'),PCB])
        jobs=[]
        for name,side,rotate in [('top','top',None),('bottom','bottom',None),('3d','top','-35,0,25')]:
            cmd=[CLI,'pcb','render','--width','1800','--height','1400','--quality','high',
                 '--background','opaque','--side',side,'--output',ROOT/'renders/bare'/(name+'-review.png')]
            if rotate:cmd+=['--rotate',rotate,'--perspective','--zoom','0.78']
            jobs.append(cmd+[PCB])
        with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,jobs))
    files=[PCB,ROOT/'design/trueskate-main-v1.kicad_pro',ROOT/'design/trueskate-main-v1.kicad_dru',SCH,ROOT/'design/routing/signals.ses',ROOT/'design/routing/signal-completions.json',ROOT/'review/checks/bank-crossings.json',
           ROOT/'design/data/circuit.json',ROOT/'bom/bom-review.csv',ROOT/'review/checks/erc-review.json',ROOT/'review/checks/drc-review.json',
           ROOT/'design/TrueSkate.pretty/SimpleFOC_Mini_v1.0.kicad_mod',ROOT/'review/checks/mini-fit-report.json',
           ROOT/'review/checks/power-routing-review.json',ROOT/'review/checks/layout-review.json',ROOT/'review/checks/two-layer-ground-review.json',ROOT/'review/checks/ground-connectivity-review.json',ROOT/'design/data/stackup.json',ROOT/'review/checks/kill-state-review.json',ROOT/'review/drawings/mini-drill-overlay.png',ROOT/'design/data/ground-link-plan.json']
    if not args.checks_only:
        files += [ROOT/name for name in ['review/drawings/schematic-review.pdf','review/drawings/mechanical-fit-review.pdf',
                    'review/drawings/net-guide-review.pdf','renders/bare/top-review.png','renders/bare/bottom-review.png','renders/bare/3d-review.png','renders/copper/top-copper-review.svg','renders/copper/bottom-copper-review.svg','review/drawings/sd-access.svg','renders/copper/return-path-gaps.svg']]
    files += [p for p in (ROOT/'renders').glob('populated-*.png')]
    files += [ROOT/'renders/provenance.json', ROOT/'design/data/ground-stitching.json', ROOT/'review/checks/ground-geometry-review.json', ROOT/'review/checks/return-path-review.json',ROOT/'review/checks/reverse-polarity-review.json',ROOT/'review/checks/silkscreen-review.json']
    status=dict(copper_decision='Two layers, 1 oz; copper/thermal qualification stopped by user.',
                kicad_version=drc['kicad_version'],checked_at=drc['date'],
                erc='PASS',drc='PASS: no violations, opens, parity issues, exclusions or ignored checks',
                human_review_required=False,human_review_optional=True,manufacturing_exports_generated=((ROOT/'manufacturing/manifest.json').exists() and json.loads((ROOT/'manufacturing/manifest.json').read_text()).get('source_pcb_sha256')==hashlib.sha256(PCB.read_bytes()).hexdigest()),
                requirements_not_fully_satisfied=decisions['outstanding_items'],
                accepted_prototype_decisions=decisions,
                files_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},
                independent_checks=(audit+board_audit+ground_audit+mini_audit+power_audit+layout_audit+layer_audit+connectivity_audit+return_audit+protection_audit+silk_audit).strip())
    (ROOT/'review/checks/review-status.json').write_text(json.dumps(status,indent=2)+'\n')
    print('Review checks passed. Human review is optional; no upload/order performed.',flush=True)
if __name__=='__main__':main()
