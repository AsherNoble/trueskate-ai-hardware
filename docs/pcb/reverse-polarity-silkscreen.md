# Reverse-polarity protection and assembly silkscreen

Current board remains **150 × 140 mm, two layers, 1 oz**. All existing component positions, Teensy assignments, Mini holes/courtyards, encoder mapping and hardware kill logic are retained. Three hand-soldered THT parts are added after F1; the silkscreen is replaced.

## Protection circuit and parts

`J5 +12 V → F1 → 12V_PREPOL → Q1 drain → Q1 source → 12V_FUSED → six Minis/capacitors`.

| Part | Selection | JLC library | Function |
|---|---|---|---|
| Q1 | Infineon IRF4905PbF, TO-220AB | [C2564](https://jlcpcb.com/partdetail/C2564) | P-channel, −55 V, 20 mΩ maximum at VGS=−10 V/TJ=25°C; −74 A at TC=25°C |
| D1 | ST(Semtech) 1N4742A, DO-41 | [C2545](https://jlcpcb.com/partdetail/C2545) | Nominal 12 V, 1 W gate/source zener |
| R2 | TyoHM RD1/4W10KJT/BA1, axial | [C433778](https://jlcpcb.com/partdetail/C433778) | 10 kΩ, 0.25 W, ±5%, gate to GND |

All three were verified in JLC's live library; saved page text is in `pcb/sources/reverse-polarity/`. Listing/stock is time-dependent; these parts stay hand soldered. All components, including J31–J36 JST connectors, are hand soldered.

The TO-220 pad pitch stays 2.54 mm; Q1 uses 1.4 mm finished drills and 2.2 mm pads. This clears the datasheet’s maximum 1.01 × 0.61 mm lead rectangle (1.18 mm diagonal), with assembly allowance.

**Pinout is 1=G, 2=D (also exposed tab), 3=S.** Q1 drain connects to the fused unprotected input and source to the protected rail. This reverses the conventional high-side load-switch orientation: the body diode points from input/drain toward output/source. With correct polarity it initially charges the output and negative VGS then turns on the channel. With reversed input and initially uncharged output, the diode is reverse biased and VGS is approximately zero.

D1's **band/cathode/pad 1 connects to Q1 source**, its anode/pad 2 to gate. R2 joins gate to GND. The 12 V value is nominal (11.4–12.6 V at the specified test current); no transient-clamp qualification is claimed. Q1's absolute VGS rating is ±20 V. See [Infineon's datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-irf4905-datasheet-en.pdf) and the [independent topology report](../../pcb/review/checks/reverse-polarity-review.json).

### Copper and cooling

The existing shared bus is 12 mm wide. The new source connection flares into 6/12 mm copper. The short **4.58 mm source and 5 mm drain lead escapes use parallel 2 mm tracks on both layers**, with four Ø1.2/0.6 mm vias at each flare. Fused-input copper is 6 mm wide. The closely spaced TO-220 pins prevent a 12 mm-wide trace directly at the pads. Existing per-axis/phase routing remains unchanged. GND pours, island removal and the 389 reviewed ground stitches remain; the eight new vias are power vias, not GND stitches.

**Q1 needs no heat sink below ~5 A continuous.** The v1 operating assumption is a few sustained amps from a current-limited bench PSU. At the 20 mΩ room-temperature reference, I²R gives **0.18 W at 3 A** and **0.50 W at 5 A**; this is accepted within bare TO-220 free-air capability for this prototype. **12 A is the copper-sizing worst case, not a sustained operating point.** No heat sink is required or selected for v1, and sustained-12 A temperature validation is not outstanding. Copper/thermal qualification remains stopped. Q1's exposed tab remains connected to the unprotected drain.

Charged-output polarity reversal, inrush and surge testing are **out of scope for this prototype**. The single P-MOS topology's electrical behavior is unchanged; these are scope decisions, not claims that those cases were tested or that the circuit provides reverse-current/load-disconnect protection.

### Accepted v1 operating decisions

- **Kill-buffer supply ramp: accepted for v1.** During the 3.3 V ramp the Teensy does not drive PWM; firmware boots with the motor disabled and only calls `initFOC()` on command. EN alone is not a motion command, so an isolated EN-high transient during this ramp is accepted as non-hazardous for this operating sequence. The original datasheet DC guarantees are unchanged; the ramp is removed from the outstanding list.
- **Encoder 3.3 V load: accepted for v1.** [PJRC specifies 250 mA as the recommended maximum external load](https://www.pjrc.com/store/teensy41.html#power). Six AS5048A at the assumed ~15 mA each total **~90 mA**, leaving **~160 mA** for the two SN74LV125A and the carrier bias circuitry. This is an external-load allowance, not a total regulator rating from which the Teensy's own consumption must be subtracted again. TI specifies 20 µA/package quiescent ICC under the datasheet test conditions; the carrier's 19 possible 10 kΩ bias loads add no more than about 6.6 mA at 3.3 V/5% resistance tolerance. The nominal encoder-plus-buffer/bias budget is comfortably below 250 mA. [TI datasheet](https://www.ti.com/lit/ds/symlink/sn74lv125a.pdf). The encoder current is a design assumption, not a new measurement.
- **Return paths and SPI integrity: accepted for v1 on two layers.** Keep the [measured gap audit](../../pcb/review/checks/return-path-review.json) and [gap map](../../pcb/renders/copper/return-path-gaps.svg) as documentation. Use **1–4 MHz SPI**, reducing the clock further if encoder reads glitch. This pass records the firmware policy without changing firmware.

## Silkscreen

The title is `TSAI-FOC6 v1 · 2026-10`, with `Asher Noble · CC BY-NC`, the full GitHub URL, and a blank **15 × 6 mm filled white board-number box**. `USB ONLY` is removed from the PCB. The literal `USB →` label is rotated 180° so its arrow points toward the physical left-facing socket.

All six source-derived Mini silhouettes are printed with a **0.35 mm outward visibility allowance**; the existing +0.5 mm mechanical courtyards are unchanged. Each column has a chip icon in its visible gutter, oriented using U1 pad 1 in the tagged EasyEDA PCB: U1 centre (4108,3085.5), pad 1 (4091.366,3096.783), relative to H1.9 (4089.5,3046), 0.254 mm/unit. The icon is an orientation aid, not an extra component footprint. No text is printed inside a socketed module's body. Teensy has its full rectangular outline with a 0.35 mm visibility allowance.

There are **28 pin-1 triangles**: control and phase groups on each Mini, six motor headers, six JSTs, both Teensy sockets, the input and kill headers. Bulk positive terminals have external `+` marks. A1–A6/M1–M6/ENC1–ENC6 remain. Each encoder gutter carries `TODO` and all six numbered signal names taken from the same `encoder_pin_order` source as the README and netlist. The harness remains **VERIFY WITH MULTIMETER AGAINST AS5048A BOARD**.

Input `+12 V`/`GND` labels align with actual pins. The fuse and switch labels are `F1 ATO · rate to supply` and `KILL (NC) · open = motors off`. `Populate A1-A3 first` is present. **All 79 text items are at least 1 mm high with 0.15 mm strokes.** No text intersects a socketed module body; strict DRC checks pad/mask/edge clearance. The board number box remains empty. [Silkscreen audit](../../pcb/review/checks/silkscreen-review.json).

## Validation and outstanding work

**ERC and strict DRC pass with zero violations, opens and schematic-parity issues; no DRC exclusions or ignored checks. A clean rebuild also passes.** Existing reviewed ERC ignore categories remain unchanged. Independent checks cover all 299 schematic contacts, 36 isolated NCs, 65 footprints, unchanged Mini drill geometry, the protection pin/diode topology, existing kill/partial-population states, GND connectivity and text/module bounds. The accepted two-layer reference gaps remain documented by the current return-path audit.

The only outstanding items are:

1. **1:1 print fit check** — the user will check SD socket/card clearance, module/socket heights and mechanical fit.
2. **SH pin order verification** — the user will check continuity against the AS5048A board and provide the verified order. Existing TODO labels remain until then.
3. **Optional human review.**

No board or firmware changes accompany these decisions. The recorded gap audit remains marked **accepted for v1**. Fabrication and assembly files are in [pcb/manufacturing](../../pcb/manufacturing/README.md), with PCB assembly OFF and all parts hand soldered.

Assembly comparison: [manufacturing packages](../../pcb/manufacturing/README.md#assembly-and-cost-comparison-five-carriers). The selected order is bare PCB; all components including the six JSTs are hand soldered. Full-carrier stocked-only assembly is unavailable on the unchanged board; see the separate 79-part planning scope and stock evidence. This procurement limitation does not add a prototype validation item.

Selected build: **bare PCB, all parts hand soldered including J31–J36**. Upload only the fabrication ZIP and leave PCB assembly off.
