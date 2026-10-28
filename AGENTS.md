# Repository instructions

Hand-control layer for TrueSkate-AI. The agent issues touch gestures; this
repo makes a robotic finger perform them, the way WebDriverAgent does for the
phones.

## Navigation

- `README.md`: structure and build/test commands.
- `docs/bringup.md`: what the bench has actually proved. Read before changing
  firmware — several findings here are non-obvious and were expensive.
- `docs/protocol.md`: host↔Teensy serial protocol. DRAFT, unreviewed, unbuilt.
- `docs/wiring.md`, `docs/pinmap.md`: bench wiring and pin assignments.
- `firmware/bringup/`: bench sketches kept unchanged for the record. Do not
  edit them; they are evidence, not code.

## Conventions

- Firmware: PlatformIO, `cd firmware && pio run`. Do not flash without asking.
- Host: uv, `cd host && uv sync --extra dev && uv run pytest`.
- Use absolute filesystem paths in tools. Do not rely on tilde expansion.
- Commit messages: `type: message`, one coherent commit at a time.
- Prefer terse factual updates: what changed, evidence, next step.

## Gesture and coordinate contracts

These mirror TrueSkate-AI's `GESTURES.md`, which is authoritative. Do not
diverge from it here — the whole point is that the agent cannot tell whether
a phone touch or a finger executed a gesture.

- Coordinates are normalised `[0, 1]`. One transform only: normalised point →
  rig frame. No offsets, no per-device correction.
- A *gesture* is waypoints + duration + easing power; a *gesture recipe* is
  N gestures + N−1 delays, and negative delays (overlap) are legal.
- Spin is a HOLD on the rotate button, not a tap.
- Do not use "action" or "swipe" to describe a touch.

## Hardware invariants

- The Teensy owns everything time-critical: FOC, trajectory execution,
  safety. The host sends commands and reads state. Never add a control loop
  to the host.
- Firmware boots with the motor disabled. `initFOC` runs only on command,
  because it moves the shaft and needs the bench PSU live.
- `loopFOC()` must be called explicitly in SimpleFOC 2.4, including open loop.
- `SIMPLEFOC_TEENSY4_FORCE_CENTER_ALIGNED_3PWM` belongs in `build_flags`. A
  `#define` in a sketch does not reach the library's `.cpp` files.
- In voltage torque mode the target is VOLTS and `current_limit` is inert;
  `voltage_limit` is the only current cap.
- SimpleFOC is pinned to the version the bench verified. Do not float it.
- Never move a motor phase lead with the rail live.

## Commit and push rules

- Work in a session worktree/branch; main checkout is read-only.
- Use `type: message`; make small WIP commits after working steps.
- Never commit on `main` or bypass hooks with `--no-verify`.
- Squash locally to one commit, force-push the branch, then use a PR with **Squash and merge**. No bypass.
- Run archive and public-safety checks before merging.
- After merging, delete the local branch, remote branch and worktree.
- Preserve others’ dirty work; never commit secrets or personal identifiers.
