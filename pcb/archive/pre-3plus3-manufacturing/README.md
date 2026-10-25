# Current Gerber upload package

Upload **[trueskate-main-v1-2layer-1oz-JLCPCB.zip](trueskate-main-v1-2layer-1oz-JLCPCB.zip)**
as a single file to JLCPCB. The ZIP contains the current board's Gerbers and
separate plated/non-plated drill files. No upload or order was made here.

## Order settings

| Setting | Value |
|---|---|
| Board | FR-4, 160 × 120 mm, single PCB |
| Layers | 2 |
| Thickness | 1.6 mm |
| Copper | 1 oz on both sides |
| Solder mask / silkscreen | Green / white |
| Finish | Lead-free HASL |
| Via covering | Tented on both sides |
| Electrical test | Standard full flying-probe test |
| Impedance control | None |

The reference quote used five boards. The ZIP is for PCB fabrication; optional
component assembly uses separate BOM/placement uploads. Check that JLC detects
the 160 × 120 mm outline and two copper layers. Keep the original scale and orientation.

## Contents and checks

- Nine Gerbers: top/bottom copper, paste, mask and silkscreen, plus board outline.
- Two Excellon drill files: **721 plated holes, 4 non-plated holes**.
- Gerber job metadata.
- All twelve upload files are at the ZIP root, with no enclosing folder.

Fresh KiCad 10.0.6 ERC reports zero violations under the existing reviewed project
configuration; its four pre-existing ignored check types are listed in
[validation/erc.json](validation/erc.json). Strict DRC reports zero violations,
opens or schematic mismatches, with no ignored checks or exclusions.
All 725 exported hole positions/tool sizes match the native board within KiCad's
0.001 mm drill-coordinate rounding; maximum position difference is **0.000708 mm**.
The native board was not modified. ZIP contents and CRC were checked.

[manifest.json](manifest.json) records source commit, source PCB hash and export
hashes. [validation/](validation/) contains ERC/DRC, the native hole list, drill
report and drill maps. [preview/](preview/) contains independent Gerber-parser
copper/silkscreen/drill overlays, viewed from the top for both sides; these omit
solder mask so traces and via drills can be inspected.

The package describes the selected two-layer, 1 oz board. The earlier copper/
thermal evaluation remains stopped, as recorded in
[copper-options.md](../../docs/pcb/copper-options.md).

To regenerate: run `pcb/scripts/export_manufacturing.py` with Python 3.11 and the
installed KiCad 10 CLI/bundled Python. It rechecks ERC/DRC and hole geometry before
creating the ZIP. It does not upload files or place orders.
