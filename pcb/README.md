# TrueSkate carrier PCB

**Current board: 150 × 140 mm, two layers, 1 oz copper.** ERC and strict DRC pass.
The most recent JLC quote is **US$15.80 for five bare boards**, excluding shipping,
tax and assembly. Copper/thermal qualification is stopped.

[Current protection and silkscreen revision](../docs/pcb/reverse-polarity-silkscreen.md) · [3+3 layout and SD access](../docs/pcb/3plus3-layout.md).

**Q1 needs no heat sink below ~5 A continuous.** Normal sustained load is a few amps on the current-limited bench PSU; 12 A is a copper-sizing worst case. [Accepted v1 operating decisions](../docs/pcb/reverse-polarity-silkscreen.md).

PJRC's recommended external 3.3 V allowance is **250 mA**. Six nominal ~15 mA encoders total ~90 mA, leaving ~160 mA for buffers/bias circuitry. Return-path gaps are **accepted for v1**; retain the measured audit and use 1–4 MHz SPI, lower if reads glitch. No firmware change is included here.

## Outstanding

1. **1:1 print fit check** (user).
2. **SH pin order verification** by multimeter (user); TODO labels remain until the verified order is provided.
3. **Optional human review.**

## Open these first

| I want to… | Open |
|---|---|
| Upload Gerbers to JLCPCB | [Current manufacturing ZIP](manufacturing/trueskate-main-v1-2layer-1oz-JLCPCB.zip) · [Bare-PCB settings and hand-assembly BOM](manufacturing/README.md) |
| Edit the board or schematic in KiCad | [trueskate-main-v1.kicad_pro](design/trueskate-main-v1.kicad_pro) |
| See the assembled board | [Perspective](renders/populated-perspective.png) · [Top](renders/populated-top.png) · [Bottom](renders/populated-bottom.png) |
| Buy parts | [BOM](bom/bom-review.csv) · [BOM changes](bom/bom-diff.md) |
| Understand wiring and pin assignments | [Net guide](review/drawings/net-guide-review.pdf) · [Net documentation](../docs/pcb/nets.md) |
| Print a 1:1 fit template | [Mechanical fit drawing](review/drawings/mechanical-fit-review.pdf) |
| Review the schematic | [Schematic PDF](review/drawings/schematic-review.pdf) |
| Check the copper | [Top](renders/copper/top-copper-review.svg) · [Bottom](renders/copper/bottom-copper-review.svg) |
| Read assembly, kill-switch and population details | [Carrier notes](../docs/pcb/carrier.md) |
| See what was checked | [Review status](review/checks/review-status.json) · [Ground/layout report](../docs/pcb/two-layer-ground.md) |

## Folder guide

| Folder | Contents |
|---|---|
| `design/` | Current KiCad project, board, schematics and local libraries. `data/` holds generator inputs and route records; `routing/` holds the frozen signal-routing exchange. |
| `bom/` | Current purchasing list and BOM changes. |
| `manufacturing/` | Current Gerber/drill ZIP, order settings and export checks. |
| `renders/` | Current populated images, bare-board views and copper plots. |
| `review/` | Printable PDFs and drill overlay in `drawings/`; machine-readable checks in `checks/`. |
| `scripts/` | Generation, validation and rendering tools; [commands](scripts/README.md). |
| `sources/` | Manufacturer references, verified Mini geometry and the current JLC quote. |
| `archive/` | Superseded fabrication, mockups, four-layer views and the stopped copper evaluation. |

Current design and review files are outside `archive/`. Historical manufacturing
packages in the archive do not describe this board.

## VERIFY WITH MULTIMETER AGAINST AS5048A BOARD

**Provisional harness assignment.** Contact numbers are JST footprint numbers,
not wire colours. Verify continuity and connector viewing direction against the
actual AS5048A board before powering a harness.

<!-- SH_TABLE_START -->
| SH contact | Proposed signal | Carrier net (axis n) |
|---|---|---|
| 1 | CLK | `SPI_SCK` |
| 2 | MISO | `SPI_MISO` |
| 3 | MOSI | `SPI_MOSI` |
| 4 | CSn | `An_CS` |
| 5 | 3V3 | `3V3` |
| 6 | GND | `GND` |
<!-- SH_TABLE_END -->

Change `design/data/design.json:encoder_pin_order` in one place to update all six
connectors, then regenerate/reroute and rerun the checks. Only J31–J36 JST headers
are hand soldered; other fitted components are hand-soldered through-hole.

**Fuse rated to the connected supply.** See [carrier notes](../docs/pcb/carrier.md)
for the hardware kill circuit, partial population and remaining physical checks.

Assembly choices and cost comparison: [bare PCB / JST-only / full-carrier feasibility](manufacturing/README.md#assembly-and-cost-comparison-five-carriers). Full carrier is blocked by stocked-part availability; its files are explicitly planning-only.

Selected build: **bare PCB, all parts hand soldered including J31–J36**. Upload only the fabrication ZIP and leave PCB assembly off.
