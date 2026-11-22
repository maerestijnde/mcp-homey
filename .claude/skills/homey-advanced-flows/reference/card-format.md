# Advanced flow format

This is what `create_advanced_flow` and `update_advanced_flow` expect, and what `get_flow` returns. It is based on real flows from a Homey Pro and on the validator in `src/homey_mcp/client/flows.py`.

## The flow

| Field | Required | Notes |
|---|---|---|
| `name` | yes | Non-empty string |
| `cards` | yes | Object: card UUID → card |
| `enabled` | no | Defaults to `false` in the tools |
| `folder` | no | Folder id from `get_flow_folders` |

`get_flow` also returns `id`, `broken` and `triggerable`. `triggerable` is true when the flow has a `start` card, so it can be run with `trigger_flow`. You don't send these fields.

## Every card

- **Key**: a fresh, random UUID v4. Keys like `card1` are rejected.
- **`type`**: `trigger`, `condition`, `action`, `start`, `delay`, `any`, `all` or `note`.
- **`x`, `y`**: position on the canvas. Use x += 400 per step and y += 150 per parallel branch.
- **`ownerUri`**: optional. Older flows have it, newer ones don't. Leave it out.

## Card types

| Type | Fields | Outputs |
|---|---|---|
| `trigger` | `id`, `args` | `outputSuccess` |
| `condition` | `id`, `args`, optional `droptoken`, optional `inverted` | `outputTrue`, `outputFalse` |
| `action` | `id`, `args` | `outputSuccess`, `outputError` |
| `start` | none (manual start button) | `outputSuccess` |
| `delay` | `args.delay = {"number": "5", "multiplier": 1}` | `outputSuccess` |
| `any` | none | `outputSuccess` |
| `all` | `input: ["<card UUID>::outputTrue", ...]` | `outputSuccess` |
| `note` | `value` (text), `color` (`yellow`, `red`, `green`, `blue`), optional `width` and `height` | none |

- A flow needs at least one `trigger` or `start` card.
- An output is a **list of card UUIDs** to continue with. Leave it out or use `[]` for nothing.
- **delay**: `number` is a string. `multiplier` is `1` for seconds or `60` for minutes. Example: `{"number": "2", "multiplier": 60}` = 2 minutes.
- **any** continues as soon as one incoming path arrives. Point several cards' outputs at it.
- **all** waits for every path in `input`. Each entry is `<card UUID>::<output field>`.
- **inverted: true** flips a condition. Titles show which conditions support this, as `!{{is|is not}}`.

## Card ids

The `id` is the full card id, exactly as `get_flow_cards` or `ref/flowcards/*.json` show it.

| Pattern | Example |
|---|---|
| `homey:device:<device-id>:<card>` | `homey:device:<device-id>:on`, `…:alarm_motion_true`, `…:onoff_true` |
| `homey:zone:<zone-id>:<card>` | zone triggers (someone entered or left) |
| `homey:manager:<manager>:<card>` | `homey:manager:cron:sunset`, `homey:manager:cron:after_sunset`, `homey:manager:logic:lt`, `homey:manager:notifications:create_notification`, `homey:manager:logic:webhook` |
| `homey:app:<app-id>:<card>` | cards from installed apps |

A few ids are both a condition and an action (for example HomeyScript `runCode_v2`). Set `type` to the role you want.

## Arguments

- **Plain values**: text, numbers, booleans and times (`"07:30"`), keyed by the arg `name` from the card.
- **Required args** must be present. Optional ones may be left out.
- **Autocomplete args** take an object, not a string. These are seen in real flows:
  - `variable`: `{"id": "<variable-id>", "name": "Battery mode"}`
  - `user`: `{"id": "<user-id>", "name": "..."}` (sometimes with `athomId` and `image`)
  - `app`: `{"id": "<app-id>", "name": "..."}`

  This server can't look up autocomplete values. Copy the object from an existing flow that uses the same card.

## Tokens

These formats were seen in real flows. When in doubt, copy them from an existing flow.

- **Device value inside a text arg**: `[[homey:device:<device-id>|<capability>]]`. Example: `"Battery at [[homey:device:<device-id>|measure_battery_soc]]%"`.
- **Value from another card in the flow, inside a text arg**: `[[card::<card-uuid>::<token-id>]]`, for example `::error` on an `outputError` path. The token ids a card provides are in its `tokens` list.
- **`droptoken` on a condition** (the value a logic condition compares, for cards whose `droptoken` field is set):
  - `homey:manager:logic|<variable-id>`: a logic variable
  - `homey:device:<device-id>|<capability>`: a device value
  - `trigger::<card-uuid>::<token-id>`: a token from the trigger card

## Full example

Hallway light on for 5 minutes when there's motion after sunset. Replace `<motion-sensor-id>` and `<light-id>` with device ids from `get_devices`. Generate new UUIDs for your own flows.

```json
{
  "name": "Hallway: light on motion after sunset",
  "enabled": false,
  "cards": {
    "6f1c2a10-8b3e-4d2a-9c4f-1a2b3c4d5e01": {
      "type": "trigger",
      "id": "homey:device:<motion-sensor-id>:alarm_motion_true",
      "args": {},
      "x": 0, "y": 0,
      "outputSuccess": ["6f1c2a10-8b3e-4d2a-9c4f-1a2b3c4d5e02"]
    },
    "6f1c2a10-8b3e-4d2a-9c4f-1a2b3c4d5e02": {
      "type": "condition",
      "id": "homey:manager:cron:after_sunset",
      "args": {},
      "x": 400, "y": 0,
      "outputTrue": ["6f1c2a10-8b3e-4d2a-9c4f-1a2b3c4d5e03"]
    },
    "6f1c2a10-8b3e-4d2a-9c4f-1a2b3c4d5e03": {
      "type": "action",
      "id": "homey:device:<light-id>:on",
      "args": {},
      "x": 800, "y": 0,
      "outputSuccess": ["6f1c2a10-8b3e-4d2a-9c4f-1a2b3c4d5e04"]
    },
    "6f1c2a10-8b3e-4d2a-9c4f-1a2b3c4d5e04": {
      "type": "delay",
      "args": {"delay": {"number": "5", "multiplier": 60}},
      "x": 1200, "y": 0,
      "outputSuccess": ["6f1c2a10-8b3e-4d2a-9c4f-1a2b3c4d5e05"]
    },
    "6f1c2a10-8b3e-4d2a-9c4f-1a2b3c4d5e05": {
      "type": "action",
      "id": "homey:device:<light-id>:off",
      "args": {},
      "x": 1600, "y": 0
    },
    "6f1c2a10-8b3e-4d2a-9c4f-1a2b3c4d5e06": {
      "type": "note",
      "value": "Motion in the hallway after sunset: light on for 5 minutes.",
      "color": "yellow",
      "x": 0, "y": 200
    }
  }
}
```

Pass `name`, `cards` and `enabled` as separate arguments to `create_advanced_flow`.
