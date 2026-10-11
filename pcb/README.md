# USB-powered six-axis carrier v1: review package

**NOT RELEASED FOR FABRICATION.** A 160 x 120 mm, two-layer, entirely through-hole
carrier: socketed Teensy and six Minis, encoder breakout sockets, fused 12 V,
local capacitors, EN pull-downs and star ground. No factory assembly. Removed
features belong to [v2](../docs/pcb/v2-backlog.md).

Start with [the one-page net guide](../docs/pcb/nets.md), then
[the beginner walkthrough](../docs/pcb/design-notes.md) and
[human-review checklist](../docs/pcb/hardware-check.md).

- Open `trueskate-main-v1.kicad_pro` in KiCad 10.
- `schematic-review.pdf`: native nine-page drawing.
- `net-guide-review.pdf`: one-page plain-English guide to all 67 real nets.
- `mechanical-fit-review.pdf`: 1:1 top view; print at actual size and check the
  50 mm ruler. Mini socket fit and base fit have already been confirmed.
- `top-review.png`, `bottom-review.png`, `3d-review.png`: native board renders;
  plug-in Teensy/Mini/breakout boards and wiring omitted.
- `bom-review.csv` and [grouped BOM](../docs/pcb/bom.md): hand-soldered parts,
  selected LCSC entries and labeled cost allowances.
- `erc-review.json`, `drc-review.json`, `review-status.json`: checked reports,
  independent audits and artifact hashes. See [verification](../docs/pcb/verification.md).
- `design.json`, `generate.py`, `kicad_source.py`: editable design source.
  `routing/signals.ses`: frozen signal routes. `manual-routes.json`,
  `ground-links.json`, `ground-stitching.json`: deliberate power/ground records.
  See [tooling](../docs/pcb/tooling.md).

`rebuild.py` reconstructs the board and reimports signals only.
`export_review.py` validates and produces review PDFs/PNGs only. Neither creates
Gerbers, drills or assembly files. Do not regenerate over unrecorded manual
KiCad edits. Upstream geometry evidence stays in `sources/`.

The runtime firmware is still the earlier one-axis bench implementation, not
six-axis carrier firmware. Do not flash it assuming otherwise. Human electrical
review before ordering remains essential: ERC/DRC is not a current-capacity,
noise, power-sequencing or motion-safety certification.
