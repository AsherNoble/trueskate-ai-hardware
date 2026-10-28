# JLCPCB upload package

Current revision: **TSAI-FOC6 v1 · 2026-10**, with Q1 reverse-input protection and the revised assembly silkscreen.

Upload **[trueskate-main-v1-2layer-1oz-JLCPCB.zip](trueskate-main-v1-2layer-1oz-JLCPCB.zip)** as one ZIP. It contains the nine Gerber layers, plated/non-plated drills and job file at its root.

Settings: **150 × 140 mm, two layers, 1 oz, 1.6 mm FR4, green mask, white silk, lead-free HASL, tented vias**. Select **PCB assembly OFF**. All components, including J31–J36 JST connectors, are hand soldered. The ZIP includes Gerbers and both drill files; do not upload a BOM or CPL for this order. The [hand-assembly BOM](trueskate-main-v1-hand-assembly-BOM.csv) is for purchasing and bench assembly.

For purchasing, use the [formatted sourcing workbook](../bom/trueskate-main-v1-sourcing-BOM.xlsx) with Have/Don’t have dropdowns: matching parts share one row with summed quantities and all references retained. Quantities cover one complete six-axis carrier, including optional axes. It is derived from the unchanged hand-assembly BOM above; costs remain estimates per item. The eight 100nF capacitors use the specified Vishay part for sourcing, including C1/C2, whose original rows leave the supplier code blank. Generic 10k resistors are combined across circuit roles; R2 stays separate because it specifies a particular supplier part and a different unit estimate. Original assembly notes are retained. Mini socket kits and the separately listed single receptacles retain the source BOM's quantities and scope.

Fresh ERC and strict DRC pass. Every exported drill hit matches the native board: 773 plated holes and four non-plated mounting holes. Source/ZIP hashes and rounding tolerances are in [manifest.json](manifest.json). The manifest's commit is the rollback base; its PCB hash identifies the current uncommitted working-tree revision.

Read the [protection/silkscreen report](../../docs/pcb/reverse-polarity-silkscreen.md) before ordering. Q1 needs no heat sink below ~5 A continuous; 12 A is a copper-sizing worst case. Charged-output reversal, inrush and surge tests are out of scope. Copper/thermal qualification is stopped, and the retained gap audit is accepted for v1. Outstanding: user 1:1 print fit check, user SH pin order verification, and optional human review. No upload or order was made.


## Assembly and cost comparison (five carriers)

**Selected: bare PCB; solder all parts, including the JSTs, by hand.**

All options use the same Gerber ZIP above. [Comparison CSV](assembly-options/cost-comparison.csv) records costs and unknowns separately.

| Option | Files / selection | Factory parts per board | Price status for five |
| --- | --- | ---: | --- |
| Bare PCB | [Instructions](assembly-options/bare-pcb/README.md); assembly OFF | 0 | Recorded PCB quote US$15.80 before shipping/tax |
| JST only | [BOM](assembly-options/jst-only/BOM.csv) + [CPL](assembly-options/jst-only/CPL.csv); top side | 6 | PCB + 30 connectors US$35.64 before assembly fees, attrition, shipping/tax |
| Full carrier | [Planning scope and blockers](assembly-options/full-carrier-planning/README.md) | 79 | Unavailable under stocked-only policy; NOT upload-ready |

The JST price uses C160405 at US$0.6612 each at quantity 30; this is a parts subtotal, not a PCBA quote. JLC's checkout must calculate setup, placement/assembly and any part-handling fees. PCB price evidence: `../sources/jlc-3plus3/quote.json`. No quote/order upload was performed.

Full assembly excludes plug-in Teensy/Mini modules and external accessories. The 15-hole Mini footprints expand into 24 physical socket parts, including 12 single machine-pin power receptacles. The full files deliberately use non-upload headers and filenames: unresolved MPNs and body-centroid/rotation qualification cannot be represented as approved JLC selections. U1/U2 now select TI SN74HC125N DIP-14 C2890, with unchanged footprint/pinout and layout; JLC assembly stock is unverified. Powered-off EN qualification remains unresolved; see [carrier state review](../../docs/pcb/carrier.md). The earlier zero-stock buffer search applies to the superseded LV part. Exact bulk capacitors C128476 also had zero stock. No sourcing/consignment was performed.

The selected order is bare PCB. Optional JST-only CSVs remain only in `assembly-options/jst-only/` for comparison; there are no default PCBA upload CSVs at the manufacturing root. Coordinates use the Gerber absolute origin, mm, X right/Y up; negative Y values are intentional. SH wiring TODOs stay unchanged pending the user's multimeter check.
