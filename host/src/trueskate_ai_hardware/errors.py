"""Exception hierarchy for the hardware layer."""


class HardwareError(Exception):
    """Base class for every failure raised by this package."""


class LinkError(HardwareError):
    """The serial link to the controller failed or was never opened."""


class MotorError(HardwareError):
    """A motor operation could not be completed."""


class MotionTimeoutError(MotorError):
    """Motion did not settle within the requested timeout."""


class ConfigError(HardwareError):
    """A hand config is missing, malformed, or internally inconsistent."""


class WorkspaceError(HardwareError):
    """A requested point lies outside the finger's reachable workspace."""
