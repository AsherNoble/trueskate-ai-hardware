# Edge layout review

Board remains **160 × 120 mm**. Axes 1–6 run left to right at 25 mm pitch.
Front Y=0: motor headers and outward-facing JST SH connectors. Each Mini rotates
90° in-plane to fit its 21.512 mm-wide courtyard into a column; it is not mirrored.
Back Y=120: input, ATO fuse, NC kill header and Teensy USB. PJRC's 1.27 mm end offset
and 0.70 mm USB projection place the USB shell flush with first socket holes at
Y=118.03. Plug-in modules and cables are not included in the renders.

No Teensy pins change. Axes 1–3 use nine distinct FlexPWM submodules; 4–6 share
some of them. See [pin/timer allocation and the single provisional SH mapping table](../../pcb/README.md).

## Electrical changes

- Six JLC-assembled SM06B-SRSS-TB connectors replace the adapter-board sockets.
  All other fitted parts remain hand-soldered THT. SH contacts remain deliberately
  UNVERIFIED against the user's AS5048A board; the old socket confirmation is not reused.
- Six 10k CS pull-ups permit unused encoder columns to remain unpopulated.
- Two shared SN74LV125AN buffers gate six existing EN signals. Opening the NC loop
  raises /OE, tri-states all outputs and lets the six existing 10k EN pull-downs
  drive low independently of firmware. Added input pull-downs and bypass capacitors.
  Reclosing restores the commanded state; there is no restart latch or rail isolation.
- Ground topology changes explicitly: JP1–JP6 and the NT1 star are removed;
  Mini control/power grounds and logic use continuous common top/bottom pours.
  This supports reference planes and removes six optional ground bridges.
- Copper increases from 1 oz to **2 oz**. The main 12 V trunk is 12 mm; Mini feeds
  are 2 mm. Input feed uses 2 mm on each layer, joined at plated component contacts.
  F1 changes from the old 5×20 holder to Littelfuse FLR ATO 178.6165.0001, with four
  plated pins per contact. Fuse rating still needs load/inrush qualification.

Using the IPC-2221 external-layer estimate at 70 µm copper and 10°C rise, 12 A
requires about 4.626 mm and 3 A about 0.684 mm. This calculation sizes copper;
it does not establish the assembled system's continuous rating. Current sharing,
plated holes, connector/fuse transitions, ground-plane constrictions and the
actual temperature rise need a loaded-board test. See `power-routing-review.json`.

Entire columns can be omitted without opening shared copper. Populate each Mini's
EN pull-down and capacitors with it; populate each encoder's CS pull-up with it.
Keep shared kill/control power parts fitted. Firmware must skip absent encoders.

## Requirements not fully satisfied / checks still outstanding

1. **Routing requirement 9 is not fully satisfied.** Motor phase lanes are on the
   left and encoder connectors/fanout on the right of each column, but the shared
   SPI interconnect also crosses column boundaries. Some parallel geometry remains,
   and a two-layer poured board cannot promise an uninterrupted ground reference
   below every SPI/phase segment. DRC does not prove EMC separation. This is a
   review layout, not a claim that the literal “never parallel, over ground” rule passed.
2. **SH cable order requires the requested physical multimeter check.** The table
   is a provisional assignment, with one configuration source and global net labels.
3. **12 A operation is not thermally qualified.** Copper is sized for that target;
   the fuse value, connector operating conditions, populated-system power budget,
   startup/inrush and ground return temperature rise remain bench checks.
4. **Mechanical confirmation remains:** actual USB cable shell, six Mini sockets
   and single power receptacle mating heights, capacitor height and fixture mounts.
   Mounting-hole positions changed to clear the front columns and Teensy; the old
   base-fit approval does not verify these new hole locations.
5. **Render omissions:** socketed Teensy/Mini modules, twelve single power sockets,
   external cables/switch and F1's unavailable 3D model are absent. Their footprints
   and courtyards are present in the native board and fit drawing.

The kill topology and PCB connectivity can be checked statically; actual switching,
power sequencing and Mini behavior still require a powered bench test. No firmware
was changed, no hardware flashed, and no manufacturing files were generated.

## Review outputs

[Top view](../../pcb/top-review.png), [perspective](../../pcb/3d-review.png),
[BOM diff](../../pcb/bom-diff.md), [current BOM](../../pcb/bom-review.csv),
[validation status](../../pcb/review-status.json), [Mini drill audit](../../pcb/mini-fit-report.json).

Manufacturer references: [TI buffer truth table and Ioff](https://www.ti.com/lit/ds/symlink/sn74lv125a.pdf),
[JST SH mechanical/contact numbering](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf),
[PJRC dimensions](https://www.pjrc.com/teensy/dimensions.html),
[PJRC timer allocation](https://www.pjrc.com/teensy/td_pulse.html),
[Littelfuse holder](https://www.littelfuse.com/~/media/commercial-vehicle/datasheets/automotive-fuse-holders/ato/littelfuse-fuse-holder-ato-flr-pcb-datasheet.pdf).

Final static verification: ERC 0 violations; strict DRC 0 violations, 0 opens, 0 schematic parity issues, no ignored checks. All 292 PCB contacts agree with the schematic netlist. The Mini library plus six instances pass the source drill audit at 0.000000 mm maximum position error. The final renders were visually checked for complete board framing.
