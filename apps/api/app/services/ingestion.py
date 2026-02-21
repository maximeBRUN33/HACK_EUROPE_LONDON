from __future__ import annotations

import os
import logging
import subprocess
import shutil
import re
from dataclasses import dataclass
from pathlib import Path

from app.models import Repository

CACHE_ROOT = Path(os.getenv("LEGACY_ATLAS_REPO_CACHE", Path(__file__).resolve().parents[3] / ".cache" / "repos"))
logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    local_path: Path | None
    mode: str
    message: str


def prepare_repository_source(repository: Repository) -> IngestionResult:
    logger.info("Preparing repository source repo=%s/%s", repository.owner, repository.name)
    if repository.local_path:
        local = Path(repository.local_path).expanduser()
        if local.is_dir() and any(local.rglob("*.py")):
            logger.info("Using provided local path repo=%s/%s path=%s", repository.owner, repository.name, local)
            return IngestionResult(local_path=local, mode="local", message="Using user-provided local path")

    if os.getenv("LEGACY_ATLAS_ENABLE_GIT_INGESTION", "1") != "1":
        logger.info("Git ingestion disabled repo=%s/%s", repository.owner, repository.name)
        return IngestionResult(local_path=None, mode="fallback", message="Git ingestion disabled by environment")

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    repo_dir = CACHE_ROOT / f"{repository.owner}__{repository.name}"

    repo_url = str(repository.repo_url)
    branch = repository.default_branch or "main"

    if not repo_dir.exists():
        logger.info("Cloning repository repo=%s/%s branch=%s cache_path=%s", repository.owner, repository.name, branch, repo_dir)
        clone_result = _clone_with_branch(repo_url, repo_dir, branch)

        if not clone_result[0] and _is_missing_branch_error(clone_result[1]):
            remote_default = _discover_remote_default_branch(repo_url)
            if remote_default and remote_default != branch:
                logger.warning(
                    "Requested branch missing; retrying with remote default repo=%s/%s requested=%s remote_default=%s",
                    repository.owner,
                    repository.name,
                    branch,
                    remote_default,
                )
                shutil.rmtree(repo_dir, ignore_errors=True)
                branch = remote_default
                clone_result = _clone_with_branch(repo_url, repo_dir, branch)

        if not clone_result[0]:
            logger.warning("Branch clone failed; retrying with remote HEAD repo=%s/%s", repository.owner, repository.name)
            shutil.rmtree(repo_dir, ignore_errors=True)
            clone_result = _run_command(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    repo_url,
                    str(repo_dir),
                ]
            )

        if not clone_result[0]:
            logger.warning("Clone failed repo=%s/%s reason=%s", repository.owner, repository.name, clone_result[1])
            return IngestionResult(local_path=None, mode="fallback", message=clone_result[1])
    else:
        logger.info("Refreshing cached repository repo=%s/%s branch=%s cache_path=%s", repository.owner, repository.name, branch, repo_dir)
        fetch_result = _run_command(["git", "-C", str(repo_dir), "fetch", "origin", branch, "--depth", "1"])
        if fetch_result[0]:
            _run_command(["git", "-C", str(repo_dir), "checkout", branch])
            _run_command(["git", "-C", str(repo_dir), "pull", "--ff-only", "origin", branch])
        else:
            logger.warning("Fetch failed repo=%s/%s reason=%s", repository.owner, repository.name, fetch_result[1])

    if repo_dir.is_dir() and any(repo_dir.rglob("*.py")):
        logger.info("Repository source prepared repo=%s/%s mode=git-clone path=%s branch=%s", repository.owner, repository.name, repo_dir, branch)
        return IngestionResult(local_path=repo_dir, mode="git-clone", message=f"Repository prepared in local cache (branch={branch})")

    logger.warning("No Python files found after ingestion repo=%s/%s", repository.owner, repository.name)
    return IngestionResult(local_path=None, mode="fallback", message="No Python files found after ingestion")


def _run_command(command: list[str], timeout: int = 120) -> tuple[bool, str]:
    logger.debug("Running command: %s", " ".join(command))
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=True)
        logger.debug("Command succeeded: %s", " ".join(command))
        return True, completed.stdout.strip() or "ok"
    except FileNotFoundError:
        logger.warning("Command failed, git binary not available")
        return False, "git binary not available"
    except subprocess.CalledProcessError as exc:
        error = exc.stderr.strip() or exc.stdout.strip() or "unknown git error"
        logger.warning("Command failed: %s | %s", " ".join(command), error)
        return False, error
    except subprocess.TimeoutExpired:
        logger.warning("Command timed out: %s", " ".join(command))
        return False, "git command timed out"


def _clone_with_branch(repo_url: str, repo_dir: Path, branch: str) -> tuple[bool, str]:
    return _run_command(
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


def _discover_remote_default_branch(repo_url: str) -> str | None:
    ok, output = _run_command(["git", "ls-remote", "--symref", repo_url, "HEAD"], timeout=30)
    if not ok:
        return None

    match = re.search(r"ref:\s+refs/heads/([^\s]+)\s+HEAD", output)
    if not match:
        return None
    return match.group(1)


def _is_missing_branch_error(message: str) -> bool:
    text = message.lower()
    return "remote branch" in text and "not found" in text
