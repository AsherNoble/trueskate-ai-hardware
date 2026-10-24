# Six-axis edge connector carrier — review only

160 × 120 mm, **two layers, 1 oz copper on each side**. No board growth. Six columns at 25 mm pitch;
front is Y=0, back is Y=120. J21–J26 motor headers and J31–J36 encoder connectors
sit at the front. Minis are rotated 90° in-plane, component side up, never mirrored.
The Mini courtyard follows the tagged GKO outline plus 0.5 mm. Bulk and ceramic bodies are outside it; the measured minimum body gap is 2.9136 mm to the Mini outline (2.4138 mm to its courtyard).
J5 input, F1 fuse and J6 kill header occupy the back. Teensy USB faces the back;
first socket contacts are at Y=118.03. PJRC dimensions give 1.27 mm from first contact to PCB end plus 0.70 mm USB-shell projection, placing the USB end at Y=120.00. Verify the actual cable shell clearance.

Only J31–J36 (JST SM06B-SRSS-TB, side entry, mouth toward -Y) are JLC assembled.
Other fitted components are hand-soldered through-hole. The JST shell opening is
0.725 mm inside the front outline to retain copper-to-edge clearance.

## Encoder harness mapping

The single provisional SH contact-to-net table is in the [PCB README](../../pcb/README.md#verify-with-multimeter-against-as5048a-board).
Check the actual AS5048A board with a multimeter before using a harness. Change
`pcb/design/data/design.json:encoder_pin_order` to change all six assignments,
then regenerate, reroute and validate. `pcb/scripts/update_review_docs.py` refreshes
the README table and BOM diff.

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
there is no restart latch. See `review/checks/kill-state-review.json` for checks and bounds.

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

## Copper decision

**Two layers, 1 oz, by user decision. Copper/thermal qualification is stopped.**
The historical four-layer results remain in [copper-options.md](copper-options.md).
They do not qualify this two-layer board. The current five-board JLC quote is
**US$14.80**, excluding shipping, tax and assembly.

## Fuse and power routing

**fuse rated to the connected supply.**

F1 is **one Keystone 3557-2 complete holder**, JLC/LCSC **C352820**. One part includes
both clips and holds one standard ATO blade fuse. “2 in 1” means compatibility
with two fuse formats, not two separate holder parts. The BOM specifies no fuse
amperage; the replaceable fuse is separate from the holder. The earlier 12 A design target is not a qualification of the selected copper.

The custom footprint comes from Keystone's drawing: 13.47 × 3.40 mm hole centres,
four ≥1.60 mm holes (1.65 mm selected), two electrical pads with two legs each.
The original outer-layer power bus and Mini feeds are restored from checkpoint
`62ef1ea`'s conversion log. Both copper layers are nominal 35 µm. The bottom GND
pour extends to all available board area subject to the existing clearances;
the top GND pour is retained. Disconnected islands are removed automatically.
The independent geometry audit confirms one connected GND network and zero
floating regions. See [two-layer review](two-layer-ground.md).

## Encoder routing

Each encoder's SPI, CS, 3V3 and GND escape runs down the right/JST half of its
column. The bundles jog around the Mini power annuli, then join the shared rear
routing area behind the Minis. Autorouter exclusion areas protect the phase-side
corridors. The final native-copper audit reports any exception in `review/checks/layout-review.json`.
There are no column exceptions. GND stitching follows every SPI/CS bundle and
all four board edges: **347 total GND vias**, including 306 added to the baseline.
The two-layer layout does not have a dedicated unbroken reference plane.

## Populated assembly views

[Top](../../pcb/renders/populated-top.png),
[front perspective](../../pcb/renders/populated-perspective.png), and
[rear perspective](../../pcb/renders/populated-rear.png) show all six Minis, the
Teensy, single power receptacles and fuse assembly fitted to the current carrier.
Added module models are simplified; see [model assumptions](../../pcb/renders/README.md).

## Copper review

[Top copper](../../pcb/renders/copper/top-copper-review.svg) · [Bottom copper and GND fill](../../pcb/renders/copper/bottom-copper-review.svg) ·
[Ground connectivity and JLC quote](two-layer-ground.md)

## Review artifacts and rebuilding

- `renders/bare/top-review.png`, `renders/bare/3d-review.png`, `renders/bare/bottom-review.png`: native KiCad renders;
  plug-in modules, fuse holder/fuse, single power receptacles, external switch
  and cables are omitted.
- `bom/bom-review.csv`, `bom/bom-diff.md`: current BOM and changes from commit f5fce90.
- `review/drawings/schematic-review.pdf`, `review/drawings/mechanical-fit-review.pdf`, `review/drawings/net-guide-review.pdf`.
- `review/drawings/mini-drill-overlay.png`, `review/checks/mini-fit-report.json`: exact tagged Mini geometry.
- `review/checks/drc-review.json`, `review/checks/erc-review.json`, `review/checks/review-status.json`: validation evidence.
- [Relayout report](edge-layout.md): decisions and outstanding requirements.

Run `scripts/rebuild.py` with KiCad's Python to regenerate/import the frozen outer-layer
routing session, restore the two-layer/1 oz stack with `scripts/convert_two_layer.py`, and
add the two passes of `scripts/stitch_ground.py`. Run `scripts/export_review.py` with Python 3
and `reportlab`, `pypdf`, `Pillow`, and `shapely` installed
for strict checks and review exports. Changing placement or mapping requires a new
signal-routing session. Project-local Edge_ footprints preserve manufacturer pad,
courtyard and 3D geometry while moving crowded body silkscreen to fabrication layers.
No manufacturing exports are generated. Older `archive/fabrication/` and `archive/mockups/` files
are historical and do not describe this revision. The old `four-layer-*`,
`l2-ground-review.*` and `l3-power-review.*` files also describe the archived
four-layer checkpoint only.

Sources: [JST SH datasheet](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf),
[TI SN74LV125A](https://www.ti.com/lit/ds/symlink/sn74lv125a.pdf),
[PJRC timers](https://www.pjrc.com/teensy/td_pulse.html),
[PJRC dimensions](https://www.pjrc.com/teensy/dimensions.html),
[Keystone 3557-2](https://www.keyelco.com/product.cfm/product_id/296),
[Keystone dimensional drawing](https://www.keyelco.com/product-pdf.cfm?p=296),
[DRV8313 logic limits](https://www.ti.com/lit/ds/symlink/drv8313.pdf).
