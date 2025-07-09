# Homey MCP Server

A comprehensive Model Context Protocol (MCP) server for Homey smart home automation systems, providing seamless integration with Claude AI assistants.

## 🏠 Overview

The Homey MCP Server enables Claude AI to interact directly with your Homey Pro smart home system, offering real-time device control, automation management, and advanced analytics through natural language conversations.

**Key Capabilities:**
- 📱 **Device Control**: Control lights, thermostats, sensors, and smart appliances
- 🔄 **Flow Management**: Trigger and manage Homey automation flows
- 📊 **Advanced Analytics**: Historical data analysis, energy monitoring, and usage patterns
- 🌡️ **Climate Intelligence**: Temperature and humidity monitoring across zones
- ⚡ **Energy Insights**: Power consumption tracking and optimization recommendations
- 📈 **Live Monitoring**: Real-time dashboard metrics and system status

## 🚀 Quick Start

### Prerequisites

- Homey Pro device with local API access enabled
- Python 3.11+ with uv package manager
- Claude Desktop application
- Valid Homey Personal Access Token

**Platform Support**: macOS, Windows, Linux

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd mcp-homey
   make install
   
   # Make the script executable (macOS/Linux only)
   chmod +x start_homey_mcp.sh
   ```

2. **Get Homey Token**
   - Navigate to [Homey Developer Portal](https://my.homey.app)
   - Go to **Settings → Advanced → API Keys**
   - Create new API Key with **all available scopes**

3. **Configure Claude Desktop**
   
   **⚠️ IMPORTANT: Replace all paths with YOUR actual paths**
   
   ### 🍎 **macOS/Linux**
   Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "homey": {
         "command": "/path/to/your/uv/binary",
         "args": ["run", "--directory", "/path/to/your/mcp-homey", "python", "src/homey_mcp/__main__.py"],
         "env": {
           "HOMEY_LOCAL_ADDRESS": "YOUR_HOMEY_IP_ADDRESS",
           "HOMEY_LOCAL_TOKEN": "your-token-here",
           "OFFLINE_MODE": "false",
           "DEMO_MODE": "false"
         }
       }
     }
   }
   ```
   
   **Find your uv path with:**
   ```bash
   which uv
   # Usually: /Users/yourname/.local/bin/uv
   #      or: /usr/local/bin/uv  
   #      or: /opt/homebrew/bin/uv
   ```
   
   **Example with real paths:**
   ```json
   {
     "mcpServers": {
       "homey": {
         "command": "/Users/yourname/.local/bin/uv",
         "args": ["run", "--directory", "/Users/yourname/Projects/mcp-homey", "python", "src/homey_mcp/__main__.py"],
         "env": {
           "HOMEY_LOCAL_ADDRESS": "192.168.1.100",
           "HOMEY_LOCAL_TOKEN": "abc123xyz789",
           "OFFLINE_MODE": "false",
           "DEMO_MODE": "false"
         }
       }
     }
   }
   ```

   ### 🪟 **Windows**
   Add to `%APPDATA%\Claude\claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "homey": {
         "command": "uv",
         "args": ["run", "--directory", "C:\\path\\to\\mcp-homey", "python", "src/homey_mcp/__main__.py"],
         "env": {
           "HOMEY_LOCAL_ADDRESS": "YOUR_HOMEY_IP_ADDRESS",
           "HOMEY_LOCAL_TOKEN": "your-token-here",
           "OFFLINE_MODE": "false",
           "DEMO_MODE": "false"
         }
       }
     }
   }
   ```
   
   **Find your uv path with:**
   ```powershell
   where uv
   # Usually: C:\Users\yourname\.local\bin\uv.exe
   #      or: C:\Program Files\uv\uv.exe
   ```
   
   **Example with real paths:**
   ```json
   {
     "mcpServers": {
       "homey": {
         "command": "C:\\Users\\yourname\\.local\\bin\\uv.exe",
         "args": ["run", "--directory", "C:\\Users\\yourname\\Projects\\mcp-homey", "python", "src/homey_mcp/__main__.py"],
         "env": {
           "HOMEY_LOCAL_ADDRESS": "192.168.1.100",
           "HOMEY_LOCAL_TOKEN": "abc123xyz789",
           "OFFLINE_MODE": "false",
           "DEMO_MODE": "false"
         }
       }
     }
   }
   ```
   
   **Windows Notes:**
   - Install uv first: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - Use full Windows paths with double backslashes: `C:\\Users\\Name\\Projects\\mcp-homey`
   - Restart PowerShell after installing uv
   - Use `where uv` to find the exact uv.exe path

4. **Find Your Paths**
   
   Before configuring Claude, find the correct paths for your system:
   
   **macOS/Linux:**
   ```bash
   # Find uv location
   which uv
   
   # Find project directory  
   cd path/to/mcp-homey && pwd
   
   # Example output:
   # /Users/yourname/.local/bin/uv
   # /Users/yourname/Projects/mcp-homey
   ```
   
   **Windows:**
   ```powershell
   # Find uv location
   where uv
   
   # Find project directory
   cd path\to\mcp-homey; pwd
   
   # Example output:
   # C:\Users\yourname\.local\bin\uv.exe
   # C:\Users\yourname\Projects\mcp-homey
   ```

5. **Restart Claude Desktop and test!**

## ⚙️ Operating Modes

Switch modes by editing your Claude Desktop config and restarting Claude:

### 🏠 **Normal Mode** (Real Homey)
```json
"env": {
  "HOMEY_LOCAL_ADDRESS": "YOUR_HOMEY_IP_ADDRESS",
  "HOMEY_LOCAL_TOKEN": "your-actual-token",
  "OFFLINE_MODE": "false",
  "DEMO_MODE": "false"
}
```

### 🧪 **Demo Mode** (Testing without Homey)
```json
"env": {
  "OFFLINE_MODE": "true",
  "DEMO_MODE": "true"
}
```
*Demo includes: Multi-room setup, various device types, sensors, flows, and analytics data*

### 🔧 **Development Mode** 
```json
"env": {
  "OFFLINE_MODE": "true",
  "DEMO_MODE": "false"
}
```
*Offline but minimal demo data*

## 🛠️ Available Tools (16 total)

### 📱 Device Control (8 tools)
`get_devices` • `control_device` • `get_device_status` • `find_devices_by_zone` • `control_lights_in_zone` • `set_thermostat_temperature` • `set_light_color` • `get_sensor_readings`

### 🔄 Flow Management (3 tools)  
`get_flows` • `trigger_flow` • `find_flow_by_name`

### 📊 Analytics & Insights (5 tools)
`get_device_insights` • `get_energy_insights` • `get_live_insights` • `get_energy_report_hourly` • `get_energy_report_yearly`

## 💬 Usage Examples

```
"What devices do I have?"
"Turn on the kitchen lights at 75%"
"Set thermostat to 22 degrees"
"Start the evening routine"
"Show my energy usage this month"
"Export temperature data to CSV"
```

## 🔧 Development & Debugging

### 🍎 **macOS/Linux**
```bash
# Manual testing
export OFFLINE_MODE="true" DEMO_MODE="true"
./start_homey_mcp.sh

# Development commands  
make install test lint format
python test_capabilities.py
python test_insights.py

# Debugging
tail -f homey_mcp_debug.log
make inspector  # Web UI at localhost:5173
```

### 🪟 **Windows**
```powershell
# Manual testing
$env:OFFLINE_MODE="true"; $env:DEMO_MODE="true"
uv run python src/homey_mcp/__main__.py

# Development commands
uv sync
uv run pytest
uv run python test_capabilities.py
uv run python test_insights.py

# Debugging
Get-Content homey_mcp_debug.log -Wait  # Like tail -f
```

## 🔍 Troubleshooting

### 🪟 **Windows-specific**
**❌ "uv not found"** → Install uv: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`  
**❌ Path issues** → Use full Windows paths with double backslashes: `C:\\Users\\Name\\Projects\\mcp-homey`  
**❌ PowerShell execution policy** → Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`  
**❌ Wrong uv path** → Use `where uv` to find exact path, then use full path like `C:\\Users\\yourname\\.local\\bin\\uv.exe`

### 🍎 **macOS/Linux**  
**❌ "uv not found"** → Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` and restart terminal  
**❌ "command not found"** → Use full path to uv binary: `/Users/yourname/.local/bin/uv`  
**❌ Permission denied** → Make sure uv is executable: `chmod +x /path/to/uv`  
**❌ Wrong paths** → Use `which uv` and `pwd` to get correct absolute paths  

### 🌐 **All Platforms**
**❌ Missing scopes** → Create API key with ALL scopes at [my.homey.app](https://my.homey.app)  
**❌ Connection timeout** → Verify Homey IP and network connectivity  
**❌ Unauthorized** → Check token validity and expiration

---

**Built with ❤️ for the Homey community**
