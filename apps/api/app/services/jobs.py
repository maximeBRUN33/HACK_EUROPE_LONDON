from __future__ import annotations

import os
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock

from app.models import EnrichmentPayload, RunStatus
from app.services.analysis import create_placeholder_summary, run_static_analysis
from app.services.codewords_client import CodeWordsClient
from app.services.ingestion import prepare_repository_source
from app.store import store

MAX_WORKERS = int(os.getenv("LEGACY_ATLAS_JOB_WORKERS", "2"))
SYNC_MODE = os.getenv("LEGACY_ATLAS_SYNC_JOBS", "0") == "1"
CODEWORDS_RUNTIME_HOOK_ENABLED = os.getenv("LEGACY_ATLAS_CODEWORDS_RUNTIME_HOOK", "1") == "1"
CODEWORDS_RUNTIME_SERVICE_ID = os.getenv(
    "CODEWORDS_RUNTIME_SERVICE_ID",
    "legacy_atlas_post_analysis_v1_8a477024",
)
CODEWORDS_POLL_MAX_ATTEMPTS = max(1, int(os.getenv("CODEWORDS_POLL_MAX_ATTEMPTS", "8")))
CODEWORDS_POLL_INTERVAL_SEC = max(0.1, float(os.getenv("CODEWORDS_POLL_INTERVAL_SEC", "1.5")))

_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="analysis-worker")
_lock = Lock()
logger = logging.getLogger(__name__)


def enqueue_analysis(run_id: str, repo_id: str) -> None:
    logger.info("Queueing analysis job run_id=%s repo_id=%s sync_mode=%s", run_id, repo_id, SYNC_MODE)
    if SYNC_MODE:
        _run_job(run_id=run_id, repo_id=repo_id)
        return
    _executor.submit(_run_job, run_id, repo_id)


def _run_job(run_id: str, repo_id: str) -> None:
    logger.info("Starting analysis job run_id=%s repo_id=%s", run_id, repo_id)
    run = store.get_run(run_id)
    repository = store.get_repository(repo_id)
    if run is None or repository is None:
        logger.warning("Job aborted: missing run or repository run_id=%s repo_id=%s", run_id, repo_id)
        return

    try:
        _update_run(run_id, status=RunStatus.running, step="ingesting", progress=8.0)
        ingestion = prepare_repository_source(repository)
        logger.info(
            "Ingestion completed run_id=%s repo=%s/%s mode=%s message=%s",
            run_id,
            repository.owner,
            repository.name,
            ingestion.mode,
            ingestion.message,
        )

        if ingestion.local_path is not None:
            repository.local_path = str(ingestion.local_path)
            store.save_repository(repository)
            logger.info("Repository local path updated run_id=%s path=%s", run_id, repository.local_path)

        run = store.get_run(run_id)
        if run is None:
            logger.warning("Job aborted after ingestion: run missing run_id=%s", run_id)
            return

        run.summary = {
            **create_placeholder_summary(repository, run.commit_sha),
            "ingestion_mode": ingestion.mode,
            "ingestion_message": ingestion.message,
        }
        store.save_run(run)

        def progress(step: str, pct: float) -> None:
            _update_run(run_id, status=RunStatus.running, step=step, progress=pct)
            logger.info("Analysis progress run_id=%s step=%s progress=%.1f", run_id, step, pct)

        run_static_analysis(run, repository, progress_cb=progress)
        _attach_codewords_runtime_result(run_id=run_id, repository=repository)
        _update_run(run_id, status=RunStatus.completed, step="completed", progress=100.0, finished=True)
        logger.info("Analysis job completed run_id=%s", run_id)
    except Exception as exc:  # pragma: no cover - defensive error guard
        logger.exception("Analysis job failed run_id=%s error=%s", run_id, exc)
        _update_run(
            run_id,
            status=RunStatus.failed,
            step="failed",
            progress=100.0,
            finished=True,
            error_message=str(exc),
        )


def _update_run(
    run_id: str,
    *,
    status: RunStatus,
    step: str,
    progress: float,
    finished: bool = False,
    error_message: str | None = None,
) -> None:
    with _lock:
        run = store.get_run(run_id)
        if run is None:
            return

        run.status = status
        run.current_step = step
        run.progress_pct = max(0.0, min(100.0, progress))
        run.error_message = error_message
        if run.started_at is None:
            run.started_at = datetime.now(timezone.utc)
        if finished:
            run.finished_at = datetime.now(timezone.utc)
        store.save_run(run)


def _attach_codewords_runtime_result(run_id: str, repository) -> None:
    result = _execute_codewords_runtime_hook(run_id=run_id, repository=repository)
    run = store.get_run(run_id)
    if run is None:
        return
    run.summary = {
        **run.summary,
        "codewords_runtime": result,
    }
    store.save_run(run)
    store.save_enrichment(run.id, _build_enrichment_payload(run, result))
    logger.info("CodeWords enrichment persisted run_id=%s status=%s", run_id, result.get("status"))


def _execute_codewords_runtime_hook(run_id: str, repository) -> dict:
    if not CODEWORDS_RUNTIME_HOOK_ENABLED:
        return {
            "enabled": False,
            "status": "disabled",
        }

    client = CodeWordsClient()
    if not client.is_configured():
        return {
            "enabled": True,
            "configured": False,
            "service_id": CODEWORDS_RUNTIME_SERVICE_ID,
            "status": "not_configured",
        }

    run = store.get_run(run_id)
    if run is None:
        return {
            "enabled": True,
            "configured": True,
            "service_id": CODEWORDS_RUNTIME_SERVICE_ID,
            "status": "skipped",
            "error": "run_not_found",
        }

    inputs = {
        "repository": {
            "id": str(repository.id),
            "owner": repository.owner,
            "name": repository.name,
            "url": str(repository.repo_url),
            "default_branch": repository.default_branch,
            "local_path": repository.local_path,
        },
        "analysis_run": {
            "id": str(run.id),
            "commit_sha": run.commit_sha,
            "status": run.status.value,
        },
        "analysis_summary": _build_codewords_analysis_summary(run.summary),
    }

    try:
        logger.info(
            "CodeWords runtime hook start run_id=%s service_id=%s",
            run_id,
            CODEWORDS_RUNTIME_SERVICE_ID,
        )
        trigger = client.trigger(
            service_id=CODEWORDS_RUNTIME_SERVICE_ID,
            inputs=inputs,
            async_mode=True,
        )
        result = {
            "enabled": True,
            "configured": True,
            "service_id": CODEWORDS_RUNTIME_SERVICE_ID,
            "trigger_status": trigger.status,
            "request_id": trigger.request_id,
            "poll_attempts": 0,
            "status": trigger.status,
            "raw": trigger.raw,
        }

        if not trigger.request_id:
            logger.info("CodeWords runtime hook completed without request_id run_id=%s", run_id)
            return result

        if trigger.status not in {"queued", "running"}:
            logger.info(
                "CodeWords runtime hook completed immediately run_id=%s status=%s request_id=%s",
                run_id,
                trigger.status,
                trigger.request_id,
            )
            return result

        for attempt in range(1, CODEWORDS_POLL_MAX_ATTEMPTS + 1):
            time.sleep(CODEWORDS_POLL_INTERVAL_SEC)
            poll = client.poll_result(trigger.request_id)
            result["poll_attempts"] = attempt
            result["status"] = poll.status
            result["raw"] = poll.raw
            if poll.status in {"completed", "failed"}:
                logger.info(
                    "CodeWords runtime hook finished run_id=%s request_id=%s status=%s attempts=%s",
                    run_id,
                    trigger.request_id,
                    poll.status,
                    attempt,
                )
                return result

        result["status"] = "running"
        logger.warning(
            "CodeWords runtime hook poll timeout run_id=%s request_id=%s attempts=%s",
            run_id,
            trigger.request_id,
            CODEWORDS_POLL_MAX_ATTEMPTS,
        )
        return result
    except Exception as exc:  # pragma: no cover - non-blocking integration guard
        logger.warning("CodeWords runtime hook failed run_id=%s error=%s", run_id, exc)
        return {
            "enabled": True,
            "configured": True,
            "service_id": CODEWORDS_RUNTIME_SERVICE_ID,
            "status": "error",
            "error": str(exc),
        }


def _build_codewords_analysis_summary(summary: dict) -> dict:
    normalized = dict(summary or {})
    normalized["analysis_mode"] = str(normalized.get("analysis_mode") or "fallback")
    normalized["workflow_nodes"] = _coerce_int(normalized.get("workflow_nodes"), default=0)
    normalized["lineage_edges"] = _coerce_int(normalized.get("lineage_edges"), default=0)
    normalized["risk_findings"] = _coerce_int(normalized.get("risk_findings"), default=0)
    normalized["files_scanned"] = _coerce_int(normalized.get("files_scanned"), default=0)
    normalized["functions_scanned"] = _coerce_int(normalized.get("functions_scanned"), default=0)
    normalized["parse_errors"] = _coerce_int(normalized.get("parse_errors"), default=0)
    normalized["ontology"] = _coerce_dict(normalized.get("ontology"))
    normalized["migration"] = _coerce_dict(normalized.get("migration"))
    return normalized


def _build_enrichment_payload(run, result: dict) -> EnrichmentPayload:
    raw = _coerce_dict(result.get("raw"))
    quality_checks = _coerce_dict(raw.get("quality_checks"))
    if result.get("error"):
        quality_checks = {
            **quality_checks,
            "integration_error": str(result["error"]),
        }

    runtime_meta = {key: value for key, value in result.items() if key != "raw"}
    return EnrichmentPayload(
        run_id=run.id,
        service_id=_coerce_optional_str(result.get("service_id")),
        request_id=_coerce_optional_str(result.get("request_id")),
        status=str(result.get("status") or "unknown"),
        ontology_enrichment=_coerce_dict(raw.get("ontology_enrichment")),
        migration_hints=_coerce_dict(raw.get("migration_hints")),
        quality_checks=quality_checks,
        raw={
            "runtime": runtime_meta,
            "response": raw,
        },
    )


def _coerce_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _coerce_optional_str(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
