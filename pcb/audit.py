#!/usr/bin/env python3
"""Independent allocation checks; no hardware is touched."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
design = json.loads((ROOT / "design.json").read_text())
# PJRC td_pulse.html, cross-checked against Teensyduino 1.62 pwm.c.
PWM = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
       18, 19, 22, 23, 24, 25, 28, 29, 33, 36, 37}
used = {}

def claim(pin, role):
    assert 0 <= pin <= 41, (pin, "not on socketed outer headers")
    assert pin not in used, (pin, role, used.get(pin))
    used[pin] = role

for axis in design["axes"]:
    assert len(axis["pwm"]) == 3
    for phase, pin in enumerate(axis["pwm"], 1):
        assert pin in PWM, (pin, "not PWM")
        claim(pin, f'{axis["name"]}_IN{phase}')
    for role in ("enable", "cs"):
        pin = axis[role]
        assert pin not in PWM, (pin, "must be plain digital")
        claim(pin, f'{axis["name"]}_{role}')
for bus in ("spi0", "wrist_serial8", "daughter_i2c"):
    for role, pin in design[bus].items():
        if bus == "wrist_serial8":
            assert pin not in PWM
        claim(pin, f"{bus}_{role}")
claim(design["kill_sense"], "kill_sense")
assert len([p for a in design["axes"] for p in a["pwm"]]) == 18
assert set(range(42)) - used.keys() == set(design["spare_pwm"])
assert len(set(range(42)) - PWM) == 15
assert design["wrist_serial8"]["rx"] == 34
assert design["wrist_serial8"]["tx"] == 35
ini = (ROOT.parent / "firmware/platformio.ini").read_text()
assert "lib_archive = no" in ini
assert "-D SIMPLEFOC_TEENSY4_FORCE_CENTER_ALIGNED_3PWM" not in ini
print(f"PASS: {len(used)} unique assigned pins; 18 PWM; 12 non-PWM EN/CS;")
print("Serial8 RX34/TX35/DIR41; I2C18/19; SPI0 11/12/13; kill sense10.")
print("SPI1 needs three additional non-PWM pins; none remain under this map.")
print("This is a static allocation check, not a six-axis bench test.")
