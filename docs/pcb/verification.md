# Verification and release status

**REVIEW DRAFT — DO NOT ORDER.** This is a real KiCad design-in-progress, not a
finished fabrication package. No Gerbers, drill files or assembly-placement files
are released. Source generation is reproducible; physical operation is untested.

## Checks

| Check | Result / scope |
|---|---|
| Static pin audit, `pcb/audit.py` | 39 unique assigned pins, 18 PWM pins, all 12 EN/CS on non-PWM pins, Serial8 and direction on non-PWM pins, three spares |
| Generated board audit, `pcb/verify_board.py` | Checks every generated component pad/net against circuit data, Teensy top-view orientation, selected safety/power invariants and capacitor pitch |
| Electrical rules check (ERC) | **0 violations**, strict exit code 0; KiCad 10 `kicad-cli`, `pcb/erc-review.json` |
| Design rules check (DRC) | **0 spacing/placement violations, 263 unconnected items**, strict exit code 5; `pcb/drc-review.json`. **Not DRC-clean; opens are not waived** |
| Firmware compile | `pio run -d firmware -e teensy41` succeeded after removing the center-aligned flag; no flashing |
| Mechanical evidence | Original Mini source extracted; user photos confirm AS5048A chip and downward Mini headers, not cable polarity or socket spacing; 1:1 fit template provided |
| Visual outputs | Native schematic PDF and actual-board top/bottom/3D renders; installed Teensy/Mini boards are not modelled |
| Electrical/thermal bench verification | Not performed; no claim of safe operation or six-axis timing qualification |

Read the JSON reports as well as this document: a normal tool exit without
`--exit-code-violations` does **not** mean a board passed. KiCad reports spacing
violations and unconnected items separately. A board with zero spacing violations
but hundreds of opens is **not DRC-clean**.

## Rule baseline

Proposed stack-up: two layers, 1.6 mm FR-4, 1 oz copper. The project applies:

- 0.20 mm minimum copper clearance and track width; 0.25 mm default signal width.
- 0.60 mm minimum via diameter, 0.30 mm minimum drilled hole, 0.15 mm minimum via
  annular width; default via 0.65/0.30 mm. An annular ring is the copper around a
  drilled hole. Through-hole component pads additionally need the manufacturer's
  annular-ring rule checked before release.
- 0.50 mm copper-to-board-edge clearance and 0.25 mm hole clearance.
- Deliberately routed local phase paths are 1.0 mm; bulk-capacitor-to-terminal
  paths are 1.2 mm; ceramic branches are 0.4 mm. These are not validated ampacity
  claims. No autorouter has touched power or ground.
- Input/fuse paths are 1.5 mm with a deliberate ground branch to the input star.
  Local buck paths, sense/boot connections, and a bottom GND area with vias are
  also hand-routed. These need thermal review; the converter's 2 A datasheet
  layout recommends 2 oz copper, not this draft's provisional 1 oz.

These are conservative signal-size choices relative to
[JLCPCB's published capabilities](https://jlcpcb.com/capabilities/Capab), not a
completed manufacturing qualification. Final review must also cover through-hole
annular rings, solder-mask slivers, silkscreen, finished-hole tolerances, copper
weight, drill/edge spacing, component courtyards and the chosen assembly process.
The power distribution cannot be sized from a generic minimum-width rule.

## ERC modelling limitations — not hidden waivers

The socket symbols are electrically passive: ERC does not know the internal
Teensy or Mini circuitry. Five power flags explicitly declare real sources after
passive parts: supply ground, Teensy-generated 3.3 V, protected 12 V, diode-OR VIN,
and regulated buck output after its inductor. Flags are declarations, not extra
supplies or proof that the circuit regulates correctly.

IC inputs/outputs are typed, but transistor, diode and connector symbols are
generic physical-pin representations. ERC cannot validate MOSFET orientation,
analog stability, cable reversal, voltage thresholds, heat, power sequencing or
firmware. Separate datasheet/physical checks are necessary. There are no approved
ERC/DRC suppression waivers; intentionally unused contacts have explicit no-connect
markers. Unrouted nets must be completed, not suppressed.

## Outstanding work, in order

1. **User hardware evidence:** confirm actual Mini revision/socket geometry,
   encoder board and every cable contact, and wrist variant/connector. These can
   change component placement and net order.
2. **Safety choice:** non-latching kill versus a hardware latch with manual reset.
   The current draft is non-latching and can restart when the loop is restored.
   The user explicitly requested leaving this choice flagged for now; do not
   interpret that as approval of automatic restart behavior.
3. **Circuit qualification:** exact 12 V STS3215 electrical levels and power-off
   injection behavior; final wrist bias/isolation; fuse/current budget, inrush,
   regenerative overvoltage and power-path worst-case voltages.
4. **Physical design:** confirm available base size and socket heights; refine
   buck-converter placement and SPI source-resistor placement. Finish legible
   connector/polarity/test-point silk labels; most reference designators are
   currently hidden to avoid printing over pads.
5. **Routing:** input/fuse/MOSFET and local buck connections are now hand-routed.
   Complete 12 V/5 V distribution, six separate motor returns, wrist return and
   the remaining ground-star branches. Plan
   quiet logic ground and fingertip return before signal routing. Complete signals
   with continuous return paths; do not connect separate ground names with a
   blanket plane. Remaining open connections are real unfinished design work.
6. **Release validation:** zero unrouted nets, DRC/ ERC clean with any noncritical
   waivers individually justified, schematic-to-board consistency, final BOM and
   assembly rotations/availability, power and mechanical review by an experienced
   electronics designer, then manufacturing outputs.
7. **Firmware and bench bring-up:** implement the new six-axis pin map, keep all
   requests low at boot, run `initFOC` only on command, retain explicit `loopFOC`,
   and measure simultaneous PWM/SPI/FOC timing. Never use the old bench sketch as
   though it implemented this board's wiring.

## First-prototype test sequence (after release, not permission to order now)

Use a current-limited bench supply and keep the mechanism unloaded. Do not connect
the phone or wear/hold the moving assembly for first power-up.

1. Without modules or power: inspect all soldering and polarities, confirm connector
   mappings, check for unintended rail shorts. Account for capacitors charging
   from the meter rather than interpreting every initial beep as a permanent short.
2. Verify the Teensy's VUSB/VIN link is cut before connecting board and USB power
   together. Check USB-only, board-only and both-source operation without motors;
   ensure no board power is fed back toward the PC.
3. Power the carrier alone with a low current limit; measure protected 12 V, buck
   5 V and VIN. Check converter waveforms and temperature. Disconnect and verify
   discharge before installing the Teensy.
4. With Teensy only, measure 3.3 V and startup enable states. Open/short the NC loop
   and verify all six gated outputs go low with open loop even if firmware stalls.
5. Add one *verified* encoder, check its 3.3 V and raw SPI data, then add one Mini
   and motor. Start with a conservative voltage limit; `initFOC` moves the shaft.
6. Test kill and explicit re-arm, then repeat axis by axis. Scope noise with motors
   commutating, not just stationary. Validate connector and wire temperature.
7. Add wrist only after interface qualification. Check data levels, transmit
   turn-around, kill behavior and powered-off injection before combining loads.
8. Increase simultaneous load while logging input peaks, supply rise during
   braking, 5 V/3.3 V dips, loop time and faults. Revisit fuse and copper sizing
   with measurements. Connect fingertips/phone last and check for phantom touches.

Never move phase leads on a live rail. Stopping firmware does not discharge the
bulk capacitors or establish safe isolation.
