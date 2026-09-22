# PCB requirements (v1 draft)

Status: draft. Items marked **TBD** are open decisions, listed again at the end.

## 1. Board split

| Board | Location | Carries |
|---|---|---|
| **Main board** | Right-hand base | Teensy 4.1, 6 FOC axes (index + middle), wrist bus-servo port, hardware kill, power entry, fingertip ground terminals, link to daughterboard, USB to host |
| **Beautification daughterboard** | Right-hand base | Second Teensy 4.1, 6 to 10 brushed DC channels (thumb, ring, pinky) |
| **Left-thumb board** | Left-hand base | 1 FOC axis. Own MCU, or a 7th axis cabled to the main board: **TBD** |

Split rule: time-critical FOC stays on the main board. Anything low-fidelity or pin-hungry goes elsewhere.

## 2. Actuators

| Group | Motor | Qty | Driver | Control | Signals per unit | Drive |
|---|---|---|---|---|---|---|
| Index + middle (2 curl + 1 splay each) | GM3506 (24N22P, 11 pole pairs, 5.6 Ω) | 6 | SimpleFOC Mini v1.0 (DRV8313) | Closed-loop FOC, AS5048A over SPI | 3 PWM, 1 EN, 1 CS | Tendon, motor in base |
| Wrist | Feetech STS3215, 12V | 1 (maybe 2) | Internal | Bus servo, half-duplex UART | Shared bus | Direct at wrist axis |
| Thumb, ring, pinky (beautification) | Chihai RK-520, brushed DC + quadrature encoder | 6 to 10 | DRV8871, one per motor | Position loop on daughterboard | 2 PWM, 2 encoder | Tendon, motor in base |
| Left thumb | GM3506 or other iFlight: **TBD** | 1 | SimpleFOC Mini v1.0 | Closed-loop FOC | 3 PWM, 1 EN, 1 CS | Tendon |

Wrist load estimate: ~300 g hand, ~2.1 kg·cm worst-case static torque, about 11% of STS3215 stall. Comfortable.

## 3. Power

- **Single 12V rail** for all motors: GM3506, STS3215 (12V version), Chihai RK-520.
- Input: sealed, RCM-approved wall wart for the installation. Bench PSU or LRS-75-12 for development.
- Input protection: fuse and reverse-polarity protection on the 12V input.
- Input connector: rating depends on power budget: **TBD**.
- Per FOC axis: Panasonic EEUFR1V102B 1000 µF / 35V bulk cap plus 100 nF ceramic, both at the driver.
- Teensy power: 12V to 5V buck into VIN, with USB and board power able to coexist (VUSB/VIN separation): **TBD** method.
- Chihai encoder VCC: 3.3V.

### Power budget (to fill in)

| Load | Qty | Running current | Stall / peak current | Notes |
|---|---|---|---|---|
| GM3506 | 7 | | | Bounded by `voltage_limit`; 2V gives ~0.36 A stall |
| STS3215 12V | 1 to 2 | | | Datasheet |
| Chihai RK-520 | 6 to 10 | | | Measure; brushed stall current is the big one |
| Teensy + logic | 2 to 3 | | | |
| **Total** | | | | Sizes PSU, fuse, connector, trace widths |

## 4. Main board pin allocation

Needs a pin-map audit before schematic. Constraints:

- 6 axes × (3 PWM + 1 EN) = 24 pins. PWM pins must satisfy SimpleFOC's Teensy 4 center-aligned requirements: determine from library source.
- 6 encoder CS lines, plus SPI clock/data. Consider splitting encoders across SPI buses.
- 1 half-duplex UART for the wrist servo bus.
- 1 link to the daughterboard (UART or I²C): **TBD**.
- Kill-switch input.
- USB to host.

## 5. Encoders and SPI

- AS5048A, stock SimpleFOC `AS5048_SPI` config (SPI mode 1).
- Clock target 2 to 4 MHz. Validated clean to 8 MHz with a stationary shaft; must re-verify with motors commutating.
- Loop budget: SPI read dominates (~35 µs per axis at 1 MHz, ~10 µs at 4 MHz). FOC compute ~2 to 3 µs per axis.
- Keep SPI runs short, routed away from phase outputs, with a ground return alongside.

## 6. Connectors

| Connection | Connector | Notes |
|---|---|---|
| Encoder cable | JST-SH 1.0 mm, 6-pin, on the board | Cable plugs straight in. No breakout board |
| Motor phases | 3-way terminal per axis | Phase order doesn't matter |
| SimpleFOC Mini | Sockets for the 2×5 control header and 1×3 phases | Power pads are 3.81 mm pitch, off the 2.54 mm grid. Use the Mini's open-source KiCad footprint |
| Wrist servo | Feetech 3-pin | Verify signal level: Teensy pins are not 5V tolerant |
| Chihai (daughterboard) | 6-pin per motor | M1 red, M2 white, GND black, VCC blue, C1 yellow, C2 green |
| Fingertips | 2 terminals (index, middle) | See grounding |
| Kill switch | 2-pin, off-board panel mount | |
| Daughterboard link | **TBD** | |

## 7. Grounding and noise

- Star ground, single join point.
- Fingertip return lines must not share the driver ground rail (PWM noise causes phantom touches). Ferrite bead on each fingertip line.
- Tight motor current loops. Bulk caps at the drivers, not at the input.

## 8. Safety

- Hardware kill that pulls every EN line low, independent of firmware. Normally-closed, so a broken wire also stops the motors.
- What else the kill cuts (servo bus power, daughterboard drivers): **TBD**.
- Firmware invariants: motors disabled at boot, `initFOC()` only on command, `voltage_limit` set conservatively.
- No exposed mains anywhere in the installation.

## 9. Acoustics

- Audible whine observed during alignment. PWM frequency must be at least 20 kHz. Check current `driver.pwm_frequency`.

## 10. Mechanical

- Board outline to fit the base or plinth: **TBD**.
- M3 mounting holes.
- Teensy and Minis socketed, so a dead module is a swap.

## 11. Bring-up and test

- Test points: 12V, 5V, 3.3V, GND, each SPI line.
- LEDs: power rails, per-axis enable.
- Bring up one axis at a time.

## 12. Open decisions

1. Left thumb: own board or 7th axis on the main board.
2. Wrist: one servo or two.
3. Chihai count, and whether to stay with that brand.
4. Fingertips: permanently connected or switched.
5. Teensy power path (USB and board power coexisting).
6. Input connector and fuse rating, after the power budget.
7. Daughterboard link: UART or I²C.
8. Board size and placement in the base.
9. Kill-switch scope and whether it latches.
10. STS3215 signal level.
