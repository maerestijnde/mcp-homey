# Homey MCP Server

Connect Claude to your **Homey Pro** over your local network. Ask Claude about your devices, switch things on and off, read sensors and energy usage, and let it build advanced flows for you, all in plain language.

It runs on your own computer and talks straight to your Homey on your home network. Nothing goes through a cloud service except your conversation with Claude.

---

## What it can do

19 tools, in three groups.

### Devices and rooms

| Tool | What it does |
|---|---|
| `get_devices` | List every device with its current state |
| `get_device_status` | Live state of one device |
| `control_device` | Set any capability: on/off, dim level, target temperature, blinds, … |
| `get_zones` | List your rooms (zones) |
| `find_devices_by_zone` | Everything in one room, optionally only one type (e.g. `light`) |
| `control_lights_in_zone` | All lights in a room on, off or toggle, with optional brightness |
| `get_sensor_readings` | Temperature, humidity, battery and power per room |

### Flows

| Tool | What it does |
|---|---|
| `get_flows`, `get_flow`, `get_flow_folders` | Read your basic and advanced flows |
| `trigger_flow` | Start a flow |
| `get_flow_cards` | Search the trigger, condition and action cards your Homey has |
| `run_flow_card_action` | Run one action card directly, without a flow |
| `create_advanced_flow` | Build a new advanced flow |
| `update_advanced_flow` | Change an existing advanced flow |
| `delete_advanced_flow` | Delete an advanced flow (Claude has to repeat the exact flow name) |

Creating and changing advanced flows is safe by default. Every flow is checked against the real cards on your Homey, the tools only **validate** unless Claude explicitly sets `dry_run=false`, and new flows start **disabled**. Basic flows can be read and started, not edited.

### Insights and energy

| Tool | What it does |
|---|---|
| `get_device_insights` | History of one value (e.g. temperature) over 1 hour to 1 year |
| `get_energy_data` | Energy use per device, room or type, for a period, a specific hour or a year |
| `get_live_insights` | Live snapshot: current power, temperatures, devices that are on |

### Things you can ask

```
What devices do I have in the living room?
Turn off all the lights downstairs.
Set the bedroom thermostat to 19 degrees.
How warm and humid is it in each room?
Which devices used the most energy this week?
Show me the temperature in the bathroom over the last 24 hours.
Which flows are broken?
Make an advanced flow that turns on the hallway light when motion is detected after sunset. Leave it disabled.
```

---

## Setup (about 10 minutes)

### What you need

- A **Homey Pro**. Homey Cloud and Homey Bridge have no local API, so they won't work.
- A computer on the **same network** as the Homey (Windows, macOS or Linux).
- **Claude Desktop** ([download](https://claude.ai/download)) or Claude Code.

You don't need to install Python. The next step installs `uv`, which fetches the right Python version by itself.

### Step 1: Install uv

**macOS / Linux**, in Terminal:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows**, in PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then **close the terminal and open a new one**, so it finds `uv`.

### Step 2: Download this repo

With git:

```bash
git clone https://github.com/maerestijnde/mcp-homey.git
cd mcp-homey
```

Without git: on the GitHub page, click **Code → Download ZIP**, unzip it somewhere permanent (for example `Documents/mcp-homey`), and open a terminal in that folder.

Remember where the folder is: Claude needs the full path in step 6.

### Step 3: Create a Homey API key

1. Go to **[my.homey.app](https://my.homey.app)** and sign in.
2. Pick your Homey, then open **Settings** (the gear icon, bottom left) → **API Keys**.
3. Click **New API Key**, give it a name (for example `Claude`), and **select all scopes**. If you leave scopes out, some tools will return "Unauthorized".
4. Click **Create** and **copy the key right away**. Homey shows it only once.

The key looks like three long codes separated by colons (`xxxxxxxx-…:xxxxxxxx-…:xxxx…`). Copy the whole thing.

> ⚠️ This key gives full control over your Homey. Don't share it or post it anywhere. If it leaks, delete it in the same API Keys screen and create a new one.

### Step 4: Find your Homey's IP address

In the Homey app under **Settings → General**, or in your router's list of connected devices (look for "Homey"). It looks like `192.168.1.42`.

Tip: give the Homey a fixed IP (a DHCP reservation in your router), so the setup doesn't break when the address changes.

### Step 5: Put the key and IP in `.env`

Copy the example file to `.env`:

```bash
# macOS / Linux
cp .env.example .env
```

```powershell
# Windows
copy .env.example .env
```

Open `.env` in a text editor and fill in two lines:

```ini
HOMEY_LOCAL_ADDRESS=192.168.1.42
HOMEY_LOCAL_TOKEN=paste-your-whole-api-key-here
```

Leave the rest as it is. `.env` is in `.gitignore`, so your key never ends up in git.

On macOS, Finder hides files that start with a dot. Press **Cmd+Shift+.** to show them, or run `open -e .env` from the terminal.

### Step 6: Test it

```bash
uv run python scripts/mcp_call.py get_zones
```

The first run takes a minute, because it installs everything. You should then see your rooms. If you see an error instead, check [Troubleshooting](#troubleshooting).

To see all 19 tools: `uv run python scripts/mcp_call.py`

### Step 7: Connect it to Claude

#### Claude Desktop

1. Open Claude Desktop → **Settings → Developer → Edit Config**. This opens `claude_desktop_config.json`.
2. Find the full path of `uv`:
   - macOS / Linux: `which uv` (usually `/Users/<you>/.local/bin/uv`)
   - Windows: `where uv` (usually `C:\Users\<you>\.local\bin\uv.exe`)
3. Paste this and fill in **your** paths. If the file already contains other servers, add `"homey": {...}` inside the existing `mcpServers` block.

**macOS / Linux**

```json
{
  "mcpServers": {
    "homey": {
      "command": "/Users/<you>/.local/bin/uv",
      "args": ["run", "--directory", "/Users/<you>/mcp-homey", "python", "-m", "homey_mcp"]
    }
  }
}
```

**Windows** (use double backslashes `\\` in paths)

```json
{
  "mcpServers": {
    "homey": {
      "command": "C:\\Users\\<you>\\.local\\bin\\uv.exe",
      "args": ["run", "--directory", "C:\\Users\\<you>\\mcp-homey", "python", "-m", "homey_mcp"]
    }
  }
}
```

4. **Quit Claude Desktop completely** (menu bar or system tray → Quit, closing the window is not enough) and start it again.
5. In a new chat, open the tools menu (the slider icon under the message box). `homey` should be listed. Ask: *"Which rooms do I have in Homey?"*

The key and IP come from `.env`, so they don't go in this config file.

#### Claude Code

One command, from any folder (fill in your own path):

```bash
claude mcp add homey --scope user -- uv run --directory /path/to/mcp-homey python -m homey_mcp
```

Check it with `claude mcp list`. `--scope user` makes it available in all your projects.

---

## Building advanced flows: the Claude skill

This repo comes with a Claude skill, `homey-advanced-flows`, in [`.claude/skills/`](.claude/skills/homey-advanced-flows/SKILL.md). It gives Claude:

- the exact card format: card ids, arguments, tokens and delays
- a safe way of working: validate first, create flows disabled, then check that the flow isn't broken
- fixes for the usual errors

How to use it:

- **Claude Code**: nothing to do. Claude loads it automatically when you work in this folder.
- **Claude Desktop**: zip the `homey-advanced-flows` folder, then upload the zip under **Settings → Capabilities → Skills**. Skills need a paid Claude plan. On macOS:

  ```bash
  cd .claude/skills && zip -r ~/Desktop/homey-advanced-flows.zip homey-advanced-flows
  ```

  On Windows, right-click the folder → **Send to → Compressed (zipped) folder**.

---

## Trying it without a Homey

Set this in `.env` to get a fake house with demo devices, flows and energy data:

```ini
OFFLINE_MODE=true
DEMO_MODE=true
```

Set both back to `false` to use your real Homey. Restart Claude after every change to `.env`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Unauthorized` / `401` | The key is incomplete (copy all three parts) or doesn't have all scopes. Create a new one. |
| Timeout / `Cannot reach Homey` | Wrong IP, or your computer isn't on the same network as the Homey. Try opening `http://<homey-ip>` in a browser. Keep `HOMEY_USE_HTTPS=false`. |
| `uv: command not found` | Open a new terminal after installing uv. In Claude Desktop, use the full path from `which uv` / `where uv`. |
| `homey` doesn't show up in Claude Desktop | Usually a JSON typo (a missing comma or quote) or a wrong path. Fix it, then fully quit and restart Claude. |
| Claude says it works, but the data looks fake | `DEMO_MODE` is still `true` in `.env`. |

Logs:

- This server: `homey_mcp_server.log` in the repo folder
- Claude Desktop on macOS: `~/Library/Logs/Claude/mcp-server-homey.log`
- Claude Desktop on Windows: `%APPDATA%\Claude\logs\mcp-server-homey.log`

---

## Development

```bash
uv sync --dev                                   # install with dev tools
uv run pytest                                   # run tests
uv run python scripts/mcp_call.py <tool> '<json>'  # call one tool without restarting Claude
```

Example: `uv run python scripts/mcp_call.py get_flows '{"flow_type": "advanced"}'`

### Saving your flow cards locally

Handy when you build flows with Claude Code inside this repo. Claude can then read the real structure of your cards and flows from files, instead of fetching them again every time.

```bash
uv run python scripts/flowlab.py cards   # all flow cards     -> ref/flowcards/
uv run python scripts/flowlab.py flows   # all advanced flows -> ref/advancedflows/
```

`ref/` is in `.gitignore`, because these files contain your device IDs and flow names. Keep it that way. The dump doesn't update itself: run it again after you add devices or apps.

See [CONTRIBUTING.md](CONTRIBUTING.md). License: [MIT](LICENSE).
