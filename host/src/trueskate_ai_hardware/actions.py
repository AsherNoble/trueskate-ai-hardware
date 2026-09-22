"""Touch primitives, mirroring the WDA interface TrueSkate-AI already speaks.

The schema here is the one documented in TrueSkate-AI's GESTURES.md and
consumed by ``trueskate_ai.sim.touch_actions``: a *gesture* is a list of
normalised waypoints plus a duration and an easing power, and a *gesture
recipe* is an ordered list of gestures with N-1 inter-gesture delays.
Nothing is renamed, so a recipe from a trick library validates here
unchanged and the agent does not need to know whether a phone or a finger
executes it.

Per GESTURES.md, "action" and "swipe" are not used to describe touches.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

# Valid gesture area, from trueskate_ai.sim.gestures. Utility touches
# (reset, loading-screen dismiss) sit outside these and are not bound by them.
X_BOUND_MIN = 0.12
X_BOUND_MAX = 1.0
Y_BOUND_MIN = 0.12
Y_BOUND_MAX = 0.88

# Normalised position of True Skate's rotate/spin button.
DEFAULT_SPIN_BUTTON_XY = (0.0604, 0.4040)

Point = tuple[float, float]


def _check_normalised(x: float, y: float, *, where: str) -> None:
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
        raise ValueError(f"{where}: ({x}, {y}) is not normalised to [0, 1]")


@dataclass(frozen=True)
class SpinHold:
    """The rotate button held down across part of a schedule.

    ``t_start``/``t_end`` are fractions of the schedule's total duration, as
    in a recipe's ``spin`` block. True Skate's spin is a HOLD, not a tap.
    """
    enabled: bool = False
    t_start: float = 0.0
    t_end: float = 0.0

    def __post_init__(self) -> None:
        if not self.enabled:
            return
        if not (0.0 <= self.t_start <= 1.0 and 0.0 <= self.t_end <= 1.0):
            raise ValueError("spin t_start/t_end must be fractions in [0, 1]")
        if self.t_end <= self.t_start:
            raise ValueError(
                f"spin hold window is empty: [{self.t_start}, {self.t_end}]"
            )

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "SpinHold":
        if not d:
            return cls()
        return cls(
            enabled=bool(d.get("enabled", False)),
            t_start=float(d.get("t_start", 0.0)),
            t_end=float(d.get("t_end", 0.0)),
        )


@dataclass(frozen=True)
class Gesture:
    """A single touch path: normalised waypoints, duration, easing profile.

    ``easing_power`` follows GESTURES.md: velocity is proportional to
    ``t ** easing_power`` over normalised progress, so 1.0 is constant
    velocity, below 1.0 decelerates, above 1.0 accelerates.
    """
    points: tuple[Point, ...]
    duration: float
    easing_power: float = 1.0

    def __post_init__(self) -> None:
        if len(self.points) < 2:
            raise ValueError("a gesture needs at least 2 waypoints")
        for x, y in self.points:
            _check_normalised(x, y, where="gesture waypoint")
        if self.duration <= 0:
            raise ValueError(f"duration must be positive, got {self.duration}")
        if self.easing_power <= 0:
            raise ValueError(
                f"easing_power must be positive, got {self.easing_power}"
            )

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Gesture":
        return cls(
            points=tuple((float(x), float(y)) for x, y in d["points"]),
            duration=float(d["duration"]),
            easing_power=float(d.get("easing_power", 1.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "points": [list(p) for p in self.points],
            "duration": self.duration,
            "easing_power": self.easing_power,
        }


@dataclass(frozen=True)
class GestureRecipe:
    """An ordered list of gestures plus N-1 inter-gesture delays.

    ``delays[i]`` is the wait between the end of gesture *i* and the start
    of gesture *i+1*. Negative delays mean overlap and are legal; the
    executor is responsible for ordering slots by absolute start time.
    """
    gestures: tuple[Gesture, ...]
    delays: tuple[float, ...] = ()
    spin: SpinHold = field(default_factory=SpinHold)

    def __post_init__(self) -> None:
        if not self.gestures:
            raise ValueError("a recipe needs at least 1 gesture")
        expected = len(self.gestures) - 1
        if len(self.delays) != expected:
            raise ValueError(
                f"delays length {len(self.delays)} does not match N-1 "
                f"({expected}) for N={len(self.gestures)}"
            )

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GestureRecipe":
        return cls(
            gestures=tuple(Gesture.from_dict(g) for g in d["gestures"]),
            delays=tuple(float(x) for x in d.get("delays", ())),
            spin=SpinHold.from_dict(d.get("spin")),
        )

    def start_times(self) -> list[float]:
        """Absolute start time of each slot, from the delay chain.

        A sufficiently negative delay can place a later slot first, so these
        are not guaranteed to be non-decreasing; callers sort as needed.
        """
        starts = [0.0]
        for i in range(1, len(self.gestures)):
            starts.append(
                starts[i - 1] + self.gestures[i - 1].duration + self.delays[i - 1]
            )
        return starts

    def total_duration(self) -> float:
        starts = self.start_times()
        base = min(starts)
        return max(
            s - base + g.duration for s, g in zip(starts, self.gestures)
        )


def in_gesture_bounds(x: float, y: float) -> bool:
    """Whether a normalised point lies inside the valid gesture area."""
    return X_BOUND_MIN <= x <= X_BOUND_MAX and Y_BOUND_MIN <= y <= Y_BOUND_MAX


def easing_segment_durations(
    n_segments: int, total_duration: float, easing_power: float
) -> list[float]:
    """Split a gesture's duration across its segments under an easing power.

    Mirrors ``easing_to_segment_durations`` in TrueSkate-AI, but returns
    seconds rather than integer milliseconds: the Teensy takes a trajectory,
    not a W3C pointer payload.
    """
    if n_segments < 1:
        raise ValueError("n_segments must be >= 1")
    boundaries = [(i / n_segments) ** easing_power for i in range(n_segments + 1)]
    raw = [boundaries[i + 1] - boundaries[i] for i in range(n_segments)]
    total_raw = sum(raw)
    return [d / total_raw * total_duration for d in raw]
