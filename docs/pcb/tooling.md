# Native source and review tools

Direct KiCad scripting preserves the verified Mini socket geometry and emits
editable native files without an intermediate schematic-language translation.
It reproduces deliberate power/ground routes while KiCad's CLI checks the
resulting schematic and copper.

## Software installed

KiCad **10.0.6** was already installed. Homebrew installed **Freerouting 2.5.0**
from the official JAR via local tap `trueskate/pcb-tools`; the formula is retained
at `pcb/scripts/freerouting.rb`. An initial 2.2.2 install hit an internal routing
error and was replaced with 2.5.0.

Homebrew also upgraded **OpenJDK 27**, libpng 1.6.59, pcre2 10.49, glib 2.90.0,
xorgproto 2026.1, cairo 1.18.6, harfbuzz 14.5.1 and xz 5.8.4. ReportLab, pypdf,
Pillow and Poppler were already available. Tap creation enabled Homebrew's
developer mode. No cloud routing, PCB upload, firmware flash or remote git push.

## Rebuild

```sh
'/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3' '/Users/ashernoble/Projects/Robotics & hardware/trueskate-ai-hardware/pcb/scripts/rebuild.py'
```

Sequence: `pcb/scripts/extract_mini.py` → `generate.py` →
`route_signals.py export/import` → `finish_signals.py` → `finish_ground.py` →
`convert_two_layer.py` → two passes of `stitch_ground.py`. It reuses
`pcb/design/routing/signals.ses`; it does not launch an autorouter. Do not
regenerate over unrecorded manual KiCad edits.

`pcb/design/data/design.json` is the agreed pin map. `pcb/scripts/kicad_source.py`
writes schematic/project files into `pcb/design/`. `generate.py` writes placement,
BOM and locked manual power/phase segments. Ground route records live in
`pcb/design/data/`; checks and exported review geometry live in `pcb/review/checks/`.

`SaveBoard(..., aSkipSettings=True)` prevents standalone Python from overwriting
project rules with application defaults. Project schema versions are explicit.
Final CLI DRC refills/saves the project-aware copper before review exports.

## Signal routing

The DSN contains locked manual copper and 250 um signal width/clearance,
0.7/0.3 mm vias. Freerouting ran headlessly, telemetry disabled, Manual class
excluded. Paths with spaces required temporary DSN/SES copies in `/private/tmp`.
Only PWM, EN, EN_CMD, CS, SPI, 3V3 and EN_DISABLE items are imported back. Any router power/ground changes
are discarded. Automatic neck-down widths are clamped to at least 0.2 mm;
strict DRC validates them. The frozen SES is the reproducible source.
[Official release](https://github.com/freerouting/freerouting/releases/tag/v2.5.0).

## Validate and export review material only

```sh
'/Library/Frameworks/Python.framework/Versions/3.11/bin/python3' '/Users/ashernoble/Projects/Robotics & hardware/trueskate-ai-hardware/pcb/scripts/export_review.py'
```

Python 3.11 requires ReportLab, pypdf, Pillow and Shapely (2.x). This runs strict CLI
ERC/DRC with schematic parity, independent audits, three review PDFs and three
native PNGs. `--checks-only` omits rendering. `review/checks/review-status.json` records hashes.
KiCad needs normal configuration/font-cache access; the macOS sandbox otherwise
terminates some checks/renders.

PDFs are rendered to images for visual inspection, not just text extraction.
The net guide asserts coverage of all 62 real nets. Standard KiCad
`unconnected-(...)` single-contact names are bookkeeping, not extra wires.
No script produces Gerbers, drill, placement or upload files. Stop for human
review before manufacturing.


## Mini v1.0 drill and power checks

`scripts/extract_mini.py` verifies pinned raw-source hashes, parses metric 3:3 drills,
traces EasyEDA schematic wires, and obtains the GKO outline without grid snapping.
`verify_mini.py --checks-only` independently reads actual native library and
board pads and checks all 105 contacts against the drill file. Without that flag
it writes the PNG/SVG overlay (Python 3.11 plus matplotlib).
`pcb/scripts/verify_power.py` confirms the restored locked outer-layer routes
and records their geometry. Copper/thermal qualification is stopped; that script
does not run a temperature or current-capacity calculation.

The direct-power revision reroutes the signals with Freerouting 2.5.0 against
new locked power copper. The updated SES is checked in. Telemetry was disabled;
only PWM/EN/CS/SPI routes are imported. Existing manufacturing and assembled
mockup snapshots are explicitly marked historical; rebuild does not update them.
