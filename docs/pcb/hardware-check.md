# Human review, then careful bench bring-up

No order or manufacturing exports are authorized. The next step is a human
electrical review of the native KiCad project and the net guide.

## Already resolved by the user

- Mini control/phase sockets fit the printed 1:1 template. Keep that geometry.
- Encoder breakout square pad is pin 1; order is CLK, MISO, MOSI, CSn, 3V3, GND.
- The 160 x 120 mm carrier fits the base.
- Direct Mini v1.0 power receptacles replace the previous terminal/wire scheme.
- Kill restart/latch behavior is not applicable to this v1.

These are recorded confirmations, not reasons to ask for the same photos again.
At assembly, still check each installed part and cable against the drawing.

## Ask the human reviewer to check

1. Power current and temperature margins: shared trunks, individual returns,
   phase sockets/Dupont leads, actual wire gauge, input terminal and fuse curve.
   The 3.15 A T fuse is a candidate; qualify DC breaking rating and capacitor inrush.
2. Mini EN-low margin with the 10k pull-down, including reset and USB-off with
   12 V live. No hardware kill exists; a driven-high EN defeats a pull-down.
3. Ground topology and noise: motor returns to NT1, default-open control-ground
   bridges, computer/supply grounding, SPI return continuity and all six cables.
4. Encoder 3.3 V supply current and the actual boards' power configuration.
   No 5 V data signal may reach the Teensy.
5. Regenerative voltage rise, correct 12 V polarity and safe capacitor discharge.
   V1 has no polarity protection, clamp, indicator or guaranteed discharge time.
6. Exact purchased through-hole bodies, pin diameters, insertion depth, stack
   height and header current ratings. Check real encoder-breakout body clearance,
   not just its six pin holes. Confirm capacitor polarity, terminal access and USB access.
7. Firmware migration: earlier EN8/CS10 code is not this board's six-axis map.

## Later first-power sequence (after review and ordering approval)

Keep motors unloaded and clear of fingers and the phone. Use a current-limited
bench supply, a meter, and an accessible physical 12 V disconnect.

1. With USB and 12 V disconnected, inspect soldering, verify pin mappings and
   check for unintended rail shorts. Capacitors charging from a meter can cause
   a temporary continuity beep; investigate, do not assume either outcome.
2. Without plugged-in modules, verify J5 polarity, fuse continuity, every Mini
   footprint VIN/GND pads, and that Teensy VIN has no carrier connection. Leave JP1-JP6 open.
3. Plug in the Teensy with 12 V off. Use suitable firmware with all EN outputs
   low; check encoder sockets have 3.3 V. Do not cut the USB/VIN link for this design.
4. Install one Mini and its approved power pair. With low-current 12 V present,
   confirm EN remains low during reset and with USB removed. Check all six
   pull-downs and their references before expecting default-off behavior.
5. Add one verified encoder, read raw angle while turning the shaft manually,
   and verify orientation before attaching motor power/commanding FOC.
6. Connect one motor with the rail off. Start at low voltage and PSU current
   limits. `initFOC` moves the shaft: command it only when ready. Keep explicit
   `loopFOC()` calls, including open-loop operation.
7. Repeat one axis at a time. Then measure simultaneous current, loop timing,
   rail excursions during braking, 3.3 V stability, SPI errors and temperatures.
   Determine the operating envelope and fuse selection from measured evidence.
8. Disconnect 12 V and USB before moving wires/modules. Measure residual rail
   voltage; do not assume it is zero because firmware stopped or a cable unplugged.

These checks are not a substitute for the human review or permission to power
untested hardware unattended. Never move a motor phase lead with the rail live.
