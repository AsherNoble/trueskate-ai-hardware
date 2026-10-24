# Current hardware review checklist

Use the [edge-layout report](edge-layout.md) and [PCB README](../../pcb/README.md).

1. Verify every SH harness contact against its AS5048A board with a multimeter, power off.
2. Print the new 1:1 fit template; check Mini socket/receptacle heights, Teensy USB shell,
   capacitor clearance and relocated mounting holes. Old mounting-fit approval is stale.
3. Confirm exact purchased fuse holder, input terminal, machine-pin power sockets,
   2 oz fabrication and fuse value against load/inrush and temperature requirements.
4. Test NC kill open/closed with every EN command high; open must force all six EN low.
   Repeat startup, USB loss and rail sequencing tests. Reclosing currently permits restart.
5. Verify 3.3 V regulator budget for six actual encoders and buffers; start with one column.
6. Verify the three kill states on the bench and check SPI integrity under motor load.
   Right-side routing is audited; supply-ramp behavior remains outside the DC guarantee.

Never move phase cables with 12 V live. Kill is enable inhibition, not rail isolation.
