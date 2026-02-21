from __future__ import annotations

import json
import os
import logging
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from app.integrations.mcp import load_mcp_config

ENV_TOKEN_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


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

        configured_base_url = os.getenv("CODEWORDS_RUNTIME_BASE_URL")
        mcp_url = cw_server.get("url", "https://runtime.codewords.ai")
        self.base_url = _normalize_runtime_base_url(configured_base_url or mcp_url)

        self.api_key = os.getenv("CODEWORDS_API_KEY")
        if not self.api_key:
            header = cw_server.get("headers", {}).get("Authorization", "")
            if isinstance(header, str) and header.lower().startswith("bearer "):
                resolved = _expand_env_tokens(header)
                self.api_key = resolved.split(" ", 1)[1].strip()
        if self.api_key and "${" in self.api_key:
            self.api_key = None
        self.logger = logging.getLogger(__name__)

    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def trigger(self, service_id: str, inputs: dict, async_mode: bool = True) -> CodeWordsResponse:
        if not self.is_configured():
            raise RuntimeError("CodeWords runtime not configured")
        self.logger.info("CodeWords trigger start service_id=%s async=%s", service_id, async_mode)

        route = "run_async" if async_mode else "run"
        encoded_service_id = quote(service_id, safe="")
        base_url = f"{self.base_url}/{route}/{encoded_service_id}"
        url = base_url if base_url.endswith("/") else f"{base_url}/"

        raw: dict
        try:
            # Primary format: services like devx_mcp expect direct body fields.
            raw = self._post_json(url, inputs)
        except RuntimeError as exc:
            text = str(exc).lower()
            needs_inputs_wrapper = "body" in text and "inputs" in text and "field required" in text
            if not needs_inputs_wrapper:
                raise
            # Compatibility format for services that expect {"inputs": {...}}.
            self.logger.info("CodeWords trigger retrying with inputs wrapper service_id=%s", service_id)
            raw = self._post_json(url, {"inputs": inputs})

        request_id = (
            raw.get("request_id")
            or raw.get("requestId")
            or raw.get("id")
            or raw.get("result", {}).get("request_id")
        )

        status = _infer_status(raw)
        if async_mode and request_id and status == "completed":
            status = "queued"

        self.logger.info("CodeWords trigger done service_id=%s status=%s request_id=%s", service_id, status, request_id)
        return CodeWordsResponse(status=status, request_id=request_id, raw=raw)

    def poll_result(self, request_id: str) -> CodeWordsResponse:
        if not self.is_configured():
            raise RuntimeError("CodeWords runtime not configured")
        self.logger.info("CodeWords poll start request_id=%s", request_id)

        url = f"{self.base_url}/result/{request_id}"
        raw = self._get_json(url)
        status = _infer_status(raw)
        self.logger.info("CodeWords poll done request_id=%s status=%s", request_id, status)
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


def _expand_env_tokens(value: str) -> str:
    return ENV_TOKEN_PATTERN.sub(lambda match: os.getenv(match.group(1), match.group(0)), value)


def _normalize_runtime_base_url(url: str) -> str:
    candidate = (url or "").strip()
    if not candidate:
        return "https://runtime.codewords.ai"

    parsed = urlsplit(candidate)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        # MCP endpoint can be configured as /run/devx_mcp/mcp; runtime HTTP APIs are at host root.
        if parsed.path.endswith("/mcp") or parsed.path.endswith("/mcp/"):
            return f"{parsed.scheme}://{parsed.netloc}"

    return candidate.rstrip("/")
