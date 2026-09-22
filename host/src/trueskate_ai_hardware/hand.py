"""The Hand API: the WDA touch interface, performed by a physical finger.

This mirrors ``trueskate_ai.sim.touch_actions`` deliberately, method for
method, so the agent can drive a phone touch or a robotic finger without
knowing which. The differences are the two that cannot be avoided:

  * no ``driver`` argument -- the transport is the hand's own client
  * coordinates stay normalised; there is no device_w/device_h, because the
    rig geometry lives in the config rather than in the call

Stub. Each touch method validates its arguments and refuses to move,
because the planner (normalised point -> fingertip path -> per-axis joint
trajectory) is not written and the serial protocol is still a draft. What
the signatures commit to is the interface; what they do is nothing yet.
"""
from __future__ import annotations

from typing import Sequence

from .actions import (
    DEFAULT_SPIN_BUTTON_XY,
    Gesture,
    GestureRecipe,
    Point,
    in_gesture_bounds,
)
from .config import HandConfig
from .errors import HardwareError
from .motor_client import AxisState, MotorClient
from .motor_factory import create_motor_client


class Hand:
    """One robotic hand, presenting the touch interface the agent expects."""

    def __init__(self, config: HandConfig, client: MotorClient | None = None) -> None:
        self.config = config
        if client is None:
            types = config.motor_types()
            if len(types) != 1:
                raise HardwareError(
                    f"hand {config.name!r} mixes motor families {types}; "
                    "construct the clients explicitly"
                )
            client = create_motor_client(
                types[0],
                config.axis_names(),
                port=config.port,
                baudrate=config.baudrate,
            )
        self.client = client

    # ----- lifecycle -------------------------------------------------------

    def connect(self) -> None:
        self.client.connect()

    def disconnect(self) -> None:
        self.client.disconnect()

    def align(self) -> None:
        """Run the alignment closed-loop axes need. MOVES THE HARDWARE."""
        self.client.align()

    def read_state(self) -> list[AxisState]:
        return self.client.read_state()

    def __enter__(self) -> "Hand":
        self.connect()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.disconnect()

    # ----- touch interface, mirroring sim/touch_actions.py -----------------

    def tap(self, x: float, y: float, *, pre_delay: float = 0.0,
            post_delay: float = 0.0) -> None:
        """Single tap at a normalised point."""
        self._check_point(x, y, "tap")
        raise self._not_yet("tap")

    def long_press(self, x: float, y: float, *, duration: float = 1.0) -> None:
        """Press and hold at a normalised point. Duration in seconds."""
        self._check_point(x, y, "long_press")
        if duration <= 0:
            raise ValueError(f"long_press duration must be positive, got {duration}")
        raise self._not_yet("long_press")

    def double_tap(self, x: float, y: float) -> None:
        """Double tap at a normalised point."""
        self._check_point(x, y, "double_tap")
        raise self._not_yet("double_tap")

    def curved_drag(self, gesture: Gesture) -> None:
        """Drag along a gesture's waypoints under its easing profile."""
        for x, y in gesture.points:
            self._check_point(x, y, "curved_drag")
        raise self._not_yet("curved_drag")

    def execute_recipe(
        self,
        recipe: GestureRecipe,
        *,
        spin_button_xy: Point = DEFAULT_SPIN_BUTTON_XY,
    ) -> None:
        """Execute a full gesture recipe: N gestures, N-1 delays, optional spin.

        A single finger cannot hold the spin button and drag at the same
        time, so a recipe whose spin block is enabled needs a second axis.
        That is checked here rather than discovered mid-motion.
        """
        for gesture in recipe.gestures:
            for x, y in gesture.points:
                self._check_point(x, y, "execute_recipe")

        if recipe.spin.enabled and len(self.config.axes) < 2:
            raise HardwareError(
                f"recipe needs a spin hold, but hand {self.config.name!r} has "
                f"{len(self.config.axes)} axis: the spin button must be held "
                "while another finger drags"
            )
        raise self._not_yet("execute_recipe")

    def reset_position(self) -> None:
        """Tap True Skate's reset button to return the board to its start."""
        raise self._not_yet("reset_position")

    # ----- internals -------------------------------------------------------

    def _check_point(self, x: float, y: float, where: str) -> None:
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise ValueError(f"{where}: ({x}, {y}) is not normalised to [0, 1]")
        if not in_gesture_bounds(x, y):
            # Utility touches legitimately sit outside the RL gesture area, so
            # this is not an error -- but a planner will want to know.
            pass

    def _not_yet(self, what: str) -> HardwareError:
        return HardwareError(
            f"Hand.{what}() is not implemented: the touch planner and the "
            "host<->Teensy protocol (docs/protocol.md) are still drafts."
        )
