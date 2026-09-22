"""Abstract base class for motor communication clients.

Reimplemented in the spirit of orca_core's ``MotorClient`` (MIT, ORCA;
https://github.com/orcahand/orca_core) -- no code copied. The idea worth
borrowing: a client declares its motor family through class attributes, so
callers stay family-agnostic and adding a family means adding a client
rather than branching on a type string at every call site.

The hand here is hybrid by design: GM3506 + SimpleFOC on the axes that need
real control, cheap servos later for the beautification fingers. Both are
motor families behind this interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Sequence


@dataclass(frozen=True)
class AxisState:
    """One snapshot of an axis, as reported by the controller.

    Angles are radians at the joint, velocity radians/second. ``voltage_q``
    is the commanded q-axis voltage, which in voltage torque mode is the
    only quantity bounding current -- see docs/bringup.md.
    """
    name: str
    angle: float
    velocity: float
    voltage_q: float
    enabled: bool
    ready: bool


class MotorClient(ABC):
    """Interface every motor family implements.

    Subclasses set the class attributes below so callers can ask what a
    client can do instead of asking what it is.
    """

    #: Family name as it appears in a hand config's ``motor_type``.
    motor_family: ClassVar[str] = "abstract"

    #: True when the family runs closed-loop FOC and so needs an alignment
    #: step before it can be commanded. Servos do not.
    needs_alignment: ClassVar[bool] = False

    #: True when the family can execute a host-supplied trajectory itself,
    #: rather than needing the host to stream setpoints.
    executes_trajectories: ClassVar[bool] = False

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Whether the transport is open."""

    @abstractmethod
    def connect(self) -> None:
        """Open the transport. Must leave every axis de-energised."""

    @abstractmethod
    def disconnect(self) -> None:
        """De-energise every axis, then close the transport."""

    @abstractmethod
    def axis_names(self) -> Sequence[str]:
        """Axes this client drives, in a stable order."""

    @abstractmethod
    def align(self, axes: Sequence[str] | None = None) -> None:
        """Run the alignment that closed-loop control requires.

        MOVES THE HARDWARE. No-op for families with
        ``needs_alignment = False``.
        """

    @abstractmethod
    def set_torque_enabled(self, axes: Sequence[str], enabled: bool) -> None:
        """Energise or de-energise the named axes."""

    @abstractmethod
    def read_state(self, axes: Sequence[str] | None = None) -> list[AxisState]:
        """Read the current state of the named axes."""

    @abstractmethod
    def write_target_angle(self, axes: Sequence[str], angles: Sequence[float]) -> None:
        """Command a joint angle, in radians, per axis."""

    @abstractmethod
    def write_trajectory(
        self, axis: str, times: Sequence[float], angles: Sequence[float]
    ) -> None:
        """Hand a timed angle trajectory to the controller to execute.

        Only meaningful when ``executes_trajectories`` is True. This is where
        a touch gesture ends up: the host never runs the control loop.
        """

    @abstractmethod
    def stop(self, axes: Sequence[str] | None = None) -> None:
        """Abandon any motion in progress and de-energise."""

    def __enter__(self) -> "MotorClient":
        self.connect()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.disconnect()
