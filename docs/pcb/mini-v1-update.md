> **Historical scope:** the [edge-layout revision](edge-layout.md) supersedes layout, ground, assembly and hardware-kill descriptions below. Use the current PCB README and review artifacts for this revision.

# Mini v1.0 direct-power footprint

The carrier now uses one `TrueSkate:SimpleFOC_Mini_v1.0` footprint per Mini
(J11-J16), with 10 control, 3 phase and 2 power contacts. J41-J46 and their
six external power-wire pairs are removed. Each Mini uses a 2x5 control socket,
a 1x3 phase socket and two independent machine-pin power receptacles.

## Source and geometry verification

Upstream is [SimpleFOCMini at tag v1.0](https://github.com/simplefoc/SimpleFOCMini/tree/v1.0),
commit `848e8ece46d045ac24283e2d6ee9ea4ba8ef95d5`.
The original files and SHA-256 manifest are retained in
[`pcb/sources/simplefoc-mini-v1.0`](../../pcb/sources/simplefoc-mini-v1.0).

`extract_mini.py` reads `Drill_PTH_Through.DRL` as metric, absolute, 3:3.
Transform: `x = drill_x + 1.143`, `y = -3.937 - drill_y`. This is a Gerber-to-
PCB coordinate convention change, not a physical mirror. H1 pin **9** is the
new origin; H1 pin **1** remains at (10.160, 0). The Mini is component-side up,
pins downward. Existing control/phase locations on the carrier are retained.

- Control: X = 0, 2.540, 5.080, 7.620, 10.160; Y = 0, 2.540.
- Phases: X = 3.556, 6.096, 8.636; Y = 17.653. No grid snapping.
- GND = (17.399, 3.810); VIN = (17.399, 8.763); pitch = **4.953 mm**.
- Actual source tools are **1.101 mm** (control/power) and **1.021 mm**
  (phases), versus the plan's rounded 1.10 / 1.02 mm. The footprint uses
  the exact source tool diameters. Power copper pads are 2.4 mm diameter.
- F.Fab follows `Gerber_BoardOutlineLayer.GKO`, including its arcs.
  The complete outline spans **26.083 x 21.012 mm**, including the ears.
  Courtyard bounds add 0.25 mm to that envelope.

The [overlay](../../pcb/mini-drill-overlay.png) compares the actual KiCad library
pad centres to the independently parsed upstream drills. The
[fit report](../../pcb/mini-fit-report.json) also checks every placed footprint:
**105 contacts checked; maximum position error 0.000000 mm**, below 0.05 mm.
Grey holes in the overlay include the upstream vias/mounting holes for context;
only the 15 connector contacts belong on the carrier.

## Schematic/netlist comparison

Both tagged EasyEDA files were read. The schematic wires and net labels are
traced independently; PCB pad identities associate their nets with the drills.
Compared with the carrier at WIP checkpoint `3883aa8`, **no control-header
net-assignment mismatches were found**. The existing assignments are retained.

| H1 contact | Verified upstream connection | Carrier connection |
|---|---|---|
| 1, 4 | GND | CGNDn, optional bridge left open |
| 2 | 3.3V output | NC |
| 3 | U1.27 / IN1 | An_PWM1 |
| 5 | U1.25 / IN2 | An_PWM2 |
| 6 | nRes / U1.16 | NC |
| 7 | U1.23 / IN3 | An_PWM3 |
| 8 | nSlp / U1.17 | NC |
| 9 | R4.2; R4.1 feeds EN1/2/3 | An_EN |
| 10 | nFlt / U1.18 | NC |

P1/P2/P3 remain OUT3/OUT2/OUT1, wired to PH3/PH2/PH1 respectively.
New power contacts are VIN -> 12V_FUSED and GND -> the axis's PGNDn.
The six returns still meet logic GND only at NT1 on the bare carrier.

## Power and capacitors

Each supply branch is **2.0 mm** wide and each independent return is
**1.8 mm** wide, locked on external copper, without small power vias or trace
neck-downs. Bulk-capacitor connections are 2.0 mm; the ceramic stubs are 0.6 mm
and EN pull-down stubs 0.4 mm. Those stubs do not carry the motor feed current.
The existing shared supply trunks are 3.0 mm.

For 35 um copper and a 10 C rise, the external-layer IPC-2221 estimate
`I = 0.048 * deltaT^0.44 * area_mil2^0.725` gives a minimum width of
**1.367 mm at 3 A**. Both chosen branch widths exceed it. See the equation in
[TI's layout guidance](https://www.ti.com/lit/an/snva766/snva766.pdf).
`verify_power.py` checks continuous full-width paths from F1/NT1 to all six
power contacts and from each bulk capacitor to its Mini.

C11-C16 and C21-C26 are moved alongside the power-pad edge, with physical
courtyard clearance from the Mini, neighboring modules and each other. F1
moves 8 mm toward the input to clear the first capacitor. Capacitor-pad to
matching Mini-pad distances are recorded in
[`power-routing-review.json`](../../pcb/power-routing-review.json):

| Placement | Bulk cap | Ceramic cap |
|---|---:|---:|
| Upper three Minis | 11.2 mm | 10.4 mm |
| Lower three Minis | 13.8 mm | 8.5 mm |

These are centre-to-centre distances, not trace lengths. The module's onboard
bypass capacitors remain necessary. The 3 A sizing is for individual branches;
it does not establish an 18 A simultaneous-load rating for the shared supply,
star, input connector or fuse.

## Assembly and review artifacts

The [BOM](bom.md) adds **12 single machine-pin receptacles**, removes all six
Mini supply terminals, and removes the power-wire pairs. A receptacle must fit
the 1.101 mm finished hole, accept the Mini's actual pin, align with the other
socket heights and carry at least 3 A per contact. An exact purchased MPN has
not been asserted without those mechanical specifications.

Existing files under `pcb/fabrication/2026-10-18/` and the old assembled mockups
are historical snapshots of the wire-powered revision. They are not outputs
for this footprint change. The current native board, schematic, fit drawing,
overlay and review renders describe the direct-power revision.
