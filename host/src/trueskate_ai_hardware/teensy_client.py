"""MotorClient over USB serial to the Teensy 4.1 controller.

Stub. The framed protocol is drafted in docs/protocol.md and has not been
reviewed or implemented, so every command here raises rather than sending
half-specified bytes at hardware that can move.

What is settled: the Teensy owns FOC, trajectory execution and safety, and
the host only sends commands and reads state. So this client stays thin --
it frames requests and parses replies. There is no control loop on this
side and there should never be one.

The firmware today exposes the human console from bring-up (I/T/M/G on
115200 8N1). That is not this protocol; see docs/protocol.md.
"""
from __future__ import annotations

from typing import Sequence

from .errors import LinkError
from .motor_client import AxisState, MotorClient

DEFAULT_BAUDRATE = 115200


class TeensyMotorClient(MotorClient):
    """SimpleFOC axes on a Teensy 4.1, reached over USB serial."""

    motor_family = "simplefoc"
    needs_alignment = True
    executes_trajectories = True

    def __init__(
        self,
        port: str,
        axis_names: Sequence[str],
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = 1.0,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._axes = tuple(axis_names)
        self._serial = None

    def _not_yet(self, what: str) -> LinkError:
        return LinkError(
            f"{what} is not implemented: the host<->Teensy protocol is still a "
            "draft (docs/protocol.md). Use MockMotorClient for host-side work."
        )

    @property
    def is_connected(self) -> bool:
        return self._serial is not None

    def connect(self) -> None:
        raise self._not_yet("connect()")

    def disconnect(self) -> None:
        # Safe to call on a never-opened client so context managers and
        # cleanup paths do not need to special-case the stub.
        self._serial = None

    def axis_names(self) -> Sequence[str]:
        return self._axes

    def align(self, axes: Sequence[str] | None = None) -> None:
        raise self._not_yet("align()")

    def set_torque_enabled(self, axes: Sequence[str], enabled: bool) -> None:
        raise self._not_yet("set_torque_enabled()")

    def read_state(self, axes: Sequence[str] | None = None) -> list[AxisState]:
        raise self._not_yet("read_state()")

    def write_target_angle(self, axes: Sequence[str], angles: Sequence[float]) -> None:
        raise self._not_yet("write_target_angle()")

    def write_trajectory(
        self, axis: str, times: Sequence[float], angles: Sequence[float]
    ) -> None:
        raise self._not_yet("write_trajectory()")

    def stop(self, axes: Sequence[str] | None = None) -> None:
        raise self._not_yet("stop()")
