---
name: homey-advanced-flows
description: Build, edit, inspect and debug Homey Pro advanced flows with the homey MCP server, and dump the Homey's flow cards and flows to local JSON for reference. Use when the user wants to create or change an advanced flow, find the right flow card or card id, understand or fix a broken flow, or refresh the ref/ dumps.
---

# Homey advanced flows

Tools come from the `homey` MCP server in this repo. Card format, tokens and a full example are in [reference/card-format.md](reference/card-format.md). Read it before you write your first `cards` object.

## Ground rules

- **Validate before writing.** `create_advanced_flow` and `update_advanced_flow` default to `dry_run=true`, which only validates. Fix every reported error, show the user a short summary of the flow, and only then call it again with `dry_run=false`.
- **New flows start disabled.** Keep `enabled=false` unless the user explicitly asks to enable it.
- **`cards` replaces all cards.** On update, first `get_flow`, then edit that card set and send all of it back. If you send only the new cards, every other card in the flow is deleted.
- **Deleting needs the exact name.** `delete_advanced_flow` requires `confirm_name` to match the flow's current name. Confirm with the user before you delete.
- **Basic (standard) flows are read-only.** They can be read and triggered, not created or edited.
- **Demo mode blocks writes.** If writes fail with "disabled in demo/offline mode", `DEMO_MODE` or `OFFLINE_MODE` is on in `.env`, or the Homey isn't reachable.

## Building a new flow

1. **Write the logic in plain words first**: when (trigger) → only if (conditions) → then (actions). Agree on it with the user if anything is ambiguous.
2. **Look up the devices** with `get_devices` or `find_devices_by_zone`. Device cards carry the device id inside the card id.
3. **Find the cards.**
   - If `ref/flowcards/{trigger,condition,action}.json` exist (Claude Code in this repo), search them first. That is the fastest way. Each entry has `id`, `title`, `args` (name and type), `tokens` and `droptoken`.
   - Otherwise use `get_flow_cards` with `card_type` plus `search` (text in the id or title) or `filter_uri` (for example `homey:device:<device-id>`), and `summary_mode=true`. The Homey has thousands of cards, so never list them unfiltered. Then fetch the chosen card without `summary_mode` to see its args.
4. **Copy from a similar flow.** Use `get_flows(flow_type="advanced")` and then `get_flow`, or read `ref/advancedflows/*.json`. This is the only reliable way to get autocomplete arguments right, such as variables, users and apps: they take an object like `{"id": ..., "name": ...}`, and this server can't look those up.
5. **Build the `cards` object.** Give every card a fresh random UUID v4 as its key, and lay the cards out left to right.
6. **Validate** with `create_advanced_flow(name, cards, dry_run=true)` and repeat until it passes.
7. **Create** with `dry_run=false`, after the user has seen the summary.
8. **Verify** with `get_flow(<new id>)`. `broken` must be `false` and the card count must match. A broken flow almost always means a wrong card id or argument value: fix it with `update_advanced_flow`.
9. **Enable only when asked**, with `update_advanced_flow(flow_id, enabled=true, dry_run=false)`.

## Editing an existing flow

1. `get_flow(flow_id)` to get the current cards.
2. Change that card object. Keep existing UUIDs, give new cards new UUIDs, and remove links to any card you delete.
3. `update_advanced_flow(flow_id, cards=<full set>, dry_run=true)`, then `dry_run=false`.
4. Check `get_flow` again: `broken` must be `false`.

To rename, move or enable a flow, send only that field (`name`, `folder` or `enabled`) and leave out `cards`.

## Local dumps and raw API (Claude Code only)

These need a shell in this repo and a filled-in `.env`. Claude Desktop can't run them.

```bash
uv run python scripts/flowlab.py cards          # all flow cards     -> ref/flowcards/
uv run python scripts/flowlab.py flows          # all advanced flows -> ref/advancedflows/
uv run python scripts/flowlab.py get <flow-id>  # raw flow JSON
```

- `ref/` is git-ignored because it holds device ids and flow names. Never commit it, and never copy real ids from it into tracked files.
- The dump doesn't refresh itself. Run `cards` again after you add devices or apps, and `flows` again after you change flows in the Homey app.
- `flowlab.py create|update|delete` talk to the HTTP API directly and **skip validation**. Use the MCP tools for real work, and use flowlab only to debug the API itself.
- To test a change to this server's code without restarting Claude, run `uv run python scripts/mcp_call.py <tool> '<json>'`.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Invalid advanced flow:` and a list of errors | The validator caught it before the Homey saw it. Every line names the card and the problem; fix each one. |
| `no trigger card '…'` / `no action card '…'` | Wrong id or wrong `type`. Search the cards again. Device card ids look like `homey:device:<device-id>:<card>`. |
| `missing required arg '…'` | Fill in the arg. Its name is in the card's `args`. |
| `Homey rejected the flow (4xx)` | The structure is valid, but the Homey refused a value, usually an autocomplete arg. Copy its shape from an existing flow. |
| Flow saved, but `broken: true` | It points to a device or app that doesn't exist (any more), or an arg value is invalid. |
| An empty flow called `null` appears | The flow body was wrapped as `{"advancedflow": {...}}`. The body must be the flow object itself. The MCP tools already do this right; this only happens with hand-written API calls. |
