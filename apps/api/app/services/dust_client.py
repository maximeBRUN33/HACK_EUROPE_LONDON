from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class DustSemanticResponse:
    answer: str
    citations: list[dict]
    risk_implications: list[str]
    related_nodes: list[str]
    raw_text: str


class DustClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("DUST_API_BASE_URL", "https://dust.tt/api/v1").rstrip("/")
        self.workspace_id = os.getenv("DUST_WORKSPACE_ID", "")
        self.api_key = os.getenv("DUST_API_KEY", "")
        self.configuration_id = os.getenv("DUST_ASSISTANT_CONFIGURATION_ID", "")

    def is_configured(self) -> bool:
        return bool(self.workspace_id and self.api_key and self.configuration_id)

    def semantic_copilot(self, question: str, context: dict) -> DustSemanticResponse:
        if not self.is_configured():
            raise RuntimeError("Dust client not configured")

        system_request = (
            "You are Legacy Atlas copilot. Use only provided context and do not invent files or symbols. "
            "Return strict JSON with keys: answer, citations, risk_implications, related_nodes."
        )
        user_prompt = (
            f"Question: {question}\n\n"
            f"Context:\n{json.dumps(context, ensure_ascii=True)}\n\n"
            "JSON format:\n"
            '{"answer":"...","citations":[{"file_path":"...","symbol":"...","reason":"..."}],'
            '"risk_implications":["..."],"related_nodes":["..."]}'
        )

        creation = self._create_conversation(system_request, user_prompt)

        conversation_id = _first_non_empty(
            creation.get("conversation", {}).get("sId"),
            creation.get("conversation", {}).get("id"),
            creation.get("conversation_id"),
            creation.get("sId"),
        )
        message_id = _first_non_empty(
            creation.get("message", {}).get("sId"),
            creation.get("message", {}).get("id"),
            creation.get("message_id"),
        )

        if not conversation_id:
            raise RuntimeError("Dust conversation id missing in response")

        raw_text = self._collect_answer_text(conversation_id=conversation_id, message_id=message_id)
        parsed = _extract_json_payload(raw_text)

        if not parsed:
            raise RuntimeError("Dust did not return valid JSON response")

        answer = str(parsed.get("answer", "")).strip()
        citations = parsed.get("citations", [])
        risk_implications = parsed.get("risk_implications", [])
        related_nodes = parsed.get("related_nodes", [])

        return DustSemanticResponse(
            answer=answer or "No answer generated",
            citations=_normalize_citations(citations),
            risk_implications=[str(item) for item in risk_implications if str(item).strip()],
            related_nodes=[str(item) for item in related_nodes if str(item).strip()],
            raw_text=raw_text,
        )

    def _create_conversation(self, system_request: str, user_prompt: str) -> dict:
        url = f"{self.base_url}/w/{self.workspace_id}/assistant/conversations"
        payload = {
            "title": "Legacy Atlas Copilot Query",
            "visibility": "unlisted",
            "message": {
                "content": f"{system_request}\n\n{user_prompt}",
                "mentions": [{"configurationId": self.configuration_id}],
                "context": {
                    "timezone": "UTC",
                    "origin": "api",
                    "username": "legacy-atlas",
                    "fullName": "Legacy Atlas",
                },
            },
        }
        return self._request_json(method="POST", url=url, payload=payload)

    def _collect_answer_text(self, conversation_id: str, message_id: str | None) -> str:
        deadline = time.time() + 25
        last_payload: dict = {}

        while time.time() < deadline:
            payload = self._poll_events(conversation_id=conversation_id, message_id=message_id)
            last_payload = payload

            text = _extract_text_from_events(payload)
            if text:
                return text

            time.sleep(1.0)

        fallback_text = _extract_text_from_events(last_payload)
        if fallback_text:
            return fallback_text

        raise RuntimeError("Dust response timeout")

    def _poll_events(self, conversation_id: str, message_id: str | None) -> dict:
        if message_id:
            url = f"{self.base_url}/w/{self.workspace_id}/assistant/conversations/{conversation_id}/messages/{message_id}/events"
            try:
                return self._request_json(method="GET", url=url)
            except RuntimeError:
                pass

        url = f"{self.base_url}/w/{self.workspace_id}/assistant/conversations/{conversation_id}/events"
        return self._request_json(method="GET", url=url)

    def _request_json(self, method: str, url: str, payload: dict | None = None) -> dict:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url=url, method=method, data=data)
        request.add_header("Authorization", f"Bearer {self.api_key}")
        request.add_header("Content-Type", "application/json")

        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310
                text = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Dust HTTP error {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Dust network error: {exc.reason}") from exc

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Dust returned non-JSON response") from exc

        if isinstance(parsed, dict):
            return parsed
        return {"payload": parsed}


def _first_non_empty(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return None


def _extract_text_from_events(payload: dict) -> str:
    events = payload.get("events")
    if not isinstance(events, list):
        events = [payload]

    candidates: list[str] = []

    for event in events:
        if not isinstance(event, dict):
            continue

        for key in ("answer", "text", "content"):
            value = event.get(key)
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())

        message = event.get("message")
        if isinstance(message, dict):
            for key in ("content", "text"):
                value = message.get(key)
                if isinstance(value, str) and value.strip():
                    candidates.append(value.strip())

        if isinstance(event.get("payload"), dict):
            payload_text = event["payload"].get("text")
            if isinstance(payload_text, str) and payload_text.strip():
                candidates.append(payload_text.strip())

    return candidates[-1] if candidates else ""


def _extract_json_payload(text: str) -> dict | None:
    text = text.strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None

    snippet = match.group(0)
    try:
        parsed = json.loads(snippet)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict):
        return parsed
    return None


def _normalize_citations(citations: object) -> list[dict]:
    normalized: list[dict] = []
    if not isinstance(citations, list):
        return normalized

    for citation in citations:
        if isinstance(citation, dict):
            normalized.append(
                {
                    "file_path": str(citation.get("file_path") or citation.get("file") or "unknown"),
                    "symbol": str(citation.get("symbol") or "unknown"),
                    "reason": str(citation.get("reason") or "Dust citation"),
                }
            )
    return normalized
