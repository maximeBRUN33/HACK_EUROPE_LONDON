from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock

from app.models import RunStatus
from app.services.analysis import create_placeholder_summary, run_static_analysis
from app.services.ingestion import prepare_repository_source
from app.store import store

MAX_WORKERS = int(os.getenv("LEGACY_ATLAS_JOB_WORKERS", "2"))
SYNC_MODE = os.getenv("LEGACY_ATLAS_SYNC_JOBS", "0") == "1"

_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="analysis-worker")
_lock = Lock()


def enqueue_analysis(run_id: str, repo_id: str) -> None:
    if SYNC_MODE:
        _run_job(run_id=run_id, repo_id=repo_id)
        return
    _executor.submit(_run_job, run_id, repo_id)


def _run_job(run_id: str, repo_id: str) -> None:
    run = store.get_run(run_id)
    repository = store.get_repository(repo_id)
    if run is None or repository is None:
        return

    try:
        _update_run(run_id, status=RunStatus.running, step="ingesting", progress=8.0)
        ingestion = prepare_repository_source(repository)

        if ingestion.local_path is not None:
            repository.local_path = str(ingestion.local_path)
            store.save_repository(repository)

        run = store.get_run(run_id)
        if run is None:
            return

        run.summary = {
            **create_placeholder_summary(repository, run.commit_sha),
            "ingestion_mode": ingestion.mode,
            "ingestion_message": ingestion.message,
        }
        store.save_run(run)

        def progress(step: str, pct: float) -> None:
            _update_run(run_id, status=RunStatus.running, step=step, progress=pct)

        run_static_analysis(run, repository, progress_cb=progress)
        _update_run(run_id, status=RunStatus.completed, step="completed", progress=100.0, finished=True)
    except Exception as exc:  # pragma: no cover - defensive error guard
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
