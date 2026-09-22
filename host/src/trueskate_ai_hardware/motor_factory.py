"""Resolve a motor family name to its MotorClient implementation.

The single place mapping ``motor_type`` to a concrete client -- the pattern
orca_core uses, and the reason nothing else in this package branches on a
family string. Imports are lazy so a mock-only run never imports pyserial.
"""
from __future__ import annotations

from typing import Sequence

from .errors import ConfigError
from .motor_client import MotorClient

MOCK = "mock"
SIMPLEFOC = "simplefoc"
SUPPORTED_MOTOR_TYPES = (MOCK, SIMPLEFOC)


def motor_client_class(motor_type: str) -> type[MotorClient]:
    """Return the MotorClient subclass driving ``motor_type``."""
    if motor_type == MOCK:
        from .mock_client import MockMotorClient

        return MockMotorClient

    if motor_type == SIMPLEFOC:
        from .teensy_client import TeensyMotorClient

        return TeensyMotorClient

    raise ConfigError(
        f"Unknown motor_type: {motor_type!r}. "
        f"Expected one of [{', '.join(SUPPORTED_MOTOR_TYPES)}]."
    )


def create_motor_client(
    motor_type: str,
    axis_names: Sequence[str],
    *,
    port: str | None = None,
    baudrate: int | None = None,
) -> MotorClient:
    """Construct (but do not connect) the client for ``motor_type``."""
    cls = motor_client_class(motor_type)

    if motor_type == MOCK:
        return cls(axis_names)

    if port is None:
        raise ConfigError(f"motor_type {motor_type!r} requires a serial port")
    if baudrate is None:
        return cls(port, axis_names)
    return cls(port, axis_names, baudrate)
