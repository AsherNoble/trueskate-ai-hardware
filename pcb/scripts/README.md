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
session and then restores the two-layer stack and GND stitching. Rerun strict
checks afterwards. Changes to placement or pin assignments require a new routing
session. `generate.py` and its helper scripts are implementation tools; start
with `rebuild.py` rather than invoking each stage manually.

`update_review_docs.py` refreshes the single SH mapping table in `../README.md`
and the BOM diff. `freerouting.rb` pins the optional autorouter; no autorouter is
run by the review-export command. Archived four-layer/thermal tools are excluded
from this workflow.
