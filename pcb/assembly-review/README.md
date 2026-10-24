# Populated carrier views

These renders use the current native 160 × 120 mm carrier, including its actual
copper, component positions and installed library models. All six SimpleFOC Mini
boards, the Teensy 4.1, twelve power receptacles, and one fuse holder/fuse are shown
fitted. External cables are omitted.

- `populated-top.png`: top view.
- `populated-perspective.png`: front perspective.
- `populated-rear.png`: reverse perspective showing the controller and fuse.

The Mini board outlines and all fifteen contact positions come from the verified
v1.0 geometry. Added module electronics are simplified visual representations,
not manufacturer 3D models. Module seating heights and the fuse/holder details are
illustrative; these images do not qualify mechanical fit. Fuse colour is neutral
and no amperage is specified.

`render_assembly.py` builds the added VRML model and a disposable visual-only PCB
copy, then renders it with KiCad. Run it with KiCad's bundled Python. It verifies
that the source electrical PCB has not changed, and records its SHA-256 in
`provenance.json`. Do not use `populated-review.kicad_pcb` for manufacturing.
