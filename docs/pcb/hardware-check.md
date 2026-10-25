# Remaining v1 hardware checks

1. **1:1 print fit check** — user checks the SD socket/card, sockets/receptacles, USB shell, capacitor clearance and mounting hardware against the [fit drawing](../../pcb/review/drawings/mechanical-fit-review.pdf).
2. **SH pin order verification** — user checks the AS5048A harness with a multimeter and supplies the verified order. Keep TODO labels until then.
3. **Optional human review.**

The [prototype decisions](reverse-polarity-silkscreen.md) close the Q1 cooling, supply-ramp and 3.3 V load items for this operating scope. Charged-output reversal, inrush and surge testing are out of scope. SPI/return-path gaps are accepted for v1 at 1–4 MHz, lower if reads glitch; the measured gap audit is retained. Board remains two-layer, 1 oz. No firmware changes are included.
