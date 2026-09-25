# Checking the actual modules before committing the PCB

The supplied photographs are saved unchanged in `pcb/sources/user-*.png`.
They are useful evidence, but a picture cannot establish every electrical
connection. No wire colour has been assigned a signal from appearance alone.

## What the photographs establish

| Item | Confirmed | Still unknown |
|---|---|---|
| Encoder | The chip marking is AS5048A; a six-wire connector and a separate three-contact connector are visible | Each six-pin contact's function, the far-end plug's orientation, exact connector identity and board supply strapping |
| Mini | Male header pins point down, consistent with plugging into female carrier sockets | Board revision, exact control-to-phase socket spacing, underside clearance and power-terminal pitch |

The encoder's `PWM` and `GND` printing is beside the separate three-contact
connection. It is not a six-pin SPI pinout. The two wider outer metal tabs of the
six-contact socket are mechanical anchors, not extra signal contacts.

The carrier pin order is **CLK, MISO, MOSI, CSn, 3.3 V, GND**, verified on the
working bench breakout rather than inferred from the photos. The earlier assumed
order put CSn first; it was wrong by one position on every signal.
Keep using the bench-proven **3.3 V** supply; do not try 5 V or powered wire-order
permutations. Identifying an AS5048A chip does not establish how its board connects
the chip's supply pins.

## Simple Mini fit check

Use `pcb/mechanical-fit-review.pdf`, printed with **Actual size / 100%** selected.
Disable **Fit to page**. Measure the reference line between its tick centres: it
must be 50 mm; the carrier outline must be 160 by 120 mm. An incorrectly scaled
print cannot confirm a footprint.

1. Disconnect USB and the power supply. Disconnect the Mini from all wiring;
   verify its power terminals are discharged before handling it.
2. Lay the paper flat. It is a view from above the carrier, not a mirrored
   underside view. The upper and lower rows of Minis face opposite directions.
3. Hold the Mini in its intended installed orientation above one matching
   outline. Its downward pins must align with **both** the 2-by-5 control holes
   and the separate three phase holes simultaneously. Do not bend pins to fit.
4. Take a straight-down photo showing this alignment, then a clear top and bottom
   photo of the Mini with its labels readable. A ruler beside it helps establish
   scale independently. A paper check catches gross mismatch; it does not prove
   production tolerances or socket height.

The approved short red/black power wires remain the plan. They remove the need
to match the Mini's off-grid power terminals with rigid carrier pins.

## Encoder cable check

The next useful photograph is **both ends of the same six-wire cable**, with the
key/latch visible and the ends labelled "encoder" and "carrier". If the existing
bench harness still works, photograph the labelled breakout connections too.
Do not unplug or change motor wiring while powered.

A continuity check means testing whether two points have an electrical path using
an unpowered multimeter. With the cable disconnected at both ends, map every
contact end to end; do not assume a visually straight cable preserves connector
pin numbering. Prefer a suitable breakout over pushing oversized probes into
these small contacts. Never probe chip legs if doing so could bridge or damage
them; leave chip-to-connector verification to someone equipped for it.

Record the results here (blank means **not measured**):

| Signal from known-good bench wiring | Wire colour | Encoder-end contact and viewing direction | Carrier-end contact (verified) |
|---|---|---|---|
| CLK | purple | | 1 |
| MISO / DO | green | | 2 |
| MOSI / DI | yellow | | 3 |
| CSn | black | | 4 |
| 3.3 V | red | | 5 |
| GND | white | | 6 |

Carrier contacts come from reading the bench breakout (pin 1 = square pad,
straight traces). Wire colours come from the bench harness that passed phase 1
with CSn on Teensy 10, CLK 13, MOSI 11, MISO 12 — each wire’s signal is known
because the working configuration proved where it went, not from appearance.
Correct this table if the harness has since been re-pinned. The encoder-end
column is still **not measured**.

## Before the first encoder is plugged into an assembled board

Do this on every newly assembled carrier, with no encoder connected:

1. Power the board and meter **socket contact 5 against contact 6**: it must read
   3.3 V, not 5 V and not 12 V.
2. Confirm **contact 6 is continuous with board ground**.
3. Only then plug an encoder in.

Contacts 5 and 6 are the two that can destroy a sensor. A mirrored footprint, a
swapped regulator output or a cable plugged the wrong way round all show up as a
wrong reading here, and all of them are cheap to find at this point and expensive
to find afterwards. The signal contacts 1–4 cannot damage anything — a wrong
order there merely fails to read, as the bench history shows.

The historical bench fault included damaged **mated** contacts. Cable continuity
alone therefore does not clear the connector: check the complete unpowered mating
path for opens and adjacent shorts as well, using an appropriate breakout.

These checks resolve socket fit and direct-plug polarity. They do **not** replace
the remaining routing, power qualification, safety decision or release review.
