"""Hand config loading and validation."""
import pytest

from trueskate_ai_hardware import ConfigError, load_hand_config
from trueskate_ai_hardware.config import hand_config_from_dict

MINIMAL = {
    "name": "test-hand",
    "axes": [{"name": "index", "motor_type": "simplefoc", "angle_limits": [-1.57, 1.57]}],
}


def test_minimal_config_loads():
    cfg = hand_config_from_dict(MINIMAL)
    assert cfg.axis_names() == ("index",)
    assert cfg.axis("index").motor_type == "simplefoc"


def test_missing_axes_block_rejected():
    with pytest.raises(ConfigError, match="no 'axes' block"):
        hand_config_from_dict({"name": "x"})


def test_empty_axes_rejected():
    with pytest.raises(ConfigError, match="no axes"):
        hand_config_from_dict({"name": "x", "axes": []})


def test_duplicate_axis_names_rejected():
    data = {"name": "x", "axes": [MINIMAL["axes"][0], MINIMAL["axes"][0]]}
    with pytest.raises(ConfigError, match="duplicate axis names"):
        hand_config_from_dict(data)


def test_empty_angle_limits_rejected():
    data = {
        "name": "x",
        "axes": [{"name": "index", "motor_type": "simplefoc", "angle_limits": [1.0, 1.0]}],
    }
    with pytest.raises(ConfigError, match="is empty"):
        hand_config_from_dict(data)


def test_missing_axis_field_names_the_field():
    data = {"name": "x", "axes": [{"name": "index", "motor_type": "simplefoc"}]}
    with pytest.raises(ConfigError, match="angle_limits"):
        hand_config_from_dict(data)


def test_unknown_axis_lookup_raises():
    with pytest.raises(ConfigError, match="no axis named"):
        hand_config_from_dict(MINIMAL).axis("thumb")


def test_motor_types_are_distinct_and_ordered():
    data = {
        "name": "hybrid",
        "axes": [
            {"name": "index", "motor_type": "simplefoc", "angle_limits": [-1.0, 1.0]},
            {"name": "middle", "motor_type": "simplefoc", "angle_limits": [-1.0, 1.0]},
            {"name": "ring", "motor_type": "servo", "angle_limits": [0.0, 1.0]},
        ],
    }
    assert hand_config_from_dict(data).motor_types() == ("simplefoc", "servo")


def test_shipped_config_is_valid():
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "config" / "hand.yaml"
    cfg = load_hand_config(path)
    assert "index" in cfg.axis_names()
    assert cfg.screen is not None


def test_missing_file_raises():
    with pytest.raises(ConfigError, match="no hand config"):
        load_hand_config("/nonexistent/hand.yaml")
