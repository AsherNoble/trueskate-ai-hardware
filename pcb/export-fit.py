#!/usr/bin/env python3
"""Export an unmagnified paper-fit drawing with printable margins.

Use KiCad's bundled Python. Only a temporary copy is translated; the electrical
board's coordinates, nets, placement and copper are never edited here.
"""
from pathlib import Path
import subprocess
import tempfile
import pcbnew as k

root = Path(__file__).resolve().parent
board = k.LoadBoard(str(root / "trueskate-main-v1.kicad_pcb"))
offset = k.VECTOR2I(k.FromMM(60), k.FromMM(35))
for collection in (board.GetFootprints(), board.GetTracks(), board.GetDrawings(), board.Zones()):
    for item in collection:
        item.Move(offset)

with tempfile.TemporaryDirectory(prefix="trueskate-paper-fit-") as scratch:
    drawing = Path(scratch) / "fit.kicad_pcb"
    k.SaveBoard(str(drawing), board, True)
    subprocess.run([
        "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
        "pcb", "export", "pdf", "--mode-single",
        "--layers", "F.Fab,Edge.Cuts,Dwgs.User", "--exclude-value",
        "--sketch-pads-on-fab-layers", "--black-and-white", "--scale", "1",
        "--drill-shape-opt", "2", "--no-property-popups",
        "--output", str(root / "mechanical-fit-review.pdf"), str(drawing)
    ], check=True)
print("Exported 1:1 top-view template with margins; source PCB unchanged.")
