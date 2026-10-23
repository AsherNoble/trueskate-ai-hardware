# Through-hole sourcing and fit

No factory assembly in v1. LCSC numbers identify parts, not instructions for
JLCPCB assembly. Blank CSV cells mean generic dimensional specifications or
different manufacturers' parts, not an asserted stock match. Do not buy SMD
versions or assume that matching pitch guarantees a matching housing.

- Owned Panasonic EEUFR1V102B: 1000 uF / 35 V, diameter 12.5 mm, height 20 mm,
  pitch 5 mm. LCSC C128476 is retained for identification; purchase cost is zero
  in this budget because they are owned.
  [Panasonic product](https://na.industrial.panasonic.com/products/capacitors/aluminum-electrolytic-capacitors/series/83367/model/83812).
- C21-C26: Vishay **K104K10X7RF5UH5**, LCSC **C2979769**, through-hole 100 nF,
  50 V, X7R, 5 mm pitch, 0.50 +/- 0.05 mm leads. Size code 10 has maximum body
  width/height 3.6 mm and thickness 2.3 mm, fitting the footprint's 5 x 2.5 mm
  allowance. H5 bent leads have nominal 5 mm pitch; form gently if necessary.
  [Vishay dimensions/codes](https://www.vishay.com/docs/45171/kseries.pdf),
  [LCSC identification](https://www.lcsc.com/product-detail/C2979769.html).
- J11-J16 power contacts: **12 single machine-pin receptacles**, two per Mini.
  Specify >=3 A continuous per contact, solder tail/body compatible with the
  1.101 mm finished hole, mating contact compatible with the actual Mini pin,
  and seated height matching the control/phase sockets. The two independent
  receptacles sit at 4.953 mm pitch; do not substitute a 5.08 mm socket block.
  No exact MPN is asserted until those mechanical details are selected.
- J5: Phoenix **1715721**, MKDS 1.5/2-5.08, two contacts, pitch 5.08 mm,
  required PCB drill 1.3 mm as used by its footprint.
  [Manufacturer dimensions](https://www.phoenixcontact.com/en-us/products/printed-circuit-board-terminal-mkds-15-2-508-1715721).
- F1 holder: Schurter **0031.8201**, LCSC **C3204125**, OGN family, through-hole horizontal open
  5x20 mm fuse holder. Match this version; OGN also has surface-mount and other
  lead forms. Buy the fuse separately; the holder rating is not the carrier or
  fuse rating. [Schurter OGN](https://www.schurter.com/en/datasheet/OGN),
  [LCSC identification](https://www.lcsc.com/product-detail/C3204125.html).

Female sockets need square receptacles compatible with the modules' male pins,
straight through-hole tails, 2.54 mm pitch and suitable mating height. Mini
control/phase sockets must hold its board at the same height. The user verified
the hole pattern, not every brand of socket housing: check insertion depth and
underside clearance before soldering all six.

J1/J2 are 1x24; Mini sets are 2x5 + 1x3 + two single power receptacles; encoders are female 1x6; phases are male
1x3. R21-R26 are 10k axial DIN0207-sized resistors (roughly 6.3 x 2.5 mm body),
leads bent to 7.62 mm pitch. Dissipation is only about 1.1 mW at 3.3 V; 0.25 W
parts are ample. Review phase/socket contact current ratings for the actual load.

J41-J46 and the six Mini power-wire pairs are removed. Fit downward-facing
pins at each Mini VIN/GND hole to mate with the carrier receptacles; component
side faces up. Keep all four socket pieces at the same seated height.

Check stock, minimum quantities and prices again when buying. The review BOM
does not imply an order-ready cart or qualification of every generic connector.
