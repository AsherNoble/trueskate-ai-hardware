# Current KiCad design

Open [trueskate-main-v1.kicad_pro](trueskate-main-v1.kicad_pro) in KiCad 10.
The project opens the PCB and its hierarchical schematic sheets. The local
symbol/footprint libraries and their tables live beside the project, so KiCad's
`${KIPRJMOD}` references remain relative and portable.

`data/` contains the declarative axis/pin mapping, nominal stackup, circuit data,
manual route records and placement baseline used by the scripts. `routing/`
contains the checked-in signal-routing session. See [tool commands](../scripts/README.md)
before rebuilding: regeneration overwrites the native design.
