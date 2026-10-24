# TrueSkate simplified 3D assembly

Built from mesh primitives and curves in Blender 4.4.3. No image generation
model is used. This replaces the earlier generated mockup for understanding
the assembled carrier.

- `trueskate-assembly.blend`: editable model, materials, camera and lights.
- `assembly-perspective.png`: assembled perspective view.
- `assembly-top.png`: top view for understanding placement and cable routes.
- `assembled-overview.png`, `assembled-top-overview.png`: the two renders with
  titles and a cable-colour legend, added by `label_renders.py` using Pillow.
- `carrier-components-labelled.png`: exposed carrier with exterior component
  family labels and arrows. Plug-in modules are hidden so sockets are visible.
- `soldered-components-map.png`: individual labels for every soldered reference,
  with a separate detail panel for each axis and the shared controller/power parts.
- `build_scene.py`: deterministic scene construction and rendering script.
- `board-geometry.json`: footprint pad centres, sizes and top-layer track
  segments extracted from the current KiCad PCB with pcbnew.

The carrier outline, thickness, socket contact positions and mounting locations
come from the PCB. Six large capacitors use the documented 12.5 mm diameter and
20 mm height. Teensy uses a 61 × 18 mm body and the actual two 24-pin socket rows.
The six Minis, encoder adapters, connector bodies and GM3506 motor are simplified
representations; their detailed mechanical outlines and clearances are not qualified.
The encoder support above the illustrative motor is a conceptual bracket.

Orange wires are the three motor phases, blue is the six-conductor encoder
harness, red/black pairs are power, and the thicker black lead is USB. Only axis 1
has an external motor and encoder cable. Cable routes are illustrative and do not
define conductor pin order or physical cable lengths.

Rebuild:

```sh
'/Applications/Blender V4.4.3.app/Contents/MacOS/Blender' --background --python '/Users/ashernoble/Projects/Robotics & hardware/trueskate-ai-hardware/pcb/archive/mockups/assembly-model/build_scene.py'
```

No native KiCad source or manufacturing archive was modified.

Component callouts are drawn with Pillow over Blender renders. Their arrow
coordinates come from the Blender camera projection or the orthographic KiCad
pad positions. `annotate_components.py` checks that all 46 hand-soldered BOM
references are covered, representing 52 physical parts (each Mini reference
contains two sockets). It excludes JP1–JP6 and NT1, which are PCB features.
The plug-in modules' own factory-mounted parts are outside this carrier BOM.

To rebuild the component labels, run `render_soldering_map.py` with Blender,
then again with `-- --perspective-only`, then run `annotate_components.py` with
Python 3.11/Pillow. The temporary `assembled-components-labelled.png` is an
abandoned annotation draft with obscured targets; use the exposed-carrier view.
