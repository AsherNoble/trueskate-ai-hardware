> Historical review of checkpoint `62ef1ea`. Superseded by the two-layer, 1 oz decision; see [current layout](two-layer-ground.md).

# Four-layer carrier review

The board remains **160 × 120 mm**. All **62 footprint identities, positions,
rotations, pad positions, sizes, drills and nets are unchanged** from `fbaa70a`.
The Mini clearances, pin map, component BOM and connector locations are unchanged.

## Layer assignment

| Layer | Use |
|---|---|
| L1 / F.Cu | Components and signals, with GND fill |
| L2 / In1.Cu | One connected solid GND plane; no tracks |
| L3 / In2.Cu | 12V_IN and 12V_FUSED, isolated by clearance |
| L4 / B.Cu | Signals, with GND fill |

All 51 existing 12 V track segments move to L3. Broad solid-connected power
areas reinforce them; no small signal vias carry the supply. Through-hole pad
annuli necessarily remain on the outer layers, but there are **no outer 12 V
tracks or pours**. The input and fused areas remain separate, so F1 is not bypassed.
New custom DRC rules enforce these layer assignments.

L2 has no intentional splits or routed traces. The filled-copper audit checks
all 721 SPI/CS/EN trace segments at their centre and both edges every 0.025 mm.
Only each net's own PTH/via terminal antipads are exempt: insulating clearances
there are mandatory and cannot be filled with GND. There are no other uncovered
samples. Unused internal signal-via annuli are removed; footprint pad stacks
and outer geometry remain unchanged.

L4 is physically adjacent to L3 power, not L2. The prescribed stack does not give
L4 a directly adjacent GND reference; the verified L2 coverage is in projection.

## JLC standard stackup

**JLC041622-3313**, nominal **1.6 mm**, **2 oz outer and inner copper**. This is a
standard option in JLC's selector. Heavy copper retains the existing current
design target instead of silently switching to the default 0.5 oz inner copper.

| Construction | Thickness |
|---|---:|
| F.Cu | 0.070 mm |
| 3313 prepreg ×2 | 0.107 + 0.0765 mm |
| In1.Cu | 0.061 mm |
| FR4 core | 0.960 mm |
| In2.Cu | 0.061 mm |
| 3313 prepreg ×2 | 0.0765 + 0.107 mm |
| B.Cu | 0.070 mm |

The manufacturer construction totals 1.589 mm before mask, within nominal 1.6 mm.
Prepreg Dk is 4.1 and core Dk 4.6. `pcb/design/data/stackup.json` records the construction.
[JLC standard stackup selector](https://jlcpcb.com/impedance),
[archived selector text](../../pcb/archive/jlc-four-layer/standard-stackup-selector.txt).

The 12 A bus target is retained with broad L3 planes and direct pad connections.
At JLC's stated 61 µm inner copper, the conservative IPC-2221 internal uniform
strip references are 13.809 mm for 12 A and 2.040 mm for 3 A at 10 °C rise. The old
12 mm/2 mm tracks alone are insufficient under that model; the plane areas carry
current in parallel. This strip reference is not a plane thermal simulation.

## Five-board price comparison

Live public quote retrieved 25 October 2026 (Australia/Sydney). Both quotes:
160 × 120 mm, quantity 5, one design, individual PCBs, FR4, 1.6 mm, green mask,
white silk, lead-free HASL, standard build time, no assembly or stencil.

| Build | Copper | Five boards, USD | Per board |
|---|---|---:|---:|
| Previous 2-layer carrier | 2 oz outer | **$54.30** | $10.86 |
| New 4-layer carrier | 2 oz outer / 2 oz inner | **$122.13** | $24.43 |

Difference: **$67.83 per batch** (+124.9%). Prices exclude shipping, tax, coupons,
and the advertised JLCONE app discount. The configurator's default shipping
estimate was for another destination and is deliberately excluded. No design
files were uploaded and no order/cart entry was created.

[JLC quote calculator](https://cart.jlcpcb.com/quote),
[two-layer quote](../../pcb/archive/jlc-four-layer/quote-2layer.png),
[four-layer quote](../../pcb/archive/jlc-four-layer/quote-4layer.png).

## Review images

[L2 GND](../../pcb/archive/four-layer/l2-ground-review.png), [L3 power](../../pcb/archive/four-layer/l3-power-review.png),
[populated top](../../pcb/renders/populated-top.png),
[populated perspective](../../pcb/renders/populated-perspective.png).

## Validation and remaining items

Strict ERC/DRC reports and `archive/four-layer/four-layer-review.json` are regenerated with the native
board. No DRC exemptions or ignored checks are introduced. The separate
`design/data/placement-baseline.json` records the preserved geometry.

The existing AS5048A harness verification, physical socket/cable fit checks and
kill-buffer supply-ramp limitation remain. None is changed by the stack conversion.
