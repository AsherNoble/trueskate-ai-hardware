"""The normalised-point -> rig transform, and workspace limits."""
import pytest

from trueskate_ai_hardware import FingerWorkspace, ScreenFrame, WorkspaceError

FRAME = ScreenFrame(origin=(10.0, 20.0), x_axis=(68.0, 0.0), y_axis=(0.0, 148.0))


def test_origin_maps_to_frame_origin():
    assert FRAME.to_rig(0.0, 0.0) == pytest.approx((10.0, 20.0))


def test_far_corner_maps_to_origin_plus_both_axes():
    assert FRAME.to_rig(1.0, 1.0) == pytest.approx((78.0, 168.0))


def test_transform_is_affine_in_each_axis():
    assert FRAME.to_rig(0.5, 0.25) == pytest.approx((44.0, 57.0))


def test_rotated_frame_needs_no_angle_term():
    # Phone turned 90 deg in the rig: the axis vectors carry the rotation.
    rotated = ScreenFrame(origin=(0.0, 0.0), x_axis=(0.0, 68.0), y_axis=(-148.0, 0.0))
    assert rotated.to_rig(1.0, 0.0) == pytest.approx((0.0, 68.0))
    assert rotated.to_rig(0.0, 1.0) == pytest.approx((-148.0, 0.0))


def test_unnormalised_point_rejected():
    with pytest.raises(WorkspaceError, match="normalised"):
        FRAME.to_rig(1.2, 0.5)


WS = FingerWorkspace(x_min=0.0, x_max=68.0, y_min=0.0, y_max=148.0)


def test_workspace_contains_interior_and_edges():
    assert WS.contains((34.0, 74.0))
    assert WS.contains((0.0, 0.0))
    assert WS.contains((68.0, 148.0))


def test_workspace_excludes_outside():
    assert not WS.contains((-1.0, 74.0))
    assert not WS.contains((34.0, 200.0))


def test_require_returns_point_when_reachable():
    assert WS.require((34.0, 74.0)) == (34.0, 74.0)


def test_require_raises_when_unreachable():
    with pytest.raises(WorkspaceError, match="outside the finger workspace"):
        WS.require((34.0, 200.0))
