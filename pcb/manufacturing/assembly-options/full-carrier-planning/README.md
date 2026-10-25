# Full carrier: planning files, not an orderable assembly package

Stocked-JLC-only policy; no sourcing or consignment. PCB unchanged.

79 physical parts per carrier (395 for five), excluding plug-in Teensy and Mini modules, loose fuse, cables, encoders, motors and external switch. The six Mini footprint references each expand into four physical socket parts: CTRL, PHASE, VIN and GND. This avoids counting a custom 15-hole footprint as one purchasable connector. The existing aggregate 12-receptacle BOM row is not counted twice.

BOM-NOT-FOR-UPLOAD.csv is a complete assembly scope, not a JLC upload BOM. Blank selected LCSC cells are deliberately unresolved. Existing/candidate codes are research leads, not approved stocked substitutions. PLACEMENTS-NOT-FOR-UPLOAD.csv maps every physical part to native pads for review; pad centroids are NOT validated component body centroids or JLC zero-angle placements.

The exact SN74LV125AN PDIP-14 listing C1548088 has zero stock (live search saved in sources/jlc-assembly/SN74LV125AN-search.txt). The Mini socket/receptacle combination has no selected stocked MPN or validated common seating height. The exact bulk capacitor C128476 has zero stock for the 30 required parts. These prevent a truthful full-carrier stocked-only quote/package on the unchanged board. Do not silently substitute SMD buffers, a different logic family, ordinary sockets for machine-pin receptacles, or a different mechanical seating height.

Consequently a full-carrier price is unavailable, rather than zero. No sourcing request, consignment, board change, upload or purchase was performed. JST-only and bare-PCB packages remain usable.
