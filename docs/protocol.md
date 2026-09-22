# Host ↔ Teensy serial protocol — DRAFT

**Status: draft. Not implemented, not reviewed.** `TeensyMotorClient` raises
on every method rather than sending half-specified bytes at hardware that
can move. Review this before it is built.

Informed by `hand_serial_link.py` in
[orca_core](https://github.com/orcahand/orca_core) (MIT, ORCA) — the framing
idea is borrowed, no code is.

## Principles

The Teensy owns everything time-critical: FOC, trajectory execution, limit
enforcement, the watchdog. The host sends commands and reads state. **There
is no control loop on the host and there should never be one** — a USB round
trip is not a deadline anyone should try to meet.

A gesture therefore goes over the wire as a *trajectory*, not as a stream of
setpoints. The host plans; the Teensy executes.

## Physical layer

| Parameter | Value |
|---|---|
| Transport | USB CDC (Teensy native) |
| Baud | 115200 (nominal; USB CDC ignores it) |
| Framing | `0xAA` header, type byte, length, payload, LRC |

## Frame layout

```
+------+------+--------+---------+-----+
| 0xAA | TYPE | LEN(2) | PAYLOAD | LRC |
+------+------+--------+---------+-----+
```

- `0xAA` — fixed header. On a bad header the reader slides forward one byte
  at a time until it resyncs, counting resyncs as a health metric.
- `TYPE` — frame type; also the demux key for routing to a handler.
- `LEN` — payload length, little-endian uint16. Implausible lengths are
  treated as a lost frame and trigger resync rather than a long blocking read.
- `LRC` — checksum over every preceding byte of the frame.

Every request carries a sequence byte in its payload and every response
echoes it, so a late reply cannot be mistaken for the next answer.

## Command frames (host → Teensy)

| TYPE | Name | Payload | Notes |
|---|---|---|---|
| `0x01` | `PING` | seq | Liveness and round-trip timing. |
| `0x02` | `GET_STATE` | seq, axis mask | Returns `STATE`. |
| `0x03` | `ALIGN` | seq, axis mask | Runs `initFOC`. **Moves the shaft.** Long-running; replies `ACK` then `DONE`. |
| `0x04` | `SET_ENABLE` | seq, axis mask, bool | Energise / de-energise. |
| `0x05` | `SET_TARGET` | seq, axis, float32 | Immediate target, units per current mode. |
| `0x06` | `SET_MODE` | seq, axis, mode | 0 torque, 1 velocity, 2 angle. |
| `0x07` | `TRAJECTORY` | seq, axis, n, (t, angle)×n | Timed angle trajectory to execute. |
| `0x08` | `STOP` | seq, axis mask | Abandon motion, de-energise. Must be honoured mid-trajectory. |
| `0x09` | `GET_LIMITS` | seq, axis | Firmware's own limits, so the host can verify rather than assume. |

## Response frames (Teensy → host)

| TYPE | Name | Payload |
|---|---|---|
| `0x81` | `ACK` | seq, command type |
| `0x82` | `NACK` | seq, command type, error code |
| `0x83` | `STATE` | seq, per axis: angle, velocity, Uq, flags |
| `0x84` | `DONE` | seq, command type, result |
| `0x85` | `EVENT` | event code, detail — unsolicited |

`STATE` flags carry at least: `ready` (aligned), `enabled`, `moving`,
`fault`.

## Unsolicited events

The Teensy may emit `EVENT` at any time without a request — this is why the
host reader is a demultiplexer rather than a request/response pair. Expected
events: fault tripped, trajectory finished, watchdog fired, limit hit.

## Error handling

Open questions, all deliberately unresolved:

- **Watchdog.** If the host goes quiet mid-trajectory, does the Teensy finish
  the move or stop? Finishing is smoother; stopping is safer. Leaning stop,
  with the timeout longer than the longest legal trajectory.
- **Limit violation.** A trajectory exceeding an axis's angle limits should be
  rejected wholesale on receipt, not clipped silently and executed.
- **Alignment loss.** After a fault or a reset, `ready` must go false and stay
  false until `ALIGN` runs again. The host must not be able to command
  motion against a stale `zero_electric_angle`.
- **Trajectory buffer.** Depth, and what happens on overflow — reject the
  frame, or drop the oldest?
- **Sequence wrap.** One byte wraps at 256; fine for request/response, but
  needs stating.

## Not covered yet

Multi-axis synchronisation. A spin-hold recipe needs one finger to hold a
button while another drags, on a shared time base — the trajectory frame is
per-axis, and there is no barrier or shared start-time primitive. This is the
main gap to close before two axes exist.
