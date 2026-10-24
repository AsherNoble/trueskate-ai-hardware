# BOM diff from 1d2f9e6

| Change | Reference(s) | Details |
|---|---|---|
| Added | C1 | 100nF buffer bypass; Hand |
| Added | C2 | 100nF buffer bypass; Hand |
| Changed | F1 | 5x20 fuse holder / fuse TBD → ATO fuse holder / fuse TBD; Hand |
| Changed | J31 | ENCODER breakout FEMALE 1x6 → SM06B-SRSS-TB; JLCPCB |
| Changed | J32 | ENCODER breakout FEMALE 1x6 → SM06B-SRSS-TB; JLCPCB |
| Changed | J33 | ENCODER breakout FEMALE 1x6 → SM06B-SRSS-TB; JLCPCB |
| Changed | J34 | ENCODER breakout FEMALE 1x6 → SM06B-SRSS-TB; JLCPCB |
| Changed | J35 | ENCODER breakout FEMALE 1x6 → SM06B-SRSS-TB; JLCPCB |
| Changed | J36 | ENCODER breakout FEMALE 1x6 → SM06B-SRSS-TB; JLCPCB |
| Added | J6 | NC KILL SWITCH; Hand |
| Removed | JP1 | CONTROL GND / OPEN |
| Removed | JP2 | CONTROL GND / OPEN |
| Removed | JP3 | CONTROL GND / OPEN |
| Removed | JP4 | CONTROL GND / OPEN |
| Removed | JP5 | CONTROL GND / OPEN |
| Removed | JP6 | CONTROL GND / OPEN |
| Removed | NT1 | GROUND STAR / PCB COPPER |
| Added | R1 | 10k /OE pull-up; Hand |
| Added | R31 | 10k CS pull-up; Hand |
| Added | R32 | 10k CS pull-up; Hand |
| Added | R33 | 10k CS pull-up; Hand |
| Added | R34 | 10k CS pull-up; Hand |
| Added | R35 | 10k CS pull-up; Hand |
| Added | R36 | 10k CS pull-up; Hand |
| Added | R41 | 10k EN command pull-down; Hand |
| Added | R42 | 10k EN command pull-down; Hand |
| Added | R43 | 10k EN command pull-down; Hand |
| Added | R44 | 10k EN command pull-down; Hand |
| Added | R45 | 10k EN command pull-down; Hand |
| Added | R46 | 10k EN command pull-down; Hand |
| Added | U1 | SN74LV125AN; Hand |
| Added | U2 | SN74LV125AN; Hand |

Six SH connectors replace six 1×6 adapter sockets. Added six CS pull-ups, six buffer-input pull-downs, two PDIP buffers, two bypass capacitors, one kill pull-up and one NC-loop header. Removed six optional ground bridges and the copper star. F1 changes from 5×20 holder to ATO holder; fuse rating remains TBD after load/inrush qualification. Twelve single machine-pin receptacles remain. J41–J46 were already removed in the baseline. Bare PCB copper changes from 1 oz to 2 oz. External NC switch and verified six-wire harnesses must be procured separately.
