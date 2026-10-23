# TrueSkate v1 - every net, in plain English

A net is one named electrical connection: all its pads and copper are joined. This guide covers all 67 nets; n means axis 1-6, p means channel 1-3. The carrier is wiring, sockets, capacitors, resistors and a fuse holder; the plugged-in modules do the control.

| Net or repeated family | What it connects and why |
|---|---|
| `12V_IN` | J5 positive to F1 input. Raw motor-supply power, before the fuse. Wrong polarity can damage this board. |
| `12V_FUSED` | F1 output to all six Mini VIN pads and both capacitors per axis. The fuse interrupts sustained excess input current; it does not regulate motor current. |
| `3V3` | Teensy 3.3 V output to encoder contact 5. USB powers the Teensy; neither the carrier VIN contact nor any Mini regulator output feeds this net. |
| `GND` | Zero-volt reference for Teensy, encoders and bridge GND pads. Joins supply negative and all motor returns at copper junction NT1. USB and motor supply are not electrically isolated. |
| `PGND1 ... PGND6` | One separate motor-power return per axis: Mini GND power pad, its capacitor negatives and EN pull-down. The six returns meet GND only at NT1 on the bare carrier. |
| `CGND1 ... CGND6` | Mini control contacts 1 and 4 to that axis's optional bridge pad. Leave JP1-JP6 OPEN. The installed Mini already joins these contacts internally to its own power return; closing a bridge adds a parallel path through logic ground. |
| `SPI_SCK` | Teensy pin 13 to encoder contact 1 on all six sockets. Clock pulses tell encoders when to shift each data bit. |
| `SPI_MOSI` | Teensy pin 11 to encoder contact 3. Commands go out from the Teensy to all encoders. |
| `SPI_MISO` | Encoder contact 2 to Teensy pin 12. Only the selected encoder may send angle data back. |
| `A<n>_PWM<p> (18 nets)` | Three low-power pulse-width-modulation instructions per axis, Teensy to Mini control contacts 3/5/7. All axes use edge-aligned PWM at one common frequency (intended 25 kHz). These are NOT motor-phase power. |
| `A<n>_EN (6 nets)` | Teensy to Mini control contact 9. High enables that driver. R21-R26 each connect EN through 10k ohms to its own PGND, holding it low when the Teensy is not driving. This cannot override a stuck-high output and is not a hardware kill. |
| `A<n>_CS (6 nets)` | Teensy to encoder contact 4. Chip select is active low: choose one encoder at a time. Firmware must establish all selects high before SPI transfers. |
| `A<n>_PH<p> (18 nets)` | Three switched motor-power outputs per axis: Mini OUT1/2/3 (socket P3/P2/P1) to male phase-header contacts 1/2/3. Never move these cables with 12 V live. |

Names expand literally: for example `A2_PWM3` and `A6_PH1`. This covers every name, not just a sample.

| Axis | Movement | Teensy PWM1/2/3 | Teensy EN | Teensy CS |
|---|---|---|---|---|
| A1 | index curl 1 | 4 / 5 / 6 | 16 | 26 |
| A2 | index curl 2 | 2 / 22 / 23 | 17 | 27 |
| A3 | index splay | 7 / 36 / 29 | 20 | 32 |
| A4 | middle curl 1 | 24 / 0 / 25 | 21 | 38 |
| A5 | middle curl 2 | 3 / 33 / 37 | 30 | 39 |
| A6 | middle splay | 8 / 9 / 28 | 31 | 40 |

No-connect contacts are NOT nets: Teensy VIN and unused digital contacts; Mini 2 (its regulator output), 6 (reset), 8 (sleep), 10 (fault). Encoder square pad/marked pin 1 is CLK; order is CLK, MISO, MOSI, CSn, 3V3, GND. V1 has no polarity protection, hardware kill or guaranteed capacitor discharge. Disconnect 12 V and measure residual voltage before moving wires. Human review before ordering; this is not a manufacturing release.
