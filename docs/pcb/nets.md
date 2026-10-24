# TrueSkate v1 - every net, in plain English

Identical labels are one electrical net. Shared copper remains continuous with any axis unpopulated. The two shared kill buffers and their bias/bypass parts remain fitted. Plug-in modules perform motor control.

| Net or repeated family | What it connects and why |
|---|---|
| `12V_IN` | J5 positive to F1 input, before the fuse. Dedicated L3 input area; correct polarity required. |
| `12V_FUSED` | F1 output to all Mini VIN contacts and local capacitors. Broad fused L3 power plane, 2 oz inner copper. |
| `3V3` | Teensy regulator to encoders, CS pull-ups, kill buffers and /OE pull-up. USB powers the Teensy. |
| `GND` | Solid L2 ground plane and outer fills join supply negative, logic, Minis and capacitor returns. No isolation. |
| `SPI_SCK` | Teensy 13 to all encoders. SH contact assignment is provisional; see README verification table. |
| `SPI_MOSI` | Teensy 11 to all encoders. Host-to-encoder data. |
| `SPI_MISO` | Encoders to Teensy 12. Only the selected encoder may drive this shared line. |
| `A<n>_PWM<p>` | Three logic PWM instructions per axis from Teensy to Mini. Existing pin map retained. |
| `A<n>_EN_CMD` | Teensy EN command to a buffer input; 10k input pull-down holds an undriven command low. |
| `EN_DISABLE` | J6 NC loop shorts this net to GND to permit commands. Open loop lets R1 pull it high and disable all buffers. |
| `A<n>_EN` | Buffered enable to Mini pin9. Open kill loop makes buffer high impedance; local 10k pulls EN low. |
| `A<n>_CS` | Individual active-low encoder select with 10k pull-up. Fit with its encoder; deselect all before SPI. |
| `A<n>_PH<p>` | Mini P3/P2/P1 to male motor header1/2/3. Never move phase cables with 12V live. |

Names expand literally: for example `A2_PWM3` and `A6_PH1`. This covers every name, not just a sample.

| Axis | Movement | Teensy PWM1/2/3 | Teensy EN | Teensy CS |
|---|---|---|---|---|
| A1 | index curl 1 | 4 / 5 / 6 | 16 | 26 |
| A2 | index curl 2 | 2 / 22 / 23 | 17 | 27 |
| A3 | index splay | 7 / 36 / 29 | 20 | 32 |
| A4 | middle curl 1 | 24 / 0 / 25 | 21 | 38 |
| A5 | middle curl 2 | 3 / 33 / 37 | 30 | 39 |
| A6 | middle splay | 8 / 9 / 28 | 31 | 40 |

SH pin-to-net order is UNVERIFIED: see README and check the actual AS5048A board with a multimeter. Opening kill disables EN but does not disconnect 12V; reclosing permits the current command without a latch. Human review, mechanical fit, startup and noise tests remain required before manufacture.
