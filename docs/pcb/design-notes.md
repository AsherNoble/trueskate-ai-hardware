> Historical layout notes. Superseded by the [current 3+3 layout](3plus3-layout.md).

> **Historical scope:** the [edge-layout revision](edge-layout.md) supersedes layout, ground, assembly and hardware-kill descriptions below. Use the current PCB README and review artifacts for this revision.

# v1: a six-axis wiring carrier

This board is your perfboard wiring made repeatable, not a new motor controller.
A **printed circuit board (PCB)** replaces wires with **traces**, copper strips
on its two faces. A **net** is one named electrical connection: every pad and
trace with that name is joined. Start with [the one-page net guide](nets.md), then
use this longer explanation when you want the reasons behind a connection.

The Teensy and six SimpleFOC Minis do the active work. Everything soldered to
this carrier is **through-hole**: leads go through drilled holes and are soldered
from underneath. **Female sockets** grip the removable modules' male pins. The
carrier requires no factory assembly and has no buck supply, hardware kill,
wrist port, fingertip terminals or expansion connector. Those belong to
[v2](v2-backlog.md). Human electrical review is required before ordering; passing
software checks does not prove that a physical board will operate safely.

## Why native KiCad scripting?

Direct KiCad scripting preserves the already verified Mini socket geometry and
produces editable native schematic and board files without another translation
tool. It also makes the deliberate power routes reproducible while letting
KiCad's own command-line checks examine the result.

## 1. Teensy sockets: the brain, powered only by USB

J1 and J2 are the two 24-contact female sockets. With the USB connector facing
left, J2 is the upper row and J1 is the lower row; do not mirror this top view.
**Pitch** means the distance between neighboring pin centers: 2.54 mm along each
row, and 15.24 mm between rows. The Teensy must have downward male headers.

USB powers the Teensy. Its regulator, a circuit already on the Teensy that
reduces voltage, supplies the carrier's **3V3** net: 3.3 volts for six encoders.
The carrier's VIN socket contact is physically present but electrically
unconnected. There is no carrier connection to USB's 5 V power or to a separate
5 V supply, so this design needs no cut to the Teensy's USB/VIN connection.
Do not add external power to VIN or 3V3. Teensy input pins cannot tolerate 5 V.
[PJRC's electrical guidance](https://www.pjrc.com/store/teensy41.html) is the
reference for its 3.3 V supply and digital limits.

Without these sockets the Teensy would need to be soldered permanently, or the
connections would depend on loose wires. Without a common ground, its signals
would not have a reliable voltage reference. USB ground and motor-supply negative
are intentionally connected at the ground star: this board is not electrically
isolated from your computer.

## 2. Six Mini sockets: low-power instructions, high-power outputs

A **driver** converts the Teensy's small control signals into motor current.
J11-J16 accept the six existing Minis. Each footprint represents a
2-by-5 control socket, a 1-by-3 phase socket and two single power receptacles.
An **axis** is one controlled motor, not one motor winding. The control/phase locations are
retained; VIN/GND are added from the v1.0 plated-drill source.

Each Mini receives three **pulse-width modulation (PWM)** signals, rapid on/off
instructions whose on-time is varied. All six axes use **edge-aligned** PWM: the
timer starts each pulse at its period boundary. Timer resources can be shared
at the same frequency; the intended common setting is 25 kHz, or 25,000 periods
per second. Do not re-enable the center-aligned build flag. **Field-oriented
control (FOC)** is the firmware method that uses measured shaft angle to choose
these instructions; the carrier does not perform it.

| Axis | Movement | PWM1 / PWM2 / PWM3 | EN | CSn |
|---|---|---|---:|---:|
| A1 | Index curl 1 | 4 / 5 / 6 | 16 | 26 |
| A2 | Index curl 2 | 2 / 22 / 23 | 17 | 27 |
| A3 | Index splay | 7 / 36 / 29 | 20 | 32 |
| A4 | Middle curl 1 | 24 / 0 / 25 | 21 | 38 |
| A5 | Middle curl 2 | 3 / 33 / 37 | 30 | 39 |
| A6 | Middle splay | 8 / 9 / 28 | 31 | 40 |

These are Teensy pin numbers, not header contact numbers. **EN** means enable;
**CSn** means chip select, active low (0 V selects that encoder). All twelve
EN/CSn assignments are ordinary non-PWM pins. The nine unused Teensy contacts
are 1, 10, 14, 15, 18, 19, 34, 35 and 41; v1 has no separate spare connector.

Mini control pins 3/5/7 receive PWM1/2/3 and pin 9 receives EN. Pins 1 and 4 are
the Mini's ground and lead to the optional ground bridge. Pin 2 is the Mini's
own regulator **output**, not an encoder supply input: it is left disconnected
so six regulators cannot fight each other or back-power the Teensy. Pins 6, 8
and 10 (reset, sleep and fault) are also unconnected on the carrier; the Mini's
existing reset/sleep bias remains in use. Check the actual module's behavior
during first-power testing, not merely the socket symbol.

J21-J26 are the 1-by-3 male motor headers, accepting the existing female Dupont
cables. **Phases** are the three motor-winding connections. Their nets are
PH1/PH2/PH3, carrying switched motor power, not 3.3 V instructions. Short 1 mm
traces connect these directly to the Mini phase socket, in OUT1/OUT2/OUT3 order
(custom Mini contacts P3/P2/P1). Without those paths no motor current reaches
the windings. Never move a phase cable while motor power is live.

## 3. Encoder breakout sockets: the angle feedback

J31-J36 are female 1-by-6, 2.54 mm sockets for your existing JST breakout boards.
The breakout's square pad is contact 1, and the carrier silkscreen marks
`ENCn: 1 CLK`. Your verified order is:

| Contact | Net | Meaning |
|---:|---|---|
| 1 | SPI_SCK | Clock: tells the encoder when to shift each data bit |
| 2 | SPI_MISO | Data from the selected encoder to the Teensy |
| 3 | SPI_MOSI | Commands from the Teensy to the encoders |
| 4 | A1_CS ... A6_CS | Separate active-low select for this axis |
| 5 | 3V3 | Encoder supply, 3.3 V only |
| 6 | GND | Encoder supply return and signal reference |

**SPI**, the Serial Peripheral Interface, is this clocked data connection.
**MISO** means controller-in/peripheral-out; **MOSI** means
controller-out/peripheral-in. All six share SPI0: MOSI pin 11, MISO pin 12 and
clock pin 13. Individual chip selects let only one answer at a time. A second
SPI bus would change your agreed pin map, so it is not used in v1.

The encoder connections are in the central low-current region. The motor phase
traces and shared 12 V trunks stay outside it; the ground areas, deliberately
joined on both faces, provide a nearby return path. The traces still have six branches and
the external cables add length, so working at the bench is a test requirement,
not something a drawing can prove. Keep encoder cables away from phase wires.
Firmware must set every CSn high before starting SPI transfers and keep unused
encoders deselected. There are no added carrier CS pull-ups, signal filters or
level shifters. Without reliable angle feedback FOC can push the shaft the wrong
way; verify readings before enabling a motor.

## 4. Input terminal and fuse: motor power only

J5 accepts the 12 V bench supply: square contact 1 is positive, contact 2 is
negative. The positive path is `12V_IN -> F1 -> 12V_FUSED`. A **fuse** contains
a link intended to melt when excessive current persists. F1 is a through-hole
Schurter 0031.8201 holder for a separate 5-by-20 mm cartridge. A 3.15 A
**time-delay** cartridge (marked T, tolerating brief startup surges) is a review
candidate, not a measured final selection. Its DC breaking rating must suit the
supply; the holder is not itself the fuse.

Without a fuse, a supply capable of high current could keep heating a wiring
fault. A fuse does not regulate motor current, protect against every electronic
fault, or act as an emergency stop. In voltage-mode FOC the firmware's voltage
limit remains important; the library's `current_limit` does not limit current
in that mode. Start with a current-limited bench supply and low motor voltage.

There is no reverse-polarity protection in this simplified v1. Reversing J5 can
damage the Minis and polarized capacitors before the fuse opens. Verify polarity
with a meter before connection. The 3 mm shared supply trunks, 2 mm branches,
1.8 mm returns and 1 mm phase traces are deliberately routed and locked. They
are not a guarantee of a particular ampere rating: the human reviewer must
approve the load, sockets, wires, fuse and temperature margin together.

## 5. Direct Mini power and two capacitors per axis

Each J11-J16 now includes VIN and GND receptacles at the exact 4.953 mm
pitch in the v1.0 drill file. VIN receives 12V_FUSED; GND has its own PGNDn
return to NT1. J41-J46 and the six external power-wire pairs are removed.
The Mini plugs in component-side up with pins pointing down, without mirroring.
The power branches use 2 mm supply and 1.8 mm return copper sized for 3 A
on external 35 um copper with a 10 C temperature-rise estimate; see
[the geometry and power report](mini-v1-update.md).

A **capacitor** stores electrical charge. Each C11-C16 is your Panasonic
EEUFR1V102B, 1000 microfarads (uF), 35 V rated, 12.5 mm diameter, 20 mm high,
5 mm lead pitch. It supplies brief current bursts locally and absorbs some
supply fluctuations. This **electrolytic** type is polarized: positive lead to
the square `+` pad, negative stripe to the round PGND pad. Reversing it can cause
heating or venting. Without it more motor-current pulses travel down the shared
supply wiring.

Each C21-C26 is a non-polarized 100 nanofarad (nF), at least 50 V ceramic
capacitor with 5 mm lead spacing and a body fitting the specified footprint.
It responds to faster disturbances than the large capacitor. The pair sits
alongside the Mini power pads. The Mini's own onboard capacitors remain
essential; a carrier ceramic cannot replace them.

Six 1000 uF capacitors store about 0.43 joules at 12 V. Unplugging power does
not instantly discharge them. There is no guaranteed discharge time, indicator
or discharge resistor on this carrier: measure the voltage before handling.
Motor braking can also return energy and raise the rail. A bench supply may
not absorb it; observe rail voltage during unloaded bring-up and have the human
reviewer decide whether v1's use needs external overvoltage protection.

## 6. Ground star and optional control-ground bridges

**Ground (GND)** is the circuit's zero-volt reference and a return conductor,
not an unlimited sink for current. **Star ground** means keeping the six motor
returns separate until one deliberate junction, NT1, beside the input. PGND1
through PGND6 are those returns. GND serves the Teensy and encoders. NT1 is
already joined PCB copper, not a component to buy or a jumper to fill.

Separating the branches reduces the chance of motor current shifting an
encoder's reference voltage. It does not eliminate noise, and all grounds are
electrically common through NT1. GND **copper pours** are broad filled areas in
the center and around the control sockets, supplemented by two deliberately
drawn 0.4 mm ground links and **stitching vias**, small plated holes joining the
two copper faces. The links bypass places where signal traces divide the ground
fill; they carry quiet reference/encoder current, never an axis power return.
Motor returns are not joined to a blanket ground pour. The top ground area
wraps around socket signal paths; the bottom area stays between motor-return
rails. Nearby supply/return routing is still a two-layer compromise; noise needs
measurement with motors running.

Most ground pads connect to the broad copper through narrow **thermal-relief
spokes**, making them easier to heat with a soldering iron. Four congested ground
contacts (J1 contact 1, J2 contacts 2 and 15, JP5 contact 2) instead use solid
copper joins so a lone spoke cannot become disconnected. They will take more
heat to solder; use flux and an appropriate tip, not a prolonged low-power iron.

JP1-JP6 are optional control-GND solder/wire bridges: two through-hole pads
3 mm apart, left OPEN. CGNDn joins Mini control contacts 1 and 4 to one bridge
pad; the other pad is logic GND. With a Mini installed, those contacts already
connect internally to the Mini's power ground, which reaches NT1 through its
direct PGND copper branch. Closing JP adds a parallel return through the logic region,
possibly carrying motor current there. Do not close bridges automatically;
have the reviewer decide, and do not use them to compensate for a missing
power-return contact. The Mini requires both VIN and GND receptacles.

## 7. Six enable pull-downs: off when no output is driving

R21-R26 are 10 kilohm (10k, or 10,000 ohm) resistors from each EN net to that
axis's PGND. A **resistor** limits current; a **pull-down** gently holds an
otherwise undriven signal near zero volts. Teensy pins become **high impedance**
(neither strongly high nor low) during reset/unpowered conditions. Without
these resistors EN could float to an unpredictable state. When the Teensy
deliberately drives 3.3 V high, each resistor only draws about 0.33 milliamps,
so the output can override it.

This is a default-off measure, NOT a hardware kill or a certified safety circuit.
It cannot override a stuck-high output, guarantee every power-sequencing fault,
or prevent firmware from deliberately enabling a motor. Verify EN at the actual
Mini with USB removed and during reset while 12 V is present. For v1, physical
motor-power removal is disconnecting the 12 V supply, then confirming discharge.
The old latch/restart choice is not applicable because v1 has no kill circuit.

## 8. What is proved and what is not

You confirmed Mini fit on the full-size template, encoder contact 1 and the
160-by-120 mm base fit. Four 3.2 mm holes accept M3 screws. Allow clearance for
the screw heads, insulating spacers, 20 mm capacitors, cables and socketed modules.
The renders show carrier parts; the plugged-in Teensy, Mini boards, breakout
boards and cables are not a complete mechanical model.

See [verification](verification.md) for current strict ERC/DRC results and
[hardware checks](hardware-check.md) for review and later bench tests.
**ERC** checks schematic electrical rules; **DRC** checks PCB geometry and
connections. The socket symbols are passive, so ERC does not simulate module
internals. Neither check proves current capacity, correct firmware, noise
immunity, capacitor polarity in assembly or safe motion.

The working firmware still uses the earlier bench EN/CS assignments and only
one instantiated axis. Do not flash that build and assume it implements this
carrier. A later firmware change must use the table above, boot with all EN low,
initialize FOC only on command, call `loopFOC()` explicitly, and verify six-axis
timing. Historical bring-up sketches remain unchanged.
