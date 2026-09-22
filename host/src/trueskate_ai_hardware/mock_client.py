"""A MotorClient that needs no hardware.

Exists so the whole host path -- config loading, gesture validation,
geometry, the Hand API -- is testable and developable with the bench
unplugged. It keeps enough state to be honest about lifecycle mistakes:
commanding a de-energised axis, or an unaligned one, raises rather than
silently succeeding.

Motion is not simulated dynamically. A trajectory completes instantly and
the axis lands exactly on its final angle. That is deliberate: a fake
dynamics model would invite tests that assert on invented numbers.
"""
from __future__ import annotations

from typing import Sequence

from .errors import MotorError
from .motor_client import AxisState, MotorClient


class MockMotorClient(MotorClient):
    """In-memory stand-in for a controller, for tests and dry runs."""

    motor_family = "mock"
    needs_alignment = True
    executes_trajectories = True

    def __init__(self, axis_names: Sequence[str]) -> None:
        if not axis_names:
            raise ValueError("a mock client needs at least one axis")
        self._axes = tuple(axis_names)
        self._connected = False
        self._angle = {name: 0.0 for name in self._axes}
        self._velocity = {name: 0.0 for name in self._axes}
        self._enabled = {name: False for name in self._axes}
        self._ready = {name: False for name in self._axes}
        #: Every trajectory handed over, for tests to inspect.
        self.trajectories: list[tuple[str, tuple[float, ...], tuple[float, ...]]] = []

    # ----- lifecycle -------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        self._connected = True
        for name in self._axes:
            self._enabled[name] = False

    def disconnect(self) -> None:
        for name in self._axes:
            self._enabled[name] = False
        self._connected = False

    def axis_names(self) -> Sequence[str]:
        return self._axes

    # ----- helpers ---------------------------------------------------------

    def _require_connected(self) -> None:
        if not self._connected:
            raise MotorError("client is not connected")

    def _resolve(self, axes: Sequence[str] | None) -> tuple[str, ...]:
        if axes is None:
            return self._axes
        unknown = [a for a in axes if a not in self._angle]
        if unknown:
            raise MotorError(f"unknown axes: {unknown}")
        return tuple(axes)

    # ----- commands --------------------------------------------------------

    def align(self, axes: Sequence[str] | None = None) -> None:
        self._require_connected()
        for name in self._resolve(axes):
            self._ready[name] = True
            self._enabled[name] = False

    def set_torque_enabled(self, axes: Sequence[str], enabled: bool) -> None:
        self._require_connected()
        for name in self._resolve(axes):
            if enabled and not self._ready[name]:
                raise MotorError(f"axis {name!r} cannot be energised before align()")
            self._enabled[name] = enabled

    def read_state(self, axes: Sequence[str] | None = None) -> list[AxisState]:
        self._require_connected()
        return [
            AxisState(
                name=name,
                angle=self._angle[name],
                velocity=self._velocity[name],
                voltage_q=0.0,
                enabled=self._enabled[name],
                ready=self._ready[name],
            )
            for name in self._resolve(axes)
        ]

    def write_target_angle(self, axes: Sequence[str], angles: Sequence[float]) -> None:
        self._require_connected()
        names = self._resolve(axes)
        if len(names) != len(angles):
            raise MotorError(
                f"got {len(angles)} angles for {len(names)} axes"
            )
        for name, angle in zip(names, angles):
            if not self._enabled[name]:
                raise MotorError(f"axis {name!r} is not energised")
            self._angle[name] = float(angle)
            self._velocity[name] = 0.0

    def write_trajectory(
        self, axis: str, times: Sequence[float], angles: Sequence[float]
    ) -> None:
        self._require_connected()
        (name,) = self._resolve([axis])
        if len(times) != len(angles):
            raise MotorError(
                f"trajectory has {len(times)} times and {len(angles)} angles"
            )
        if len(times) < 2:
            raise MotorError("a trajectory needs at least 2 points")
        if any(b <= a for a, b in zip(times, times[1:])):
            raise MotorError("trajectory times must be strictly increasing")
        if not self._enabled[name]:
            raise MotorError(f"axis {name!r} is not energised")
        self.trajectories.append((name, tuple(times), tuple(angles)))
        self._angle[name] = float(angles[-1])
        self._velocity[name] = 0.0

    def stop(self, axes: Sequence[str] | None = None) -> None:
        self._require_connected()
        for name in self._resolve(axes):
            self._velocity[name] = 0.0
            self._enabled[name] = False
