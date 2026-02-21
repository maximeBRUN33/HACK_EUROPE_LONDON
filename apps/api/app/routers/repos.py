from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException

from app.models import AnalysisRun, Repository, RepositoryRegisterRequest, ScanRequest
from app.services.analysis import create_placeholder_summary
from app.services.jobs import enqueue_analysis
from app.store import store

router = APIRouter(prefix="/api/repos", tags=["repos"])


def _parse_owner_and_name(repo_url: str) -> tuple[str, str]:
    parsed = urlparse(repo_url)
    parts = [segment for segment in parsed.path.split("/") if segment]
    if len(parts) < 2:
        raise ValueError("Repository URL must include owner and repository name")
    return parts[0], parts[1].replace(".git", "")


@router.post("/register", response_model=Repository)
def register_repository(payload: RepositoryRegisterRequest) -> Repository:
    try:
        owner, name = _parse_owner_and_name(str(payload.repo_url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository = Repository(
        owner=owner,
        name=name,
        default_branch=payload.default_branch,
        repo_url=payload.repo_url,
        local_path=payload.local_path,
    )
    store.save_repository(repository)
    return repository


@router.post("/{repo_id}/scan", response_model=AnalysisRun)
def start_scan(repo_id: str, payload: ScanRequest) -> AnalysisRun:
    repository = store.get_repository(repo_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    run = AnalysisRun(repository_id=repository.id, commit_sha=payload.commit_sha)
    run.summary = create_placeholder_summary(repository, payload.commit_sha)
    run.current_step = "queued"
    run.progress_pct = 0.0
    store.save_run(run)
    enqueue_analysis(run_id=str(run.id), repo_id=str(repository.id))
    return run


@router.get("/{repo_id}/runs/{run_id}", response_model=AnalysisRun)
def get_run_status(repo_id: str, run_id: str) -> AnalysisRun:
    run = store.get_run_for_repository(repo_id, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
