"""Hand driven entirely through a mock client -- no hardware, no serial."""
import pytest

from trueskate_ai_hardware import (
    Gesture,
    GestureRecipe,
    Hand,
    HardwareError,
    MockMotorClient,
    SpinHold,
)
from trueskate_ai_hardware.config import hand_config_from_dict

ONE_AXIS = hand_config_from_dict(
    {
        "name": "one",
        "axes": [{"name": "index", "motor_type": "mock", "angle_limits": [-1.5, 1.5]}],
    }
)
TWO_AXIS = hand_config_from_dict(
    {
        "name": "two",
        "axes": [
            {"name": "index", "motor_type": "mock", "angle_limits": [-1.5, 1.5]},
            {"name": "middle", "motor_type": "mock", "angle_limits": [-1.5, 1.5]},
        ],
    }
)


def hand(cfg=ONE_AXIS) -> Hand:
    return Hand(cfg, MockMotorClient(cfg.axis_names()))


def test_hand_builds_its_own_client_from_config():
    h = Hand(ONE_AXIS)
    assert isinstance(h.client, MockMotorClient)


def test_hand_refuses_to_guess_for_a_hybrid_config():
    hybrid = hand_config_from_dict(
        {
            "name": "hybrid",
            "axes": [
                {"name": "index", "motor_type": "mock", "angle_limits": [-1.0, 1.0]},
                {"name": "ring", "motor_type": "simplefoc", "angle_limits": [0.0, 1.0]},
            ],
        }
    )
    with pytest.raises(HardwareError, match="mixes motor families"):
        Hand(hybrid)


def test_connect_align_read_round_trip():
    h = hand()
    h.connect()
    h.align()
    states = h.read_state()
    assert [s.name for s in states] == ["index"]
    assert states[0].ready and not states[0].enabled
    h.disconnect()


def test_context_manager_connects_and_disconnects():
    with hand() as h:
        assert h.client.is_connected
    assert not h.client.is_connected


# ----- the touch interface validates before it refuses ---------------------


def test_tap_rejects_unnormalised_point_before_refusing():
    with pytest.raises(ValueError, match="normalised"):
        hand().tap(1.5, 0.5)


def test_tap_is_not_implemented_yet():
    with pytest.raises(HardwareError, match="not implemented"):
        hand().tap(0.5, 0.5)


def test_long_press_rejects_non_positive_duration():
    with pytest.raises(ValueError, match="duration must be positive"):
        hand().long_press(0.5, 0.5, duration=0.0)


def test_long_press_is_not_implemented_yet():
    with pytest.raises(HardwareError, match="not implemented"):
        hand().long_press(0.5, 0.5, duration=0.4)


def test_double_tap_is_not_implemented_yet():
    with pytest.raises(HardwareError, match="not implemented"):
        hand().double_tap(0.5, 0.5)


def test_curved_drag_validates_every_waypoint():
    # Gesture itself rejects the bad point at construction.
    with pytest.raises(ValueError, match="normalised"):
        Gesture(points=((0.3, 0.3), (0.5, 1.9)), duration=0.3)


def test_curved_drag_is_not_implemented_yet():
    g = Gesture(points=((0.3, 0.3), (0.6, 0.6)), duration=0.3)
    with pytest.raises(HardwareError, match="not implemented"):
        hand().curved_drag(g)


def test_recipe_is_not_implemented_yet():
    r = GestureRecipe(gestures=(Gesture(points=((0.3, 0.3), (0.6, 0.6)), duration=0.3),))
    with pytest.raises(HardwareError, match="not implemented"):
        hand().execute_recipe(r)


def test_spin_recipe_needs_a_second_finger():
    # One finger cannot hold the spin button and drag at once; caught up
    # front rather than discovered mid-motion.
    r = GestureRecipe(
        gestures=(Gesture(points=((0.3, 0.3), (0.6, 0.6)), duration=0.3),),
        spin=SpinHold(enabled=True, t_start=0.2, t_end=0.7),
    )
    with pytest.raises(HardwareError, match="spin button must be held"):
        hand(ONE_AXIS).execute_recipe(r)


def test_spin_recipe_accepted_on_a_two_axis_hand():
    r = GestureRecipe(
        gestures=(Gesture(points=((0.3, 0.3), (0.6, 0.6)), duration=0.3),),
        spin=SpinHold(enabled=True, t_start=0.2, t_end=0.7),
    )
    # Gets past the axis-count check, then hits the not-implemented wall.
    with pytest.raises(HardwareError, match="not implemented"):
        hand(TWO_AXIS).execute_recipe(r)


def test_reset_position_is_not_implemented_yet():
    with pytest.raises(HardwareError, match="not implemented"):
        hand().reset_position()
