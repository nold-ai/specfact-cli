"""
Unit tests for project backlog context (.specfact/backlog.yaml).

Scenarios from openspec/changes/daily-standup-progress-support/specs/daily-standup/spec.md:
- Project backlog context: adapter context (org, project per adapter) from file when not passed
- Resolution order: CLI > env > file; tokens never from file
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("specfact_cli.modules.backlog.src.commands")
from specfact_cli.modules.backlog.src.commands import (
    _build_adapter_kwargs,
    _infer_ado_context_from_cwd,
    _load_backlog_config,
)


class TestLoadBacklogConfig:
    """_load_backlog_config: read .specfact/backlog.yaml (no secrets)."""

    def test_returns_empty_dict_when_no_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no backlog.yaml exists, return empty dict."""
        monkeypatch.delenv("SPECFACT_CONFIG_DIR", raising=False)
        monkeypatch.chdir(Path(__file__).resolve().parents[3])
        assert _load_backlog_config() == {}

    def test_loads_github_section_from_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When .specfact/backlog.yaml has github.repo_owner and repo_name, return them."""
        monkeypatch.setenv("SPECFACT_CONFIG_DIR", str(tmp_path))
        (tmp_path / "backlog.yaml").write_text(
            "github:\n  repo_owner: myorg\n  repo_name: myrepo\n",
            encoding="utf-8",
        )
        cfg = _load_backlog_config()
        assert cfg.get("github", {}).get("repo_owner") == "myorg"
        assert cfg.get("github", {}).get("repo_name") == "myrepo"

    def test_loads_ado_section_from_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When .specfact/backlog.yaml has ado org, project, team, return them."""
        monkeypatch.setenv("SPECFACT_CONFIG_DIR", str(tmp_path))
        (tmp_path / "backlog.yaml").write_text(
            "ado:\n  org: myorg\n  project: MyProject\n  team: My Team\n",
            encoding="utf-8",
        )
        cfg = _load_backlog_config()
        assert cfg.get("ado", {}).get("org") == "myorg"
        assert cfg.get("ado", {}).get("project") == "MyProject"
        assert cfg.get("ado", {}).get("team") == "My Team"

    def test_uses_top_level_backlog_key_when_present(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When file has top-level 'backlog' key, nested structure is used."""
        monkeypatch.setenv("SPECFACT_CONFIG_DIR", str(tmp_path))
        (tmp_path / "backlog.yaml").write_text(
            "backlog:\n  github:\n    repo_owner: foo\n    repo_name: bar\n",
            encoding="utf-8",
        )
        cfg = _load_backlog_config()
        assert cfg.get("github", {}).get("repo_owner") == "foo"
        assert cfg.get("github", {}).get("repo_name") == "bar"


class TestBuildAdapterKwargsWithConfig:
    """_build_adapter_kwargs: merge CLI > env > config; tokens never from config."""

    def test_github_uses_explicit_args_over_config(self) -> None:
        """When repo_owner/repo_name passed, they are used; config ignored for those."""
        with patch(
            "specfact_cli.modules.backlog.src.commands._load_backlog_config",
            return_value={"github": {"repo_owner": "fromfile", "repo_name": "fromfile"}},
        ):
            kwargs = _build_adapter_kwargs(
                "github",
                repo_owner="fromcli",
                repo_name="fromcli",
            )
        assert kwargs["repo_owner"] == "fromcli"
        assert kwargs["repo_name"] == "fromcli"

    def test_github_uses_config_when_args_none(self) -> None:
        """When repo_owner/repo_name not passed, values from config are used."""
        with patch(
            "specfact_cli.modules.backlog.src.commands._load_backlog_config",
            return_value={"github": {"repo_owner": "myorg", "repo_name": "myrepo"}},
        ):
            kwargs = _build_adapter_kwargs("github", repo_owner=None, repo_name=None)
        assert kwargs.get("repo_owner") == "myorg"
        assert kwargs.get("repo_name") == "myrepo"

    def test_github_env_overrides_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When env SPECFACT_GITHUB_REPO_OWNER is set, it overrides config."""
        monkeypatch.setenv("SPECFACT_GITHUB_REPO_OWNER", "fromenv")
        monkeypatch.setenv("SPECFACT_GITHUB_REPO_NAME", "fromenv")
        with patch(
            "specfact_cli.modules.backlog.src.commands._load_backlog_config",
            return_value={"github": {"repo_owner": "fromfile", "repo_name": "fromfile"}},
        ):
            kwargs = _build_adapter_kwargs("github", repo_owner=None, repo_name=None)
        assert kwargs.get("repo_owner") == "fromenv"
        assert kwargs.get("repo_name") == "fromenv"

    def test_ado_uses_config_when_args_none(self) -> None:
        """When ado_org/ado_project not passed, values from config are used."""
        with patch(
            "specfact_cli.modules.backlog.src.commands._load_backlog_config",
            return_value={
                "ado": {"org": "myorg", "project": "MyProject", "team": "My Team"},
            },
        ):
            kwargs = _build_adapter_kwargs(
                "ado",
                ado_org=None,
                ado_project=None,
                ado_team=None,
            )
        assert kwargs.get("org") == "myorg"
        assert kwargs.get("project") == "MyProject"
        assert kwargs.get("team") == "My Team"

    def test_tokens_never_from_config(self) -> None:
        """Tokens (api_token) are only from explicit args; config is not used for tokens."""
        with patch(
            "specfact_cli.modules.backlog.src.commands._load_backlog_config",
            return_value={
                "github": {"repo_owner": "o", "repo_name": "r", "api_token": "never"},
            },
        ):
            kwargs = _build_adapter_kwargs(
                "github",
                repo_owner=None,
                repo_name=None,
                github_token="fromcli",
            )
        assert kwargs.get("api_token") == "fromcli"
        assert "never" not in str(kwargs)


class TestInferAdoContextFromCwd:
    """_infer_ado_context_from_cwd: infer org/project from git remote when run in ADO clone."""

    def test_returns_org_project_from_https_url(self) -> None:
        """HTTPS dev.azure.com/org/project/_git/repo returns (org, project)."""
        with patch(
            "specfact_cli.modules.backlog.src.commands.subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="https://dev.azure.com/myorg/MyProject/_git/myrepo\n",
            ),
        ):
            org, project = _infer_ado_context_from_cwd()
        assert org == "myorg"
        assert project == "MyProject"

    def test_returns_org_project_from_ssh_url(self) -> None:
        """SSH git@ssh.dev.azure.com:v3/org/project/repo returns (org, project)."""
        with patch(
            "specfact_cli.modules.backlog.src.commands.subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="git@ssh.dev.azure.com:v3/myorg/MyProject/myrepo\n",
            ),
        ):
            org, project = _infer_ado_context_from_cwd()
        assert org == "myorg"
        assert project == "MyProject"

    def test_returns_org_project_from_ssh_url_with_user(self) -> None:
        """SSH user@ssh.dev.azure.com:v3/org/project/repo (as in .git/config) returns (org, project)."""
        with patch(
            "specfact_cli.modules.backlog.src.commands.subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="user@ssh.dev.azure.com:v3/myorg/MyProject/myrepo\n",
            ),
        ):
            org, project = _infer_ado_context_from_cwd()
        assert org == "myorg"
        assert project == "MyProject"

    def test_returns_org_project_from_ssh_url_dev_azure_no_ssh_subdomain(self) -> None:
        """SSH user@dev.azure.com:v3/org/project/repo (no ssh. subdomain, as in some .git/config) returns (org, project)."""
        with patch(
            "specfact_cli.modules.backlog.src.commands.subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="user@dev.azure.com:v3/myorg/MyProject/myrepo\n",
            ),
        ):
            org, project = _infer_ado_context_from_cwd()
        assert org == "myorg"
        assert project == "MyProject"

    def test_returns_none_when_not_ado_remote(self) -> None:
        """GitHub remote returns (None, None)."""
        with patch(
            "specfact_cli.modules.backlog.src.commands.subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="https://github.com/owner/repo\n",
            ),
        ):
            org, project = _infer_ado_context_from_cwd()
        assert org is None
        assert project is None

    def test_ado_uses_inferred_when_args_none(self) -> None:
        """When ado_org/ado_project not passed, inferred from git is used."""
        with (
            patch(
                "specfact_cli.modules.backlog.src.commands._load_backlog_config",
                return_value={},
            ),
            patch(
                "specfact_cli.modules.backlog.src.commands._infer_ado_context_from_cwd",
                return_value=("inferred-org", "inferred-project"),
            ),
        ):
            kwargs = _build_adapter_kwargs(
                "ado",
                ado_org=None,
                ado_project=None,
                ado_team=None,
            )
        assert kwargs.get("org") == "inferred-org"
        assert kwargs.get("project") == "inferred-project"
