#!/usr/bin/env python3
"""Rebuild REVIEW design from native source and the checked-in signal session.

Uses KiCad's bundled Python. Does NOT run an autorouter or export manufacturing
files. Run strict kicad-cli ERC/DRC after rebuilding. Do not run over manual edits.
"""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parent
for script,args in [('extract_mini.py',[]),('generate.py',[]),('route_signals.py',['export']),
                    ('route_signals.py',['import']),('finish_signals.py',[]),('finish_ground.py',[])]:
    subprocess.run([sys.executable,str(ROOT/script),*args],check=True)
