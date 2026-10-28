# Six-axis edge connector carrier — review only

**150 × 140 mm, two layers, 1 oz each side.** Upper bank A2/A3/A5, lower A1/A4/A6; 35 mm pitch. Teensy horizontal with USB flush at the left edge and a clear 15 × 20 mm SD service area at its right end. Input, fuse, kill header and buffers occupy the right end. Mini geometry, pin map and SH mapping are unchanged. Q1 now adds fused high-side reverse-input protection; see the [protection/silkscreen revision](reverse-polarity-silkscreen.md). See the [3+3 report](3plus3-layout.md) for dimensions, measured gaps and limitations.

All carrier parts are hand soldered, including the J31–J36 JST SH connectors facing their respective long edges. The JSTs are SMD; other fitted parts are through-hole.

## Encoder harness mapping

The single provisional SH contact-to-net table is in the [PCB README](../../pcb/README.md#verify-with-multimeter-against-as5048a-board).
Check the actual AS5048A board with a multimeter before using a harness. Change
`pcb/design/data/design.json:encoder_pin_order` to change all six assignments,
then regenerate, reroute and validate. `pcb/scripts/update_review_docs.py` refreshes
the README table and BOM diff.

## Hardware kill and partial population

U1/U2 are **SN74HC125N, TI HC CMOS**, PDIP-14. Their supply is
**Teensy USB-powered 3V3**. No Mini regulator output connects to this rail.

J6's normally-closed switch joins `EN_DISABLE` to GND. Opening it lets R1 pull
all six /OE inputs high. R21–R26 are the output pull-downs; R41–R46 bias the buffer
inputs. All are 10k, 5% or better. Every column has the same circuit:

| State (12 V motor rail present) | Buffer behavior | All six Mini EN lines |
|---|---|---|
| (a) Teensy and buffer unpowered, 3V3=0 V | HC has no specified Ioff or powered-off high-impedance guarantee | R21–R26 pull toward GND, but low is **not guaranteed by the datasheet** |
| (b) Teensy booting, valid 3.3 V, GPIO floating | R41–R46 pull inputs low; closed kill passes low, open kill gives high impedance | Expected low in either switch state; DC estimates below |
| (c) Kill switch open, valid 3.3 V, even with GPIO high | R1 pulls /OE high; outputs high impedance | R21–R26 hold low; estimated carrier EN ≤0.210 V |

This is a TI **SN74HC125N, LCSC C2890** substitution, with the same DIP-14
footprint and pinout; no layout or net changes. Unlike the previous LV-A part,
HC does not specify powered-off isolation. Do not reuse the old 5 µA Ioff bound
at VCC=0. With 12 V present the Mini remains powered; its regulator output is
isolated from carrier 3V3, but its EN input leakage still reaches each EN net.
The output clamp-current absolute maximum is not a powered-off leakage guarantee.
Case (a), including an open kill switch with no buffer power, remains unverified.

For powered states, SCLS104F §6.5 gives IOZ ≤5 µA and input leakage ≤1 µA
at VCC=6 V, and VOL ≤0.1 V at 20 µA at the tabulated 2/4.5/6 V rails.
Applying those limits at 3.3 V is an engineering estimate (3.3 V has no separate
DC table row). R1 sees six /OE inputs: 6×1 µA×10.5k = 0.063 V maximum
pull-up drop. Each floating command input sees ≤0.0105 V from buffer leakage
alone; assume the Teensy adds no pull-up or material source leakage.

Each Mini has three DRV8313 EN inputs behind a 10k series R4. Using
3×5 µA driver leakage, 10k carrier pull-downs ±5%, and R4 ±10%:
carrier EN ≤(5+15) µA×10.5k = **0.210 V** in high impedance, and
downstream driver EN ≤0.210+15 µA×11k = **0.375 V**, below **0.6 V**.
For driven low, the buffer sinks at most 15 µA (the output pull-down reduces
the sink load), within the 20 µA VOL condition: downstream estimate **0.265 V**.
These are DC estimates, not bench measurements or a guarantee through boot ramps.
They assume intact grounds, populated bias resistors and no external back-powering.

**Overall re-verification is incomplete:** case (a) has no datasheet bound;
0<VCC<2 V and brownout behavior also remain unspecified. Bench qualification
must monitor all six carrier EN and downstream driver EN nodes with 12 V present:
unpowered Teensy/buffer with kill both closed and open; USB boot/power-down with
floating command pins; and kill opening with commands high. Check for excursions
above 0.6 V, including transient pulses. A sample measurement does not establish
a production powered-off guarantee. Firmware's no-PWM/disabled-boot policy does
not supply the missing HC isolation specification.

Kill inhibits EN, not 12 V. Reclosing permits the current firmware command;
there is no restart latch. See `review/checks/kill-state-review.json` for checks and bounds.

Every axis may be omitted: J1n, J2n, J3n, C1n, C2n, R2n, R3n and R4n are optional
as a column. Fit its EN pull-down with its Mini and its CS pull-up with its encoder.
Shared copper does not pass through optional parts. Shared Q1/D1/R2, U1/U2, C1/C2, R1, Teensy,
input/fuse and the NC loop must be fitted for operation. Firmware must address only
present encoders. The six-encoder nominal load is ~90 mA, within PJRC’s 250 mA recommended external 3.3 V allowance including the buffers/bias circuitry; this budget is accepted for v1.

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
**US$15.80**, excluding shipping, tax and assembly.

## Fuse and power routing

**fuse rated to the connected supply.**

F1 is **one Keystone 3557-2 complete holder**, JLC/LCSC **C352820**. One part includes
both clips and holds one standard ATO blade fuse. “2 in 1” means compatibility
with two fuse formats, not two separate holder parts. The BOM specifies no fuse
amperage; the replaceable fuse is separate from the holder. The earlier 12 A design target is not a qualification of the selected copper.

The custom footprint comes from Keystone's drawing: 13.47 × 3.40 mm hole centres,
four ≥1.60 mm holes (1.65 mm selected), two electrical pads with two legs each.
Power uses 12 mm shared backbones/trunk, 6 mm fuse/input paths, 2 mm Mini branches and 1 mm phases. These target shared 12 A and per-axis/phase 2.5 A; qualification remains stopped. GND fills both layers, with 389 stitches and one connected network. No floating ground regions remain. The user accepted gaps in continuous opposite-side GND reference; exact measured gaps and long bottom runs are documented in the [3+3 report](3plus3-layout.md).

## Encoder routing

All six bundles avoid their phase-side corridors; no column exceptions. Global JST side reverses for the rotated lower bank. Separation, rather than a universal ban on parallel geometry, is the routing objective.

## Populated assembly views

[Top](../../pcb/renders/populated-top.png),
[front perspective](../../pcb/renders/populated-perspective.png), and
[bottom view](../../pcb/renders/populated-bottom.png) show all six Minis, the
Teensy, single power receptacles and fuse assembly fitted to the current carrier.
Added module models are simplified; see [model assumptions](../../pcb/renders/README.md).

## Copper review

[Top copper](../../pcb/renders/copper/top-copper-review.svg) · [Bottom copper and GND fill](../../pcb/renders/copper/bottom-copper-review.svg) ·
[Ground connectivity and JLC quote](two-layer-ground.md)

## Review artifacts and rebuilding

- `renders/bare/top-review.png`, `renders/bare/3d-review.png`, `renders/bare/bottom-review.png`: native KiCad renders;
  plug-in modules, fuse holder/fuse, single power receptacles, external switch
  and cables are omitted.
- `bom/bom-review.csv`, `bom/bom-diff.md`: current BOM and changes from rollback commit 800ba4a.
- `review/drawings/schematic-review.pdf`, `review/drawings/mechanical-fit-review.pdf`, `review/drawings/net-guide-review.pdf`.
- `review/drawings/mini-drill-overlay.png`, `review/checks/mini-fit-report.json`: exact tagged Mini geometry.
- `review/checks/drc-review.json`, `review/checks/erc-review.json`, `review/checks/review-status.json`: validation evidence.
- [Relayout report](3plus3-layout.md): decisions and outstanding requirements.

Run `scripts/rebuild.py` with KiCad Python: generate placement/manual copper, import the frozen SES and recorded signal completions, trim redundant tails, fill and replay reviewed ground stitches. The old conversion/ground-finishing tools describe the earlier layout and are not part of this rebuild. Run `scripts/export_review.py` with Python plus ReportLab, pypdf, Pillow and Shapely for strict checks and review material. Run `scripts/export_manufacturing.py` for the validated current ZIP; no upload/order occurs. Historical files are under `pcb/archive/`.

Sources: [JST SH datasheet](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf),
[TI SN74HC125](https://www.ti.com/lit/ds/symlink/sn74hc125.pdf),
[PJRC timers](https://www.pjrc.com/teensy/td_pulse.html),
[PJRC dimensions](https://www.pjrc.com/teensy/dimensions.html),
[Keystone 3557-2](https://www.keyelco.com/product.cfm/product_id/296),
[Keystone dimensional drawing](https://www.keyelco.com/product-pdf.cfm?p=296),
[DRV8313 logic limits](https://www.ti.com/lit/ds/symlink/drv8313.pdf).

Current prototype decisions and the only outstanding items are in the [protection/silkscreen report](reverse-polarity-silkscreen.md). Q1 needs no heat sink below ~5 A continuous; charged-output reversal, inrush and surge tests are outside v1 scope. SPI/return paths are accepted for v1 with the documented clock policy.
