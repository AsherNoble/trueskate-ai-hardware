"""The one coordinate transform: normalised screen point -> finger workspace.

TrueSkate-AI keeps a single transform in its pipeline, ``scale_to_device()``,
which multiplies a normalised [0, 1] point by the device's logical size. The
physical equivalent is the same idea with a different target frame: the
phone lies in the rig at a known position, so a normalised point maps
affinely onto the plane the fingertip travels across.

Deliberately affine and nothing more. Any lens distortion, parallax or
per-rig fudge belongs in the calibration that produces these bounds, not
here -- mirroring GESTURES.md's insistence that no offset or per-device
correction creeps into the transform itself.
"""
from __future__ import annotations

from dataclasses import dataclass

from .errors import WorkspaceError

Point = tuple[float, float]


@dataclass(frozen=True)
class ScreenFrame:
    """Where the phone's screen sits in the rig, in millimetres.

    ``origin`` is the screen's normalised (0, 0) corner. ``x_axis`` and
    ``y_axis`` are the full-width and full-height vectors from it, so a
    normalised point maps to ``origin + x*x_axis + y*y_axis``. Expressing
    both as vectors rather than a width and a height lets the phone sit
    rotated in the rig without a separate angle term.
    """
    origin: Point
    x_axis: Point
    y_axis: Point

    def to_rig(self, x: float, y: float) -> Point:
        """Map a normalised [0, 1] screen point to rig millimetres."""
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise WorkspaceError(f"({x}, {y}) is not normalised to [0, 1]")
        return (
            self.origin[0] + x * self.x_axis[0] + y * self.y_axis[0],
            self.origin[1] + x * self.x_axis[1] + y * self.y_axis[1],
        )


@dataclass(frozen=True)
class FingerWorkspace:
    """The reachable rectangle for one finger, in the same rig frame.

    A finger reaches part of the screen, not all of it -- which is why the
    hand is hybrid and why more than one finger exists. ``contains`` is the
    check a planner runs before accepting a gesture.
    """
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    def contains(self, point: Point) -> bool:
        x, y = point
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max

    def require(self, point: Point) -> Point:
        if not self.contains(point):
            raise WorkspaceError(
                f"{point} is outside the finger workspace "
                f"x[{self.x_min}, {self.x_max}] y[{self.y_min}, {self.y_max}]"
            )
        return point
