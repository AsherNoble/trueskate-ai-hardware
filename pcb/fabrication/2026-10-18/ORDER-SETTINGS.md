# JLCPCB order — TrueSkate main v1

Upload trueskate-main-v1-JLCPCB.zip intact at https://cart.jlcpcb.com/quote (Standard PCB/PCBA).

| Setting | Select |
|---|---|
| Base material | FR-4 |
| Layers | 2 |
| Dimensions | 160 × 120 mm (120 × 160 is equivalent) |
| Quantity | 5 recommended, or your preferred available quantity |
| Product type | Industrial/Consumer electronics |
| Different designs / delivery format | 1 / Single PCB |
| Thickness | 1.6 mm |
| PCB colour / silkscreen | Green / white |
| Material grade, if shown | Standard FR-4, TG135–140 |
| Surface finish | LeadFree HASL |
| Outer copper weight | 1 oz |
| Via covering | Tented, both sides |
| Minimum via hole / diameter, if asked | 0.3 mm / 0.7 mm |
| Electrical test | Flying Probe Fully Test / standard full electrical test |
| Impedance control | No |
| Gold fingers / castellated holes / edge plating | No |
| Mark on PCB | Remove Mark if offered (optional cosmetic choice) |
| PCB assembly / stencil | No / No |

Keep other special processes off/default. This is a bare board for hand soldering;
components and plug-in modules are purchased separately.
Before paying, check the uploaded Gerber preview: one rectangular 160 × 120 mm
board, two copper layers, readable labels, and mounting/component holes present.
Do not scale, mirror or panelise the upload.

The ZIP contains seven Gerber layers, job metadata, and separate plated/non-plated
Excellon drills. No BOM or placement files are needed for this bare-board order.
Fresh KiCad 10.0.6 ERC/DRC passed on 2026-10-18 with zero reported violations,
unconnected items or schematic parity issues. ERC retains the existing project's
ignored check types, listed in erc.json; DRC has no ignored checks. Source board
matches the reviewed hash and was not modified. ZIP CRC and layer/drill presence
were checked. JLCPCB's uploaded preview has not been checked here.

This export responds to the user's manufacturing-file request; it does not record
completion of the human electrical review in docs/pcb/hardware-check.md. The
board remains a prototype: six-motor current/thermal limits, fuse selection,
power sequencing and six-axis operation have not been bench validated. Existing
one-axis firmware is not ready to flash for this carrier.

References:
- https://jlcpcb.com/help/article/gerber-files-preparation
- https://jlcpcb.com/capabilities/pcb-capabilities/
- https://cart.jlcpcb.com/quote
