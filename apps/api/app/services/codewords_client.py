from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.integrations.mcp import load_mcp_config


@dataclass
class CodeWordsResponse:
    status: str
    request_id: str | None
    raw: dict


class CodeWordsClient:
    def __init__(self) -> None:
        mcp = load_mcp_config()
        servers = mcp.get("mcpServers", {})
        cw_server = servers.get("CodeWords", {})

        self.base_url = os.getenv("CODEWORDS_RUNTIME_BASE_URL", cw_server.get("url", "https://runtime.codewords.ai")).rstrip("/")
        self.api_key = os.getenv("CODEWORDS_API_KEY")
        if not self.api_key:
            header = cw_server.get("headers", {}).get("Authorization", "")
            if isinstance(header, str) and header.lower().startswith("bearer "):
                self.api_key = header.split(" ", 1)[1].strip()

    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def trigger(self, service_id: str, inputs: dict, async_mode: bool = True) -> CodeWordsResponse:
        if not self.is_configured():
            raise RuntimeError("CodeWords runtime not configured")

        route = "run_async" if async_mode else "run"
        url = f"{self.base_url}/{route}/{service_id}"
        payload = {"inputs": inputs}
        raw = self._post_json(url, payload)

        request_id = (
            raw.get("request_id")
            or raw.get("requestId")
            or raw.get("id")
            or raw.get("result", {}).get("request_id")
        )

        status = _infer_status(raw)
        if async_mode and request_id and status == "completed":
            status = "queued"

        return CodeWordsResponse(status=status, request_id=request_id, raw=raw)

    def poll_result(self, request_id: str) -> CodeWordsResponse:
        if not self.is_configured():
            raise RuntimeError("CodeWords runtime not configured")

        url = f"{self.base_url}/result/{request_id}"
        raw = self._get_json(url)
        status = _infer_status(raw)
        return CodeWordsResponse(status=status, request_id=request_id, raw=raw)

    def _post_json(self, url: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        request = Request(url=url, data=body, method="POST")
        request.add_header("Content-Type", "application/json")
        request.add_header("Authorization", f"Bearer {self.api_key}")
        return self._read_json(request)

    def _get_json(self, url: str) -> dict:
        request = Request(url=url, method="GET")
        request.add_header("Authorization", f"Bearer {self.api_key}")
        return self._read_json(request)

    def _read_json(self, request: Request) -> dict:
        try:
            with urlopen(request, timeout=20) as response:  # noqa: S310
                text = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"CodeWords HTTP error {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"CodeWords network error: {exc.reason}") from exc

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("CodeWords returned non-JSON payload") from exc

        if not isinstance(parsed, dict):
            return {"result": parsed}
        return parsed


def _infer_status(payload: dict) -> str:
    text = str(payload.get("status") or payload.get("state") or payload.get("phase") or "").lower()
    if "fail" in text or "error" in text:
        return "failed"
    if "done" in text or "success" in text or "complete" in text or text == "ok":
        return "completed"
    if "queue" in text or "pend" in text:
        return "queued"
    if "run" in text or "process" in text:
        return "running"

    if payload.get("error"):
        return "failed"
    if payload.get("result") is not None:
        return "completed"
    return "running"
