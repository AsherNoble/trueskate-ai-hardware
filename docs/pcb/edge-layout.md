# Edge-layout follow-up review

Board remains **160 × 120 mm**, 2 layers, 2 oz. No Teensy pin assignments changed.
Six 25 mm-pitch columns retain their motor/JST edge connectors. USB shell remains
flush to Y=120 by the PJRC dimensioned placement.

The real Mini v1.0 GKO outline is now expanded by **0.5 mm** for its courtyard,
including the curved ears. The upstream GKO has small disconnected endpoints;
the extraction records the maximum sub-0.12 mm closure used to make a polygon.
Capacitor bodies are outside this envelope. `layout-review.json` records each
bulk and ceramic gap; the minimum is **2.9136 mm to the Mini board outline** and
**2.4138 mm to the expanded courtyard**. Strict courtyard checks also cover other
carrier parts; no tall carrier component sits inside a Mini courtyard.

All six encoder bundles are fixed on their column's right/JST half, with SPI,
CS, 3V3 and GND escaping together. They jog around Mini power pads and join shared
routing behind the Minis. Phase corridors are excluded during automatic routing.
An independent segment-intersection audit on final copper checks all six columns;
**no column exceptions** are reported.

F1 is **Keystone 3557-2, C352820, quantity 1**. It is a complete holder containing
both clips for one standard ATO fuse. The footprint is built from Keystone's
13.47 × 3.40 mm four-hole pattern, with 1.65 mm drills against its 1.60 mm minimum.
The body envelope is 19.81 × 6.73 mm. The BOM contains no fuse amperage. README:
“fuse rated to the connected supply.” Power copper remains sized for the 12 A
bus target; the requested 12 A thermal-qualification outstanding item is removed.

U1/U2 are **TI LV-A CMOS SN74LV125AN**, supplied from **Teensy 3V3**. The
[README state table](../../pcb/README.md) and `kill-state-review.json` show all
six EN outputs low for unpowered Teensy, floating GPIO at valid 3.3 V, and open
kill switch. Conservative DC driver EN is ≤0.375 V, below 0.6 V; this includes
all three DRV8313 EN input leakages and Mini R4. Source: TI SCES124O/SLVSBA5D.

## Remaining limitations

- SH harness contact order still requires the requested multimeter check against
  the actual AS5048A board. The single README table remains explicitly unverified.
- The LV-A datasheet guarantees powered operation from 2 V and Ioff at 0 V.
  **A glitch-free EN guarantee throughout the intervening supply ramp is not proven.**
  The boot result above assumes a valid 3.3 V rail and floating GPIO, not a brownout.
- Physical cable/socket heights and relocated mounting-hole fit still need checking.
- The two-layer board does not provide a guaranteed uninterrupted ground reference
  below every trace. This is distinct from the now-enforced right-side column routing.
- Renders omit socketed Teensy/Mini boards, loose single power receptacles, external
  cables/switch, fuse and fuse holder. F1 has no 3D model; its four-hole footprint
  and dimensioned body envelope are present in the native design and fit PDF.

[Top](../../pcb/top-review.png), [perspective](../../pcb/3d-review.png),
[BOM diff](../../pcb/bom-diff.md), [current BOM](../../pcb/bom-review.csv),
[validation status](../../pcb/review-status.json).

Sources: [Keystone product](https://www.keyelco.com/product.cfm/product_id/296),
[Keystone drawing](https://www.keyelco.com/product-pdf.cfm?p=296),
[archived manufacturer catalog](../../pcb/sources/keystone-3557-2/catalog.pdf),
[TI buffer](https://www.ti.com/lit/ds/symlink/sn74lv125a.pdf),
[TI motor driver](https://www.ti.com/lit/ds/symlink/drv8313.pdf).
