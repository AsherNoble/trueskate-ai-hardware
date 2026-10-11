# Teensy 4.1 pin map

Historical bench wiring below, not the six-axis carrier map. The carrier uses
the [current PCB assignments](pcb-requirements.md#fixed-pin-map): all six axes
are edge-aligned, EN/CS move to plain digital pins, and the center-aligned build
flag has been removed. The entries below preserve what the earlier bench proved.

One axis is wired and instantiated. The second axis's pins are proposed, not
built — nothing below the divider has been tested.

## Index axis (built, verified)

| Pin | Role | Notes |
|---|---|---|
| 4 | Driver IN1 | FlexPWM, center-aligned via build flag |
| 5 | Driver IN2 | |
| 6 | Driver IN3 | |
| 8 | Driver EN | Held LOW at boot; nothing energises until commanded |
| 10 | Encoder CSn | SPI0 CS |
| 11 | Encoder MOSI (DI) | SPI0 |
| 12 | Encoder MISO (DO) | SPI0 |
| 13 | Encoder CLK | SPI0 SCK — also the onboard LED |

Pin 13 carries the onboard LED and its series resistor to ground, so it is
loaded differently from the other three. This showed up once during the
permutation scan and has caused no trouble since it settled into its correct
role as CLK.

## Reserved

| Pin | Role |
|---|---|
| USB | Host serial, 115200 (console today; framed protocol drafted in protocol.md) |

---

## Second axis (proposed, NOT built)

The middle finger needs three more PWM pins on distinct FlexPWM submodules
and one more SPI chip select. SPI0's CLK/MOSI/MISO are shared; only CS is
per-sensor.

| Pin | Role | Notes |
|---|---|---|
| 2 | Driver IN1 | proposed |
| 3 | Driver IN2 | proposed |
| 7 | Driver IN3 | proposed |
| 9 | Driver EN | proposed |
| 14 | Encoder CSn | proposed; CLK/MOSI/MISO shared with the index axis |

Verify FlexPWM submodule assignment before committing to these — three PWM
outputs driving one motor must be on timers that can be synchronised, which
is the whole reason `SIMPLEFOC_TEENSY4_FORCE_CENTER_ALIGNED_3PWM` exists.
