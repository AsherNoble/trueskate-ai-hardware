# Chihai RK-520 + DRV8871 Session Dump

Date: 2026-07-23

## Current Files

- `Motor_Test.ino`: latest local source, including motor test, timed calibration, and manual calibration commands.
- `platformio.ini`: Mega 2560 PlatformIO configuration.

## Wiring Confirmed By User

- Arduino board: Mega 2560 clone; USB serial adapter appears as `/dev/cu.usbserial-1230`.
- DRV8871 `IN1` -> Mega `D9`.
- DRV8871 `IN2` -> Mega `D10`.
- Encoder A -> Mega `D2`.
- Encoder B -> Mega `D3`.
- Motor leads -> DRV8871 `OUT1`/`OUT2`.
- DRV8871 motor supply `VM` -> 12 V supply.
- Grounds are common between the 12 V supply, DRV8871, Mega, and motor encoder.
- Encoder supply in the original diagram is 3.3 V.

## Tooling

- Arduino IDE is installed at `/Applications/Arduino IDE.app`.
- Its bundled CLI is:
  `/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli`
- Installed Arduino core: `arduino:avr` 1.8.6.
- Working FQBN: `arduino:avr:mega:cpu=atmega2560`.
- Successful upload port: `/dev/cu.usbserial-1230`.
- USB identity reported by PlatformIO: VID/PID `1A86:7523`, description `USB2.0-Serial`, consistent with a CH340-style adapter.

## Confirmed Tests

1. A preliminary one-second PWM test spun the motor successfully.
2. A two-second calibration at PWM 100 reported approximately `-24` encoder counts.
3. Closed-loop one-revolution tests used a nominal target of 22 counts with active braking.
4. Initial full-speed-to-target tests ended at `-25` and `-24` counts.
5. Reduced approach speed tests ended at `-23` and `-24` counts.
6. Brake-lead tests ended at `-24`, `-22`, and `-23` counts.

## Firmware State

The last firmware successfully uploaded to the board was the version with:

- `g`: closed-loop one-revolution test.
- `c`: two-second motor calibration.

The manual-calibration edit was applied to the local source after that upload, but the session was interrupted before compiling/uploading it. Therefore the current local source and board firmware are different.

## Current Firmware Behaviour In This Dump

The local source supports:

- `g`: run approximately one revolution using the 20-count brake-start threshold and 22-count nominal resolution.
- `c`: run for two seconds and report encoder count.
- `m`: stop/coast, zero the encoder count, and enter manual calibration mode.
- `x`: finish manual calibration and report the count accumulated since `m`.

The manual mode is intended for a user to rotate the target shaft exactly one turn by hand with 12 V motor power off. It was not uploaded during the session.

## Technical Findings

- The DRV8871 is a brushed DC motor H-bridge. It drives, PWM-controls, and brakes the motor; it does not measure shaft angle or revolution count.
- The existing encoder is incremental AB feedback. It provides relative motion, not an absolute angle after power loss.
- Public CHR-RK520 information identifies an AB Hall encoder with an 11-line/basic signal specification, but does not establish a unique gearbox/output ratio for the particular motor.
- The current interrupt routine triggers on both A transitions and reads B for direction, so 11 PPR is treated as approximately 22 counts per encoder-shaft revolution.
- If the encoder is on the motor shaft and the desired shaft is geared, the gearbox ratio still must be known or measured.
- A possible electrical risk is the 3.3 V encoder signal going into a 5 V Mega input. It may work, but the logic-high margin should be checked. If the encoder supports 5 V, powering it at 5 V is preferable; otherwise use a suitable level shifter or verify the Mega input thresholds.

## Absolute-Angle Sensor Option

The recommended hardware upgrade is an AS5600-style magnetic absolute angle sensor mounted on the shaft whose angle matters, with a small diametric magnet on the shaft. The Mega can read it over I2C (`SDA=D20`, `SCL=D21`). This gives absolute single-turn angle, while the existing AB encoder can remain for speed and multi-turn tracking.

References:

- Chihai CHR-RK520 manufacturer page: https://www.chihaimotor.com/cxbmq/653.html
- Chihai RK-520 encoder product specification: https://www.airsoftmotor.com/encoder-motor/drive-motor-with-encoder/dc-motor-with-hall-encoder-12v-10000rpm.html
- TI DRV8871 product page: https://www.ti.com/product/DRV8871
- TI DRV8871 datasheet: https://www.ti.com/lit/ds/symlink/drv8871.pdf
- ams OSRAM AS5600 datasheet: https://look.ams-osram.com/m/7059eac7531a86fd/original/AS5600-DS000365.pdf
