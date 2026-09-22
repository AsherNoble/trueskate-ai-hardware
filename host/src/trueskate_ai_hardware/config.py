"""Hand configuration: one YAML file describes a hand, as in orca_core.

A hand is a list of axes, each naming the motor family that drives it, plus
the rig geometry that maps normalised screen points onto the plane the
fingertips travel across. The hand is hybrid on purpose -- SimpleFOC axes
and (later) servo axes coexist in one config and one Hand.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError
from .geometry import FingerWorkspace, ScreenFrame


@dataclass(frozen=True)
class AxisConfig:
    """One controllable axis of the hand."""
    name: str
    motor_type: str
    #: Joint travel limits in radians; motion outside these is refused.
    angle_limits: tuple[float, float]
    workspace: FingerWorkspace | None = None

    def __post_init__(self) -> None:
        lo, hi = self.angle_limits
        if hi <= lo:
            raise ConfigError(
                f"axis {self.name!r}: angle_limits {self.angle_limits} is empty"
            )


@dataclass(frozen=True)
class HandConfig:
    """A whole hand: its axes, transport and rig geometry."""
    name: str
    axes: tuple[AxisConfig, ...]
    port: str | None = None
    baudrate: int = 115200
    screen: ScreenFrame | None = None

    def __post_init__(self) -> None:
        if not self.axes:
            raise ConfigError(f"hand {self.name!r} has no axes")
        names = [a.name for a in self.axes]
        if len(set(names)) != len(names):
            raise ConfigError(f"hand {self.name!r} has duplicate axis names: {names}")

    def axis(self, name: str) -> AxisConfig:
        for a in self.axes:
            if a.name == name:
                return a
        raise ConfigError(f"no axis named {name!r} in hand {self.name!r}")

    def axis_names(self) -> tuple[str, ...]:
        return tuple(a.name for a in self.axes)

    def motor_types(self) -> tuple[str, ...]:
        """Distinct motor families in this hand, in first-seen order."""
        seen: list[str] = []
        for a in self.axes:
            if a.motor_type not in seen:
                seen.append(a.motor_type)
        return tuple(seen)


def _workspace_from_dict(d: dict[str, Any] | None) -> FingerWorkspace | None:
    if not d:
        return None
    try:
        return FingerWorkspace(
            x_min=float(d["x_min"]),
            x_max=float(d["x_max"]),
            y_min=float(d["y_min"]),
            y_max=float(d["y_max"]),
        )
    except KeyError as exc:
        raise ConfigError(f"workspace is missing {exc.args[0]!r}") from exc


def _screen_from_dict(d: dict[str, Any] | None) -> ScreenFrame | None:
    if not d:
        return None
    try:
        return ScreenFrame(
            origin=tuple(float(v) for v in d["origin"]),  # type: ignore[arg-type]
            x_axis=tuple(float(v) for v in d["x_axis"]),  # type: ignore[arg-type]
            y_axis=tuple(float(v) for v in d["y_axis"]),  # type: ignore[arg-type]
        )
    except KeyError as exc:
        raise ConfigError(f"screen frame is missing {exc.args[0]!r}") from exc


def hand_config_from_dict(data: dict[str, Any]) -> HandConfig:
    """Build a HandConfig from already-parsed YAML."""
    if "axes" not in data:
        raise ConfigError("hand config has no 'axes' block")

    axes = []
    for entry in data["axes"]:
        try:
            axes.append(
                AxisConfig(
                    name=str(entry["name"]),
                    motor_type=str(entry["motor_type"]),
                    angle_limits=(
                        float(entry["angle_limits"][0]),
                        float(entry["angle_limits"][1]),
                    ),
                    workspace=_workspace_from_dict(entry.get("workspace")),
                )
            )
        except KeyError as exc:
            raise ConfigError(f"axis entry is missing {exc.args[0]!r}") from exc

    return HandConfig(
        name=str(data.get("name", "hand")),
        axes=tuple(axes),
        port=data.get("port"),
        baudrate=int(data.get("baudrate", 115200)),
        screen=_screen_from_dict(data.get("screen")),
    )


def load_hand_config(path: str | Path) -> HandConfig:
    """Load and validate a hand config YAML."""
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"no hand config at {p}")
    with p.open() as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ConfigError(f"{p} did not parse to a mapping")
    return hand_config_from_dict(data)
