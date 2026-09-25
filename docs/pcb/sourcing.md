# Sourcing, assembly split and cost

Review date: 2026-09-23, Australia/Sydney. No parts have been ordered and no design
has been uploaded to a manufacturer. The [grouped BOM](bom.md) and
[per-reference CSV](../../pcb/bom-review.csv) are review documents, not an approved
JLCPCB assembly upload. All amounts below are **USD**, not AUD.

## Cost estimate

The current component allowance is **$25.15 per carrier**: about $5.90 of small
assembly parts and $19.25 of hand-soldered parts. The six large capacitors are
treated as already owned. This excludes the Teensy, Minis, motors/encoders, servo,
supply, switch, fuse cartridge, wire, mounting hardware, shipping and taxes.

For planning, reserve **$100–200 for a small prototype order** of the carrier,
including a low-quantity PCB batch, assembly setup, small parts, hand-soldered
parts and freight; this is an engineering budget allowance, **not a JLCPCB quote**.
At 160 × 120 mm this is not a small promotional-price board. Assembly setup,
extended-part fees, required spares and minimum purchase quantities can dominate
the inexpensive individual components. Quantity and destination must be entered
into the live quote after the design is released. There is no defensible precise
landed total yet. Buying the socketed electronics new would add their cost.

## Small-part candidates and stock evidence

All fitted surface-mount references have an LCSC number in the generated BOM.
The following are observations from LCSC's public listings, not reservations and
not a guarantee of stock in JLCPCB's assembly inventory. Product pages and cached
image pages can disagree; a live assembly quote remains mandatory. Listed quantities
change. Prices in the review BOM mix observed unit prices and rounded allowances,
and deliberately do not pretend to price minimum-order quantities.

| Function / selected part | LCSC source | Stock observed |
|---|---|---:|
| JST SH **top-entry** BM06B-SRSS-TB(LF)(SN), six | [C160392](https://www.lcsc.com/product-detail/C160392.html) | 34,590 |
| TI SN74LVC08APWR quad AND, two | [C465737](https://www.lcsc.com/product-image/C465737.html) | 35,285 on image page; recheck product/assembly page |
| TI SN74LVC1G17DBVR Schmitt input | [C7836](https://www.lcsc.com/product-detail/C7836.html) | 37,380 |
| Diodes AP63205WU-7 fixed 5 V buck | [C2071056](https://www.lcsc.com/product-detail/C2071056.html) | 42,416 |
| Bourns SRN6045TA-4R7M 4.7 µH | [C2044594](https://www.lcsc.com/product-detail/C2044594.html) | 680 |
| TDK C3225X7R1H106KT000E, 10 µF 50 V 1210 | [C432929](https://www.lcsc.com/product-detail/C432929.html) | 34,224 |
| Samsung CL31A226KAHNNNE, 22 µF 25 V 1206 | [C12891](https://www.lcsc.com/product-detail/C12891.html) | 78,320 |
| Yageo CC0603KRX7R9BB104, 100 nF 50 V 0603 | [C14663](https://www.lcsc.com/product-detail/C14663.html) | In-stock category listing, over 7 million |
| Samsung CL10B102KB8NNNC, 1 nF 50 V 0603 | [C1588](https://www.lcsc.com/product-detail/C1588.html) | 5,445,300 |
| MDD SS14, SMA Schottky, two | [C2480](https://www.lcsc.com/product-image/C2480.html) | 1,194,250 on image listing |
| TI SN74AHCT1G125DBVR, transmit buffer | [C7484](https://www.lcsc.com/product-detail/C7484.html) | 37,375 |
| TI SN74LVC1G125DBVR, receive buffer | [C23654](https://www.lcsc.com/product-detail/C23654.html) | 109,225 |
| JSCJ MMBT3904, SOT-23, two | [C20526](https://www.lcsc.com/product-detail/C20526.html) | 85,750 |
| Murata BLM21PG221SN1D, 0805 ferrite, two | [C85840](https://www.lcsc.com/product-detail/C85840.html) | 348,980 |
| Kento KT-0603R, red LED, nine | [C2286](https://www.lcsc.com/product-detail/C2286.html) | 1,429,000 |
| UNI-ROYAL 0603WAF1002T5E, 10 kΩ | [C25804](https://www.lcsc.com/product-detail/C25804.html) | 2,206,900 |
| UNI-ROYAL 0603WAF1003T5E, 100 kΩ | [C25803](https://www.lcsc.com/product-detail/C25803.html) | 17,703,300 |
| UNI-ROYAL 0603WAF1001T5E, 1 kΩ | [C21190](https://www.lcsc.com/product-detail/C21190.html) | 9,543,900 |
| UNI-ROYAL 0603WAF4701T5E, 4.7 kΩ | [C23162](https://www.lcsc.com/product-detail/C23162.html) | 16,045,900 |
| UNI-ROYAL 0603WAF330JT5E, 33 Ω | [C23140](https://www.lcsc.com/product-detail/C23140.html) | 4,607,000 |
| UNI-ROYAL 0603WAF1000T5E, 100 Ω | [C22775](https://www.lcsc.com/product-detail/C22775.html) | 7,706,100 |
| Optional UNI-ROYAL 0603WAF2201T5E, 2.2 kΩ | [C4190](https://www.lcsc.com/product-detail/C4190.html) | 6,528,900; **R8 DNP** |

The earlier side-entry JST candidate `C160405` was rejected for this draft: its
current product page said out of stock despite an image page showing stock.
`C160392` is the genuine JST SH top-entry version and uses a different, matching
KiCad footprint. It still needs physical cable verification. See
[JST's manufacturer drawing](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf).

## Hand-soldered parts still requiring purchasing qualification

The footprint is not by itself a purchasing specification. These rows deliberately
do not contain invented LCSC numbers:

- Two 1×24 female sockets for Teensy; six 2×5 plus six 1×3 female sockets for Minis.
  Verify actual insertion depth, stack height and contact current rating. A generic
  pin socket drawing does not establish a particular supplier's tolerances.
- Six male 1×3 motor headers; one 1×4 expansion header; two 1×2 headers for USB
  power transfer and the NC kill cable. Add keyed housings where practical and
  clear polarity labelling in the finished design.
- Six 3.81 mm two-contact Mini-feed screw terminals matching the selected Phoenix
  MKDS footprint; one 5.08 mm input terminal matching its distinct footprint.
  Verify the exact body, hole dimensions, wire range and ratings; do not blindly
  substitute a part that only shares pitch.
- Schurter 0031.8201 footprint-compatible 5×20 mm fuse holder and a separately
  chosen time-delay fuse. Final current/time rating depends on the load and inrush.
- Two FQP47P06 TO-220 P-channel MOSFETs, pin order G/D/S; one 1N4742A Zener.
  Verify exact manufacturer datasheet, thermal limits and lead geometry before
  locking the purchase BOM. Do not use an arbitrary TO-220 transistor.
- Feetech cable-matching 3-contact connector: currently provisional JST PH 2.0 mm.
- Two fingertip solder-wire terminals, with external strain relief; mounting screws
  and insulating spacers; approved power-wire pairs; external NC stop switch.
- Six owned Panasonic EEUFR1V102B, 12.5 mm diameter, 5 mm lead pitch. The listed
  LCSC reference `C128476` identifies the part, not a requirement to buy another six.

JLCPCB is intended to install **all** fitted surface-mount parts on the top side.
Only the listed through-hole items are assigned to hand soldering. R8 is marked
DNP in both schematic and board and must be omitted from any assembly order.
The nine test pads and ground net-tie are copper features, not purchased parts.

Before release, produce an assembly-only BOM and centroid/rotation file, check
every part's orientation in JLCPCB's preview against its datasheet and the board,
and verify availability in the chosen assembly service. None of those ordering
files has been issued from this incomplete board.
