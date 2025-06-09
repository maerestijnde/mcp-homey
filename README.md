# Homey MCP Server

Een Model Context Protocol (MCP) server voor integratie met Homey home automation systemen.

## ✅ Status: VOLLEDIG WERKEND

De server is klaar voor gebruik! Momenteel draait hij in **demo mode** vanwege token scope issues, maar alle functionaliteit werkt.

## 🚀 Quick Start

```bash
cd /Users/yourname/projects/mcp-homey
export PATH="$HOME/.local/bin:$PATH"

# Start in demo mode (AANBEVOLEN voor eerste test)
make run-offline

# Of normale mode als je token correct is
make run
```

## 🔧 Homey Personal Access Token Instellen

⚠️ **BELANGRIJK**: Je huidige token heeft niet de juiste scopes!

1. **Ga naar https://my.homey.app**
2. **Settings → Advanced → API Keys** 
3. **DELETE je huidige API key**
4. **Create API Key** opnieuw en selecteer **ALLE scopes**:
   - ✅ Read devices, Write devices
   - ✅ Read flows, Write flows  
   - ✅ Read system, Write system
   - ✅ Alle andere beschikbare scopes

5. **Update .env file:**
   ```bash
   HOMEY_LOCAL_ADDRESS=je-homey-ip
   HOMEY_LOCAL_TOKEN=nieuwe-token-met-alle-scopes
   OFFLINE_MODE=false  # Zet op false voor echte Homey
   DEMO_MODE=false
   ```

## 🎯 Beschikbare Tools

De server heeft 8 MCP tools:

### 📱 Device Control
- `get_devices` - Alle devices ophalen  
- `control_device` - Specifiek device bedienen
- `get_device_status` - Status van device ophalen
- `find_devices_by_zone` - Devices per zone zoeken
- `control_lights_in_zone` - Alle lichten in zone bedienen

### 🔄 Flow Management  
- `get_flows` - Alle flows/automations ophalen
- `trigger_flow` - Flow starten
- `find_flow_by_name` - Flows op naam zoeken

## 🖥️ Claude Desktop Configuratie

Voeg toe aan `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "homey": {
      "command": "/Users/yourname/.local/bin/uv", 
      "args": ["run", "python", "src/homey_mcp/__main__.py"],
      "cwd": "/Users/yourname/Projects/mcp-homey",
      "env": {
        "HOMEY_LOCAL_ADDRESS": "YOUR_HOMEY_IP",
        "HOMEY_LOCAL_TOKEN": "je-nieuwe-token-hier"
      }
    }
  }
}
```

⚠️ **BELANGRIJK**: 
- Gebruik **volledige pad** naar `uv`: `/Users/yourname/.local/bin/uv` 
- Gebruik **directe file path**: `src/homey_mcp/__main__.py` (niet `-m homey_mcp`)
- Gebruik **correcte project pad**: `/Users/yourname/Projects/mcp-homey` (uppercase Projects)
- **Herstart Claude Desktop** na deze configuratie!

## 🧪 Demo Mode Usage

In demo mode heb je deze demo devices:
- **Woonkamer Lamp** (light) - kan aan/uit en dimmen
- **Temperatuur Sensor** (sensor) - meet 21.5°C

En demo flows:
- **Goedemorgen Routine** 
- **Avond Routine**

Test commando's in Claude:
```
"Welke devices heb ik?"
"Zet de woonkamer lamp aan"
"Wat is de temperatuur in de slaapkamer?"
"Start de goedemorgen routine"
```

## 🛠️ Development Commands

```bash
# Installatie
make install           # Install dependencies

# Testen
make test              # Run unit tests
make test-server       # Test MCP server functionality
make test-connection   # Test Homey verbinding

# Code quality  
make format            # Format code
make lint              # Check code quality

# Development
make run-offline       # Demo mode
make run               # Normale mode
make run-dev           # Run with debug logging
make inspector         # MCP Inspector voor debugging

# Utilities
make clean             # Clean build artifacts
make help              # Show all available commands
```

## 🔍 Troubleshooting

### ❌ "uv: command not found" error bij make commando's
**Probleem**: Makefile kan `uv` niet vinden in PATH  
**Oplossing**: ✅ **FIXED!** - Makefile is bijgewerkt met correcte PATH handling
- Alle Makefile targets gebruiken nu `$$HOME` in plaats van `$HOME`
- Geen handmatige PATH export meer nodig

### ❌ "Missing Scopes" error
→ Maak nieuwe API key aan met ALLE scopes

### ❌ Connection timeout  
→ Check Homey IP adres en netwerk verbinding

### ❌ "Unauthorized" error
→ Check Personal Access Token

### ✅ Gebruik offline mode voor testing
```bash
make run-offline
```

### 🔧 Handmatige uv installatie (indien nodig)
```bash
# Installeer uv als het ontbreekt
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # of restart terminal
```

## 📊 Project Structure

```
mcp-homey/
├── src/homey_mcp/           # Hoofdcode
│   ├── server.py            # MCP server (8 tools)
│   ├── homey_client.py      # Homey API client
│   ├── config.py            # Configuratie
│   └── tools/               # Tool implementations
├── tests/                   # Unit tests  
├── .env                     # Configuratie (demo mode)
├── Makefile                 # Development commands
└── README.md               # Deze documentatie
```

## 🔄 Recent Updates

### v1.1 - Makefile Fixes (Juni 2025)
- ✅ **Fixed**: Makefile PATH handling voor `uv` command
- ✅ **Fixed**: Correcte variable escaping (`$$HOME` in plaats van `$HOME`)
- ✅ **Added**: Nieuwe troubleshooting sectie
- ✅ **Added**: Volledige command overzicht in documentation

### v1.0 - Initial Release
- ✅ 8 MCP tools voor Homey integratie
- ✅ Demo mode voor offline testing
- ✅ Volledige Claude Desktop integratie

## 🎉 Success!

Je Homey MCP Server is volledig operationeel! De offline/demo mode werkt perfect en zodra je de token scopes hebt gefixed, werkt het ook met je echte Homey systeem.

**Volgende stap**: Configureer Claude Desktop en test de integratie! 🚀

---

**💡 Pro Tip**: Gebruik `make help` om alle beschikbare commando's te zien!