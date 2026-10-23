# Mechanical record - carrier v1

Board: 160 x 120 mm, two copper layers, nominal 1.6 mm thickness. Four 3.2 mm
M3 holes at (5,5), (155,5), (155,115), (5,115), measured from top-left in mm.
User confirmed the base fits. Use insulating spacers and check screw-head clearance.

The single `SimpleFOC_Mini_v1.0` footprint uses the 15 contact drills from
[SimpleFOCMini tag v1.0](https://github.com/simplefoc/SimpleFOCMini/tree/v1.0),
commit `848e8ece46d045ac24283e2d6ee9ea4ba8ef95d5`. Raw drill, outline,
EasyEDA PCB/schematic and SHA-256 provenance are in
`pcb/sources/simplefoc-mini-v1.0/`. `extract_mini.py` verifies them directly.

Top view, origin = H1 pin 9 at drill (-1.143, -3.937), +X right,
+Y toward the phase header. Component side faces up, pins down: NOT mirrored.
Upper modules rotate 180 degrees; lower modules use 0 degrees. Translating
the old footprint origin preserves every control/phase contact on the carrier.

| Contact | X mm | Y mm | Drill mm | Function |
|---|---:|---:|---:|---|
| 1 | 10.160 | 0.000 | 1.101 | Control GND |
| 2 | 10.160 | 2.540 | 1.101 | 3.3V output / NC |
| 3 | 7.620 | 0.000 | 1.101 | PWM1 |
| 4 | 7.620 | 2.540 | 1.101 | Control GND |
| 5 | 5.080 | 0.000 | 1.101 | PWM2 |
| 6 | 5.080 | 2.540 | 1.101 | nRESET / NC |
| 7 | 2.540 | 0.000 | 1.101 | PWM3 |
| 8 | 2.540 | 2.540 | 1.101 | nSLEEP / NC |
| 9 | 0.000 | 0.000 | 1.101 | EN via R4 |
| 10 | 0.000 | 2.540 | 1.101 | nFAULT / NC |
| P1 | 8.636 | 17.653 | 1.021 | OUT3 / PH3 |
| P2 | 6.096 | 17.653 | 1.021 | OUT2 / PH2 |
| P3 | 3.556 | 17.653 | 1.021 | OUT1 / PH1 |
| GND | 17.399 | 3.810 | 1.101 | Axis PGND |
| VIN | 17.399 | 8.763 | 1.101 | 12V_FUSED |

The source tools are exactly 1.101 / 1.021 mm (the plan rounded to 1.10 / 1.02).
Power pitch is 4.953 mm, not 5.08 or 3.81 mm. Use independent machine-pin
receptacles. The previous bench note about a 3.81 mm module is historical;
this footprint targets the explicitly requested tagged v1.0 geometry.

F.Fab follows the actual GKO lines and arcs. Its bounding envelope is
26.083 x 21.012 mm, including the scalloped outline features. F.CrtYd adds
0.25 mm on every side. Four 2 mm holes and small vias in the upstream board
are shown in the overlay for context; they are not additional carrier contacts.

Teensy sockets: two 1x24 at 2.54 mm pitch, 15.24 mm row separation. USB faces
left; J2/VIN row above, J1/GND row below. Encoder sockets: female 1x6 at 2.54 mm,
pin 1 CLK, all pointing in the same numbered direction. Phase headers: male 1x3.
Owned EEUFR1V102B capacitors: 12.5 mm diameter, 20 mm high, 5 mm pitch.

Renders omit plugged-in modules, breakout boards and cable bodies. Power
receptacles are represented by their real footprint holes; a particular vendor's
3D body is not asserted. The regenerated 1:1 PDF includes all 15 contact holes.
The [overlay/report](mini-v1-update.md) checks both the library and all six
board instances against the upstream drill centres.
