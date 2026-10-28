import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from homey_mcp.config import HomeyMCPConfig
from homey_mcp.homey_client import HomeyAPIClient


@pytest.fixture
def mock_config():
    """Mock configuratie voor tests."""
    return HomeyMCPConfig(homey_local_address="192.168.1.100", homey_local_token="test-token")


@pytest.fixture
def homey_client(mock_config):
    """Homey client fixture."""
    return HomeyAPIClient(mock_config)


@pytest.mark.asyncio
async def test_homey_client_connect(homey_client):
    """Test connectie naar Homey."""
    with patch.object(homey_client, "session") as mock_session:
        mock_response = AsyncMock()
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        # Set session to mock
        homey_client.session = mock_session

        # Test connect method internals
        await homey_client.connect()

        # Verify session get was called
        mock_session.get.assert_called_with("/api/manager/system")


def test_config_creation():
    """Test dat configuratie correct wordt aangemaakt."""
    config = HomeyMCPConfig(homey_local_address="192.168.1.100", homey_local_token="test-token")

    assert config.homey_local_address == "192.168.1.100"
    assert config.homey_local_token == "test-token"
    assert config.log_level == "DEBUG"  # waarde uit .env file


@pytest.mark.asyncio
async def test_get_device_reads_live_not_cache(homey_client):
    """get_device moet live lezen, ook als de device-cache nog vers is."""
    import time
    from unittest.mock import MagicMock

    homey_client._device_cache = {"dev1": {"id": "dev1", "capabilitiesObj": {"onoff": {"value": True}}}}
    homey_client._cache_timestamp = time.time()

    live = MagicMock(status_code=200)
    live.json.return_value = {"id": "dev1", "zone": "z1", "capabilitiesObj": {"onoff": {"value": False}}}
    homey_client.session = MagicMock()
    homey_client.session.get = AsyncMock(return_value=live)

    with patch.object(homey_client.devices, "get_zones", AsyncMock(return_value={"z1": {"name": "Garage"}})):
        device = await homey_client.get_device("dev1")

    homey_client.session.get.assert_called_with("/api/manager/devices/device/dev1")
    assert device["capabilitiesObj"]["onoff"]["value"] is False
    assert device["zoneName"] == "Garage"
    assert homey_client._device_cache["dev1"] is device


@pytest.mark.asyncio
async def test_get_device_not_found(homey_client):
    from unittest.mock import MagicMock

    homey_client.session = MagicMock()
    homey_client.session.get = AsyncMock(return_value=MagicMock(status_code=404))

    with pytest.raises(ValueError, match="not found"):
        await homey_client.get_device("nope")
