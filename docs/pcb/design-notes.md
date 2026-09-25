# TrueSkate main board v1 — beginner's design walkthrough

Status: **review prototype, NOT ready to order**. Start here, then read
[verification.md](verification.md) for exactly what has and has not passed.
The schematic is a proposed electrical design; the board has component placement
and hand-routed local power traces, but still needs its remaining routing and engineering review.
Do not upload these files for manufacture yet.

## What this board does

A printed circuit board (PCB) replaces many loose wires with copper connections.
This one is a *carrier*: it holds a removable Teensy 4.1 computer module and six
removable SimpleFOC Mini motor-driver modules. A driver converts low-power control
signals into current through a motor. An axis is one independently controlled
motor: two curl motors and one splay motor for each of index and middle fingers.

An encoder measures shaft angle. Field-oriented control (FOC) repeatedly uses that
angle to choose motor currents. That fast loop stays on the Teensy; the host still
sends gestures, not individual motor-control steps. This work does not add a host
control loop or change the gesture-coordinate contract.

Only the main board is included. The wrist gets one port for the **12 V variant**
of the STS3215. There are no beautification drivers and no left-thumb board.

The input document actually present in this checkout is
[../pcb-requirements.md](../pcb-requirements.md). The newer user instructions take
precedence: edge-aligned control for all six axes, male motor-phase headers, and
the approved short screw-terminal power wires. The historical bring-up sketches
are unchanged.

## How to read the files

A schematic describes **what connects to what**, not where it sits. A *net* is a
named electrical connection; matching red labels on different PDF pages are the
same wire. A *footprint* describes physical solder pads and holes. A *trace* is a
strip of copper joining pads. A *via* is a small plated hole joining the two copper
layers. An *unconnected item* means the required copper path does not exist yet.

The PDF's rectangles represent physical connectors or integrated circuits (ICs,
several circuit elements in one package). Pin numbers are component contact
numbers. For the Teensy socket, the name beside a pin is the Teensy signal, while
the small outside number is the carrier socket's contact number. An X means a
deliberately unused contact, not an accidental missing wire. `R` references are
resistors, `C` capacitors, `D` diodes, `Q` transistors, `U` ICs, `J` connectors,
`L` inductors, `FB` ferrite beads and `TP` test points.

Direct KiCad scripting was chosen because it preserves the Mini's off-grid socket
geometry and generates native, editable KiCad files without a conversion layer.
The generator also makes the six repeated circuits and pin allocation auditable.
Edit [../../pcb/generate.py](../../pcb/generate.py) and
[../../pcb/design.json](../../pcb/design.json), then regenerate: rerunning it
overwrites generated schematic, placement and routing files. Do not make manual
KiCad edits and then blindly regenerate.

## 1. Controller and pin allocation

The Teensy plugs into two 24-contact **female sockets**, 2.54 mm between adjacent
contacts and 15.24 mm between rows. It is not soldered to this carrier. Choose
socket height sufficient to clear the small parts beneath it, provisionally at
least 8.5 mm; check the actual module underside before buying headers. The USB
connector faces the left side of the board and needs cable clearance.

Pulse-width modulation (PWM) switches a signal rapidly; changing its fraction of
time high changes the average drive. All six axes use **edge-aligned PWM** at one
common initial frequency of 25 kHz, above ordinary hearing. Center-aligned PWM is
not enabled. Channels sharing timer hardware must share frequency, even though
their duties differ. Allocation has been checked statically; simultaneous six-axis
waveforms and loop timing have not been bench-tested.

| Axis | Movement | PWM 1 / 2 / 3 | EN request | Encoder CS |
|---|---|---|---|---|
| A1 | Index curl 1 | 4 / 5 / 6 | 16 | 26 |
| A2 | Index curl 2 | 2 / 22 / 23 | 17 | 27 |
| A3 | Index splay | 7 / 36 / 29 | 20 | 32 |
| A4 | Middle curl 1 | 24 / 0 / 25 | 21 | 38 |
| A5 | Middle curl 2 | 3 / 33 / 37 | 30 | 39 |
| A6 | Middle splay | 8 / 9 / 28 | 31 | 40 |

EN means enable: the Teensy requests permission for a motor to run. CS means chip
select: pulling one encoder's CS low asks that encoder to answer. All twelve
EN/CS pins are **not PWM-capable**. The user requirement is stronger than simply
not calling PWM on those pins, and this map satisfies it.

| Shared function | Teensy pins |
|---|---|
| Encoder SPI0: MOSI / MISO / clock | 11 / 12 / 13 |
| Wrist Serial8: receive / transmit / transmit-enable | 34 / 35 / 41 |
| Future I2C link: data / clock | 18 / 19 |
| Hardware-kill status input | 10 |
| Unassigned spare contacts | 1, 14, 15 |

Serial peripheral interface (SPI) is a clocked connection with controller-to-sensor
data (MOSI), sensor-to-controller data (MISO), and a clock. Universal asynchronous
receiver/transmitter (UART) is a serial connection without a separate clock.
Inter-integrated circuit (I2C) is a two-wire addressed link for the future board.
The wrist's entire UART allocation is on non-PWM pins.

**Why not SPI0 plus SPI1?** There are only fifteen non-PWM digital pins on the
socketed outer headers. Twelve go to EN/CS, two to Serial8 and one to its direction
control. SPI1 would need pins 26, 27 and 39, already needed for those roles.
Using it would require changing an explicit constraint or adding pin-expansion
hardware. The v1 proposal therefore uses SPI0 for all six encoders.
The authoritative capability reference is [PJRC's PWM table](https://www.pjrc.com/teensy/td_pulse.html).

The existing production sketch is still the one-axis bench program: **it is not
the firmware for this new pin map**. Only its build configuration was changed:
the center-aligned build flag was removed and `lib_archive = no` retained.
Six-axis initialization, independent commands, common PWM frequency and measured
loop deadlines remain firmware work before this board can operate.

## 2. Removable Mini modules and motor phases

Each Mini gets a 2×5 control socket and a separate three-contact phase socket.
The footprint was extracted from the original
[SimpleFOCMini v1.0 source](https://github.com/simplefoc/SimpleFOCMini/tree/v1.0),
commit `848e8ece46d045ac24283e2d6ee9ea4ba8ef95d5`, not guessed from a photo.
That revision uses EasyEDA source files, not KiCad. The source files, licence,
extraction script and extracted coordinates are retained in `pcb/sources/`.

Pitch means the distance between adjacent contacts. The phase socket's position
relative to the control socket is **not** an integer multiple of 2.54 mm. Snapping
both sockets to a convenient grid would make a rigid module impossible to insert.
See [mechanical.md](mechanical.md) for the coordinates and the remaining fit check.

Important: Mini control pin 2 is the Mini's own 3.3 V regulator **output**, not a
3.3 V power input. It is left unconnected. Tying it to the Teensy's regulator would
make two supplies fight each other. Reset, sleep and fault are also not connected
to the carrier; the original module's own circuitry supplies its normal operating
bias. This depends on using the verified module revision.

Each Mini receives power through the **approved short red/black wire pair** from
J41–J46 into its existing screw terminal. The carrier terminal uses 3.81 mm pitch;
its pitch does not have to match the Mini because wires join them. Keep each pair
short, run its two wires together, strain-relieve it, and mark polarity at both
ends. Removing a Mini means releasing these two wires as well as unplugging it.
Its module-side control and phase headers must have downward-facing male pins to
mate with the carrier's female sockets; confirm what is actually fitted.

The Mini's control-ground contacts are deliberately unused. Its ground reference
comes from its dedicated power-return wire. This avoids a second motor-current
return through the controller area. The cost is that ground bounce on the power
return also changes the driver's logic reference. Short, stout paired wires and
an oscilloscope check are required; this choice is not proof of adequate signal
margin by itself.

A motor has three phase wires: the three winding-drive connections. J21–J26 are
**male 1×3, 2.54 mm headers**, matching your female Dupont ends. Three deliberately
routed 1.0 mm traces join each Mini's phase socket to its motor header. These are
short local routes, not a validated continuous-current rating. Contact quality
and cable gauge may become the limit before copper does. Start with conservative
voltage limits, measure temperature, and never move a phase lead with power live.

## 3. Encoder connectors and signal quality

J31–J36 are genuine JST SH six-contact, 1.0 mm **top-entry** surface-mount sockets,
part `BM06B-SRSS-TB(LF)(SN)`, LCSC `C160392`. Surface mount means soldered to pads
on the surface rather than leads pushed through holes; JLCPCB assembles these.
The cable plugs in vertically. The original side-entry candidate had conflicting
stock listings, while the top-entry part showed stock on its current product page.
[JST's SH drawing](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf) covers both types;
the change does not establish the unknown motor-side pin order.

The footprint-pin order is **verified**, read from the working bench breakout
with pin 1 the square pad and the traces running straight from socket to header:

| Contact | Signal |
|---|---|
| 1 | CLK: SPI clock |
| 2 | MISO |
| 3 | MOSI |
| 4 | CSn: active-low chip select |
| 5 | VDD: 3.3 V supply |
| 6 | GND: ground |

**CSn is contact 4, not contact 1.** The earlier assumed order had CSn first and
every signal shifted by one; anything built to that order will not work.

What this settles is the *signal order along the connector*. It does not settle
which physical end of the carrier footprint KiCad calls contact 1 — check that
against the fabrication drawing before release, because a mirrored footprint
puts 3.3 V where ground should be. “AS5048A” specifies the chip, not how a
manufacturer wired its connector. The
[iFlight motor listing](https://shop.iflight.com/index.php?product_id=1584&route=product%2Fproduct)
and [encoder listing](https://shop.iflight.com/product-cat123/as5048a-magnetic-encoder-pro262)
did not establish your complete board-to-board cable mapping. A wrong power order
can destroy the encoder or Teensy. **Do not order or plug in on this assumption.**

Each CS line has a 10 kΩ pull-up: a resistor that holds it high while the Teensy
starts, so encoders do not all speak at once. A 33 Ω series resistor on each CS,
and at the shared clock/MOSI source, is intended to soften sharp electrical edges
and reduce reflections. A reflection is a small echo along a cable that can be
mistaken for another transition. These values are starting points, not a substitute
for waveform measurements. Source resistors should ultimately be beside the
source pins; present CS-resistor placement still needs that routing refinement.

Each encoder connector has a 100 nF bypass capacitor: a small local charge store
that helps keep its supply quiet. Keep SPI traces in the controller region,
separated from phase copper, with a continuous logic-ground return beneath them.
The planned six-cable fan-out needs testing with motors actually switching.
Start at the bench-proven 1 MHz; raise toward 2–4 MHz only after error and timing
measurements. Static-shaft tests at 8 MHz do not prove a moving six-axis harness.

## 4. The 12 V input, fuse and reverse-polarity protection

J5 is a two-contact 5.08 mm input terminal. Select a real part rated for at least
10 A, with its footprint and wire range checked before purchase. Feed it only from
a regulated, enclosed **12 V DC** supply. DC means fixed polarity; this board does
not accept mains electricity. No work on exposed mains is part of this design.

F1 is a replaceable 5×20 mm fuse. A fuse opens when excessive current heats it;
without one, a wiring fault can keep heating a connector or track. **5 A time-delay
is a candidate, not a final approved rating.** Time-delay fuses tolerate short
startup surges. Choose the exact fuse, holder and supply after measuring the
combined load and validating protection of the weakest wire or connector.

Q1 is a P-channel MOSFET (a transistor used as a low-loss power switch), proposed
FQP47P06. Its drain faces the fused input and source faces the protected rail. That
orientation lets its internal diode initially feed a correctly connected supply
but block a reversed one; its gate then turns on for lower loss. R3 pulls the gate
down. D3 is a 12 V Zener diode, a device selected to clamp gate-to-source voltage.
Without reverse protection, a swapped input pair could damage every powered block.

There is no completed transient-suppression or braking-energy circuit. A motor can
return energy to the supply while slowing down, and many wall supplies cannot
absorb it. The 35 V capacitors do **not** make the 12 V servo safe at 35 V. The
[12 V STS3215 page](https://www.feetechrc.com/525603.html) specifies a 4–14 V operating
range and 2.7 A stall current at 12 V. Supply rise during braking must be measured;
add appropriately engineered clamping or a dissipative braking path if necessary.

The tentative input envelope is 12 V, 5 A total (60 W). It is not a promise that
all six motors plus a stalled wrist can operate together. Motor winding current
is not the same as input-supply current. In SimpleFOC voltage-torque mode,
`current_limit` is inert: `voltage_limit` is the relevant software bound, and even
that is not a measured hardware current regulator. Do not size the whole system
by multiplying a single optimistic bench measurement.

## 5. Local motor capacitors

C11–C16 are your Panasonic **EEUFR1V102B**, 1000 µF, 35 V capacitors. Capacitance
measures stored charge per volt; these large local reservoirs supply short motor
current pulses and reduce disturbances along the input wiring. Each has a 100 nF
ceramic capacitor beside it for faster disturbances. Removing them would put more
pulsed current into the shared cable and logic supply. The Mini's own close-in
ceramics still matter: the carrier capacitor is separated by the power wires.

The [Panasonic dimensions](https://na.industrial.panasonic.com/products/capacitors/aluminum-electrolytic-capacitors/series/83367/model/83812)
are **12.5 mm diameter, 20 mm high, 5.0 mm lead spacing**. The footprint uses those
values. These are polarised: the negative stripe goes to the motor return; the
positive lead goes to +12 V. Reversing one can cause heating, venting or rupture.

Together the six store about 0.432 joule at 12 V:
`energy = 0.5 × 0.006 farad × 12²`. They also draw an initial charging surge.
Inrush, fuse survival and supply startup therefore need testing. Hardware kill
does not instantly empty them. Disconnect power and verify the rail is discharged
before moving wiring; a software stop is not power isolation.

## 6. Five volts, three volts and safe USB coexistence

U4, AP63205, is a **buck converter**: an efficient switching supply that turns
12 V into 5 V. L1, an inductor (a coil that stores magnetic energy), and its
capacitors smooth the switched energy into the 5 V output. C5 is the input bypass;
C6 is the bootstrap capacitor that supports the converter's internal high-side
switch; C7/C8 smooth the output. Its fixed-5 V part number matters: do not substitute
an adjustable or different-voltage variant without redesigning it.

The [manufacturer's reference circuit and layout guidance](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf)
are the starting point. The switch node (`BUCK_SW`) must stay small and away from
SPI. The input-capacitor/current loop must be very short. The local converter
connections are now hand-routed, with a separate output-voltage sensing branch
and a bottom-side ground area connected through plated vias. This area carries
return current and spreads heat; it joins the input ground junction through its
own branch, not a motor return. An electrically correct but badly laid-out
converter can create noise or fail.

**Thermal qualification remains open.** The datasheet recommends 2 oz copper
for a 2 A layout; this draft still proposes 1 oz and does not claim a 2 A usable
output. Measure the actual Teensy/encoder/logic demand and converter temperature,
and revise copper weight or layout if needed. Having a ground area is not proof
of sufficient cooling. The rest of the 5 V distribution remains unrouted.

D1/D2 are Schottky diodes, one-way devices with comparatively low forward voltage
loss. They select whichever is available, board-generated 5 V or USB 5 V, without
feeding one source backwards into the other. Their combined output `VIN_OR` feeds
Teensy VIN. The voltage is a little below 5 V; check the minimum during full-load
and low-USB-voltage tests against the Teensy's allowed VIN range.

**Required physical modification:** cut the Teensy's factory VUSB-to-VIN link as
described by [PJRC](https://www.pjrc.com/store/teensy41.html), confirm it is open
with a continuity meter, and wire the isolated **VUSB pad** to J3. Do not confuse
that with the USB-host 5 V pad. No cutting or soldering has been done by this task.
If the link is left intact, the diodes on the carrier cannot prevent back-feeding
the PC. Never use both sources until this is checked.

The Teensy supplies the 3.3 V logic/encoder rail. Its pins are **not 5 V tolerant**:
feeding a 5 V signal directly can damage them. PJRC limits external loading of its
3.3 V output to 250 mA. Add up actual encoder, logic and future-link consumption;
the daughterboard connector is not an unrestricted power supply. Initially reserve
only 25 mA for expansion until a measured budget says otherwise.

## 7. Hardware kill

J4 connects a **normally closed (NC)** switch: the contacts conduct when the stop
button is not pressed. Opening it, or breaking its wire, makes `KILL_RAW` low via
R2. R1 limits a shorted cable's current; C1 filters brief noise. U3 has a Schmitt
input, meaning separate thresholds for going high and low, which helps avoid
chatter from a slowly changing signal.

U1/U2 contain AND gates: an output is high only if **both** inputs are high. Each
driver enable is `Teensy request AND KILL_OK`. Firmware can request movement but
cannot override an open NC loop. R11–R16 hold requests low during startup;
R21–R26 hold driver-side enables low if gate drive is absent. Without these parts,
an uninitialized input or software fault could leave a driver enabled.

The fourth gate of U2 also prevents wrist transmission while killed. Q4 pulls the
gate of the wrist's Q2 supply switch down only when kill permission is present;
otherwise R51 turns that switch off. Driver disable causes loss of commanded
torque, **not active braking**. A hanging load can fall or a tendon can relax.

This circuit is **non-latching**. Reclosing the switch restores permission and can
restart a motor if firmware has left its request high. A latching stop would
require a separate deliberate reset; that is preferable where unexpected restart
could hurt someone and remains a release decision. Firmware must lower all
requests on kill and demand explicit re-arming, but firmware alone cannot turn a
non-latching hardware circuit into a certified safety function.

This is not a safety-rated emergency stop. It does not guarantee protection from
a shorted power transistor, a ground fault or every possible component failure.
Bench-test the stop at each axis with stalled firmware and with USB-only power.
Test with no finger, phone or person in the mechanism's path initially.

## 8. Wrist servo and voltage translation

J6 provisionally uses a three-contact JST PH 2.0 mm through-hole connector, ordered
**GND, switched 12 V, DATA** by footprint contact number. “Feetech three-pin” alone
does not prove the housing, orientation or cable reversal. Verify the actual plug.

Half-duplex means both devices share one data wire and take turns speaking.
Teensy pin 35 transmits; pin 34 receives; pin 41 requests transmit mode. Q3 controls
the active-low output-enable pin on U5. When disabled, U5 is high impedance: it
electrically releases the wire so the servo can answer. R58 makes transmit default
off during boot. Firmware must wait for the last transmitted stop bit before
releasing the line, then allow the servo's specified reply timing.
R60 holds the transmit input at the UART's idle-high state during boot. R59 weakly
holds the shared data wire low if the servo is unpowered, so the receiver input
does not float; confirm the actual servo's idle pull-up can overcome this 100 kΩ
load. Ignore receiver activity while the servo is disabled.

The 12 V product is described as TTL half-duplex, but an exact electrical input/
output-threshold specification for this particular servo has **not** been verified.
The often-linked 6 V C001 datasheet must not be passed off as proof for the 12 V
C018. The draft conservatively provides a 5 V transmitter and a 5 V-tolerant
receiver rather than exposing a Teensy pin directly to the bus.

U5, SN74AHCT1G125, recognizes the Teensy's 3.3 V high and drives a 5 V output. It
uses `BUCK_5V`, **not** diode-reduced `VIN_OR`: AHCT requires at least 4.5 V.
[TI's AHCT data](https://www.ti.com/product/SN74AHCT1G125) specify overvoltage-tolerant
inputs, including input-leakage conditions with its supply at zero. U6,
[SN74LVC1G125](https://www.ti.com/product/SN74LVC1G125), is powered from 3.3 V but
accepts a 5 V input and outputs a Teensy-safe level. Its partial-power-down feature
limits back-powering when the Teensy supply is absent. The two families are not
interchangeable merely because they share a package.

R7 limits bus contention current and damps edges. R8 is an **unpopulated optional**
pull-up footprint: do not install it before measuring the servo's bus bias and
powered-off behavior. Otherwise the pull-up could feed a supposedly off servo
through its data pin. U5 itself does not provide the same power-off isolation as
U6: residual servo power, a failed buck supply, USB-only operation and power-down
sequencing need explicit injection-current tests or a revised isolated interface.
This is a release hold, not a waived issue. Supply kill, digital tri-state and
complete electrical isolation are different things.

## 9. Grounding and fingertip terminals

Ground is the common voltage reference and the return path for supply current,
not a magical place where current disappears. Motor current flowing through the
same narrow conductor as a sensor reference can move that reference voltage and
create bad readings or phantom screen touches.

The proposed **star ground** gives each motor its own return branch (`PGND1` to
`PGND6`) and the wrist its own `WRIST_GND`. They meet logic ground and the fingertip
branch only at NT1, a *net tie*: intentional copper that joins separately named
nets at a controlled location. It is copper, not a component you buy or solder.
NT1 is beside the input connector, with its first pad at (18, 22) mm. The input
return and converter ground branch are hand-routed; motor, wrist and fingertip
return branches and the main logic-ground plane are **not yet routed**. A ground
plane is a broad copper area that provides a low-impedance reference. Only a small
converter ground area exists so far; do not pour one over every named ground and
accidentally undo the star separation.

Fingertips connect to J8/J9 via separate ferrite beads FB1/FB2. A bead passes DC but
opposes high-frequency noise. Both have their own quiet branch to the star, not a
tap on a Mini ground wire. They are not resistive touch sensors, switched touch
outputs, galvanic isolation or protective earth. Galvanic isolation means there
is no direct conductive electrical path; this circuit does have one. Phone, USB
and supply grounding must be tested together because off-board cables can create
additional paths that bypass a carefully drawn star.

## 10. Future link and test points

J7 exposes GND, 3.3 V, I2C data and I2C clock. R54/R55 are 4.7 kΩ pull-ups needed
because I2C devices pull the lines low but normally do not drive them high. Keep
this cable short and check combined pull-up strength if the daughterboard also
has resistors. There is no daughterboard motor supply on this connector. An
external 5 V pull-up would violate the Teensy's input limits.

TP1–TP9 expose ground, protected 12 V, buck 5 V, VIN, 3.3 V, SPI clock, MOSI,
MISO and kill status. A test point is a safe place to put a meter or oscilloscope
probe without slipping between fine connector pins. D11–D19 are light-emitting
diodes (LEDs): three indicate the 12 V, 5 V and 3.3 V rails, and six indicate the
hardware-gated driver enables. Their 4.7 kΩ series resistors limit current, keeping
the load on each enable output small. Low-current visibility needs testing.
These show voltage presence, not actual shaft movement or a proven safety state.
An LED going dark does not prove capacitors are fully discharged; use a meter.

## 11. Size, assembly and what the pictures mean

Proposed size is **160 × 120 mm**, two copper layers, 1.6 mm board thickness and
1 oz copper (the conventional name for approximately 35 µm copper). Four 3.2 mm
non-plated holes accept M3 mounting screws, with centres 5 mm from each edge.
This is an initial spacious layout for six modules and six tall capacitors, not
a confirmed fit to the robot base. Leave clearance for the 20 mm capacitors,
socketed modules, screwdriver access, USB and cable bend radii.

JLCPCB assembles all small surface-mount parts, including the JST SH sockets.
You hand-solder the female sockets, male headers, screw terminals, fuse holder,
large capacitors, TO-220 transistors and leaded Zener. Purchase the fuse separately.
Fit and electrically inspect the carrier before plugging in expensive modules.

The PNGs are rendered from the actual KiCad placement, not AI-generated product
images. Standard component models are illustrative package shapes, not exact
supplier colours. The Teensy and Mini circuit boards themselves are **not modelled**;
their carrier sockets are. The bottom view deliberately shows missing routing:
the board is not made complete by a polished render.

## What I need from the real hardware

Before freezing connector wiring or completing a fabrication release:

1. Clear top/bottom photos of one actual Mini, its revision text and headers,
   beside a ruler. Confirm control-to-phase socket positions and power-terminal
   pitch against the source-derived drawing.
2. Close photos of the motor's encoder board, any pin labels, and both ends of its
   six-wire cable. An order screenshot or product link would help. With all power
   disconnected, identify end-to-end contact continuity; do not guess by colour.
3. A photo/measurement of the STS3215 plug and confirmation that the actual unit
   is the 12 V version. Obtain its exact electrical interface specification or
   measure safely using a suitable breakout before connecting the Teensy.
4. Available base dimensions, intended motor voltage limits and measured total
   running/peak input current. Decide whether kill must require a manual reset.

These checks can change footprints, polarity, power protection and board routing.
Until resolved, this package is for understanding and review, not ordering.
