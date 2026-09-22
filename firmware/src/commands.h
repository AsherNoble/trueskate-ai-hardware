// Serial command surface, carried over from bringup/03_closed_loop.ino.
//
//   I          run initFOC (moves the shaft -- PSU must be on)
//   T<volts>   set the torque target; in voltage torque mode this is VOLTS
//   M<0|1|2>   motion mode: 0 torque, 1 velocity, 2 angle
//   G          closed-loop demo move: 720 deg at 60 rpm
//
// This is the human-facing console, not the host protocol. The framed
// host<->Teensy protocol is drafted in docs/protocol.md and not built yet.

#pragma once

#include <SimpleFOC.h>

class Axis;

void commandsBegin(Commander& commander, Axis& axis);
