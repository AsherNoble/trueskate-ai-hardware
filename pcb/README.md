# Six-axis edge connector carrier — review only

160 × 120 mm, **four layers**, JLC041622-3313, **2 oz outer/inner copper**. No board growth. Six columns at 25 mm pitch;
front is Y=0, back is Y=120. J21–J26 motor headers and J31–J36 encoder connectors
sit at the front. Minis are rotated 90° in-plane, component side up, never mirrored.
The Mini courtyard follows the tagged GKO outline plus 0.5 mm. Bulk and ceramic bodies are outside it; the measured minimum body gap is 2.9136 mm to the Mini outline (2.4138 mm to its courtyard).
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

U1/U2 are **SN74LV125AN, TI LV-A low-voltage CMOS**, PDIP-14. Their supply is
**Teensy USB-powered 3V3**. No Mini regulator output connects to this rail.

J6's normally-closed switch joins `EN_DISABLE` to GND. Opening it lets R1 pull
all six /OE inputs high. R21–R26 are the output pull-downs; R41–R46 bias the buffer
inputs. All are 10k, 5% or better. Every column has the same circuit:

| State | Buffer behavior | All six Mini EN lines |
|---|---|---|
| Teensy unpowered, 3V3=0 V | Ioff isolates outputs | R21–R26 hold low; conservative carrier EN ≤0.210 V |
| Teensy booting, valid 3.3 V, GPIO floating | R41–R46 pull inputs low; closed kill passes low, open kill gives high impedance | Low in either switch state |
| Kill switch open, even with GPIO high | /OE high; outputs high impedance | R21–R26 hold low, ≤0.210 V |

The Mini's own 10k R4 is in series with its three DRV8313 EN inputs. Including
5 µA buffer leakage, 3×5 µA driver-input leakage and resistor tolerances gives a
conservative downstream EN bound of **0.375 V**, below the conservative **0.6 V**
low-input limit. An actively driven low during boot has a lower bound ceiling of
0.265 V. These are datasheet DC calculations, not measured waveforms. They assume
intact grounds, populated pull-downs, no back-powering, carrier resistors ≤5% and
Mini R4 ≤10% tolerance. The supply transition between 0 and 2 V is outside the
buffer's guaranteed operating range; a glitch-free supply-ramp guarantee is not
established by this circuit or by ERC.

Kill inhibits EN, not 12 V. Reclosing permits the current firmware command;
there is no restart latch. See `kill-state-review.json` for checks and bounds.

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

## Fuse and 12 A copper

**fuse rated to the connected supply.**

F1 is **one Keystone 3557-2 complete holder**, JLC/LCSC **C352820**. One part includes
both clips and holds one standard ATO blade fuse. “2 in 1” means compatibility
with two fuse formats, not two separate holder parts. The BOM specifies no fuse
amperage; the replaceable fuse is separate from the holder. Keep the connected
supply within the carrier's 12 A design envelope.

The custom footprint comes from Keystone's drawing: 13.47 × 3.40 mm hole centres,
four ≥1.60 mm holes (1.65 mm selected), two electrical pads with two legs each.
All 12 V tracks are on L3 and reinforced by broad input/fused power areas.
L2 is one connected, unrouted GND plane. JLC specifies 70 µm finished outer copper
and 61 µm inner copper for this standard 2 oz stack. The 12 A target relies on
the planes, not the old track widths alone. See [four-layer review](../docs/pcb/four-layer.md).

## Encoder routing

Each encoder's SPI, CS, 3V3 and GND escape runs down the right/JST half of its
column. The bundles jog around the Mini power annuli, then join the shared rear
routing area behind the Minis. Autorouter exclusion areas protect the phase-side
corridors. The final native-copper audit reports any exception in `layout-review.json`.
There are no column exceptions. The filled L2 plane covers all SPI/CS/EN traces
across their width, except necessary insulating antipads at their own PTH/via
terminals. L4 is adjacent to the L3 power plane rather than directly to L2.

## Populated assembly views

[Top](assembly-review/populated-top.png),
[front perspective](assembly-review/populated-perspective.png), and
[rear perspective](assembly-review/populated-rear.png) show all six Minis, the
Teensy, single power receptacles and fuse assembly fitted to the current carrier.
Added module models are simplified; see [model assumptions](assembly-review/README.md).

## Inner copper review

[L2 solid GND](l2-ground-review.svg) · [L3 power](l3-power-review.svg) ·
[stackup and JLC price comparison](../docs/pcb/four-layer.md)

## Review artifacts and rebuilding

- `top-review.png`, `3d-review.png`, `bottom-review.png`: native KiCad renders;
  plug-in modules, fuse holder/fuse, single power receptacles, external switch
  and cables are omitted.
- `bom-review.csv`, `bom-diff.md`: current BOM and changes from commit f5fce90.
- `schematic-review.pdf`, `mechanical-fit-review.pdf`, `net-guide-review.pdf`.
- `mini-drill-overlay.png`, `mini-fit-report.json`: exact tagged Mini geometry.
- `drc-review.json`, `erc-review.json`, `review-status.json`: validation evidence.
- [Relayout report](../docs/pcb/edge-layout.md): decisions and outstanding requirements.

Run `rebuild.py` with KiCad's Python to regenerate/import the frozen outer-layer
routing session, then apply `convert_four_layer.py` with `stackup.json`; run `export_review.py` with the documented Python/reportlab environment
for strict checks and review exports. Changing placement or mapping requires a new
signal-routing session. Project-local Edge_ footprints preserve manufacturer pad,
courtyard and 3D geometry while moving crowded body silkscreen to fabrication layers.
No manufacturing exports are generated. Older `fabrication/` and `mockups/` files
are historical and do not describe this revision.

Sources: [JST SH datasheet](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf),
[TI SN74LV125A](https://www.ti.com/lit/ds/symlink/sn74lv125a.pdf),
[PJRC timers](https://www.pjrc.com/teensy/td_pulse.html),
[PJRC dimensions](https://www.pjrc.com/teensy/dimensions.html),
[Keystone 3557-2](https://www.keyelco.com/product.cfm/product_id/296),
[Keystone dimensional drawing](https://www.keyelco.com/product-pdf.cfm?p=296),
[DRV8313 logic limits](https://www.ti.com/lit/ds/symlink/drv8313.pdf).
