# Six-axis edge connector carrier — review only

160 × 120 mm, two layers, **2 oz copper**. No board growth. Six columns at 25 mm pitch;
front is Y=0, back is Y=120. J21–J26 motor headers and J31–J36 encoder connectors
sit at the front. Minis are rotated 90° in-plane, component side up, never mirrored.
Bulk/ceramic capacitors sit immediately behind each Mini, near its power contacts.
J5 input, F1 fuse and J6 kill header occupy the back. Teensy USB faces the back;
first socket contacts are at Y=118.03. PJRC dimensions give 1.27 mm from first contact to PCB end plus 0.70 mm USB-shell projection, placing the USB end at Y=120.00. Verify the actual cable shell clearance.

Only J31–J36 (JST SM06B-SRSS-TB, side entry, mouth toward -Y) are JLC assembled.
Other fitted components are hand-soldered through-hole. The JST shell opening is
0.725 mm inside the front outline to retain copper-to-edge clearance.

## VERIFY WITH MULTIMETER AGAINST AS5048A BOARD

**Provisional harness assignment, NOT a verified AS5048A pinout.** Connector contact
numbers are the JST datasheet/footprint numbers, not left-to-right wire colors.
Check continuity with power disconnected from every harness contact to the AS5048A
board signal/power pads. Check which mating face is being viewed; do not infer
orientation from cable colors or the old 1×6 adapter. Do not power an unverified cable.

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

Change **only `design.json:encoder_pin_order`** to change the electrical assignment.
`generate.py` applies it to every connector using global net labels; reroute and rerun
checks after changing it. `update_review_docs.py` refreshes this table and the BOM diff.
The previous adapter-board pin-order confirmation does not verify this SH cable.

## Hardware kill and partial population

J6 connects a normally-closed switch between `EN_DISABLE` and GND. Closed permits
Teensy EN commands through U1/U2 (SN74LV125AN, powered by 3.3 V). Open lets R1 pull
all six /OE inputs high: outputs become high impedance and R21–R26 pull every Mini
EN low, even with Teensy outputs stuck high. R41–R46 bias undriven buffer inputs low.
Unused buffer inputs are tied off; their outputs are unused. C1/C2 bypass the buffers.
The Ioff feature prevents buffer output backfeed when its supply is absent.

Kill removes enable, **not 12 V**. Reclosing permits the current firmware command;
there is no restart latch. Bench-test power sequencing and the actual Mini response.

Every axis may be omitted: J1n, J2n, J3n, C1n, C2n, R2n, R3n and R4n are optional
as a column. Fit its EN pull-down with its Mini and its CS pull-up with its encoder.
Shared copper does not pass through optional parts. Shared U1/U2, C1/C2, R1, Teensy,
input/fuse and the NC loop must be fitted for operation. Firmware must address only
present encoders. The USB-powered 3.3 V rail still needs a six-encoder load check.

## Unchanged Teensy allocation

| Axis | PWM pins | FlexPWM submodules | EN | CS |
|---|---|---|---|---|
| 1 | 4, 5, 6 | 2.0, 2.1, 2.2 | 16 | 26 |
| 2 | 2, 22, 23 | 4.2, 4.0, 4.1 | 17 | 27 |
| 3 | 7, 36, 29 | 1.3, 2.3, 3.1 | 20 | 32 |
| 4 | 24, 0, 25 | 1.2, 1.1, 1.3 | 21 | 38 |
| 5 | 3, 33, 37 | 4.2, 2.0, 2.3 | 30 | 39 |
| 6 | 8, 9, 28 | 1.3, 2.2, 3.1 | 31 | 40 |

Axes 1–3 use mutually distinct submodules; 4–6 share some of those resources.
They are not six independently frequency-programmable motor groups. SPI remains
11/12/13. **No pins reassigned.** Existing firmware is still the earlier bench code.

## Review artifacts and rebuilding

- `top-review.png`, `3d-review.png`, `bottom-review.png`: native KiCad renders;
  plug-in modules, external switch and cables are omitted.
- `bom-review.csv`, `bom-diff.md`: current BOM and changes from commit 1d2f9e6.
- `schematic-review.pdf`, `mechanical-fit-review.pdf`, `net-guide-review.pdf`.
- `mini-drill-overlay.png`, `mini-fit-report.json`: exact tagged Mini geometry.
- `drc-review.json`, `erc-review.json`, `review-status.json`: validation evidence.
- [Relayout report](../docs/pcb/edge-layout.md): decisions and outstanding requirements.

Run `rebuild.py` with KiCad's Python to regenerate and import the frozen routing
session; run `export_review.py` with the documented Python/reportlab environment
for strict checks and review exports. Changing placement or mapping requires a new
signal-routing session. Project-local Edge_ footprints preserve manufacturer pad,
courtyard and 3D geometry while moving crowded body silkscreen to fabrication layers.
No manufacturing exports are generated. Older `fabrication/` and `mockups/` files
are historical and do not describe this revision.

Sources: [JST SH datasheet](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf),
[TI SN74LV125A](https://www.ti.com/lit/ds/symlink/sn74lv125a.pdf),
[PJRC timers](https://www.pjrc.com/teensy/td_pulse.html),
[PJRC dimensions](https://www.pjrc.com/teensy/dimensions.html),
[Littelfuse FLR PCB](https://www.littelfuse.com/~/media/commercial-vehicle/datasheets/automotive-fuse-holders/ato/littelfuse-fuse-holder-ato-flr-pcb-datasheet.pdf).
