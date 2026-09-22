// TrueSkate-AI hardware -- Teensy 4.1 finger controller.
//
// Time-critical work lives here: FOC, trajectory execution, safety. The
// host never runs a control loop; it sends commands and reads state back.
//
// Ported from bringup/03_closed_loop.ino with its behaviour intact:
//   - motor disabled at boot, so flashing with the PSU off is safe
//   - initFOC only on the 'I' command, because it moves the shaft
//   - loopFOC() called explicitly (SimpleFOC 2.4 requires it)
//   - driver energised only on demand
//
// One axis is instantiated. A second is an AxisConfig entry plus another
// Axis -- see axis_config.h.

#include <SimpleFOC.h>

#include "axis.h"
#include "axis_config.h"
#include "commands.h"

Axis index_axis(INDEX_AXIS);
Commander commander(Serial);

void setup() {
  Serial.begin(115200);

  const uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) {
  }

  SimpleFOCDebug::enable(&Serial);

  Serial.println("trueskate-ai-hardware / teensy41");

  if (!index_axis.begin()) {
    Serial.println("FATAL: axis begin() failed");
  }

  commandsBegin(commander, index_axis);

  Serial.println();
  Serial.println("setup() complete. Motor DISABLED, PSU may still be off.");
  Serial.println("Turn the PSU on (12V, 0.5A), then send 'I' to align.");
  Serial.println("Commands: I = initFOC, T<volts> = target, M0/M1/M2 = mode, G = demo move");
  Serial.println();
}

void loop() {
  commander.run();

  // The auto-enable rule applies to torque mode only: elsewhere a nonzero
  // target is a position, not a request to energise.
  if (index_axis.ready() &&
      index_axis.motionMode() == MotionControlType::torque) {
    const bool want = index_axis.targetGet() != 0.0f;
    if (want != index_axis.enabled()) {
      if (want) {
        index_axis.enable();
      } else {
        index_axis.disable();
      }
      Serial.printf("driver %s\n", want ? "ENABLED" : "disabled");
    }
  }

  index_axis.update();
}
