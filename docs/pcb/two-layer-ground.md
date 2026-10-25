# Current two-layer ground review

Current board: **150 × 140 mm, 1 oz each side**. Both sides have GND pour with automatic island removal. **389 ground stitches**, Ø0.7/0.3 mm. Every retained region belongs to one cross-layer network; no floating regions. Sampled maximum stitch distance: SPI/CS 9.600 mm, perimeter 2.062 mm.

The user explicitly relaxed continuous-bottom-GND coverage for the 3+3 two-layer design. Routing includes substantial bottom SPI/EN runs and measured opposite-ground gaps. See the [full 3+3 report and per-net table](3plus3-layout.md), [exact gap paths](../../pcb/review/checks/return-path-review.json), [gap map](../../pcb/renders/copper/return-path-gaps.svg) and [connectivity audit](../../pcb/review/checks/ground-connectivity-review.json).

Copper/thermal qualification remains stopped. ERC and strict DRC pass; neither establishes thermal performance, impedance or signal integrity. Five-board JLC quote: **US$15.80**, excluding shipping, tax and assembly. Current manufacturing files are linked from the [PCB index](../../pcb/README.md).
