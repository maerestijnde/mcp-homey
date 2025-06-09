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
