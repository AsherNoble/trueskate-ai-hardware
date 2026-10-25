# Populated carrier views

These renders use the current native 150 × 140 mm carrier, including its actual
copper, component positions and installed library models. All six SimpleFOC Mini
boards, the Teensy 4.1, twelve power receptacles, and one fuse holder/fuse are shown
fitted. An illustrative partly withdrawn microSD card is shown; external cables are omitted.

- `populated-top.png`: top view.
- `populated-perspective.png`: front perspective.
- `populated-bottom.png`: underside view with modules fitted.

The Mini board outlines and all fifteen contact positions come from the verified
v1.0 geometry. Added module electronics are simplified visual representations,
not manufacturer 3D models. Module seating heights and the fuse/holder details are
illustrative; these images do not qualify mechanical fit. Fuse colour is neutral
and no amperage is specified.

`../scripts/render_assembly.py` builds the added VRML model and a disposable visual-only PCB
copy, then renders it with KiCad. Run it with KiCad's bundled Python. It verifies
that the source electrical PCB has not changed, and records its SHA-256 in
`provenance.json`. Do not use `.cache/populated-review.kicad_pcb` for manufacturing.

`bare/` contains the native board views without the added plug-in bodies;
`copper/` contains top/bottom copper plots. `models/` holds the generated populated
visual model. `.cache/` is disposable and ignored by Git.

| View | Modules fitted | Carrier without plug-in modules |
|---|---|---|
| Top | [Top](populated-top.png) | [Top](bare/top-review.png) |
| Bottom | [Bottom](populated-bottom.png) | [Bottom](bare/bottom-review.png) |
| Perspective | [Perspective](populated-perspective.png) | [Perspective](bare/3d-review.png) |

[SD service envelope](../review/drawings/sd-access.png) · [Measured reference gaps](copper/return-path-gaps.png).
