from .device_data import DeviceInsightsTools
from .energy import EnergyInsightsTools
from .live import LiveInsightsTools


class InsightsTools:
    def __init__(self, homey_client):
        self.homey_client = homey_client
        self.device_data = DeviceInsightsTools(homey_client)
        self.energy = EnergyInsightsTools(homey_client)
        self.live = LiveInsightsTools(homey_client)

    def get_tools(self):
        """Return all insights tools."""
        tools = []
        tools.extend(self.device_data.get_tools())
        tools.extend(self.energy.get_tools())
        tools.extend(self.live.get_tools())
        return tools


__all__ = ["InsightsTools"]