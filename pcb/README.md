# Main control PCB v1 — review package

**NOT FOR FABRICATION.** Circuit and placement draft with partial local routing.
Unconnected nets are not waived; this is not the requested finished DRC-clean board.

Start with [the beginner walkthrough](../docs/pcb/design-notes.md), then
[verification and release holds](../docs/pcb/verification.md).

- Open `trueskate-main-v1.kicad_pro` in KiCad 10.
- `schematic-review.pdf`: native, multi-page electrical drawing.
- `mechanical-fit-review.pdf`: 1:1 top-view paper template; print at actual size
  and verify its 50 mm scale before use. See [hardware checks](../docs/pcb/hardware-check.md).
- `top-review.png`, `bottom-review.png`, `3d-review.png`: actual carrier placement;
  removable Teensy/Mini boards omitted, not a validated mechanical assembly.
- `bom-review.csv` and [grouped BOM](../docs/pcb/bom.md): quantities, assembly split,
  LCSC candidates and cost allowances; see [sourcing](../docs/pcb/sourcing.md).
- `erc-review.json`, `drc-review.json`: current tool reports. `*-initial.*` files
  are earlier diagnostic snapshots, not final verification evidence.
- `design.json`, `generate.py`, `audit.py`, `verify_board.py`, `extract_mini.py`:
  reproducible source and static checks. See [tooling](../docs/pcb/tooling.md).

Target: 160 × 120 mm, two layers. Direct KiCad scripting uses native files and
KiCad's bundled Python. Do not rerun the generator over unsaved/manual KiCad edits.

Upstream mechanical evidence belongs in `sources/`; generated artifacts
must not be confused with validated manufacturing outputs.
