# Bring-up notes

Verified findings from bench bring-up of the index axis. Each is tied to the
sketch in `firmware/bringup/` that established it.

## Wiring

| Signal | Teensy 4.1 pin |
|---|---|
| Driver IN1 | 4 |
| Driver IN2 | 5 |
| Driver IN3 | 6 |
| Driver EN | 8 |
| Encoder CSn | 10 |
| Encoder CLK | 13 |
| Encoder MOSI (DI) | 11 |
| Encoder MISO (DO) | 12 |
| Encoder VDD | 3.3V |
| Encoder GND | GND |

Encoder VDD is **3.3V**. A 5V test changed nothing and risks exceeding the
chip's limits if the breakout is strapped for 3.3V operation.

### Encoder harness

Connector contact order read from the JST breakout, pin 1 being the square pad
with the traces running straight from socket to header. Wire colours are from the
harness that passed phase 1.

| JST contact | Signal | Colour | Teensy pin |
|---|---|---|---|
| 1 | CLK | purple | 13 |
| 2 | MISO / DO | green | 12 |
| 3 | MOSI / DI | yellow | 11 |
| 4 | CSn | black | 10 |
| 5 | VDD 3.3V | red | 3.3V |
| 6 | GND | white | GND |

**CSn is contact 4, not contact 1.** An earlier draft of the carrier assumed CSn
first, which shifted every signal by one position.

## SimpleFOC 2.4

**`loopFOC()` must be called explicitly**, including in open loop.
`move()` does not call it. (Open-loop bench sketch, not kept in this repo.)

**`velocity_openloop` drives the phases even at a zero target.** Zero
velocity is not idle — it is a held commutation. Use `motor.disable()` when
dark phases are wanted. (Open-loop bench sketch, not kept in this repo.)

**In voltage torque mode, `T` is volts, not amps, and `current_limit` is
inert.** `BLDCMotor(pp, R)` does *not* switch the torque controller: the
constructor sets `TorqueControlType::voltage` unconditionally, and that
branch never reads `phase_resistance` —

```cpp
case TorqueControlType::voltage:
  voltage.q = _constrain(current_sp, -voltage_limit, voltage_limit) + feed_forward_voltage.q;
```

`current_limit` constrains the setpoint only in the `estimated_current`,
`dc_current` and `foc_current` branches. **`voltage_limit` is the only
current cap on this path**: at 5.6 Ω, `voltage_limit = 2` allows ~0.36 A at
stall.

**`SIMPLEFOC_TEENSY4_FORCE_CENTER_ALIGNED_3PWM` must be a build flag.** A
`#define` in the sketch never reaches the library's own `.cpp` translation
units, where the PWM setup lives. See `firmware/platformio.ini`.

## Encoder

**Stock `AS5048_SPI` is correct** — it is already `SPI_MODE1` at 1 MHz, and
SimpleFOC's `read()` shifts by `1 + data_start_bit - bit_resolution` = 0, so
it takes bits 13:0 unshifted. No custom `MagneticSensorSPIConfig_s` is
needed. (`06_sensor_only`)

**`01_encoder_check` read every word one bit shifted** — a quarter turn read
as ~180°, jitter doubled, and parity failed on 100% of frames. It used the
same `SPI_MODE1` at 1 MHz with the same framing, so **the cause is unknown**.
The sketch is kept as `01_encoder_check_BROKEN.ino`; its diagnostics output
is void.

**True encoder diagnostics word: `0x01A3`** — AGC 163, OCF ok, no COF, no
COMP faults. Read via the bit-banged reference in `04_spi_perm_scan`. The
AGC 71 / COF / magnitude 9063 figures from `01_encoder_check` were artefacts
of its bit shift.

**Root cause of the encoder failure: a damaged JST plug and breakout
socket** — one contact open, two shorted together. Not a wire-order problem.
Three permutations and two supply voltages produced only stuck-high and
stuck-low lines until the breakout was replaced. A software permutation scan
(`04_spi_perm_scan`) found the live mapping immediately afterwards.

## Motor

**`initFOC` results** (reproducible across reflashes):

```
MOT:sensor dir: CW
MOT:PP check: OK!
MOT:Zero elec. angle: 1.86
```

Pole-pair check **OK at 11**, so the motor is a genuine 24N/22P GM3506, not
a 12N/14P clone. `sensor_direction = 1` (CW) — no inversion needed.

`ERR-MOT:No current sense.` is expected and not a fault: the SimpleFOC Mini
has no current sensing, and voltage torque mode does not need it.
`MOT:Ready.` follows it.

**First closed-loop move: 720° at 60 rpm.** Travelled 718.86° in 2236 ms,
cruise velocity 59–64 rpm, `Uq` peak **0.57 V of a 2 V limit** — the
controller never saturated. Default PID values; no tuning needed at this
speed and load. The 1.14° shortfall is the arrival tolerance (0.02 rad),
not a tracking error.

## Mechanical

**The SimpleFOC Mini's power pads are 3.81 mm pitch**, off the 2.54 mm
breadboard grid. Use the supplied screw terminal; do not try to seat the
board across breadboard rows by its power pads.
