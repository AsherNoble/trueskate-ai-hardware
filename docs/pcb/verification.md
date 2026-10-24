# Current carrier verification

`pcb/scripts/export_review.py` runs KiCad ERC and strict DRC with all severities, all track
errors, schematic parity and zone refill. No exclusions or ignored rules. It then
compares the actual PCB to the exported schematic netlist, audits assembly types,
pin allocation, Mini source geometry, locked copper, EN/CS topology and power widths.
`review/checks/review-status.json` records results and hashes for the exported revision.

The original all-THT/star-ground validation belongs to commit 1d2f9e6. Current
requirements and limitations are in [edge-layout.md](edge-layout.md). DRC is not a
thermal, EMC, firmware or motion-safety test. The generic schematic symbols do not
simulate power sequencing or logic behavior; `scripts/verify_kill.py` separately checks the
buffer pin mapping and NC-loop topology against the TI truth table.
