#!/usr/bin/env python3
"""Extract original v1.0 connector coordinates without snapping to a grid."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = json.loads((ROOT / "sources/mini-v1.0-pcb.json").read_text())
SCALE = 0.254  # EasyEDA Standard coordinate unit = 10 mil
ORIGIN = (4129.5, 3046.0)  # Control header pin 1, viewed from component side
connectors = {}
for shape in source["shape"]:
    if not shape.startswith("LIB~"):
        continue
    fields = shape.split("#@$")
    if "package`HDR-TH_10P" in fields[0]:
        key = "control"
    elif "package`HDR-TH_3P" in fields[0]:
        key = "phase"
    else:
        continue
    connectors[key] = []
    for item in fields:
        if item.startswith("PAD~"):
            f = item.split("~")
            connectors[key].append({
                "pin": f[8], "upstream_net": f[7],
                "x_mm": round((float(f[2]) - ORIGIN[0]) * SCALE, 6),
                "y_mm": round((float(f[3]) - ORIGIN[1]) * SCALE, 6),
            })
    connectors[key].sort(key=lambda p: int(p["pin"]))
power = []
for shape in source["shape"]:
    if shape.startswith("PAD~"):
        f = shape.split("~")
        if f[8] in ("2", "3"):
            power.append({"net": f[7], "x_mm": round((float(f[2])-ORIGIN[0])*SCALE, 6),
                          "y_mm": round((float(f[3])-ORIGIN[1])*SCALE, 6)})
assert len(connectors["control"]) == 10 and len(connectors["phase"]) == 3
assert connectors["control"][0]["x_mm"] == 0
assert connectors["phase"][0]["x_mm"] == -1.524
result = {"units": "mm", "view": "top/component side; y increases down",
          "origin": "H1 pin 1", "connectors": connectors, "power_evidence_only": power,
          "power_pitch_mm": round(abs(power[0]["y_mm"]-power[1]["y_mm"]), 6),
          "warning": "Physical board differs in power pitch per bench notes. Verify before fabrication."}
(ROOT / "sources/mini-geometry.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps(result, indent=2))
