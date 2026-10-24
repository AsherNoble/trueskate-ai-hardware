#!/usr/bin/env python3
"""Rebuild REVIEW design from native source and the checked-in signal session.

Uses KiCad's bundled Python. Does NOT run an autorouter or export manufacturing
files. Run strict kicad-cli ERC/DRC after rebuilding. Do not run over manual edits.
"""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
for script,args in [('scripts/extract_mini.py',[]),('scripts/generate.py',[]),('scripts/route_signals.py',['export']),
                    ('scripts/route_signals.py',['import']),('scripts/finish_signals.py',[]),('scripts/finish_ground.py',[]),('scripts/convert_two_layer.py',[]),('scripts/stitch_ground.py',[]),('scripts/stitch_ground.py',[])]:
    subprocess.run([sys.executable,str(ROOT/script),*args],check=True)
