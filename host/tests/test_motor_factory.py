"""The one place motor_type maps to a client."""
import pytest

from trueskate_ai_hardware import ConfigError, MockMotorClient, TeensyMotorClient
from trueskate_ai_hardware.motor_factory import create_motor_client, motor_client_class


def test_mock_family_resolves():
    assert motor_client_class("mock") is MockMotorClient


def test_simplefoc_family_resolves():
    assert motor_client_class("simplefoc") is TeensyMotorClient


def test_unknown_family_lists_the_supported_ones():
    with pytest.raises(ConfigError, match="Expected one of"):
        motor_client_class("dynamixel")


def test_create_mock_needs_no_port():
    c = create_motor_client("mock", ["index"])
    assert isinstance(c, MockMotorClient)


def test_create_simplefoc_requires_a_port():
    with pytest.raises(ConfigError, match="requires a serial port"):
        create_motor_client("simplefoc", ["index"])


def test_create_returns_an_unconnected_client():
    assert not create_motor_client("mock", ["index"]).is_connected
