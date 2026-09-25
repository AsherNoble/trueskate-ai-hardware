# Reproducing the review design

No packages were installed during this work. The machine already had Homebrew,
KiCad 10.0.6 (including pcbnew Python bindings and component libraries), PlatformIO,
Poppler (`pdftoppm`) and Java. Homebrew was inspected; no unrelated taps or packages
were changed. No autorouter was used. Network downloads were upstream mechanical
source files and manufacturer reference material, not installed software.

The commands below use task-specific variables expanded from absolute paths.
Run only after saving any manual edits elsewhere: the generator overwrites its
generated KiCad files. It does not change the historical bring-up firmware.

```sh
PCB_DIR='/Users/ashernoble/Projects/Robotics & hardware/trueskate-ai-hardware/pcb'
KICAD_PY='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
KICAD_MODELS='/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels'

"$KICAD_PY" "$PCB_DIR/extract_mini.py"
"$KICAD_PY" "$PCB_DIR/audit.py"
"$KICAD_PY" "$PCB_DIR/generate.py"
"$KICAD_PY" "$PCB_DIR/verify_board.py"

"$KICAD_CLI" sch erc --format json --exit-code-violations \
  --output "$PCB_DIR/erc-review.json" "$PCB_DIR/trueskate-main-v1.kicad_sch"
"$KICAD_CLI" pcb drc --format json --exit-code-violations \
  --output "$PCB_DIR/drc-review.json" "$PCB_DIR/trueskate-main-v1.kicad_pcb"

"$KICAD_CLI" sch export pdf --output "$PCB_DIR/schematic-review.pdf" \
  "$PCB_DIR/trueskate-main-v1.kicad_sch"
"$KICAD_PY" "$PCB_DIR/export-fit.py"
"$KICAD_CLI" pcb render --side top --width 2000 --height 1500 --background opaque \
  -D "KICAD10_3DMODEL_DIR=$KICAD_MODELS" --output "$PCB_DIR/top-review.png" \
  "$PCB_DIR/trueskate-main-v1.kicad_pcb"
"$KICAD_CLI" pcb render --side bottom --width 2000 --height 1500 --background opaque \
  -D "KICAD10_3DMODEL_DIR=$KICAD_MODELS" --output "$PCB_DIR/bottom-review.png" \
  "$PCB_DIR/trueskate-main-v1.kicad_pcb"
"$KICAD_CLI" pcb render --rotate 325,0,30 --width 2000 --height 1500 --background opaque \
  -D "KICAD10_3DMODEL_DIR=$KICAD_MODELS" --output "$PCB_DIR/3d-review.png" \
  "$PCB_DIR/trueskate-main-v1.kicad_pcb"
```

At the current stage, **DRC is expected to return a failure status** because of
unconnected nets. Do not remove `--exit-code-violations` merely to make a release
pipeline green. Earlier interactive calls omitted that option to gather reports;
their exit code alone was not used to claim a clean board.

In this agent environment, KiCad DRC needed access to its normal application
configuration/caches and was run with explicit approval outside the restrictive
sandbox. Font-cache warnings during PDF/ERC generation did not prevent output.
The Python binding emitted a wxApp warning but produced board files that loaded
in `kicad-cli`. The native PDF was rendered with Poppler for visual review; the
PDF skill's render-and-inspect workflow was used instead of trusting export alone.

The fit exporter moves a temporary copy 60 mm right and 35 mm down on A4 paper,
then exports at scale 1. This preserves dimensions while leaving printable margins;
it does not move any part on the source PCB. The 50 mm printed reference must still
be measured because printer dialogs can apply an additional scale factor.
