# Native source and review tools

Direct KiCad scripting preserves the verified Mini socket geometry and emits
editable native files without an intermediate schematic-language translation.
It reproduces deliberate power/ground routes while KiCad's CLI checks the
resulting schematic and copper.

## Software installed

KiCad **10.0.6** was already installed. Homebrew installed **Freerouting 2.5.0**
from the official JAR via local tap `trueskate/pcb-tools`; the formula is retained
at `pcb/tools/freerouting.rb`. An initial 2.2.2 install hit an internal routing
error and was replaced with 2.5.0.

Homebrew also upgraded **OpenJDK 27**, libpng 1.6.59, pcre2 10.49, glib 2.90.0,
xorgproto 2026.1, cairo 1.18.6, harfbuzz 14.5.1 and xz 5.8.4. ReportLab, pypdf,
Pillow and Poppler were already available. Tap creation enabled Homebrew's
developer mode. No cloud routing, PCB upload, firmware flash or remote git push.

## Rebuild

```sh
'/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3' '/Users/ashernoble/Projects/Robotics & hardware/trueskate-ai-hardware/pcb/rebuild.py'
```

Sequence: `extract_mini.py` -> `generate.py` -> `route_signals.py export` -> `route_signals.py import`
-> `finish_ground.py`. It does not launch an autorouter: it reuses checked-in
`routing/signals.ses`. Do not regenerate over unrecorded manual KiCad edits.

`design.json` is the agreed pin map; `kicad_source.py` writes schematic/project
files. `generate.py` writes placement and locked manual segments for power,
phases, control grounds and encoder supply. `finish_ground.py` adds explicit
quiet-ground links (`ground-link-plan.json` -> `ground-links.json`) and checked stitching vias
(`ground-stitching.json`). No PGND branch is autorouted.

`SaveBoard(..., aSkipSettings=True)` prevents standalone Python from overwriting
project rules with application defaults. Project schema versions are explicit.
Final CLI DRC refills/saves the project-aware copper before review exports.

## Signal routing

The DSN contains locked manual copper and 250 um signal width/clearance,
0.7/0.3 mm vias. Freerouting ran headlessly, telemetry disabled, Manual class
excluded. Paths with spaces required temporary DSN/SES copies in `/private/tmp`.
Only PWM, EN, CS and SPI items are imported back. Any router power/ground changes
are discarded. Automatic neck-down widths are clamped to at least 0.2 mm;
strict DRC validates them. The frozen SES is the reproducible source.
[Official release](https://github.com/freerouting/freerouting/releases/tag/v2.5.0).

## Validate and export review material only

```sh
'/Library/Frameworks/Python.framework/Versions/3.11/bin/python3' '/Users/ashernoble/Projects/Robotics & hardware/trueskate-ai-hardware/pcb/export_review.py'
```

Python 3.11 supplies the already-installed PDF libraries. This runs strict CLI
ERC/DRC with schematic parity, independent audits, three review PDFs and three
native PNGs. `--checks-only` omits rendering. `review-status.json` records hashes.
KiCad needs normal configuration/font-cache access; the macOS sandbox otherwise
terminates some checks/renders.

PDFs are rendered to images for visual inspection, not just text extraction.
The net guide asserts coverage of all 67 real nets. Standard KiCad
`unconnected-(...)` single-contact names are bookkeeping, not extra wires.
No script produces Gerbers, drill, placement or upload files. Stop for human
review before manufacturing.


## Mini v1.0 drill and power checks

`extract_mini.py` verifies pinned raw-source hashes, parses metric 3:3 drills,
traces EasyEDA schematic wires, and obtains the GKO outline without grid snapping.
`verify_mini.py --checks-only` independently reads actual native library and
board pads and checks all 105 contacts against the drill file. Without that flag
it writes the PNG/SVG overlay (Python 3.11 plus matplotlib).
`verify_power.py` uses KiCad Python to check continuous full-width supply and
return paths, and records the 3 A / 35 um / 10 C calculation and capacitor spacing.

The direct-power revision reroutes the signals with Freerouting 2.5.0 against
new locked power copper. The updated SES is checked in. Telemetry was disabled;
only PWM/EN/CS/SPI routes are imported. Existing manufacturing and assembled
mockup snapshots are explicitly marked historical; rebuild does not update them.
