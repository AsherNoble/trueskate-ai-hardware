"""Gesture/recipe schema, against the conventions in TrueSkate-AI GESTURES.md."""
import pytest

from trueskate_ai_hardware import Gesture, GestureRecipe, SpinHold, in_gesture_bounds
from trueskate_ai_hardware.actions import easing_segment_durations


def g(duration=0.3, points=((0.3, 0.3), (0.6, 0.6)), easing=1.0) -> Gesture:
    return Gesture(points=points, duration=duration, easing_power=easing)


def test_gesture_needs_two_waypoints():
    with pytest.raises(ValueError, match="at least 2"):
        Gesture(points=((0.5, 0.5),), duration=0.3)


def test_gesture_rejects_unnormalised_points():
    with pytest.raises(ValueError, match="normalised"):
        Gesture(points=((0.5, 0.5), (1.4, 0.5)), duration=0.3)


def test_gesture_rejects_non_positive_duration():
    with pytest.raises(ValueError, match="duration"):
        g(duration=0.0)


def test_gesture_round_trips_through_dict():
    d = {
        "points": [[0.3, 0.3], [0.5, 0.4], [0.6, 0.6]],
        "duration": 0.35,
        "easing_power": 1.5,
    }
    assert Gesture.from_dict(d).to_dict() == d


def test_gesture_easing_power_defaults_to_linear():
    assert Gesture.from_dict({"points": [[0.2, 0.2], [0.4, 0.4]], "duration": 0.1}).easing_power == 1.0


def test_recipe_delay_count_must_be_n_minus_one():
    with pytest.raises(ValueError, match="does not match N-1"):
        GestureRecipe(gestures=(g(), g()), delays=())


def test_single_gesture_recipe_takes_no_delays():
    assert GestureRecipe(gestures=(g(),)).delays == ()


def test_recipe_start_times_follow_the_delay_chain():
    r = GestureRecipe(gestures=(g(0.2), g(0.3), g(0.1)), delays=(0.1, 0.05))
    assert r.start_times() == pytest.approx([0.0, 0.3, 0.65])


def test_negative_delays_are_legal_and_overlap():
    r = GestureRecipe(gestures=(g(0.2), g(0.2)), delays=(-0.1,))
    assert r.start_times() == pytest.approx([0.0, 0.1])


def test_delay_negative_enough_reorders_slots():
    # A later slot can start before an earlier one; start_times reports it
    # honestly rather than clamping.
    r = GestureRecipe(gestures=(g(0.2), g(0.2)), delays=(-0.5,))
    assert r.start_times()[1] < 0


def test_total_duration_spans_from_earliest_start():
    r = GestureRecipe(gestures=(g(0.2), g(0.2)), delays=(-0.5,))
    assert r.total_duration() == pytest.approx(0.5)


def test_recipe_from_dict_with_spin():
    r = GestureRecipe.from_dict(
        {
            "gestures": [{"points": [[0.3, 0.3], [0.6, 0.6]], "duration": 0.3}],
            "delays": [],
            "spin": {"enabled": True, "t_start": 0.2, "t_end": 0.7},
        }
    )
    assert r.spin.enabled and r.spin.t_end == 0.7


def test_spin_window_must_be_non_empty():
    with pytest.raises(ValueError, match="empty"):
        SpinHold(enabled=True, t_start=0.5, t_end=0.5)


def test_disabled_spin_skips_validation():
    assert not SpinHold(enabled=False, t_start=0.9, t_end=0.1).enabled


def test_gesture_bounds_match_trueskate_constants():
    assert in_gesture_bounds(0.12, 0.12)
    assert in_gesture_bounds(1.0, 0.88)
    assert not in_gesture_bounds(0.05, 0.5)   # spin button column
    assert not in_gesture_bounds(0.5, 0.95)   # home indicator zone


def test_linear_easing_splits_evenly():
    d = easing_segment_durations(4, 1.0, 1.0)
    assert d == pytest.approx([0.25] * 4)


def test_easing_segments_always_sum_to_total():
    for power in (0.5, 1.0, 2.0, 3.0):
        assert sum(easing_segment_durations(5, 0.4, power)) == pytest.approx(0.4)


def test_accelerating_easing_starts_slow():
    # easing_power > 1: early segments cover less time than later ones.
    d = easing_segment_durations(4, 1.0, 2.0)
    assert d[0] < d[-1]


def test_decelerating_easing_starts_fast():
    d = easing_segment_durations(4, 1.0, 0.5)
    assert d[0] > d[-1]
