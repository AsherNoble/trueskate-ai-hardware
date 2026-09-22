# trueskate-ai-hardware

Hand-control layer for TrueSkate-AI. Slots in where WebDriverAgent does for
the phones: the agent sends touch gestures, this repo makes a robotic finger
perform them.

Time-critical control (FOC, trajectory execution, safety) runs on a Teensy
4.1. The host sends commands and reads state back; it never runs a control
loop.

## Structure

```
firmware/   PlatformIO project, board teensy41
  src/        controller firmware, one Axis per finger
  bringup/    bench sketches kept for the record, unchanged
host/       Python package (uv), touch API + motor clients
  src/        trueskate_ai_hardware
  config/     hand.yaml
  tests/      mock-path tests, no hardware needed
docs/       wiring, pin map, bring-up notes, protocol draft
```

## Build the firmware

```sh
cd firmware && pio run
```

Does not flash. Add `-t upload` with the board connected.

## Run the host tests

```sh
cd host && uv sync --extra dev && uv run pytest
```

## Status

Firmware drives one axis and builds. The host is a skeleton: the touch API
mirrors the interface but does not move anything, and the serial protocol in
`docs/protocol.md` is a draft. `MockMotorClient` works with no hardware.

Start with [docs/bringup.md](docs/bringup.md) for what the bench has proved.

## Licence

MIT. `orca_core` (MIT, ORCA) was studied as a reference for the motor-client
and serial-framing patterns; no code was copied.
