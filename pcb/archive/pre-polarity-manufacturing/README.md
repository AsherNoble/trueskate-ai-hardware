# JLCPCB upload package

Upload **[trueskate-main-v1-2layer-1oz-JLCPCB.zip](trueskate-main-v1-2layer-1oz-JLCPCB.zip)** as one ZIP. It contains all Gerber layers and plated/non-plated drill files at its root.

Current board: **150 × 140 mm**, two layers, **1 oz**, 1.6 mm FR4, green mask, white silk, lead-free HASL, tented vias. Order quantity: 5. Live quote: **US$15.80**, excluding shipping, tax and assembly. The previous 160 × 120 mm release is in `../archive/pre-3plus3-manufacturing/` and is superseded.

Fresh ERC and strict DRC pass. Every exported drill hit is matched to the native board; ZIP integrity and source hashes are recorded in [manifest.json](manifest.json). The manifest's commit is the rollback base; the PCB hash identifies this uncommitted 3+3 working-tree revision.

The user accepted measured continuous-ground-reference gaps on this two-layer design. Read [the layout report and unresolved physical checks](../../docs/pcb/3plus3-layout.md) before ordering. Copper/thermal qualification is stopped. No files were uploaded and no order was placed.
