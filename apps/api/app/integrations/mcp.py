from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_MCP_CONFIG = Path(__file__).resolve().parents[4] / "dust-integration" / "references" / "mcp-config.json"


def load_mcp_config(path: Path | None = None) -> dict[str, Any]:
    target = path or DEFAULT_MCP_CONFIG
    if not target.exists():
        return {"mcpServers": {}, "source": str(target), "exists": False}

    with target.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return {"source": str(target), "exists": True, **payload}


def safe_mcp_summary(config: dict[str, Any]) -> dict[str, Any]:
    servers = config.get("mcpServers", {})
    summary: dict[str, Any] = {
        "source": config.get("source"),
        "exists": bool(config.get("exists", True)),
        "servers": {},
    }

    for name, server in servers.items():
        server_summary = {
            "url": server.get("url"),
            "command": server.get("command"),
            "has_headers": "headers" in server,
            "header_keys": sorted(list(server.get("headers", {}).keys())),
        }
        summary["servers"][name] = server_summary

    return summary
