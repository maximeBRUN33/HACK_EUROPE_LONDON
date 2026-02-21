from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.models import Repository

CACHE_ROOT = Path(os.getenv("LEGACY_ATLAS_REPO_CACHE", Path(__file__).resolve().parents[3] / ".cache" / "repos"))


@dataclass
class IngestionResult:
    local_path: Path | None
    mode: str
    message: str


def prepare_repository_source(repository: Repository) -> IngestionResult:
    if repository.local_path:
        local = Path(repository.local_path).expanduser()
        if local.is_dir() and any(local.rglob("*.py")):
            return IngestionResult(local_path=local, mode="local", message="Using user-provided local path")

    if os.getenv("LEGACY_ATLAS_ENABLE_GIT_INGESTION", "1") != "1":
        return IngestionResult(local_path=None, mode="fallback", message="Git ingestion disabled by environment")

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    repo_dir = CACHE_ROOT / f"{repository.owner}__{repository.name}"

    repo_url = str(repository.repo_url)
    branch = repository.default_branch or "main"

    if not repo_dir.exists():
        clone_result = _run_command(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                branch,
                repo_url,
                str(repo_dir),
            ]
        )
        if not clone_result[0]:
            return IngestionResult(local_path=None, mode="fallback", message=clone_result[1])
    else:
        fetch_result = _run_command(["git", "-C", str(repo_dir), "fetch", "origin", branch, "--depth", "1"])
        if fetch_result[0]:
            _run_command(["git", "-C", str(repo_dir), "checkout", branch])
            _run_command(["git", "-C", str(repo_dir), "pull", "--ff-only", "origin", branch])

    if repo_dir.is_dir() and any(repo_dir.rglob("*.py")):
        return IngestionResult(local_path=repo_dir, mode="git-clone", message="Repository prepared in local cache")

    return IngestionResult(local_path=None, mode="fallback", message="No Python files found after ingestion")


def _run_command(command: list[str], timeout: int = 120) -> tuple[bool, str]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=True)
        return True, completed.stdout.strip() or "ok"
    except FileNotFoundError:
        return False, "git binary not available"
    except subprocess.CalledProcessError as exc:
        error = exc.stderr.strip() or exc.stdout.strip() or "unknown git error"
        return False, error
    except subprocess.TimeoutExpired:
        return False, "git command timed out"
