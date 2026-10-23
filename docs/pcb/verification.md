# Carrier v1 verification and limits

Review design, **not a fabrication release**. Checked with KiCad 10.0.6 on
2026-10-24. The machine-readable reports and file hashes in
[`pcb/review-status.json`](../../pcb/review-status.json) identify the checked
revision of the artifacts. No manufacturing files were regenerated for this update; the older
`pcb/fabrication/2026-10-18/` snapshot is explicitly marked obsolete for this layout.

## Automated results

- Electrical rule check (ERC): zero errors or warnings, no exclusions.
- Design rule check (DRC): zero violations, zero unconnected items, zero
  schematic/PCB parity issues, no exclusions and no ignored check types.
- Native schematic netlist and actual PCB agree on 217 connected contacts and
  34 individually isolated, intentionally unused contacts.
- All 47 schematic references use through-hole footprints. Four additional
  M3 holes are board-only features. There are no surface-mount parts.
- Fixed pin map: 18 PWM outputs, 12 non-PWM EN/CS pins, SPI0 and nine unused
  digital contacts. All six axes are edge-aligned; the center-aligned build
  flag is absent and `lib_archive = no` is retained.
- Teensy VIN is isolated; Mini regulator outputs and unused control contacts
  are isolated. Encoder socket order, six 10k pull-downs, six default-open
  control-ground bridges and source-derived Mini hole geometry are checked.
- The updated 178 deliberate power/phase/ground/supply segments are unchanged
  after signal routing. Explicit quiet-ground links use 15 locked
  segments. All 32 ground vias are deliberately placed and locked.
- Final copper contains 615 track segments and 68 vias (36 signal, 32 ground).
  Only PWM, EN, CS and SPI nets may contain imported automatic routes.
- The one-page guide covers all 67 real nets exactly once. KiCad's 34
  `unconnected-(...)` names label unused single contacts, not additional wires.

`export_review.py` fails if any strict check fails. `audit.py`,
`verify_board.py`, `verify_mini.py`, `verify_power.py` and `tools/check_ground_bridges.py` add independent checks
against the circuit source, exported netlist and actual copper geometry.

## Board rule profile

The target is ordinary **two-layer, 1 oz copper, green solder mask**, 1.6 mm
board material. A copper ounce is a thickness specification, not board weight.
Solder mask is the insulating coating over copper; silkscreen is the printed
label layer. These settings are checked against
[JLCPCB's published capabilities](https://jlcpcb.com/capabilities/pcb-capabilities).
They are deliberately less demanding than the smallest available copper sizes.

| Check | Project minimum / chosen size |
|---|---:|
| Copper track width / spacing | 0.20 / 0.20 mm |
| Via outside diameter / drilled hole | 0.70 / 0.30 mm |
| Via annular ring (copper around hole) | 0.20 mm |
| Hole-to-hole and hole-to-other-copper clearance | 0.45 mm |
| Copper to board edge | 0.50 mm |
| Solder-mask web / opening expansion | 0.10 / 0 mm (1:1) |
| Label height / character stroke / label-to-pad clearance | 1.0 / 0.15 / 0.15 mm |

Motor power uses deliberately routed 3 mm main supply copper, 2 mm supply
branches, 1.8 mm individual motor returns and 1 mm phase routes. The Mini supply/return paths
exceed the 1.367 mm IPC-2221 estimate for 3 A on external 35 um copper at a
10 C rise. `verify_power.py` checks continuous full-width branches. This does
not establish a simultaneous six-motor current rating.

## Visual and mechanical review

The native schematic PDF has nine pages; the net guide and fit template each
have one. Review PDFs are rendered to images and inspected for clipping and
readability. Detail sheets use portrait A4 with enlarged labels. Native top,
bottom and angled 3D renders are also inspected. Plug-in Teensy, Mini and encoder
boards and external wires are omitted from the render; it is not an assembled
rig model.

The original control/phase socket positions, encoder pin 1/order and base size
are retained. The new power receptacles follow the exact v1.0 drill geometry.
The library and all six instances have 0.000000 mm maximum contact-centre error
against the source drills. See the [drill overlay and pin audit](mini-v1-update.md).

## What the checks cannot prove

ERC checks declared electrical connections; DRC checks geometric rules. Neither
simulates motors or proves safe current, correct purchased parts, solder quality,
signal integrity, firmware behavior or compatibility with the exact power supply.

Human review and bench tests still need to establish:

1. Simultaneous motor current, rail heating, connector limits, supply current
   limit and the fuse cartridge. 3.15 A time-delay is only a candidate.
2. Input and electrolytic-capacitor polarity, encoder voltage/current budget,
   socket orientation/height and final purchased header fit/current rating.
3. Reliable encoder communication over six real cables. The central on-board
   SPI copper totals 193.5 mm SCK, 206.2 mm MOSI and 195.4 mm MISO across all
   branches; these are not single-cable lengths or a speed guarantee.
4. EN stays low while the Teensy resets or USB is disconnected; power-up/down
   behavior is tested with a current-limited supply and restrained mechanics.
5. Motor energy returned to the supply does not raise 12 V excessively; the
   large capacitors store charge and must be measured before rewiring.
6. Ground performance with JP1-JP6 left **open**. Closing them creates additional
   ground paths through the Mini and needs deliberate review.
7. Six-axis firmware migration and edge-aligned timing. The runtime remains the
   one-axis bench version with old EN/CS assignments; it is not ready to flash
   for this carrier. Bench evidence in `firmware/bringup/` is unchanged.

There is no hardware kill or reverse-polarity protection in this simplified v1.
Cutting USB is not a motor-power disconnect. See the
[human-review and staged bring-up checklist](hardware-check.md) before ordering.
The removed full-feature draft is recoverable from local checkpoint `36e9dca`.

## Tool diagnostics

Standalone KiCad Python prints a wxApp-traits diagnostic in this environment;
the scripts exit successfully and their assertions run. Native PDF/PNG commands
may print a Fontconfig cache-version warning. These are tool-environment messages,
not ignored ERC/DRC findings. See [tooling](tooling.md) for reproduction commands
and installed software. No firmware flash, cloud routing, PCB upload or git push
was performed.
