> **Historical scope:** the [edge-layout revision](edge-layout.md) supersedes layout, ground, assembly and hardware-kill descriptions below. Use the current PCB README and review artifacts for this revision.

# v2 backlog - not fitted or routed on v1

The user changed v1 to a USB-powered, entirely through-hole perfboard-style
carrier. The prior fuller draft is recoverable at local Git checkpoint
`36e9dca`; it is an incomplete design, not a source of release-ready circuits.
Do not copy those circuits back without renewed design review.

| Future block | Decisions and work deferred |
|---|---|
| Board-powered Teensy | 12V-to-5V buck regulator, USB/VIN coexistence, power-source isolation, ripple/thermal/layout qualification |
| Hardware kill | Normally-closed loop, independent all-axis disable, fault behavior, switch wiring and explicit safety review |
| Kill latch/manual reset | User left the restart choice undecided; releasing a stop must not silently be treated as permission to restart. Moot on v1 because no kill circuit exists |
| Wrist STS3215 | 12 V port, verified connector/polarity, half-duplex UART, exact variant's signal voltage, level shifting and powered-off behavior |
| Fingertips | Two quiet return terminals, ferrite options, phone/touch/USB ground behavior |
| Daughterboard link | Dedicated I2C or UART port, connector, supply/current budget, pull-ups and protection |
| Direct encoder cables | SMD JST-SH sockets, physical cable/pin-one verification, factory assembly inventory and rotations; v1 uses verified existing breakout boards |
| Reverse-polarity protection | Appropriate through-hole or SMD power path, voltage/current/thermal and failure-mode checks |
| Additional conditioning | Optional SPI damping/filtering, idle CS pull-ups if needed, status LEDs/test features; add only with a reason from measurement |
| Power protection | Regenerative rail rise, clamp or braking-energy handling, guaranteed discharge/voltage indication, per-axis protection if measurements justify it |
| Production assembly | SMD/fine-pitch parts, live LCSC/JLCPCB stock checks, assembly BOM and placement files |

No beautification motors or left-thumb board are implied by this backlog.
Six-axis firmware and bench qualification remain necessary for v1; they are not
silently deferred to a future PCB revision. V1 contains no special spare port;
unused Teensy contacts remain unconnected on its existing sockets.
