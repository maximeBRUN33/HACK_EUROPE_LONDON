from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.integrations.mcp import load_mcp_config, safe_mcp_summary
from app.models import CodeWordsResultResponse, CodeWordsTriggerRequest, CodeWordsTriggerResponse
from app.services.codewords_client import CodeWordsClient
from app.services.dust_client import DustClient

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/mcp/status")
def get_mcp_status() -> dict:
    config = load_mcp_config()
    return safe_mcp_summary(config)


@router.post("/codewords/trigger", response_model=CodeWordsTriggerResponse)
def trigger_codewords(payload: CodeWordsTriggerRequest) -> CodeWordsTriggerResponse:
    client = CodeWordsClient()
    if not client.is_configured():
        raise HTTPException(status_code=503, detail="CodeWords integration is not configured")

    try:
        response = client.trigger(service_id=payload.service_id, inputs=payload.inputs, async_mode=payload.async_mode)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

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
        raise HTTPException(status_code=503, detail="CodeWords integration is not configured")

    try:
        response = client.poll_result(request_id=request_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

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
    return DustStatusResponse(
        configured=client.is_configured(),
        workspace_id=client.workspace_id or None,
        configuration_id=client.configuration_id or None,
    )
