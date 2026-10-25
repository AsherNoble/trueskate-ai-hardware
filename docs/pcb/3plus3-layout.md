> Placement report for the 3+3 base revision. Power, BOM and silkscreen are superseded by the [current reverse-polarity revision](reverse-polarity-silkscreen.md); use current machine-readable reports for hashes and copper-region counts.

# 3+3 carrier relayout

Current board: **150 × 140 × 1.6 mm, two layers, 1 oz each side**. Rollback checkpoint: `800ba4a` (includes the user's modified top render). No Teensy pins or electrical nets were reassigned. The verified Mini library is byte-for-byte unchanged.

## Placement and SD access

Top view: upper bank **A2, A3, A5**; lower bank **A1, A4, A6**, left to right. Axis pitch is 35 mm. Lower columns rotate 180° in-plane; no Mini is mirrored. Both cable connectors face their bank's board edge. Teensy is horizontal, USB shell flush at X=0. Input terminal and kill header face the right edge; F1 and both kill buffers are nearby.

150 × 100 mm was the starting target. Opposing the existing Mini/capacitor groups, preserving their courtyard gaps, keeping the 12 mm bus and providing the Teensy corridor required 140 mm depth in the implemented arrangement. This is a chosen clean layout, not a proof that 150 × 100 mm is impossible. Growth was accepted because the five-board price premium is only **US$3.10**.

Four Ø3.2 mm M3 holes are at **(4,4), (146,4), (146,136), (4,136) mm**. Reserve the standard M3 mounting footprint for screw heads/standoffs; check the enclosure and chosen hardware physically.

The Teensy PCB extends X=0.70…61.66 mm, Y=61.11…78.89 mm. Its first socket pads are X=1.97 mm at Y=62.38/77.62 mm. Its SD end faces right, into the corridor. The reserved card-service area is **X=61.66…81.66 mm, Y=62.50…77.50 mm**: **20 mm insertion/removal depth × 15 mm width**. It is clear of every other component courtyard, with a conservative **14.5 mm minimum separation to their bounding boxes**. Components are excluded regardless of height. The cap/Mini minimum body gap remains **2.9136 mm to the board outline, 2.4138 mm to the +0.5 mm courtyard**.

The 15 × 20 mm allowance is a design envelope, not a manufacturer socket specification. The render corrects the previous Teensy PCB offset and depicts an illustrative partly withdrawn 15 × 11 × 1 mm card. Actual socket revision, seated protrusion, insertion stroke, header height and fingertip access still need a physical check. [Dimensioned access illustration](../../pcb/review/drawings/sd-access.svg), [native mechanical drawing](../../pcb/review/drawings/mechanical-fit-review.pdf).

## Crossings and routing

The placement estimate was **11 per-axis row mismatches + three shared SPI signals = 14**. EN commands route through the right-end buffers, so this is not a physical route count. The finished board has **25 crossings of Y=70 mm by 20 distinct signal/supply nets**, including buffer wiring. Under the actual Teensy PCB, **2 crossing events are on top and 9 on bottom**. [Exact crossing coordinates](../../pcb/review/checks/bank-crossings.json).

All six encoder escapes remain on the JST side and avoid the protected phase corridors; there are no column exceptions. The lower bank's JST side is left in the global top view because those columns rotate. Phase and encoder corridors can run in the same direction at separation; the accepted rule avoids close parallel coupling rather than prohibiting all parallel geometry.

Shared fused-power bank backbones/common trunk are **12 mm wide**; fuse/input conductors are **6 mm**, Mini supply branches **2 mm**, ceramic taps **0.6 mm**, and all phase paths **1 mm**. Nominal copper is 35 µm. Shared 12 A and per-Mini/per-phase 2.5 A remain design targets. Ground is poured on both sides, with **389 0.7/0.3 mm GND stitches** and automatic island removal. Independent polygon/contact connectivity finds one GND network, zero floating regions, and 33/30 interconnected top/bottom regions. Maximum sampled stitch distance: **9.600 mm along SPI/CS**, **2.062 mm at edge targets**.

**User decision: relax continuous-bottom-GND coverage for this two-layer design and document measured gaps.** A top-only SPI/EN routing attempt left 48 connections unrouted; the completed two-layer design uses substantial bottom routing, rather than only short jumpers. This attempt is not a proof that no better two-layer route exists. GND connectivity does not establish continuous reference coverage.

### Measured reference gaps

Total bottom SPI/CS/EN/EN-command/OE trace length is **1703.829 mm**. The summed routed centreline lacking opposite-layer GND, outside own pad/via transitions, is **1560.973 mm**. These are summed conductor lengths, not one continuous gap. The audit includes EN command and /OE nets conservatively, in addition to SPI, CS and Mini EN.

| Net | Top length (mm) | Bottom length (mm) | Length without opposite-side GND (mm) |
|---|---:|---:|---:|
| `A1_CS` | 94.775 | 0.000 | 43.429 |
| `A1_EN` | 75.570 | 92.260 | 74.775 |
| `A1_EN_CMD` | 93.693 | 28.938 | 34.505 |
| `A2_CS` | 43.739 | 46.705 | 42.673 |
| `A2_EN` | 115.600 | 68.182 | 71.608 |
| `A2_EN_CMD` | 96.223 | 25.514 | 40.177 |
| `A3_CS` | 41.951 | 41.334 | 46.605 |
| `A3_EN` | 63.894 | 88.250 | 75.725 |
| `A3_EN_CMD` | 114.182 | 34.630 | 53.971 |
| `A4_CS` | 39.296 | 42.167 | 44.241 |
| `A4_EN` | 43.380 | 65.997 | 63.756 |
| `A4_EN_CMD` | 98.334 | 48.987 | 35.304 |
| `A5_CS` | 88.357 | 27.417 | 45.736 |
| `A5_EN` | 0.000 | 158.744 | 42.776 |
| `A5_EN_CMD` | 80.893 | 46.904 | 31.727 |
| `A6_CS` | 39.191 | 62.298 | 53.402 |
| `A6_EN` | 36.727 | 41.407 | 29.897 |
| `A6_EN_CMD` | 0.000 | 118.954 | 38.209 |
| `EN_DISABLE` | 42.658 | 57.597 | 10.183 |
| `SPI_MISO` | 497.715 | 200.783 | 225.925 |
| `SPI_MOSI` | 350.470 | 232.511 | 230.389 |
| `SPI_SCK` | 409.520 | 174.250 | 225.960 |

Method: intersect each routed centreline with the actual filled opposite-layer GND geometry. Exclude only that net's own PTH/via transition radius plus 0.3 mm; apply 0.002 mm numerical tolerance. Exact gap paths and source-board hash are in [return-path-review.json](../../pcb/review/checks/return-path-review.json); [red gap map](../../pcb/renders/copper/return-path-gaps.svg). This centreline audit does not prove ground width beside a route, impedance, EMC performance or acceptable SPI timing. Bench signal-integrity testing remains necessary.

Ground-via seeding is a heuristic and can select different legal points between runs. The rebuild therefore replays the **389 reviewed via positions** from `ground-stitching.json`, just as it replays the frozen signal routes. Reseeding is an explicit routing change requiring fresh checks.

## Validation and unresolved checks

ERC and strict DRC pass: zero violations, opens or schematic-parity issues, no DRC exclusions/ignored checks. Existing reviewed ERC ignore categories are retained. All 292 schematic contacts agree with the PCB; the six Mini instances match the tagged source drill coordinates with **0.000000 mm maximum position error**. Kill DC-state and 8192 partial-population/command/loop cases pass the existing static checks. No supply-ramp guarantee is added.

BOM: **no additions, removals, value/quantity or assembly changes** versus `800ba4a`. F1 remains one complete Keystone 3557-2 (C352820); fuse amperage remains unspecified. Only the six JST headers are JLC assembled.

Remaining physical/electrical checks: actual SD socket/card/header fit; enclosure, cable-shell and mounting hardware fit; provisional encoder harness contact order; six-encoder 3.3 V load and SPI signal integrity; buffer supply-ramp behavior between 0 and 2 V. Copper/thermal qualification remains stopped; no per-neck temperature, current-capacity or supply-drop qualification is claimed. The historical copper report is unchanged.

## JLC price and release

Live quote, 2026-10-25, five bare FR4 boards, two layers, 1 oz, 1.6 mm, green mask/white silk, tented vias, lead-free HASL: **US$15.80 at 150 × 140 mm**, versus **US$12.70 at 150 × 100 mm**. Excludes shipping, tax and assembly. [Quote evidence](../../pcb/sources/jlc-3plus3/quote.json), [screenshot](../../pcb/sources/jlc-3plus3/150x140.png), [JLC quote tool](https://cart.jlcpcb.com/quote). No order or upload was made.

[Current manufacturing ZIP](../../pcb/manufacturing/trueskate-main-v1-2layer-1oz-JLCPCB.zip) supersedes the 160 × 120 mm release. Export checks compare every native drill hole and validate ZIP integrity. Manufacturing checks do not close the physical and signal-integrity limitations above.
