# PCB tools

All commands resolve paths from the script location, independent of the shell's
working directory. The native design is in `../design/`, purchasing files in
`../bom/`, rendered views in `../renders/`, and check results in `../review/`.

## Validate and export review files

Use Python 3.11+ with `reportlab`, `pypdf`, `Pillow` and `shapely` installed:

```sh
python3 /absolute/path/to/trueskate-ai-hardware/pcb/scripts/export_review.py --checks-only
python3 /absolute/path/to/trueskate-ai-hardware/pcb/scripts/export_review.py
```

The first command runs ERC, strict DRC and independent audits. The second also
refreshes review PDFs, bare-board renders and copper plots. These scripts use
the installed macOS KiCad 10 CLI and bundled Python paths; see
[toolchain notes](../../docs/pcb/tooling.md) for the exact local commands.

## Render the populated carrier

Run `render_assembly.py` with KiCad's bundled Python. It writes three populated
images to `../renders/`, a reusable visual model to `../renders/models/`, and
disposable PCB/log files to the ignored `../renders/.cache/` directory.

## Rebuild the native design

Run `rebuild.py` with KiCad's bundled Python **only when intentionally regenerating**
the board: it overwrites native design and route data. It uses the frozen signal
session plus `signal-completions.json`, trims fanout, then fills and replays the reviewed ground stitches. Rerun strict
checks afterwards. Changes to placement or pin assignments require a new routing
session. `generate.py` and its helper scripts are implementation tools; start
with `rebuild.py` rather than invoking each stage manually.

`update_review_docs.py` refreshes the single SH mapping table in `../README.md`
and the BOM diff. `freerouting.rb` pins the optional autorouter; no autorouter is
run by the review-export command. Archived four-layer/thermal tools are excluded
from this workflow.

## Export the manufacturing ZIP

Run `export_manufacturing.py` with Python 3.11. Fresh ERC/strict DRC, native hole
matching and ZIP integrity checks gate the output in `../manufacturing/`.
The script exports fabrication files only; it does not upload or order boards.

`layout_3plus3.py` defines placement. `complete_routes.py --apply` replays frozen clearance-checked completions; search mode needs NumPy/Shapely and fresh routing geometry. `audit_return_paths.py` records exact centreline reference gaps and the SVG map; the documented continuous-plane requirement is relaxed by user decision.

`apply_silkscreen.py` runs at the end of rebuild. `verify_silkscreen.py` checks required strings and text/module bounds; strict DRC additionally checks copper/mask/edge clearance. `verify_protection.py` checks Q1 G/D/S, D1 K/A and gate pull-down topology. Q1 lead escapes use parallel top/bottom copper and eight reviewed power vias, separately from GND stitching.

`export_assembly.py` exports the six-JST JLC BOM/CPL without saving the board, then runs `compare_assembly.py` for bare/JST/full-scope comparison. Full-scope files are NOT upload files while stocked compatible parts and mechanical placements remain unresolved.

Current selected export mode is **bare-pcb**: no factory assembly, no default JLC BOM/CPL. `export_assembly.py` emits a hand-assembly BOM; optional comparison files are retained separately.
