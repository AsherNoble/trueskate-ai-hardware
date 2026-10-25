#!/usr/bin/env python3
"""Rebuild REVIEW design from native source and the checked-in signal session.

Uses KiCad's bundled Python. Does NOT run an autorouter or export manufacturing
files. Run strict kicad-cli ERC/DRC after rebuilding. Do not run over manual edits.
"""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
stitch_path=ROOT/'design/data/ground-stitching.json'
frozen_stitches=stitch_path.read_bytes()
for script,args in [('scripts/extract_mini.py',[]),('scripts/generate.py',[]),('scripts/route_signals.py',['export']),
                    ('scripts/route_signals.py',['import']),('scripts/complete_routes.py',['--apply']),('scripts/finish_signals.py',[]),('scripts/prepare_ground.py',[])]:
    subprocess.run([sys.executable,str(ROOT/script),*args],check=True)
stitch_path.write_bytes(frozen_stitches)
subprocess.run([sys.executable,str(ROOT/'scripts/replay_ground.py')],check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/apply_silkscreen.py')],check=True)
