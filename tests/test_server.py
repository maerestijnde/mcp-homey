import pytest

from homey_mcp.server import get_server


def test_server_creation():
    """Test dat de server correct wordt aangemaakt."""
    server = get_server()
    assert server is not None
    assert hasattr(server, "name")
    assert server.name == "Homey Integration Server"


def test_import_modules():
    """Test dat alle modules correct importeren."""
    from homey_mcp.config import get_config
    from homey_mcp.homey_client import HomeyAPIClient
    from homey_mcp.tools import DeviceControlTools, FlowManagementTools

    # Test dat configuratie werkt
    config = get_config()
    assert config.log_level == "DEBUG"

    # Test dat classes bestaan
    assert DeviceControlTools is not None
    assert FlowManagementTools is not None
    assert HomeyAPIClient is not None
