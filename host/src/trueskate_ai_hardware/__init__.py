"""Host-side hand control for TrueSkate-AI.

Slots in where WebDriverAgent does for the phones: the agent issues touch
gestures, this package makes a robotic finger perform them. The touch
interface mirrors ``trueskate_ai.sim.touch_actions`` so callers do not know
which of the two is executing.
"""
from .actions import (
    DEFAULT_SPIN_BUTTON_XY,
    Gesture,
    GestureRecipe,
    SpinHold,
    X_BOUND_MAX,
    X_BOUND_MIN,
    Y_BOUND_MAX,
    Y_BOUND_MIN,
    in_gesture_bounds,
)
from .config import AxisConfig, HandConfig, load_hand_config
from .errors import (
    ConfigError,
    HardwareError,
    LinkError,
    MotionTimeoutError,
    MotorError,
    WorkspaceError,
)
from .geometry import FingerWorkspace, ScreenFrame
from .hand import Hand
from .mock_client import MockMotorClient
from .motor_client import AxisState, MotorClient
from .motor_factory import create_motor_client, motor_client_class
from .teensy_client import TeensyMotorClient

__all__ = [
    "AxisConfig",
    "AxisState",
    "ConfigError",
    "DEFAULT_SPIN_BUTTON_XY",
    "FingerWorkspace",
    "Gesture",
    "GestureRecipe",
    "Hand",
    "HandConfig",
    "HardwareError",
    "LinkError",
    "MockMotorClient",
    "MotionTimeoutError",
    "MotorClient",
    "MotorError",
    "ScreenFrame",
    "SpinHold",
    "TeensyMotorClient",
    "WorkspaceError",
    "X_BOUND_MAX",
    "X_BOUND_MIN",
    "Y_BOUND_MAX",
    "Y_BOUND_MIN",
    "create_motor_client",
    "in_gesture_bounds",
    "load_hand_config",
    "motor_client_class",
]
