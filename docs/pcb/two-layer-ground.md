# Two-layer, 1 oz carrier

Decision: retain **160 × 120 mm**, use **two layers with 1 oz copper on both
sides**, and stop copper/thermal qualification. The earlier calculations are
preserved in [copper-options.md](copper-options.md) as historical four-layer
results; they are not a qualification of this board.

## Baseline and routing

`62ef1ea` was a four-layer checkpoint. It was used as the starting point, then
converted back to two layers. Its recorded outer-layer power routes were
restored, including overlapping top/bottom input tracks as separate conductors.
The independent routing audit confirms all **299 locked manual segments** match
the original route records. No signal pin assignments changed.

All **62 footprint identities, placements, orientations and pad geometries**
match the checkpoint's placement baseline. The 160 × 120 mm outline is unchanged.
F.Cu/B.Cu are nominal **35 µm** each; nominal total thickness is 1.6 mm.
No inner copper layers remain. The BOM is unchanged.

## GND fill and stitching

Both GND zone outlines cover the full board. Native copper-to-edge, hole, pad and
track clearances determine the usable fill. Bottom GND occupies all available
space subject to those rules. Disconnected-island removal is enabled on both
zones. Ground regions that connect through the opposite layer are retained.

There are **347 GND stitching vias**: 41 retained from the baseline and **306
added**. They are 0.7 mm diameter / 0.3 mm drill, locked and recorded in
[ground-stitching.json](../../pcb/ground-stitching.json). Stitch placement checks
clearance against non-GND copper and holes on both sides; it does not alter
signal, phase or power routes.

- All four edges are covered by targets at 8 mm pitch. The greatest target-to-via
  distance is **5.025 mm**, allowing for edge connectors and mounting holes.
- Every segment of SCK, MISO, MOSI and all six CS routes is sampled at intervals
  of at most 3 mm. All six front-column SPI bundles have nearby stitching; their
  greatest sampled distance to a stitch is **4.431 mm**.
- The crowded shared rear fanout has a larger maximum distance of **10.146 mm**.
  Clearance rules are preserved there. These measurements are proximity checks,
  not an impedance or return-path guarantee.

The independent filled-copper graph audit unions actual GND zones, pad outlines,
tracks and via copper on each side, then joins them through every plated GND
contact. Result: **one connected GND network, zero floating regions**. There are
32 connected copper regions on top and 35 on bottom before cross-layer joins;
they are all parts of that one electrical network. KiCad also reports zero
isolated zone islands and zero opens.

Bottom GND copper area in that model is **15,115 mm²**; top is **10,990 mm²**.
Plated contacts are represented as solid electrical nodes in this area figure,
so it is not a fabrication copper-area measurement.

[Native geometry audit](../../pcb/ground-connectivity-review.json) ·
[Stitch coverage measurements](../../pcb/two-layer-ground-review.json) ·
[Top copper](../../pcb/top-copper-review.svg) ·
[Bottom copper](../../pcb/bottom-copper-review.svg).

## Checks

KiCad **10.0.6** ERC and strict DRC pass:

- ERC: zero violations.
- DRC: all severities, all track errors and schematic parity enabled, zones
  refilled; zero violations, opens, parity issues, exclusions or ignored checks.
- Independent netlist, original routing, placement, Mini drill, courtyard,
  encoder-lane, kill-state and ground-connectivity checks pass.

The existing harness/physical-fit and supply-ramp notes remain unchanged.
Copper/thermal qualification is stopped; it is not part of this pass claim.
No manufacturing exports or PCB orders were created.

[Check evidence](../../pcb/review-status.json) ·
[Top render](../../pcb/top-review.png) ·
[Bottom render](../../pcb/bottom-review.png) ·
[Populated perspective](../../pcb/assembly-review/populated-perspective.png).

## JLC price

Live public quote on **2026-10-25**: **US$14.80 for five boards**.

160 × 120 mm; 2 layers; 1.6 mm; 1 oz; green solder mask; white silkscreen;
lead-free HASL; standard two-day manufacture. Board price excludes shipping,
tax and assembly. The quote was read without uploading the design or placing
an order.

[Quote screenshot](../../pcb/sources/jlc-two-layer-1oz/quote.png) ·
[Quote settings and provenance](../../pcb/sources/jlc-two-layer-1oz/provenance.json).
