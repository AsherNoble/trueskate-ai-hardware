# Wiring

## Bench setup

- Teensy 4.1 on USB.
- GM3506 gimbal motor, 24N/22P, 11 pole pairs, ~5.6 Ω phase resistance.
- SimpleFOC Mini (DRV8313) driver.
- AS5048A magnetic encoder on SPI0.
- Bench PSU at 12 V with a 0.5 A current limit.

## Power

| Rail | Source |
|---|---|
| Teensy logic | USB |
| Encoder VDD | Teensy 3.3V |
| Driver / motor | Bench PSU, 12 V, 0.5 A limit |

The DRV8313 will not run below 8 V, so the motor rail is a bench supply, not
USB. The encoder runs from the Teensy's own 3.3V and works with the PSU off —
which is what makes encoder bring-up safe to do with dark phases.

### Power-up order

1. Motor phases into M1/M2/M3 with the PSU **off**.
2. Set the PSU to 12 V and a 0.5 A limit.
3. Teensy on USB, firmware already flashed. It boots with the motor disabled.
4. PSU on.
5. Send `I` to align.

Never move a phase lead with the rail live.

## Connections

See [pinmap.md](pinmap.md) for the pin table and [bringup.md](bringup.md)
for the encoder wire-colour table.

## SimpleFOC Mini mechanical

The Mini's **power pads are 3.81 mm pitch**, which does not land on a 2.54 mm
breadboard grid. Use the screw terminal supplied with the board. The signal
header is on the standard 2.54 mm pitch and breadboards normally.

## Encoder harness

The first bring-up attempt failed entirely because of a **damaged JST plug and
breakout socket** — one signal contact open, two shorted together. It survived
a continuity check of the loose harness and only showed up as stuck-high and
stuck-low lines under a powered permutation scan.

If the encoder reads all-ones or all-zeros, check the connector before
re-ordering wires.
