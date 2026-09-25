# Mechanical evidence and connector release holds

See [the photo findings and paper-fit procedure](hardware-check.md) for what the
user's supplied photographs establish and the remaining practical checks.

The module source is pinned to upstream SimpleFOCMini v1.0 commit
`848e8ece46d045ac24283e2d6ee9ea4ba8ef95d5`.
`pcb/extract_mini.py` converts EasyEDA coordinate units using 0.254 mm per unit.
`pcb/sources/mini-geometry.json` records extracted coordinates; the raw source
and its licence remain beside it. Never substitute v1.1 geometry without review.

## Mini socket coordinates

Top view, origin at control pin 1; X right, Y down; millimetres. Positive/negative
signs matter. The bottom row of axes uses these coordinates directly; the top row
rotates the whole footprint 180 degrees.

| Contact | X | Y | Meaning |
|---|---:|---:|---|
| 1 | 0 | 0 | Ground, not joined through the carrier control socket |
| 2 | 0 | 2.540 | Mini regulator output; leave open |
| 3 | -2.540 | 0 | IN1 |
| 4 | -2.540 | 2.540 | Ground, open at carrier socket |
| 5 | -5.080 | 0 | IN2 |
| 6 | -5.080 | 2.540 | Reset, use module's bias |
| 7 | -7.620 | 0 | IN3 |
| 8 | -7.620 | 2.540 | Sleep, use module's bias |
| 9 | -10.160 | 0 | Enable |
| 10 | -10.160 | 2.540 | Fault output, open |
| P1 | -1.524 | 17.653 | OUT3 |
| P2 | -4.064 | 17.653 | OUT2 |
| P3 | -6.604 | 17.653 | OUT1 |

**Mismatch to resolve:** the archived v1.0 source power-pad centres are 4.953 mm
apart. The user's description says 3.81 mm. This may indicate a different physical
revision; it is not permission to assume that the rest of the geometry matches.
The approved wire-pair power connection is independent of pitch, but rigid sockets
still require physical confirmation. The custom footprint's 27 × 24 mm courtyard
is a provisional clearance envelope, not a measured enclosure model.

Panasonic EEUFR1V102B: diameter 12.5 mm, height 20 mm, lead pitch 5 mm.
Teensy outer sockets: 24 contacts each at 2.54 mm pitch, rows 15.24 mm apart.
With USB facing left, **J2/VIN is the upper row and J1/GND/pin 0 is the lower
row**, as shown on the [PJRC top-view card](https://www.pjrc.com/teensy/card11a_rev4_web.pdf).
Both socket contact-1 positions are at the USB end. Do not mirror this top view.
M3 holes: 3.2 mm diameter, at (5,5), (155,5), (155,115), (5,115) on the proposed
160 × 120 mm carrier. Mounting hardware must not touch solder joints or module
undersides. Check USB cable insertion and module-removal room with a paper model.

## Encoder and wrist orientation

JST footprint contact numbers are authoritative for the *proposed carrier*, not
evidence of the existing cable. Determine pin 1 from the manufacturer's connector
drawing, record the viewing direction, then check all six wires end to end with
power removed. In particular confirm 3.3 V and ground before any power-up. Do not
infer voltage from a connector's colour or number of contacts.

J6's PH 2.0 mm footprint is also provisional. Do not order that connector until
the actual Feetech housing, keyed orientation and cable mapping are confirmed.
