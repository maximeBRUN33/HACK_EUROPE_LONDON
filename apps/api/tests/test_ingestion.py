from pathlib import Path

from app.models import Repository
from app.services import ingestion


def test_prepare_repository_source_resolves_branch_before_clone(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LEGACY_ATLAS_ENABLE_GIT_INGESTION", "1")
    monkeypatch.setattr(ingestion, "CACHE_ROOT", tmp_path)
    monkeypatch.setattr(ingestion, "_resolve_effective_branch", lambda _url, _branch: "version-15")

    captured: dict[str, str] = {}

    def fake_clone(repo_url: str, repo_dir: Path, branch: str) -> tuple[bool, str]:
        captured["repo_url"] = repo_url
        captured["branch"] = branch
        repo_dir.mkdir(parents=True, exist_ok=True)
        (repo_dir / "app.py").write_text("print('ok')\n", encoding="utf-8")
        return True, "ok"

    monkeypatch.setattr(ingestion, "_clone_with_branch", fake_clone)

    repository = Repository(
        owner="frappe",
        name="erpnext",
        default_branch="main",
        repo_url="https://github.com/frappe/erpnext",
    )
    result = ingestion.prepare_repository_source(repository)

    assert result.mode == "git-clone"
    assert result.resolved_branch == "version-15"
    assert captured["repo_url"] == "https://github.com/frappe/erpnext"
    assert captured["branch"] == "version-15"
    assert result.local_path is not None
    assert result.local_path.is_dir()


def test_resolve_effective_branch_uses_remote_default_when_requested_missing(monkeypatch) -> None:
    monkeypatch.setattr(ingestion, "_branch_exists", lambda _url, _branch: False)
    monkeypatch.setattr(ingestion, "_discover_remote_default_branch", lambda _url: "develop")

    resolved = ingestion._resolve_effective_branch("https://github.com/frappe/erpnext", "main")
    assert resolved == "develop"
