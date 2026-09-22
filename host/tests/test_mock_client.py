"""Mock client lifecycle: the rules a real controller must also enforce."""
import pytest

from trueskate_ai_hardware import MockMotorClient, MotorError


def make() -> MockMotorClient:
    return MockMotorClient(["index", "middle"])


def test_starts_disconnected():
    assert not make().is_connected


def test_connect_leaves_axes_de_energised():
    c = make()
    c.connect()
    assert c.is_connected
    assert all(not s.enabled for s in c.read_state())


def test_commands_before_connect_raise():
    c = make()
    with pytest.raises(MotorError):
        c.read_state()


def test_cannot_energise_before_align():
    c = make()
    c.connect()
    with pytest.raises(MotorError, match="before align"):
        c.set_torque_enabled(["index"], True)


def test_align_then_energise():
    c = make()
    c.connect()
    c.align()
    c.set_torque_enabled(["index"], True)
    state = {s.name: s for s in c.read_state()}
    assert state["index"].ready and state["index"].enabled
    # align() does not energise anything by itself.
    assert not state["middle"].enabled


def test_write_target_angle_requires_energised_axis():
    c = make()
    c.connect()
    c.align()
    with pytest.raises(MotorError, match="not energised"):
        c.write_target_angle(["index"], [0.5])


def test_write_target_angle_moves_axis():
    c = make()
    c.connect()
    c.align()
    c.set_torque_enabled(["index"], True)
    c.write_target_angle(["index"], [0.5])
    state = {s.name: s for s in c.read_state()}
    assert state["index"].angle == pytest.approx(0.5)
    assert state["middle"].angle == pytest.approx(0.0)


def test_angle_count_must_match_axis_count():
    c = make()
    c.connect()
    c.align()
    c.set_torque_enabled(["index", "middle"], True)
    with pytest.raises(MotorError, match="angles for"):
        c.write_target_angle(["index", "middle"], [0.1])


def test_unknown_axis_rejected():
    c = make()
    c.connect()
    with pytest.raises(MotorError, match="unknown axes"):
        c.read_state(["thumb"])


def test_trajectory_recorded_and_lands_on_final_angle():
    c = make()
    c.connect()
    c.align()
    c.set_torque_enabled(["index"], True)
    c.write_trajectory("index", [0.0, 0.1, 0.2], [0.0, 0.3, 0.6])
    assert len(c.trajectories) == 1
    name, times, angles = c.trajectories[0]
    assert name == "index"
    assert times == (0.0, 0.1, 0.2)
    assert c.read_state(["index"])[0].angle == pytest.approx(0.6)


def test_trajectory_rejects_non_increasing_times():
    c = make()
    c.connect()
    c.align()
    c.set_torque_enabled(["index"], True)
    with pytest.raises(MotorError, match="strictly increasing"):
        c.write_trajectory("index", [0.0, 0.1, 0.1], [0.0, 0.1, 0.2])


def test_trajectory_rejects_mismatched_lengths():
    c = make()
    c.connect()
    c.align()
    c.set_torque_enabled(["index"], True)
    with pytest.raises(MotorError, match="times and"):
        c.write_trajectory("index", [0.0, 0.1], [0.0])


def test_stop_de_energises():
    c = make()
    c.connect()
    c.align()
    c.set_torque_enabled(["index"], True)
    c.stop()
    assert all(not s.enabled for s in c.read_state())


def test_disconnect_de_energises():
    c = make()
    c.connect()
    c.align()
    c.set_torque_enabled(["index"], True)
    c.disconnect()
    assert not c.is_connected


def test_context_manager_round_trip():
    with make() as c:
        assert c.is_connected
    assert not c.is_connected


def test_family_attributes():
    assert MockMotorClient.motor_family == "mock"
    assert MockMotorClient.needs_alignment
    assert MockMotorClient.executes_trajectories
