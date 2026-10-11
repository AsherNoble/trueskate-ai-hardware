# Carrier v1 bill of materials

A **bill of materials (BOM)** lists what to buy and where it goes. Everything
placed on this carrier is through-hole and hand soldered. No JLCPCB assembly,
SMD purchase list or factory-placement file is needed. The per-reference source
is [bom-review.csv](../../pcb/bom-review.csv).

| References | Qty | What to obtain | LCSC / part status | Budget USD |
|---|---:|---|---|---:|
| J1, J2 | 2 | Female 1x24 straight sockets, 2.54 mm pitch | Generic; match body and mating height | 3.00 |
| J11-J16 | 6 sets | Each: female 2x5 control + female 1x3 phase sockets, 2.54 mm | Verified Mini holes; matching-height pieces | 4.20 |
| J21-J26 | 6 | Male 1x3 phase headers, 2.54 mm | Generic; review contact current rating | 0.60 |
| J31-J36 | 6 | Female 1x6 breakout sockets, 2.54 mm | Generic; square pad is CLK | 3.00 |
| R21-R26 | 6 | 10k axial, 1/4 W, 5% or better, 7.62 mm pitch | Generic DIN0207-sized body | 0.30 |
| C11-C16 | 6 | Panasonic EEUFR1V102B, 1000 uF / 35 V, diameter 12.5 mm, pitch 5 mm | **C128476**, owned | 0.00 |
| C21-C26 | 6 | Vishay K104K10X7RF5UH5, 100 nF / 50 V, X7R, pitch 5 mm | **C2979769**, through-hole | 0.78 |
| J41-J46 | 6 | Phoenix MKDS 1/2-3.81, **1727010** | Selected MPN; no asserted LCSC equivalent | 15.00 |
| J5 | 1 | Phoenix MKDS 1.5/2-5.08, **1715721** | Selected MPN; pitch 5.08 mm | 2.00 |
| F1 holder | 1 | Schurter **0031.8201**, horizontal open 5x20 mm | **C3204125**, exact footprint | 1.80 |
| F1 cartridge | 1 + spares | 5x20 mm fuse with appropriate DC breaking rating | **Rating not finalized**; 3.15 A time-delay is a candidate | Extra |
| JP1-JP6 | 6 PCB features | Default OPEN; optional wire bridges only if reviewed | No component to buy | 0.00 |
| NT1 | 1 PCB feature | Ground star is already-connected copper | No component to buy | 0.00 |

**Board-part allowance: USD 30.68**, excluding owned capacitors. Allow roughly
USD 30-50 for carrier parts, fuse, power-wire pairs and hardware. These are
engineering allowances, not a distributor quotation. The ceramic listing was
checked at about USD 0.126 each in a small-quantity tier; purchase multiples may
require more than six. [LCSC ceramic listing](https://www.lcsc.com/product-detail/C2979769.html).

Bare PCB cost is additional and unquoted. A five-board 160 x 120 mm order is not
a tiny promotional board; use a provisional USD 20-50 batch allowance only,
plus shipping/tax, until a fabricator quotes the reviewed design. No design has
been uploaded or order prepared. Approximate initial cash allowance:
**USD 50-100 before shipping/tax**, assuming Teensy, Minis, encoders, breakout
boards, motors and large capacitors are owned. This is not the whole rig's
replacement cost.

There are 53 schematic references, seven of which are copper/optional bridge
features. Each Mini reference represents two sockets: 52 soldered physical
carrier pieces, plus fuse cartridge, wiring and mounting hardware. Use four M3
insulating spacers/screws. Have the reviewer approve the dimensions and complete
purchase list in [sourcing](sourcing.md).
