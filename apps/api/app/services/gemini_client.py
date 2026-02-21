from __future__ import annotations

import json
import logging
import os
import ssl
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass
class GeminiWebItem:
    platform: str
    title: str
    url: str
    snippet: str
    why_relevant: str


@dataclass
class GeminiWebCompareResult:
    model: str
    status: str
    summary: str
    items: list[GeminiWebItem]
    raw: dict


class GeminiClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com").rstrip("/")
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip() or "gemini-2.0-flash"
        self.ssl_verify = os.getenv("GEMINI_SSL_VERIFY", "1").strip() not in {"0", "false", "False"}
        self.ca_bundle = os.getenv("GEMINI_CA_BUNDLE", "").strip()
        self.ssl_context = _build_ssl_context(verify=self.ssl_verify, ca_bundle=self.ca_bundle)
        self.logger = logging.getLogger(__name__)
        if not self.ssl_verify:
            self.logger.warning("Gemini SSL verification disabled via GEMINI_SSL_VERIFY=0 (development only)")
        elif self.ca_bundle:
            self.logger.info("Gemini custom CA bundle configured path=%s", self.ca_bundle)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def web_compare(self, *, question: str, answer: str, max_results: int, platforms: list[str]) -> GeminiWebCompareResult:
        if not self.is_configured():
            raise RuntimeError("Gemini client not configured")

        normalized_platforms = _normalize_platforms(platforms)
        prompt = _build_prompt(
            question=question,
            answer=answer,
            max_results=max_results,
            platforms=normalized_platforms,
        )
        payload = {
            "tools": [{"google_search": {}}],
            "generationConfig": {
                "temperature": 0.2,
            },
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        }

        endpoint = f"{self.base_url}/v1beta/models/{quote(self.model, safe='')}:generateContent?key={quote(self.api_key, safe='')}"
        self.logger.info("Gemini web comparison start model=%s platforms=%s", self.model, ",".join(normalized_platforms))
        raw = self._request_json(endpoint, payload)
        result = _parse_response(raw=raw, model=self.model, platforms=normalized_platforms, max_results=max_results)
        self.logger.info("Gemini web comparison done model=%s status=%s items=%s", self.model, result.status, len(result.items))
        return result

    def _request_json(self, url: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        request = Request(url=url, data=body, method="POST")
        request.add_header("Content-Type", "application/json")
        try:
            with urlopen(request, timeout=30, context=self.ssl_context) as response:  # noqa: S310
                text = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Gemini HTTP error {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Gemini network error: {exc.reason}") from exc

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini returned non-JSON payload") from exc

        if isinstance(parsed, dict):
            return parsed
        return {"payload": parsed}


def _build_prompt(*, question: str, answer: str, max_results: int, platforms: list[str]) -> str:
    platform_text = ", ".join(platforms)
    return (
        "You are a software engineering research assistant. "
        "Find web references (prefer Reddit threads and X posts) that are similar to the provided copilot answer and question. "
        f"Target platforms: {platform_text}. "
        f"Return at most {max_results} results.\n\n"
        f"Question:\n{question}\n\n"
        f"Copilot answer:\n{answer}\n\n"
        "Return strict JSON object with this shape only:\n"
        "{"
        '"summary":"short overview",'
        '"items":[{"platform":"reddit|x|other","title":"...","url":"https://...","snippet":"short summary","why_relevant":"..."}]'
        "}\n"
        "Rules: avoid fabricated links, keep snippets concise, prioritize sources with concrete engineering discussion."
    )


def _parse_response(*, raw: dict, model: str, platforms: list[str], max_results: int) -> GeminiWebCompareResult:
    text = _extract_text(raw)
    parsed = _extract_json_obj(text) if text else {}
    parsed_items = parsed.get("items", []) if isinstance(parsed, dict) else []

    items = _normalize_items(parsed_items, platforms=platforms)
    if not items:
        items = _items_from_grounding(raw, platforms=platforms)

    if len(items) > max_results:
        items = items[:max_results]

    summary = ""
    if isinstance(parsed, dict):
        summary = str(parsed.get("summary", "")).strip()
    if not summary:
        summary = "Relevant public discussions were found for comparison."

    return GeminiWebCompareResult(
        model=model,
        status="completed" if items else "empty",
        summary=summary,
        items=items,
        raw=raw,
    )


def _extract_text(raw: dict) -> str:
    candidates = raw.get("candidates", [])
    if not isinstance(candidates, list):
        return ""
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content", {})
        if not isinstance(content, dict):
            continue
        parts = content.get("parts", [])
        if not isinstance(parts, list):
            continue
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"].strip():
                return part["text"].strip()
    return ""


def _extract_json_obj(text: str) -> dict:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    snippet = text[start : end + 1]
    try:
        parsed = json.loads(snippet)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _normalize_items(items: object, *, platforms: list[str]) -> list[GeminiWebItem]:
    if not isinstance(items, list):
        return []
    normalized: list[GeminiWebItem] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", "")).strip()
        if not url.startswith(("http://", "https://")):
            continue
        platform = _platform_label(str(item.get("platform", "")).strip(), url)
        if platforms and platform not in platforms and platform != "other":
            continue
        normalized.append(
            GeminiWebItem(
                platform=platform,
                title=str(item.get("title", "")).strip() or "Untitled source",
                url=url,
                snippet=str(item.get("snippet", "")).strip() or "No snippet provided.",
                why_relevant=str(item.get("why_relevant", "")).strip(),
            )
        )
    return _dedupe_items(normalized)


def _items_from_grounding(raw: dict, *, platforms: list[str]) -> list[GeminiWebItem]:
    results: list[GeminiWebItem] = []
    candidates = raw.get("candidates", [])
    if not isinstance(candidates, list):
        return results

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        metadata = candidate.get("groundingMetadata", {})
        if not isinstance(metadata, dict):
            continue
        chunks = metadata.get("groundingChunks", [])
        if not isinstance(chunks, list):
            continue
        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue
            web = chunk.get("web")
            if not isinstance(web, dict):
                continue
            url = str(web.get("uri", "")).strip()
            if not url.startswith(("http://", "https://")):
                continue
            platform = _platform_label("", url)
            if platforms and platform not in platforms and platform != "other":
                continue
            title = str(web.get("title", "")).strip() or "Referenced source"
            results.append(
                GeminiWebItem(
                    platform=platform,
                    title=title,
                    url=url,
                    snippet=title,
                    why_relevant="Grounded web reference used by Gemini search.",
                )
            )
    return _dedupe_items(results)


def _normalize_platforms(platforms: list[str]) -> list[str]:
    if not platforms:
        return ["reddit", "x"]
    allowed = {"reddit", "x", "other"}
    normalized = []
    for platform in platforms:
        text = str(platform).strip().lower()
        if text in {"twitter"}:
            text = "x"
        if text in allowed and text not in normalized:
            normalized.append(text)
    return normalized or ["reddit", "x"]


def _platform_label(platform: str, url: str) -> str:
    explicit = platform.strip().lower()
    if explicit in {"reddit", "x", "other"}:
        return explicit
    if explicit == "twitter":
        return "x"

    lower_url = url.lower()
    if "reddit.com/" in lower_url:
        return "reddit"
    if "x.com/" in lower_url or "twitter.com/" in lower_url:
        return "x"
    return "other"


def _dedupe_items(items: list[GeminiWebItem]) -> list[GeminiWebItem]:
    seen: set[str] = set()
    deduped: list[GeminiWebItem] = []
    for item in items:
        if item.url in seen:
            continue
        seen.add(item.url)
        deduped.append(item)
    return deduped


def _build_ssl_context(*, verify: bool, ca_bundle: str) -> ssl.SSLContext:
    if not verify:
        return ssl._create_unverified_context()

    if ca_bundle:
        return ssl.create_default_context(cafile=ca_bundle)

    certifi_path = _resolve_certifi_path()
    if certifi_path:
        return ssl.create_default_context(cafile=certifi_path)

    return ssl.create_default_context()


def _resolve_certifi_path() -> str | None:
    try:
        import certifi  # type: ignore

        return certifi.where()
    except Exception:
        return None
