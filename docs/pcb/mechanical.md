# Mechanical record - carrier v1

Board: 160 x 120 mm, two copper layers, nominal 1.6 mm thickness. Four 3.2 mm
M3 holes at (5,5), (155,5), (155,115), (5,115), measured from top-left in mm.
User confirmed the base fits. Use insulating spacers and check screw-head clearance.

The user verified the Mini socket fit on a 1:1 print. Its coordinates below are
unchanged from [SimpleFOCMini v1.0](https://github.com/simplefoc/SimpleFOCMini/tree/v1.0),
pinned commit `848e8ece46d045ac24283e2d6ee9ea4ba8ef95d5`. Raw EasyEDA source and
license are in `pcb/sources/`; conversion is 0.254 mm per source unit.

Top view, origin at control pin 1, X right/Y down. Upper-row Minis rotate the
whole footprint 180 degrees; lower-row Minis use these coordinates directly.

| Contact | X mm | Y mm | Function |
|---|---:|---:|---|
| 1 | 0 | 0 | Control ground via default-open bridge |
| 2 | 0 | 2.540 | Mini 3.3 V output, unconnected |
| 3 | -2.540 | 0 | PWM1 |
| 4 | -2.540 | 2.540 | Control ground via default-open bridge |
| 5 | -5.080 | 0 | PWM2 |
| 6 | -5.080 | 2.540 | Reset, carrier unconnected |
| 7 | -7.620 | 0 | PWM3 |
| 8 | -7.620 | 2.540 | Sleep, carrier unconnected |
| 9 | -10.160 | 0 | EN |
| 10 | -10.160 | 2.540 | Fault, carrier unconnected |
| P1 | -1.524 | 17.653 | OUT3 / PH3 |
| P2 | -4.064 | 17.653 | OUT2 / PH2 |
| P3 | -6.604 | 17.653 | OUT1 / PH1 |

The old source's power-pad pitch is 4.953 mm, while the actual bench module was
reported as 3.81 mm. This is retained as provenance, not a remaining socket-fit
hold: approved wires carry power and the user physically checked the rigid sockets.
No rigid power pins are placed on the carrier.

Teensy sockets: two 1x24 at 2.54 mm pitch, 15.24 mm row separation. USB faces
left; J2/VIN row above, J1/GND row below. Encoder sockets: female 1x6 at 2.54 mm,
pin 1 CLK, all pointing in the same numbered direction. Phase headers: male 1x3.
Owned EEUFR1V102B capacitors: 12.5 mm diameter, 20 mm high, 5 mm pitch.

Renders omit plugged-in modules, breakout boards and cable bodies. The custom
27 x 24 mm Mini courtyard is a clearance envelope, not a complete 3D model.
The regenerated full-size PDF is a record/check aid, not a request to repeat
the already accepted fit test. Print at 100% and measure its 50 mm ruler if reused.
