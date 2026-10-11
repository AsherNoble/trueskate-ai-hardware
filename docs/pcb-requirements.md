# PCB requirements: passive carrier v1

This replaces the earlier full-feature draft after the user's scope reduction.
The old draft is recoverable at local checkpoint `36e9dca`. Requirements live
here; `docs/pcb/requirements.md` and `pcb/requirements.md` are not separate files
in this checkout.

## In scope

- Main board only: six GM3506 / SimpleFOC Mini v1.0 / AS5048A axes, index and
  middle fingers, each with two curl motors and one splay motor.
- Teensy 4.1 and all six Minis in female through-hole sockets. Preserve the
  source-derived, user-fit-verified Mini socket hole geometry.
- Teensy powered by USB ONLY. VIN socket contact electrically unconnected.
  No buck, external logic supply, USB/VIN isolation or Teensy modification.
- Six female 1x6, 2.54 mm encoder sockets for existing JST breakout boards.
  From the verified square pad: **1 CLK, 2 MISO, 3 MOSI, 4 CSn, 5 3V3, 6 GND**.
  Mark contact 1 on silkscreen.
- Six male 1x3 phase headers for existing female Dupont motor leads.
- Six approved short paired power wires from carrier screw terminals to each
  Mini's existing terminals; no rigid socket for its off-grid power pads.
- Per axis: owned Panasonic EEUFR1V102B 1000 uF / 35 V plus a through-hole
  100 nF ceramic beside the local Mini supply terminal.
- 12 V input screw terminal and through-hole 5x20 mm fuse holder. Cartridge
  selection requires measured load/inrush and human review.
- Six separate motor-return branches to a star beside the input. Teensy/encoder
  ground meets the returns there, not along their rails.
- Six control-ground solder/wire bridges, default OPEN.
- 10k axial pull-down from each EN to that axis's PGND, holding EN low during
  reset/unpowered Teensy conditions. Not a hardware kill.
- Entire carrier through-hole, hand soldered, no factory assembly.
- Two layers, 160 x 120 mm, M3 mounting holes. Size confirmed to fit the base.

## Fixed pin map

| Axis | Movement | PWM1 / PWM2 / PWM3 | EN | CSn |
|---|---|---|---:|---:|
| A1 | Index curl 1 | 4 / 5 / 6 | 16 | 26 |
| A2 | Index curl 2 | 2 / 22 / 23 | 17 | 27 |
| A3 | Index splay | 7 / 36 / 29 | 20 | 32 |
| A4 | Middle curl 1 | 24 / 0 / 25 | 21 | 38 |
| A5 | Middle curl 2 | 3 / 33 / 37 | 30 | 39 |
| A6 | Middle splay | 8 / 9 / 28 | 31 | 40 |

All axes use **edge-aligned PWM**, intended common 25 kHz. Do not add
`SIMPLEFOC_TEENSY4_FORCE_CENTER_ALIGNED_3PWM`; keep `lib_archive = no` and the
bench-verified SimpleFOC version. EN/CS assignments are non-PWM digital pins.
SPI0: MOSI 11, MISO 12, CLK 13; no split that changes the agreed map.
Unused pins: 1, 10, 14, 15, 18, 19, 34, 35, 41.

## Removed from v1

[V2 backlog](pcb/v2-backlog.md): buck/USB power management, reverse-polarity
protection, kill/latch, wrist port/level shifting, fingertip grounds/ferrites,
daughterboard link, direct JST-SH sockets, indicators and extra signal filters.
No beautification or left-thumb board is being designed here.

## Completion and review gate

Native KiCad project, finished copper, strict CLI ERC/DRC reports, schematic
PDF, top/bottom/3D PNGs, review BOM/cost, beginner block explanation, and one-page
explanation covering all real nets. Power, phases and ground deliberately
routed, never entrusted to the signal autorouter.

Mini fit, encoder pin 1/order and base size are resolved user confirmations.
Restart behavior is not applicable without a kill circuit. Firmware migration,
electrical/current-budget review and physical bench tests remain separate.
**Stop for human review before Gerber, drill, placement, upload or order files.**
