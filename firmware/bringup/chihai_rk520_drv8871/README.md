# Chihai CHR-RK520 + DRV8871 — bring-up archive

Bench work on the **beautification-finger motor family**, from 2026-07-23.
Kept here as evidence, unchanged. Like the rest of `bringup/`, do not edit it.

This is not the index/middle axis. Different motor, different driver,
different board:

| | This archive | The hand's driven axes |
|---|---|---|
| Motor | Chihai CHR-RK520, brushed DC + gearbox | GM3506 gimbal BLDC |
| Driver | DRV8871 H-bridge | SimpleFOC Mini (DRV8313) |
| Feedback | Incremental AB encoder, ~22 counts/rev | AS5048A absolute, 16384 counts/rev |
| Board | Arduino Mega 2560 | Teensy 4.1 |

It has its own `platformio.ini` targeting `megaatmega2560`, so it builds from
*this* directory, not from `firmware/`. The repo's own envs (`teensy41`,
`loop_timing`) do not compile anything in here — `build_src_filter` keeps
them to `src/` and `bench/`.

`SESSION_NOTES.md` is the substantive record: confirmed wiring, tooling, test
results, and the open questions. Three worth carrying forward:

- **The local source and the board firmware diverged.** A manual-calibration
  edit was made after the last successful upload and never compiled.
- **The gearbox ratio is unknown.** 11 PPR is treated as ~22 counts per
  *encoder-shaft* revolution; if the encoder sits on the motor shaft ahead of
  the gearbox, the output ratio still has to be measured.
- **3.3 V encoder signals feed 5 V Mega inputs.** It appeared to work, but the
  logic-high margin was never verified.

Also note the AB encoder is incremental, so it gives no absolute angle after
power loss. `SESSION_NOTES.md` proposes an AS5600 on the shaft that matters —
the same absolute-angle approach the driven axes already use with the AS5048A.

`platformio.ini` pins `upload_port = /dev/cu.usbserial-1230`, which was that
session's CH340 adapter and will not be right on another machine.
