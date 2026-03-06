"""Unit tests for backlog add interactive issue creation command."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from typer.testing import CliRunner


# ruff: noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "modules" / "backlog-core" / "src"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from backlog_core.commands.add import _has_github_repo_issue_type_mapping
from backlog_core.main import backlog_app


runner = CliRunner()


class _FakeAdapter:
    def __init__(self, items: list[dict], relationships: list[dict], created: list[dict]) -> None:
        self._items = items
        self._relationships = relationships
        self.created = created

    def fetch_all_issues(self, project_id: str, filters: dict | None = None) -> list[dict]:
        _ = project_id, filters
        return self._items

    def fetch_relationships(self, project_id: str) -> list[dict]:
        _ = project_id
        return self._relationships

    def create_issue(self, project_id: str, payload: dict) -> dict:
        _ = project_id
        self.created.append(payload)
        return {"id": "123", "key": "123", "url": "https://example.test/issues/123"}


def test_has_github_repo_issue_type_mapping_story_fallback_to_feature() -> None:
    """When story is unavailable but feature exists, mapping should still be considered available."""
    provider_fields = {"github_issue_types": {"type_ids": {"feature": "IT_FEATURE_ID"}}}
    assert _has_github_repo_issue_type_mapping(provider_fields, "story") is True


def test_has_github_repo_issue_type_mapping_story_missing_without_feature() -> None:
    """When both story and feature are unavailable, mapping is unavailable."""
    provider_fields = {"github_issue_types": {"type_ids": {"bug": "IT_BUG_ID"}}}
    assert _has_github_repo_issue_type_mapping(provider_fields, "story") is False


def test_backlog_add_non_interactive_requires_type_and_title(monkeypatch) -> None:
    """Non-interactive add fails when required options are missing."""
    from specfact_cli.adapters.registry import AdapterRegistry

    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: _FakeAdapter([], [], []))

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--non-interactive",
        ],
    )

    assert result.exit_code == 1
    assert "required in --non-interactive mode" in result.stdout


def test_backlog_add_validates_missing_parent(monkeypatch) -> None:
    """Add fails when provided parent key/id cannot be resolved."""
    from specfact_cli.adapters.registry import AdapterRegistry

    adapter = _FakeAdapter(items=[], relationships=[], created=[])
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--type",
            "story",
            "--parent",
            "FEAT-123",
            "--title",
            "Implement X",
            "--non-interactive",
        ],
    )

    assert result.exit_code == 1
    assert "Parent 'FEAT-123' not found" in result.stdout


def test_backlog_add_uses_default_hierarchy_when_no_github_custom_mapping_file(monkeypatch, tmp_path: Path) -> None:
    """Add falls back to default hierarchy when github_custom mapping file is absent."""
    from specfact_cli.adapters.registry import AdapterRegistry

    items = [
        {
            "id": "42",
            "key": "STORY-1",
            "title": "Story Parent",
            "type": "story",
            "status": "todo",
        }
    ]
    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=items, relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--type",
            "task",
            "--parent",
            "STORY-1",
            "--title",
            "Implement X",
            "--body",
            "Body",
            "--non-interactive",
        ],
    )

    assert result.exit_code == 0
    assert created_payloads


def test_backlog_add_auto_applies_github_custom_mapping_file(monkeypatch, tmp_path: Path) -> None:
    """Add automatically loads .specfact github_custom mapping file when present."""
    from specfact_cli.adapters.registry import AdapterRegistry

    custom_mapping_file = tmp_path / ".specfact" / "templates" / "backlog" / "field_mappings" / "github_custom.yaml"
    custom_mapping_file.parent.mkdir(parents=True, exist_ok=True)
    custom_mapping_file.write_text(
        """
creation_hierarchy:
  task: [epic]
""".strip(),
        encoding="utf-8",
    )

    items = [
        {
            "id": "42",
            "key": "STORY-1",
            "title": "Story Parent",
            "type": "story",
            "status": "todo",
        }
    ]
    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=items, relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--type",
            "task",
            "--parent",
            "STORY-1",
            "--title",
            "Implement X",
            "--body",
            "Body",
            "--non-interactive",
        ],
    )

    assert result.exit_code == 1
    assert "Type 'task' is not allowed under parent type 'story'" in result.stdout


def test_backlog_add_honors_creation_hierarchy_from_custom_config(monkeypatch, tmp_path: Path) -> None:
    """Add validates child->parent relationship using explicit hierarchy config."""
    from specfact_cli.adapters.registry import AdapterRegistry

    config_file = tmp_path / "custom.yaml"
    config_file.write_text(
        """
creation_hierarchy:
  story: [feature]
""".strip(),
        encoding="utf-8",
    )

    items = [
        {
            "id": "42",
            "key": "FEAT-123",
            "title": "Parent",
            "type": "feature",
            "status": "todo",
        }
    ]
    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=items, relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--template",
            "github_projects",
            "--custom-config",
            str(config_file),
            "--type",
            "story",
            "--parent",
            "FEAT-123",
            "--title",
            "Implement X",
            "--body",
            "Acceptance criteria: ...",
            "--non-interactive",
        ],
    )

    assert result.exit_code == 0
    assert created_payloads and created_payloads[0]["parent_id"] == "42"


def test_backlog_add_ado_requires_saved_required_custom_field(monkeypatch, tmp_path: Path) -> None:
    """Add should fail before adapter create when saved metadata marks a custom ADO field as required."""
    from specfact_cli.adapters.registry import AdapterRegistry

    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=[], relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)
    monkeypatch.chdir(tmp_path)

    spec_dir = tmp_path / ".specfact"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "backlog-config.yaml").write_text(
        yaml.safe_dump(
            {
                "backlog_config": {
                    "providers": {
                        "ado": {
                            "adapter": "ado",
                            "project_id": "test-org/test-project",
                            "settings": {
                                "selected_work_item_type": "User Story",
                                "field_mapping_file": ".specfact/templates/backlog/field_mappings/ado_custom.yaml",
                                "required_fields_by_work_item_type": {"User Story": ["Custom.FinOpsCategory"]},
                                "allowed_values_by_work_item_type": {
                                    "User Story": {"Custom.FinOpsCategory": ["Business", "Compliance"]}
                                },
                            },
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    mapping_file = spec_dir / "templates" / "backlog" / "field_mappings" / "ado_custom.yaml"
    mapping_file.parent.mkdir(parents=True, exist_ok=True)
    mapping_file.write_text(
        yaml.safe_dump({"field_mappings": {"Custom.FinOpsCategory": "finops_category"}}),
        encoding="utf-8",
    )

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "test-org/test-project",
            "--adapter",
            "ado",
            "--type",
            "story",
            "--title",
            "Implement finops guardrail",
            "--body",
            "Body",
            "--non-interactive",
        ],
    )

    assert result.exit_code == 1
    assert "missing required custom field" in result.stdout.lower()
    assert "finops_category" in result.stdout.lower()
    assert not created_payloads


def test_backlog_add_ado_validates_and_forwards_custom_fields(monkeypatch, tmp_path: Path) -> None:
    """Add should validate picklist values and forward resolved ADO custom field payload."""
    from specfact_cli.adapters.registry import AdapterRegistry

    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=[], relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)
    monkeypatch.chdir(tmp_path)

    spec_dir = tmp_path / ".specfact"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "backlog-config.yaml").write_text(
        yaml.safe_dump(
            {
                "backlog_config": {
                    "providers": {
                        "ado": {
                            "adapter": "ado",
                            "project_id": "test-org/test-project",
                            "settings": {
                                "selected_work_item_type": "User Story",
                                "field_mapping_file": ".specfact/templates/backlog/field_mappings/ado_custom.yaml",
                                "required_fields_by_work_item_type": {"User Story": ["Custom.FinOpsCategory"]},
                                "allowed_values_by_work_item_type": {
                                    "User Story": {"Custom.FinOpsCategory": ["Business", "Compliance"]}
                                },
                            },
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    mapping_file = spec_dir / "templates" / "backlog" / "field_mappings" / "ado_custom.yaml"
    mapping_file.parent.mkdir(parents=True, exist_ok=True)
    mapping_file.write_text(
        yaml.safe_dump({"field_mappings": {"Custom.FinOpsCategory": "finops_category"}}),
        encoding="utf-8",
    )

    invalid_result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "test-org/test-project",
            "--adapter",
            "ado",
            "--type",
            "story",
            "--title",
            "Implement finops guardrail",
            "--body",
            "Body",
            "--custom-field",
            "finops_category=Wrong",
            "--non-interactive",
        ],
    )

    assert invalid_result.exit_code == 1
    assert "allowed values" in invalid_result.stdout.lower()
    assert "business" in invalid_result.stdout.lower()
    assert "compliance" in invalid_result.stdout.lower()

    created_payloads.clear()
    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "test-org/test-project",
            "--adapter",
            "ado",
            "--type",
            "story",
            "--title",
            "Implement finops guardrail",
            "--body",
            "Body",
            "--custom-field",
            "finops_category=Business",
            "--non-interactive",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert created_payloads
    assert created_payloads[0]["provider_fields"]["fields"]["Custom.FinOpsCategory"] == "Business"


def test_backlog_add_check_dor_blocks_invalid_draft(monkeypatch, tmp_path: Path) -> None:
    """Add fails DoR check when configured required fields are missing."""
    from specfact_cli.adapters.registry import AdapterRegistry

    dor_dir = tmp_path / ".specfact"
    dor_dir.mkdir(parents=True, exist_ok=True)
    (dor_dir / "dor.yaml").write_text(
        """
rules:
  acceptance_criteria: true
""".strip(),
        encoding="utf-8",
    )

    adapter = _FakeAdapter(items=[], relationships=[], created=[])
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--type",
            "story",
            "--title",
            "Implement X",
            "--body",
            "No explicit section",
            "--non-interactive",
            "--check-dor",
            "--repo-path",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "Definition of Ready" in result.stdout


class _FakeAdoAdapter(_FakeAdapter):
    def _get_current_iteration(self) -> str | None:
        return "Project\\Sprint 42"

    def _list_available_iterations(self) -> list[str]:
        return ["Project\\Sprint 41", "Project\\Sprint 42"]


def test_backlog_add_interactive_multiline_body_uses_end_marker(monkeypatch) -> None:
    """Interactive add supports multiline body input terminated by marker."""
    from specfact_cli.adapters.registry import AdapterRegistry

    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=[], relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    import importlib

    add_module = importlib.import_module("backlog_core.commands.add")

    def _select(message: str, _choices: list[str], default: str | None = None) -> str:
        lowered = message.lower()
        if "issue type" in lowered:
            return "story"
        if "description format" in lowered:
            return "markdown"
        if "acceptance criteria" in lowered:
            return "no"
        if "add parent issue" in lowered:
            return "no"
        return default or "markdown"

    monkeypatch.setattr(add_module, "_select_with_fallback", _select)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--body-end-marker",
            "::END::",
        ],
        input="Interactive title\nline one\nline two\n::END::\n\n\n\n",
    )

    assert result.exit_code == 0
    assert created_payloads
    assert created_payloads[0]["description"] == "line one\nline two"


def test_backlog_add_interactive_ado_selects_current_iteration(monkeypatch) -> None:
    """Interactive add can set sprint from current ADO iteration selection."""
    import importlib

    add_module = importlib.import_module("backlog_core.commands.add")

    from specfact_cli.adapters.registry import AdapterRegistry

    created_payloads: list[dict] = []
    adapter = _FakeAdoAdapter(items=[], relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    def _select(message: str, _choices: list[str], default: str | None = None) -> str:
        lowered = message.lower()
        if "issue type" in lowered:
            return "story"
        if "sprint/iteration" in lowered:
            return "current: Project\\Sprint 42"
        if "description format" in lowered:
            return "markdown"
        if "acceptance criteria" in lowered:
            return "no"
        if "add parent issue" in lowered:
            return "no"
        return "markdown"

    monkeypatch.setattr(add_module, "_select_with_fallback", _select)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "dominikusnold/Specfact CLI",
            "--adapter",
            "ado",
        ],
        input="ADO story\nbody line\n::END::\n\n\n",
    )

    assert result.exit_code == 0
    assert created_payloads
    assert created_payloads[0]["sprint"] == "Project\\Sprint 42"


def test_backlog_add_interactive_collects_story_fields_and_parent(monkeypatch) -> None:
    """Interactive story flow captures AC/priority/story points and selected parent."""
    import importlib

    add_module = importlib.import_module("backlog_core.commands.add")

    from specfact_cli.adapters.registry import AdapterRegistry

    items = [
        {
            "id": "42",
            "key": "FEAT-123",
            "title": "Parent feature",
            "type": "feature",
            "status": "todo",
        }
    ]
    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=items, relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    def _select(message: str, _choices: list[str], default: str | None = None) -> str:
        lowered = message.lower()
        if "issue type" in lowered:
            return "story"
        if "description format" in lowered:
            return "markdown"
        if "acceptance criteria" in lowered:
            return "yes"
        if "add parent issue" in lowered:
            return "yes"
        if "select parent issue" in lowered:
            return "FEAT-123 | Parent feature | type=feature"
        return "markdown"

    monkeypatch.setattr(add_module, "_select_with_fallback", _select)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
        ],
        input="Story title\nbody line\n::END::\n\nac line\n::END::\nhigh\n5\n",
    )

    assert result.exit_code == 0
    assert created_payloads
    payload = created_payloads[0]
    assert payload["acceptance_criteria"] == "ac line"
    assert payload["priority"] == "high"
    assert payload["story_points"] == 5
    assert payload["parent_id"] == "42"


def test_backlog_add_interactive_parent_selection_falls_back_to_all_candidates(monkeypatch) -> None:
    """Interactive parent picker falls back to all candidates when type inference yields no matches."""
    import importlib

    add_module = importlib.import_module("backlog_core.commands.add")

    from specfact_cli.adapters.registry import AdapterRegistry

    items = [
        {
            "id": "42",
            "key": "STORY-1",
            "title": "Parent",
            "type": "custom",
            "status": "todo",
        }
    ]
    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=items, relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    def _select(message: str, _choices: list[str], default: str | None = None) -> str:
        lowered = message.lower()
        if "issue type" in lowered:
            return "task"
        if "description format" in lowered:
            return "markdown"
        if "acceptance criteria" in lowered:
            return "no"
        if "add parent issue" in lowered:
            return "yes"
        if "select parent issue" in lowered:
            return "STORY-1 | Parent | type=custom"
        return default or "markdown"

    monkeypatch.setattr(add_module, "_select_with_fallback", _select)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
        ],
        input="Task title\nBody line\n::END::\n\n\n\n",
    )

    assert result.exit_code == 0
    assert "No hierarchy-compatible parent candidates found from inferred types." in result.stdout
    assert created_payloads
    assert created_payloads[0]["parent_id"] == "42"


def test_backlog_add_ado_default_template_enables_epic_parent_candidates(monkeypatch) -> None:
    """ADO add without explicit template should still resolve epic parent candidate for feature."""
    import importlib

    add_module = importlib.import_module("backlog_core.commands.add")

    from specfact_cli.adapters.registry import AdapterRegistry

    items = [
        {
            "id": "900",
            "key": "EPIC-900",
            "title": "Platform Epic",
            "work_item_type": "Epic",
            "status": "New",
        }
    ]
    created_payloads: list[dict] = []
    adapter = _FakeAdoAdapter(items=items, relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    def _select(message: str, _choices: list[str], default: str | None = None) -> str:
        lowered = message.lower()
        if "issue type" in lowered:
            return "feature"
        if "sprint/iteration" in lowered:
            return "(skip sprint/iteration)"
        if "description format" in lowered:
            return "markdown"
        if "acceptance criteria" in lowered:
            return "no"
        if "add parent issue" in lowered:
            return "yes"
        if "select parent issue" in lowered:
            return "EPIC-900 | Platform Epic | type=epic"
        return default or "markdown"

    monkeypatch.setattr(add_module, "_select_with_fallback", _select)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "dominikusnold/Specfact CLI",
            "--adapter",
            "ado",
        ],
        input="Feature title\nFeature body\n::END::\n\n\n",
    )

    assert result.exit_code == 0
    assert created_payloads
    assert created_payloads[0].get("parent_id") == "900"


def test_backlog_add_warns_on_ambiguous_create_failure(monkeypatch) -> None:
    """CLI warns user when duplicate-safe create fails with ambiguous transport error."""
    import requests

    from specfact_cli.adapters.registry import AdapterRegistry

    class _TimeoutAdapter(_FakeAdapter):
        def create_issue(self, project_id: str, payload: dict) -> dict:  # type: ignore[override]
            _ = project_id, payload
            raise requests.Timeout("network timeout")

    adapter = _TimeoutAdapter(items=[], relationships=[], created=[])
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--type",
            "story",
            "--title",
            "Implement X",
            "--non-interactive",
        ],
    )

    assert result.exit_code == 1
    assert "may already exist remotely" in result.stdout
    assert "before retrying to avoid duplicates" in result.stdout


def test_backlog_add_interactive_ado_sprint_lookup_uses_project_context(monkeypatch) -> None:
    """ADO sprint lookup uses project_id-resolved org/project context before selection."""
    import importlib

    add_module = importlib.import_module("backlog_core.commands.add")

    from specfact_cli.adapters.registry import AdapterRegistry

    class _ContextAdoAdapter(_FakeAdapter):
        def __init__(self) -> None:
            super().__init__(items=[], relationships=[], created=[])
            self.org = None
            self.project = None

        def _resolve_graph_project_context(self, project_id: str) -> tuple[str, str]:
            assert project_id == "dominikusnold/Specfact CLI"
            return "dominikusnold", "Specfact CLI"

        def _get_current_iteration(self) -> str | None:
            if self.org == "dominikusnold" and self.project == "Specfact CLI":
                return r"Specfact CLI\2026\Sprint 01"
            return None

        def _list_available_iterations(self) -> list[str]:
            if self.org == "dominikusnold" and self.project == "Specfact CLI":
                return [r"Specfact CLI\2026\Sprint 01", r"Specfact CLI\2026\Sprint 02"]
            return []

    adapter = _ContextAdoAdapter()
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    def _select(message: str, _choices: list[str], default: str | None = None) -> str:
        lowered = message.lower()
        if "issue type" in lowered:
            return "story"
        if "sprint/iteration" in lowered:
            return r"current: Specfact CLI\2026\Sprint 01"
        if "description format" in lowered:
            return "markdown"
        if "acceptance criteria" in lowered:
            return "no"
        if "add parent issue" in lowered:
            return "no"
        return default or "markdown"

    monkeypatch.setattr(add_module, "_select_with_fallback", _select)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "dominikusnold/Specfact CLI",
            "--adapter",
            "ado",
        ],
        input="Story title\nBody\n::END::\n\n\n",
    )

    assert result.exit_code == 0
    assert adapter.created
    assert adapter.created[0].get("sprint") == r"Specfact CLI\2026\Sprint 01"


def test_backlog_add_forwards_github_project_v2_provider_fields(monkeypatch, tmp_path: Path) -> None:
    """backlog add forwards GitHub ProjectV2 config from custom config into create payload."""
    from specfact_cli.adapters.registry import AdapterRegistry

    config_file = tmp_path / "custom.yaml"
    config_file.write_text(
        """
provider_fields:
  github_project_v2:
    project_id: PVT_PROJECT_1
    type_field_id: PVT_FIELD_TYPE
    type_option_ids:
      story: PVT_OPTION_STORY
""".strip(),
        encoding="utf-8",
    )

    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=[], relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--template",
            "github_projects",
            "--custom-config",
            str(config_file),
            "--type",
            "story",
            "--title",
            "Implement X",
            "--body",
            "Acceptance criteria",
            "--non-interactive",
        ],
    )

    assert result.exit_code == 0
    assert created_payloads
    provider_fields = created_payloads[0].get("provider_fields")
    assert isinstance(provider_fields, dict)
    github_project_v2 = provider_fields.get("github_project_v2")
    assert isinstance(github_project_v2, dict)
    assert github_project_v2.get("project_id") == "PVT_PROJECT_1"
    assert github_project_v2.get("type_field_id") == "PVT_FIELD_TYPE"
    assert github_project_v2.get("type_option_ids", {}).get("story") == "PVT_OPTION_STORY"


def test_backlog_add_forwards_github_project_v2_from_backlog_config(monkeypatch, tmp_path: Path) -> None:
    """backlog add loads GitHub ProjectV2 config from .specfact/backlog-config.yaml provider settings."""
    from specfact_cli.adapters.registry import AdapterRegistry

    spec_dir = tmp_path / ".specfact"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "backlog-config.yaml").write_text(
        """
backlog_config:
  providers:
    github:
      adapter: github
      project_id: nold-ai/specfact-demo-repo
      settings:
        provider_fields:
          github_project_v2:
            project_id: PVT_PROJECT_SPEC
            type_field_id: PVT_FIELD_TYPE_SPEC
            type_option_ids:
              task: PVT_OPTION_TASK_SPEC
        github_issue_types:
          type_ids:
            task: IT_TASK_SPEC
""".strip(),
        encoding="utf-8",
    )

    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=[], relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-demo-repo",
            "--adapter",
            "github",
            "--template",
            "github_projects",
            "--type",
            "task",
            "--title",
            "Implement task",
            "--body",
            "Body",
            "--non-interactive",
            "--repo-path",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert created_payloads
    provider_fields = created_payloads[0].get("provider_fields")
    assert isinstance(provider_fields, dict)
    github_project_v2 = provider_fields.get("github_project_v2")
    assert isinstance(github_project_v2, dict)
    assert github_project_v2.get("project_id") == "PVT_PROJECT_SPEC"
    assert github_project_v2.get("type_field_id") == "PVT_FIELD_TYPE_SPEC"
    assert github_project_v2.get("type_option_ids", {}).get("task") == "PVT_OPTION_TASK_SPEC"
    github_issue_types = provider_fields.get("github_issue_types")
    assert isinstance(github_issue_types, dict)
    assert github_issue_types.get("type_ids", {}).get("task") == "IT_TASK_SPEC"
    assert "repository issue-type mapping is not configured" not in result.stdout


def test_backlog_add_warns_when_github_issue_type_mapping_missing(monkeypatch) -> None:
    """backlog add warns when repository issue-type mapping is unavailable for selected type."""
    from specfact_cli.adapters.registry import AdapterRegistry

    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=[], relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-demo-repo",
            "--adapter",
            "github",
            "--type",
            "spike",
            "--title",
            "Sample task",
            "--body",
            "Body",
            "--non-interactive",
        ],
    )

    assert result.exit_code == 0
    assert "repository issue-type mapping is not configured" in result.stdout


def test_backlog_add_prefers_root_issue_type_ids_when_provider_fields_issue_types_empty(
    monkeypatch, tmp_path: Path
) -> None:
    """backlog add should use root github_issue_types when provider_fields copy is empty."""
    from specfact_cli.adapters.registry import AdapterRegistry

    spec_dir = tmp_path / ".specfact"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "backlog-config.yaml").write_text(
        """
backlog_config:
  providers:
    github:
      adapter: github
      project_id: nold-ai/specfact-demo-repo
      settings:
        provider_fields:
          github_issue_types:
            type_ids: {}
        github_issue_types:
          type_ids:
            task: IT_TASK_SPEC
""".strip(),
        encoding="utf-8",
    )

    created_payloads: list[dict] = []
    adapter = _FakeAdapter(items=[], relationships=[], created=created_payloads)
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda _adapter: adapter)

    result = runner.invoke(
        backlog_app,
        [
            "add",
            "--project-id",
            "nold-ai/specfact-demo-repo",
            "--adapter",
            "github",
            "--type",
            "task",
            "--title",
            "Implement task",
            "--body",
            "Body",
            "--non-interactive",
            "--repo-path",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert created_payloads
    provider_fields = created_payloads[0].get("provider_fields")
    assert isinstance(provider_fields, dict)
    github_issue_types = provider_fields.get("github_issue_types")
    assert isinstance(github_issue_types, dict)
    assert github_issue_types.get("type_ids", {}).get("task") == "IT_TASK_SPEC"
    assert "repository issue-type mapping is not configured" not in result.stdout
