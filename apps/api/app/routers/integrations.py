import logging
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter
from pydantic import BaseModel

from app.errors import api_error
from app.integrations.mcp import load_mcp_config, safe_mcp_summary
from app.models import (
    CodeWordsResultResponse,
    CodeWordsTriggerRequest,
    CodeWordsTriggerResponse,
    IntegrationProviderReadiness,
    IntegrationReadinessResponse,
)
from app.services.codewords_client import CodeWordsClient
from app.services.dust_client import DustClient

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
logger = logging.getLogger(__name__)


@router.get("/mcp/status")
def get_mcp_status() -> dict:
    config = load_mcp_config()
    logger.info("MCP status requested source=%s exists=%s", config.get("source"), config.get("exists"))
    return safe_mcp_summary(config)


@router.post("/codewords/trigger", response_model=CodeWordsTriggerResponse)
def trigger_codewords(payload: CodeWordsTriggerRequest) -> CodeWordsTriggerResponse:
    client = CodeWordsClient()
    if not client.is_configured():
        raise api_error(
            status_code=503,
            detail_code="CODEWORDS_NOT_CONFIGURED",
            message="CodeWords integration is not configured",
        )

    try:
        response = client.trigger(service_id=payload.service_id, inputs=payload.inputs, async_mode=payload.async_mode)
    except RuntimeError as exc:
        logger.warning("CodeWords trigger failed service_id=%s error=%s", payload.service_id, exc)
        raise api_error(
            status_code=502,
            detail_code="CODEWORDS_TRIGGER_FAILED",
            message=str(exc),
            provider="codewords",
        ) from exc

    logger.info(
        "CodeWords triggered service_id=%s async=%s status=%s request_id=%s",
        payload.service_id,
        payload.async_mode,
        response.status,
        response.request_id,
    )
    return CodeWordsTriggerResponse(
        service_id=payload.service_id,
        status=response.status,
        request_id=response.request_id,
        raw=response.raw,
    )


@router.get("/codewords/result/{request_id}", response_model=CodeWordsResultResponse)
def poll_codewords_result(request_id: str) -> CodeWordsResultResponse:
    client = CodeWordsClient()
    if not client.is_configured():
        raise api_error(
            status_code=503,
            detail_code="CODEWORDS_NOT_CONFIGURED",
            message="CodeWords integration is not configured",
        )

    try:
        response = client.poll_result(request_id=request_id)
    except RuntimeError as exc:
        logger.warning("CodeWords poll failed request_id=%s error=%s", request_id, exc)
        raise api_error(
            status_code=502,
            detail_code="CODEWORDS_POLL_FAILED",
            message=str(exc),
            provider="codewords",
        ) from exc

    logger.info("CodeWords poll request_id=%s status=%s", request_id, response.status)
    return CodeWordsResultResponse(
        request_id=request_id,
        status=response.status,
        raw=response.raw,
    )


class DustStatusResponse(BaseModel):
    configured: bool
    workspace_id: str | None = None
    configuration_id: str | None = None


@router.get("/dust/status", response_model=DustStatusResponse)
def get_dust_status() -> DustStatusResponse:
    client = DustClient()
    logger.info("Dust status requested configured=%s workspace=%s", client.is_configured(), client.workspace_id or "")
    return DustStatusResponse(
        configured=client.is_configured(),
        workspace_id=client.workspace_id or None,
        configuration_id=client.configuration_id or None,
    )


@router.get("/readiness", response_model=IntegrationReadinessResponse)
def get_integrations_readiness() -> IntegrationReadinessResponse:
    codewords = _codewords_readiness()
    dust = _dust_readiness()
    mcp = _mcp_readiness()
    logger.info(
        "Integration readiness codewords=%s dust=%s mcp=%s",
        codewords.reachable,
        dust.reachable,
        mcp.reachable,
    )
    return IntegrationReadinessResponse(codewords=codewords, dust=dust, mcp=mcp)


def _codewords_readiness() -> IntegrationProviderReadiness:
    client = CodeWordsClient()
    if not client.is_configured():
        return IntegrationProviderReadiness(configured=False, reachable=False, detail="codewords_not_configured")
    reachable, latency_ms, detail = _probe_url(f"{client.base_url}/health")
    return IntegrationProviderReadiness(
        configured=True,
        reachable=reachable,
        latency_ms=latency_ms,
        detail=detail or "ok",
    )


def _dust_readiness() -> IntegrationProviderReadiness:
    client = DustClient()
    if not client.is_configured():
        return IntegrationProviderReadiness(configured=False, reachable=False, detail="dust_not_configured")
    reachable, latency_ms, detail = _probe_url(client.base_url)
    return IntegrationProviderReadiness(
        configured=True,
        reachable=reachable,
        latency_ms=latency_ms,
        detail=detail or "ok",
    )


def _mcp_readiness() -> IntegrationProviderReadiness:
    config = load_mcp_config()
    servers = config.get("mcpServers", {})
    if not config.get("exists") or not isinstance(servers, dict) or not servers:
        return IntegrationProviderReadiness(configured=False, reachable=False, detail="mcp_config_missing")

    http_urls: list[str] = []
    for server in servers.values():
        if not isinstance(server, dict):
            continue
        url = server.get("url")
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            http_urls.append(url)

    if not http_urls:
        return IntegrationProviderReadiness(configured=True, reachable=True, detail="mcp_config_loaded_no_http_probe")

    probe_target = http_urls[0]
    reachable, latency_ms, detail = _probe_url(probe_target)
    return IntegrationProviderReadiness(
        configured=True,
        reachable=reachable,
        latency_ms=latency_ms,
        detail=detail or f"probe:{probe_target}",
    )


def _probe_url(url: str, timeout_sec: float = 4.0) -> tuple[bool, int | None, str | None]:
    start = time.perf_counter()
    request = Request(url=url, method="GET")
    try:
        with urlopen(request, timeout=timeout_sec) as response:  # noqa: S310
            _ = response.read(1)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return True, elapsed_ms, None
    except HTTPError as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        # HTTP responses still prove network/path reachability.
        return True, elapsed_ms, f"http_{exc.code}"
    except URLError as exc:
        return False, None, str(exc.reason)
