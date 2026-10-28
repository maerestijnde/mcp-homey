"""Dev harness: talk to the Homey flow API directly, without restarting Claude.

    uv run python scripts/flowlab.py cards              # dump all flow cards -> ref/flowcards/
    uv run python scripts/flowlab.py flows              # dump all advanced flows -> ref/advancedflows/
    uv run python scripts/flowlab.py get <id>
    uv run python scripts/flowlab.py create <file.json> # body: {"name":..., "enabled":..., "cards":{...}}
    uv run python scripts/flowlab.py update <id> <file.json>
    uv run python scripts/flowlab.py delete <id>
"""

import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from homey_mcp.config import get_config  # noqa: E402

REF = Path(__file__).parent.parent / "ref"
FLOW = "/api/manager/flow"


def client() -> httpx.Client:
    c = get_config()
    scheme = "https" if c.homey_use_https else "http"
    return httpx.Client(
        base_url=f"{scheme}://{c.homey_local_address}",
        headers={"Authorization": f"Bearer {c.homey_local_token}"},
        timeout=c.request_timeout,
        verify=c.homey_verify_ssl,
    )


def call(h: httpx.Client, method: str, path: str, body=None):
    r = h.request(method, path, json=body)
    if r.is_error:
        sys.exit(f"{method} {path} -> {r.status_code}: {r.text}")
    return r.json() if r.content else None


def save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def summarize(card: dict) -> dict:
    # what an LLM needs to build a card: full id + arg names/types + tokens it drops
    return {
        "id": card["id"],
        "title": card.get("titleFormatted") or card.get("title"),
        "args": [{"name": a["name"], "type": a["type"]} for a in card.get("args") or []],
        "tokens": [t["id"] for t in card.get("tokens") or []],
        "droptoken": card.get("droptoken"),
    }


def main(argv: list[str]) -> None:
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    with client() as h:
        if cmd == "cards":
            for kind in ("trigger", "condition", "action"):
                cards = call(h, "GET", f"{FLOW}/flowcard{kind}")
                cards = list(cards.values()) if isinstance(cards, dict) else cards
                save(REF / "flowcards" / f"{kind}.full.json", cards)
                save(REF / "flowcards" / f"{kind}.json", [summarize(c) for c in cards])
                print(f"{kind}: {len(cards)} cards")
        elif cmd == "flows":
            flows = call(h, "GET", f"{FLOW}/advancedflow")
            for f in flows.values():
                save(REF / "advancedflows" / f"{f['id']}.json", f)
            print(f"{len(flows)} advanced flows -> {REF / 'advancedflows'}")
        elif cmd == "get":
            print(json.dumps(call(h, "GET", f"{FLOW}/advancedflow/{args[0]}"), indent=2))
        elif cmd == "create":
            body = json.loads(Path(args[0]).read_text())
            res = call(h, "POST", f"{FLOW}/advancedflow", body)
            print(json.dumps({k: res[k] for k in ("id", "name", "enabled", "broken")}, indent=2))
        elif cmd == "update":
            body = json.loads(Path(args[1]).read_text())
            res = call(h, "PUT", f"{FLOW}/advancedflow/{args[0]}", body)
            print(json.dumps({k: res[k] for k in ("id", "name", "enabled", "broken")}, indent=2))
        elif cmd == "delete":
            call(h, "DELETE", f"{FLOW}/advancedflow/{args[0]}")
            print("deleted", args[0])
        else:
            sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
