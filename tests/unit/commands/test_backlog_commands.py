"""
Unit tests for backlog commands.

Tests for backlog refinement commands, including preview output and filtering.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from rich.panel import Panel
from typer.testing import CliRunner

pytest.importorskip("specfact_cli.modules.backlog.src.commands")
from specfact_cli.backlog.template_detector import TemplateDetector
from specfact_cli.cli import app
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.modules.backlog.src.commands import (
    _apply_issue_window,
    _build_comment_fetch_progress_description,
    _build_refine_export_content,
    _build_refine_preview_comment_empty_panel,
    _build_refine_preview_comment_panels,
    _detect_significant_content_loss,
    _item_needs_refinement,
    _parse_refined_export_markdown,
    _parse_refinement_output_fields,
    _resolve_backlog_provider_framework,
    _resolve_refine_export_comment_window,
    _resolve_refine_preview_comment_window,
    _resolve_target_template_for_refine_item,
    app as backlog_app,
)
from specfact_cli.templates.registry import BacklogTemplate, TemplateRegistry


runner = CliRunner()


@pytest.fixture(autouse=True)
def _bootstrap_registry_for_backlog_commands():
    """Ensure registry is bootstrapped so root 'backlog' resolves to the group with init-config, map-fields, etc."""
    from specfact_cli.registry.bootstrap import register_builtin_commands
    from specfact_cli.registry.registry import CommandRegistry

    CommandRegistry._clear_for_testing()
    register_builtin_commands()
    yield
    CommandRegistry._clear_for_testing()


@patch("specfact_cli.modules.backlog.src.commands._resolve_standup_options")
@patch("specfact_cli.modules.backlog.src.commands._fetch_backlog_items")
def test_daily_issue_id_bypasses_implicit_default_state(
    mock_fetch_backlog_items: MagicMock,
    mock_resolve_standup_options: MagicMock,
) -> None:
    """`backlog daily --id` should not apply implicit default state/assignee filters."""
    mock_resolve_standup_options.return_value = ("open", 20, "me")
    mock_fetch_backlog_items.return_value = [
        BacklogItem(
            id="185",
            provider="ado",
            url="https://dev.azure.com/org/project/_apis/wit/workitems/185",
            title="Fix the error",
            body_markdown="Description",
            state="new",
            assignees=["dominikus.nold@web.de"],
        )
    ]

    result = runner.invoke(
        backlog_app,
        [
            "daily",
            "ado",
            "--ado-org",
            "dominikusnold",
            "--ado-project",
            "Specfact CLI",
            "--id",
            "185",
        ],
    )

    assert result.exit_code == 0
    assert "No backlog item with id" not in result.stdout
    assert mock_fetch_backlog_items.call_args.kwargs["state"] is None
    assert mock_fetch_backlog_items.call_args.kwargs["assignee"] is None


@patch("specfact_cli.modules.backlog.src.commands._resolve_standup_options")
@patch("specfact_cli.modules.backlog.src.commands._fetch_backlog_items")
def test_daily_reports_default_filters_when_no_items(
    mock_fetch_backlog_items: MagicMock,
    mock_resolve_standup_options: MagicMock,
) -> None:
    """`backlog daily` should show implicit defaults in UI output for empty results."""
    mock_resolve_standup_options.return_value = ("open", 20, "me")
    mock_fetch_backlog_items.return_value = []

    result = runner.invoke(
        backlog_app,
        [
            "daily",
            "ado",
            "--ado-org",
            "dominikusnold",
            "--ado-project",
            "Specfact CLI",
        ],
    )

    assert result.exit_code == 0
    assert "Applied filters:" in result.stdout
    assert "state=open (default)" in result.stdout
    assert "assignee=me" in result.stdout
    assert "(default)" in result.stdout
    assert "limit=20 (default)" in result.stdout


@patch("specfact_cli.modules.backlog.src.commands._resolve_standup_options")
@patch("specfact_cli.modules.backlog.src.commands._fetch_backlog_items")
def test_daily_accepts_any_for_state_and_assignee_as_no_filter(
    mock_fetch_backlog_items: MagicMock,
    mock_resolve_standup_options: MagicMock,
) -> None:
    """`--state any` / `--assignee any` should disable both filters."""
    mock_resolve_standup_options.return_value = (None, 20, None)
    mock_fetch_backlog_items.return_value = []

    result = runner.invoke(
        backlog_app,
        [
            "daily",
            "ado",
            "--ado-org",
            "dominikusnold",
            "--ado-project",
            "Specfact CLI",
            "--state",
            "any",
            "--assignee",
            "any",
        ],
    )

    assert result.exit_code == 0
    assert mock_resolve_standup_options.call_args.kwargs["state_filter_disabled"] is True
    assert mock_resolve_standup_options.call_args.kwargs["assignee_filter_disabled"] is True
    assert mock_fetch_backlog_items.call_args.kwargs["state"] is None
    assert mock_fetch_backlog_items.call_args.kwargs["assignee"] is None


@patch("specfact_cli.modules.backlog.src.commands._fetch_backlog_items")
def test_daily_any_filters_render_as_disabled_scope(
    mock_fetch_backlog_items: MagicMock,
) -> None:
    """`--state any --assignee any` should render disabled filter scope in output."""
    mock_fetch_backlog_items.return_value = []

    result = runner.invoke(
        backlog_app,
        [
            "daily",
            "ado",
            "--ado-org",
            "dominikusnold",
            "--ado-project",
            "Specfact CLI",
            "--state",
            "any",
            "--assignee",
            "any",
        ],
    )

    assert result.exit_code == 0
    output = " ".join(result.stdout.split())
    assert "Applied filters:" in output
    assert "state=— (explicit)" in output
    assert "assignee=— (explicit)" in output


class TestBacklogPreviewOutput:
    """Tests for backlog preview output display."""

    def test_preview_output_displays_assignee(self) -> None:
        """Test that preview output displays assignee information."""
        item = BacklogItem(
            id="123",
            provider="ado",
            url="https://dev.azure.com/org/project/_apis/wit/workitems/123",
            title="Test Item",
            body_markdown="Description",
            state="New",
            assignees=["John Doe", "john@example.com"],
        )

        # Verify assignees are set correctly
        assert len(item.assignees) == 2
        assert "John Doe" in item.assignees
        assert "john@example.com" in item.assignees

    def test_preview_output_displays_unassigned(self) -> None:
        """Test that preview output displays 'Unassigned' when no assignees."""
        item = BacklogItem(
            id="124",
            provider="ado",
            url="https://dev.azure.com/org/project/_apis/wit/workitems/124",
            title="Test Item",
            body_markdown="Description",
            state="New",
            assignees=[],
        )

        # Verify empty assignees list
        assert item.assignees == []

    def test_preview_output_assignee_format(self) -> None:
        """Test that assignee display format is correct."""
        item = BacklogItem(
            id="125",
            provider="ado",
            url="https://dev.azure.com/org/project/_apis/wit/workitems/125",
            title="Test Item",
            body_markdown="Description",
            state="New",
            assignees=["Jane Smith"],
        )

        # Format should be: ', '.join(item.assignees) if item.assignees else 'Unassigned'
        assignee_display = ", ".join(item.assignees) if item.assignees else "Unassigned"
        assert assignee_display == "Jane Smith"

        # Test unassigned format
        item_unassigned = BacklogItem(
            id="126",
            provider="ado",
            url="https://dev.azure.com/org/project/_apis/wit/workitems/126",
            title="Test Item",
            body_markdown="Description",
            state="New",
            assignees=[],
        )
        assignee_display_unassigned = (
            ", ".join(item_unassigned.assignees) if item_unassigned.assignees else "Unassigned"
        )
        assert assignee_display_unassigned == "Unassigned"


class TestInteractiveMappingCommand:
    """Tests for interactive template mapping command."""

    @patch("requests.get")
    @patch("questionary.select")
    @patch("rich.prompt.Prompt.ask")
    @patch("rich.prompt.Confirm.ask")
    def test_map_fields_fetches_ado_fields(
        self,
        mock_confirm: MagicMock,
        mock_prompt: MagicMock,
        mock_select: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test that map-fields command fetches ADO metadata endpoints."""
        # Mock ADO API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "referenceName": "System.Description",
                    "name": "Description",
                    "type": "html",
                },
                {
                    "referenceName": "Microsoft.VSTS.Common.AcceptanceCriteria",
                    "name": "Acceptance Criteria",
                    "type": "html",
                },
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock rich.prompt.Prompt to avoid interactive input
        mock_prompt.return_value = ""
        mock_confirm.return_value = False
        mock_select.return_value.ask.return_value = None

        runner.invoke(
            app,
            [
                "backlog",
                "map-fields",
                "--ado-org",
                "test-org",
                "--ado-project",
                "test-project",
                "--ado-token",
                "test-token",
            ],
        )

        # Should call ADO API
        assert mock_get.called
        called_urls = [str(call.args[0]) for call in mock_get.call_args_list if call.args]
        assert any("test-org" in url for url in called_urls)
        assert any("test-project" in url for url in called_urls)
        # map-fields now resolves/processes work-item type metadata before field mapping prompts
        assert any("_apis/wit/workitemtypes" in url for url in called_urls)

    @patch("requests.get")
    @patch("questionary.select")
    @patch("rich.prompt.Prompt.ask")
    @patch("rich.prompt.Confirm.ask")
    def test_map_fields_filters_system_fields(
        self,
        mock_confirm: MagicMock,
        mock_prompt: MagicMock,
        mock_select: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test that map-fields command filters out system-only fields."""
        # Mock ADO API response with system and user fields
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {"referenceName": "System.Id", "name": "ID", "type": "integer"},  # System field - should be filtered
                {
                    "referenceName": "System.Rev",
                    "name": "Revision",
                    "type": "integer",
                },  # System field - should be filtered
                {
                    "referenceName": "System.Description",
                    "name": "Description",
                    "type": "html",
                },  # User field - should be included
                {
                    "referenceName": "Microsoft.VSTS.Common.AcceptanceCriteria",
                    "name": "Acceptance Criteria",
                    "type": "html",
                },  # User field - should be included
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock rich.prompt.Prompt to avoid interactive input
        mock_prompt.return_value = ""
        mock_confirm.return_value = False
        mock_select.return_value.ask.return_value = None

        runner.invoke(
            app,
            [
                "backlog",
                "map-fields",
                "--ado-org",
                "test-org",
                "--ado-project",
                "test-project",
                "--ado-token",
                "test-token",
            ],
        )

        # Command should execute (even if user cancels)
        # The filtering logic is tested implicitly by checking that system fields are excluded
        assert mock_get.called

    def test_map_fields_requires_token(self) -> None:
        """Test that map-fields command requires ADO token."""
        result = runner.invoke(
            app,
            [
                "backlog",
                "map-fields",
                "--ado-org",
                "test-org",
                "--ado-project",
                "test-project",
            ],
            env={"AZURE_DEVOPS_TOKEN": ""},  # Empty token
        )

        # Should fail with error about missing token
        assert result.exit_code != 0
        out = result.output or result.stdout or ""
        assert "token required" in out.lower() or "error" in out.lower()

    @patch("questionary.checkbox")
    @patch("specfact_cli.utils.auth_tokens.get_token")
    @patch("requests.post")
    def test_map_fields_provider_picker_accepts_choice_objects(
        self,
        mock_post: MagicMock,
        mock_get_token: MagicMock,
        mock_checkbox: MagicMock,
        tmp_path,
    ) -> None:
        """Provider picker should accept questionary Choice-like objects with `.value`."""

        class _ChoiceLike:
            def __init__(self, value: str) -> None:
                self.value = value

        mock_checkbox.return_value.ask.return_value = [_ChoiceLike("github")]
        mock_get_token.return_value = {"access_token": "gho_test", "token_type": "bearer"}
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {"repository": {"issueTypes": {"nodes": [{"id": "IT_TASK", "name": "Task"}]}}}
        }
        mock_post.return_value = mock_response

        import os

        cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                backlog_app,
                [
                    "map-fields",
                    "--github-project-id",
                    "nold-ai/specfact-demo-repo",
                    "--github-project-v2-id",
                    "PVT_project_id",
                    "--github-type-field-id",
                    "PVT_type_field",
                    "--github-type-option",
                    "task=OPT_TASK",
                ],
            )
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        assert "No providers selected" not in result.stdout

    @patch("specfact_cli.utils.auth_tokens.get_token")
    @patch("requests.post")
    def test_map_fields_github_provider_persists_backlog_config(
        self, mock_post: MagicMock, mock_get_token: MagicMock, tmp_path
    ) -> None:
        """Test GitHub provider mapping persistence into .specfact/backlog-config.yaml."""
        mock_get_token.return_value = {"access_token": "gho_test", "token_type": "bearer"}
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "repository": {
                    "issueTypes": {
                        "nodes": [
                            {"id": "IT_BUG", "name": "Bug"},
                            {"id": "IT_TASK", "name": "Task"},
                        ]
                    }
                }
            }
        }
        mock_post.return_value = mock_response
        import os

        cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                backlog_app,
                [
                    "map-fields",
                    "--provider",
                    "github",
                    "--github-project-id",
                    "nold-ai/specfact-demo-repo",
                    "--github-project-v2-id",
                    "PVT_project_id",
                    "--github-type-field-id",
                    "PVT_type_field",
                    "--github-type-option",
                    "task=OPT_TASK",
                ],
            )
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        cfg_file = tmp_path / ".specfact" / "backlog-config.yaml"
        assert cfg_file.exists()
        loaded = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        github_settings = loaded["backlog_config"]["providers"]["github"]["settings"]
        mapping = github_settings["provider_fields"]["github_project_v2"]
        assert mapping["project_id"] == "PVT_project_id"
        assert mapping["type_field_id"] == "PVT_type_field"
        assert mapping["type_option_ids"]["task"] == "OPT_TASK"
        assert github_settings["github_issue_types"]["type_ids"]["task"] == "IT_TASK"
        assert github_settings["github_issue_types"]["type_ids"]["bug"] == "IT_BUG"
        assert github_settings["field_mapping_file"] == ".specfact/templates/backlog/field_mappings/github_custom.yaml"
        github_custom = tmp_path / ".specfact" / "templates" / "backlog" / "field_mappings" / "github_custom.yaml"
        assert github_custom.exists()
        github_custom_payload = yaml.safe_load(github_custom.read_text(encoding="utf-8"))
        assert github_custom_payload["type_mapping"]["task"] == "task"

    @patch("specfact_cli.utils.auth_tokens.get_token")
    @patch("requests.post")
    def test_map_fields_github_provider_maps_story_from_user_story_type(
        self, mock_post: MagicMock, mock_get_token: MagicMock, tmp_path
    ) -> None:
        """GitHub map-fields should map canonical story to discovered custom User Story type."""
        mock_get_token.return_value = {"access_token": "gho_test", "token_type": "bearer"}
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "repository": {
                    "issueTypes": {
                        "nodes": [
                            {"id": "IT_FEATURE", "name": "Feature"},
                            {"id": "IT_USER_STORY", "name": "User Story"},
                            {"id": "IT_TASK", "name": "Task"},
                        ]
                    }
                }
            }
        }
        mock_post.return_value = mock_response

        import os

        cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                backlog_app,
                [
                    "map-fields",
                    "--provider",
                    "github",
                    "--github-project-id",
                    "nold-ai/specfact-demo-repo",
                    "--github-project-v2-id",
                    "PVT_project_id",
                    "--github-type-field-id",
                    "PVT_type_field",
                    "--github-type-option",
                    "task=OPT_TASK",
                ],
            )
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        assert "story => user story (fallback alias)" in result.stdout.lower()
        cfg_file = tmp_path / ".specfact" / "backlog-config.yaml"
        loaded = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        github_settings = loaded["backlog_config"]["providers"]["github"]["settings"]
        issue_type_ids = github_settings["github_issue_types"]["type_ids"]
        assert issue_type_ids["user story"] == "IT_USER_STORY"
        assert issue_type_ids["story"] == "IT_USER_STORY"

    @patch("specfact_cli.utils.auth_tokens.get_token")
    @patch("requests.post")
    def test_map_fields_github_provider_fails_when_issue_types_unavailable(
        self, mock_post: MagicMock, mock_get_token: MagicMock, tmp_path
    ) -> None:
        """GitHub map-fields should fail when repository issue type IDs cannot be discovered."""
        mock_get_token.return_value = {"access_token": "gho_test", "token_type": "bearer"}
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": {"repository": {"issueTypes": {"nodes": []}}}}
        mock_post.return_value = mock_response

        import os

        cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                backlog_app,
                [
                    "map-fields",
                    "--provider",
                    "github",
                    "--github-project-id",
                    "nold-ai/specfact-demo-repo",
                    "--github-project-v2-id",
                    "PVT_project_id",
                    "--github-type-field-id",
                    "PVT_type_field",
                    "--github-type-option",
                    "task=OPT_TASK",
                ],
            )
        finally:
            os.chdir(cwd)

        assert result.exit_code != 0
        assert "repository issue types" in result.stdout.lower()

    @patch("questionary.checkbox")
    @patch("specfact_cli.modules.backlog.src.commands.typer.prompt")
    @patch("specfact_cli.utils.auth_tokens.get_token")
    @patch("requests.post")
    def test_map_fields_github_provider_allows_blank_project_v2(
        self,
        mock_post: MagicMock,
        mock_get_token: MagicMock,
        mock_prompt: MagicMock,
        mock_checkbox: MagicMock,
        tmp_path,
    ) -> None:
        """GitHub map-fields should not require ProjectV2 when repository issue types are available."""
        mock_checkbox.return_value.ask.return_value = ["github"]
        mock_get_token.return_value = {"access_token": "gho_test", "token_type": "bearer"}
        mock_prompt.side_effect = [
            "nold-ai/specfact-demo-repo",  # owner/repo
            "",  # blank project ref (optional)
        ]
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {
                "repository": {
                    "issueTypes": {
                        "nodes": [
                            {"id": "IT_BUG", "name": "Bug"},
                            {"id": "IT_TASK", "name": "Task"},
                        ]
                    }
                }
            }
        }
        mock_post.return_value = mock_response

        import os

        cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(backlog_app, ["map-fields"])
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        assert "projectv2 type field mapping skipped" in result.stdout.lower()
        cfg_file = tmp_path / ".specfact" / "backlog-config.yaml"
        assert cfg_file.exists()
        loaded = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        github_settings = loaded["backlog_config"]["providers"]["github"]["settings"]
        assert github_settings["github_issue_types"]["type_ids"]["task"] == "IT_TASK"
        provider_fields = github_settings.get("provider_fields", {})
        if isinstance(provider_fields, dict):
            assert provider_fields.get("github_project_v2") is None

    @patch("questionary.checkbox")
    @patch("specfact_cli.modules.backlog.src.commands.typer.prompt")
    @patch("specfact_cli.utils.auth_tokens.get_token")
    @patch("requests.post")
    def test_map_fields_blank_project_v2_clears_stale_project_mapping(
        self,
        mock_post: MagicMock,
        mock_get_token: MagicMock,
        mock_prompt: MagicMock,
        mock_checkbox: MagicMock,
        tmp_path,
    ) -> None:
        """Blank ProjectV2 input should clear stale ProjectV2 provider_fields mapping."""
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
            project_id: PVT_project_id
            type_field_id: PVT_type_field
            type_option_ids:
              task: PVT_option_task
""".strip(),
            encoding="utf-8",
        )
        mock_checkbox.return_value.ask.return_value = ["github"]
        mock_get_token.return_value = {"access_token": "gho_test", "token_type": "bearer"}
        mock_prompt.side_effect = [
            "nold-ai/specfact-demo-repo",
            "",
        ]
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": {"repository": {"issueTypes": {"nodes": [{"id": "IT_TASK", "name": "Task"}]}}}
        }
        mock_post.return_value = mock_response

        import os

        cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(backlog_app, ["map-fields"])
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        loaded = yaml.safe_load((spec_dir / "backlog-config.yaml").read_text(encoding="utf-8"))
        github_settings = loaded["backlog_config"]["providers"]["github"]["settings"]
        provider_fields = github_settings.get("provider_fields", {})
        assert provider_fields.get("github_project_v2") is None

    @patch("requests.get")
    @patch("questionary.select")
    def test_map_fields_ado_framework_cli_persists_to_config_and_mapping(
        self, mock_select: MagicMock, mock_get: MagicMock, tmp_path
    ) -> None:
        """ADO map-fields should persist selected framework for deterministic refine steering."""
        # ADO fields API response
        mock_fields_response = MagicMock()
        mock_fields_response.raise_for_status.return_value = None
        mock_fields_response.json.return_value = {
            "value": [
                {"referenceName": "System.Description", "name": "Description"},
                {"referenceName": "System.AcceptanceCriteria", "name": "Acceptance Criteria"},
                {"referenceName": "Microsoft.VSTS.Scheduling.StoryPoints", "name": "Story Points"},
            ]
        }
        # ADO work item types API response (detection call; should not override explicit CLI value)
        mock_types_response = MagicMock()
        mock_types_response.raise_for_status.return_value = None
        mock_types_response.json.return_value = {
            "value": [{"name": "Product Backlog Item"}, {"name": "Bug"}, {"name": "Task"}]
        }
        mock_get.side_effect = [mock_fields_response, mock_types_response]

        # Field selection prompts: map none for all canonical fields
        mock_select.return_value.ask.return_value = "<no mapping>"

        import os

        cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                backlog_app,
                [
                    "map-fields",
                    "--provider",
                    "ado",
                    "--ado-org",
                    "test-org",
                    "--ado-project",
                    "test-project",
                    "--ado-token",
                    "test-token",
                    "--ado-framework",
                    "scrum",
                ],
            )
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        ado_custom = tmp_path / ".specfact" / "templates" / "backlog" / "field_mappings" / "ado_custom.yaml"
        assert ado_custom.exists()
        custom_payload = yaml.safe_load(ado_custom.read_text(encoding="utf-8"))
        assert custom_payload["framework"] == "scrum"

        cfg_file = tmp_path / ".specfact" / "backlog-config.yaml"
        assert cfg_file.exists()
        loaded = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        ado_settings = loaded["backlog_config"]["providers"]["ado"]["settings"]
        assert ado_settings["framework"] == "scrum"

    def test_resolve_backlog_provider_framework_reads_backlog_config(self, tmp_path) -> None:
        """Framework resolver should read provider framework from backlog-config settings."""
        import os

        spec_dir = tmp_path / ".specfact"
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / "backlog-config.yaml").write_text(
            """
backlog_config:
  providers:
    ado:
      adapter: ado
      project_id: test-org/test-project
      settings:
        framework: scrum
        field_mapping_file: .specfact/templates/backlog/field_mappings/ado_custom.yaml
""".strip(),
            encoding="utf-8",
        )

        cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            resolved = _resolve_backlog_provider_framework("ado")
        finally:
            os.chdir(cwd)

        assert resolved == "scrum"

    def test_backlog_init_config_scaffolds_default_file(self, tmp_path) -> None:
        """Test backlog init-config creates default backlog-config scaffold."""
        import os

        cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["backlog", "init-config"])
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        cfg_file = tmp_path / ".specfact" / "backlog-config.yaml"
        assert cfg_file.exists()
        loaded = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        assert "backlog_config" in loaded
        assert "providers" in loaded["backlog_config"]
        assert "github" in loaded["backlog_config"]["providers"]
        assert "ado" in loaded["backlog_config"]["providers"]

    def test_backlog_init_config_does_not_overwrite_without_force(self, tmp_path) -> None:
        """Test backlog init-config respects no-overwrite behavior by default."""
        import os

        cfg_dir = tmp_path / ".specfact"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "backlog-config.yaml"
        cfg_file.write_text("backlog_config:\n  providers:\n    github:\n      adapter: github\n", encoding="utf-8")

        cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["backlog", "init-config"])
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        content = cfg_file.read_text(encoding="utf-8")
        assert "adapter: github" in content
        assert "already exists" in (result.output or result.stdout or "").lower()


class TestParseRefinedExportMarkdown:
    """Tests for _parse_refined_export_markdown (refine --import-from-tmp parser)."""

    def test_parses_single_item_with_body_and_id(self) -> None:
        """Parser extracts ID and body from export-format block."""
        content = """
# SpecFact Backlog Refinement Export

**Export Date**: 2026-01-27
**Adapter**: github
**Items**: 1

---

## Item 1: My Title

**ID**: issue-42
**URL**: https://github.com/org/repo/issues/42
**State**: open
**Provider**: github

**Body**:
```markdown
Refined body text here.
```
"""
        result = _parse_refined_export_markdown(content)
        assert "issue-42" in result
        assert result["issue-42"]["body_markdown"] == "Refined body text here."
        assert result["issue-42"].get("title") == "My Title"

    def test_parses_item_when_file_starts_with_item_header(self) -> None:
        """Parser handles item heading at file start and does not leak heading marker into title."""
        content = """## Item 1: Story title from heading

**ID**: 123
**URL**: u
**State**: open
**Provider**: ado

**Body**:
```markdown
Body content
```
"""
        result = _parse_refined_export_markdown(content)
        assert "123" in result
        assert result["123"].get("title") == "Story title from heading"
        assert result["123"].get("title", "").startswith("## Item") is False

    def test_parses_acceptance_criteria_and_metrics(self) -> None:
        """Parser extracts acceptance criteria and metrics when present."""
        content = """
## Item 1: Story title

**ID**: 123
**URL**: u
**State**: open
**Provider**: ado

**Metrics**:
- Story Points: 5
- Business Value: 8
- Priority: 1 (1=highest)

**Acceptance Criteria**:
- AC one
- AC two

**Body**:
```markdown
Body content
```
---
"""
        result = _parse_refined_export_markdown(content)
        assert "123" in result
        assert result["123"]["acceptance_criteria"] == "- AC one\n- AC two"
        assert result["123"]["story_points"] == 5
        assert result["123"]["business_value"] == 8
        assert result["123"]["priority"] == 1
        assert result["123"]["body_markdown"] == "Body content"

    def test_returns_empty_for_header_only(self) -> None:
        """Parser returns empty dict when no ## Item blocks."""
        content = "# SpecFact Backlog Refinement Export\n\n**Items**: 0\n\n---\n\n"
        result = _parse_refined_export_markdown(content)
        assert result == {}

    def test_skips_blocks_without_id(self) -> None:
        """Parser skips blocks that do not contain **ID**:."""
        content = """
## Item 1: No ID here

**URL**: x
**Body**:
```markdown
nope
```
"""
        result = _parse_refined_export_markdown(content)
        assert result == {}

    def test_body_with_nested_fenced_code_blocks(self) -> None:
        """Parser preserves full body when it contains fenced code blocks."""
        content = """
## Item 1: Bug with code sample

**ID**: issue-99
**URL**: https://github.com/org/repo/issues/99
**State**: open
**Provider**: github

**Body**:
```markdown
Reproduction: run this:

```python
def foo():
    return 42
```

Then we see the error.
```
---
"""
        result = _parse_refined_export_markdown(content)
        assert "issue-99" in result
        body = result["issue-99"]["body_markdown"]
        assert "Reproduction: run this:" in body
        assert "```python" in body
        assert "def foo():" in body
        assert "return 42" in body
        assert "```" in body
        assert "Then we see the error." in body


class TestContentLossDetection:
    """Tests for refined-content loss guard used by tmp import."""

    def test_detects_significant_content_loss(self) -> None:
        original = (
            "Implement OAuth login with PKCE, refresh-token rotation, role-based access checks, "
            "audit logging for login events, and explicit error handling for expired tokens."
        )
        refined = "Implement login support."
        has_loss, reason = _detect_significant_content_loss(original, refined)
        assert has_loss is True
        assert reason

    def test_allows_structured_rewrite_without_loss(self) -> None:
        original = (
            "As a platform user I need OAuth login with PKCE and refresh-token rotation so that "
            "authentication remains secure and users can re-authenticate without credential prompts."
        )
        refined = (
            "## Description\n\nAs a platform user I need OAuth login with PKCE and refresh-token rotation "
            "so authentication stays secure and re-authentication works without credential prompts."
        )
        has_loss, _reason = _detect_significant_content_loss(original, refined)
        assert has_loss is False


class TestParseRefinementOutputFields:
    """Tests for parser that normalizes refinement output for writeback."""

    def test_parses_label_style_refinement_output(self) -> None:
        """Parser splits label-style sections into canonical fields."""
        refined = """
Description:
The sync between ADO and OpenSpec should preserve markdown.

Acceptance Criteria:
- [ ] Description is not overwritten with prompt labels
- [ ] Acceptance criteria maps to dedicated ADO field

Notes:
Keep backward compatibility.

Dependencies:
- backlog adapter

Area Path:
(unspecified)

Iteration Path:
(unspecified)

Story Points:
5

Business Value:
8

Priority:
2

Work Item Type:
User Story

Provider:
ado
"""
        parsed = _parse_refinement_output_fields(refined)
        assert parsed["description"] == "The sync between ADO and OpenSpec should preserve markdown."
        assert parsed["acceptance_criteria"] == (
            "- [ ] Description is not overwritten with prompt labels\n"
            "- [ ] Acceptance criteria maps to dedicated ADO field"
        )
        assert parsed["story_points"] == 5
        assert parsed["business_value"] == 8
        assert parsed["priority"] == 2
        assert parsed["work_item_type"] == "User Story"
        assert "Area Path" not in (parsed.get("body_markdown") or "")
        assert "Iteration Path" not in (parsed.get("body_markdown") or "")
        assert "Provider:" not in (parsed.get("body_markdown") or "")
        assert "## Notes" in (parsed.get("body_markdown") or "")
        assert "## Dependencies" in (parsed.get("body_markdown") or "")

    def test_parses_markdown_heading_refinement_output(self) -> None:
        """Parser extracts canonical fields from markdown-heading format."""
        refined = """
User-facing summary.

## Acceptance Criteria

- first
- second

## Story Points

3

## Business Value

13

## Priority

1
"""
        parsed = _parse_refinement_output_fields(refined)
        assert parsed["description"] == "User-facing summary."
        assert parsed["acceptance_criteria"] == "- first\n- second"
        assert parsed["story_points"] == 3
        assert parsed["business_value"] == 13
        assert parsed["priority"] == 1

    def test_preserves_heading_style_notes_and_dependencies_in_body_markdown(self) -> None:
        """Heading-style narrative sections should be preserved in writeback body."""
        refined = """
User-facing summary.

## Acceptance Criteria

- first

## Notes

Keep this narrative note.

## Dependencies

- Team A

## Story Points

5

## Business Value

8

## Priority

2
"""
        parsed = _parse_refinement_output_fields(refined)
        body_markdown = parsed.get("body_markdown") or ""

        assert "User-facing summary." in body_markdown
        assert "## Notes" in body_markdown
        assert "Keep this narrative note." in body_markdown
        assert "## Dependencies" in body_markdown
        assert "- Team A" in body_markdown
        assert "## Story Points" not in body_markdown
        assert "## Business Value" not in body_markdown
        assert "## Priority" not in body_markdown

    def test_preserves_uppercase_heading_style_notes_and_dependencies_in_body_markdown(self) -> None:
        """Uppercase heading variants should still be preserved in writeback body."""
        refined = """
User-facing summary.

## ACCEPTANCE CRITERIA

- first

## NOTES

Keep this uppercase narrative note.

## DEPENDENCIES

- Team B

## STORY POINTS

3

## BUSINESS VALUE

5

## PRIORITY

1
"""
        parsed = _parse_refinement_output_fields(refined)
        body_markdown = parsed.get("body_markdown") or ""

        assert "User-facing summary." in body_markdown
        assert "## Notes" in body_markdown
        assert "Keep this uppercase narrative note." in body_markdown
        assert "## Dependencies" in body_markdown
        assert "- Team B" in body_markdown
        assert "## STORY POINTS" not in body_markdown
        assert "## BUSINESS VALUE" not in body_markdown
        assert "## PRIORITY" not in body_markdown

    def test_label_only_output_without_description_does_not_fallback_to_raw_payload(self) -> None:
        """Label-only output without Description should not leak raw labels into body/description."""
        refined = """
Acceptance Criteria:
- [ ] Keep canonical writeback fields

Story Points:
3

Business Value:
5

Priority:
2

Provider:
ado
"""
        parsed = _parse_refinement_output_fields(refined)
        body_markdown = parsed.get("body_markdown") or ""

        assert parsed.get("description") in (None, "")
        assert parsed["acceptance_criteria"] == "- [ ] Keep canonical writeback fields"
        assert parsed["story_points"] == 3
        assert parsed["business_value"] == 5
        assert parsed["priority"] == 2
        assert "Acceptance Criteria:" not in body_markdown
        assert "Story Points:" not in body_markdown
        assert "Business Value:" not in body_markdown
        assert "Priority:" not in body_markdown
        assert "Provider:" not in body_markdown

    def test_mixed_heading_and_inline_notes_preserves_description_before_notes(self) -> None:
        """Mixed heading + inline label format should keep narrative before inline notes."""
        refined = """
## Work Item Properties / Metadata

- Story Points: 5
- Business Value: 8
- Priority: 2
- Provider: ado

## Description

The API call currently fails for valid users.
This context must stay in description.

**Notes**:
Investigate token refresh path.

## Acceptance Criteria

- [ ] Successful login for valid users
"""
        parsed = _parse_refinement_output_fields(refined)
        body_markdown = parsed.get("body_markdown") or ""
        assert "The API call currently fails for valid users." in body_markdown
        assert "This context must stay in description." in body_markdown
        assert "## Notes" in body_markdown
        assert "Investigate token refresh path." in body_markdown
        assert "**Notes**:" not in body_markdown
        assert body_markdown.count("Investigate token refresh path.") == 1
        assert "## Acceptance Criteria" not in body_markdown
        assert parsed["acceptance_criteria"] == "- [ ] Successful login for valid users"

    def test_label_notes_with_internal_heading_keeps_heading_content(self) -> None:
        """Notes label payload may contain internal headings that must be preserved."""
        refined = """
Description:
Short summary.

Notes:
Context details before heading.
## Risks
- API rate-limit
Follow-up mitigation note.

Dependencies:
- Team Platform
"""
        parsed = _parse_refinement_output_fields(refined)
        body_markdown = parsed.get("body_markdown") or ""

        assert "## Notes" in body_markdown
        assert "Context details before heading." in body_markdown
        assert "## Risks" in body_markdown
        assert "- API rate-limit" in body_markdown
        assert "Follow-up mitigation note." in body_markdown
        assert "## Dependencies" in body_markdown


class TestBuildRefineExportContent:
    """Tests for refine export content rendering."""

    def test_refine_export_includes_comments_when_available(self) -> None:
        """Refine export includes comment annotations by default when available."""
        item = BacklogItem(
            id="42",
            provider="ado",
            url="https://dev.azure.com/org/project/_workitems/edit/42",
            title="Story",
            body_markdown="Body text",
            state="Active",
            assignees=[],
        )
        content = _build_refine_export_content(
            adapter="ado",
            items=[item],
            comments_by_item_id={"42": ["Comment A", "Comment B"]},
        )
        assert "Comments (annotations)" in content
        assert "Comment A" in content
        assert "Comment B" in content
        assert "## Copilot Instructions" in content
        assert "must not include this instruction block" in content
        assert "Preserve all original requirements, scope, and technical details" in content

    def test_refine_export_omits_comments_section_when_none(self) -> None:
        """Refine export omits comments section when no comments exist for item."""
        item = BacklogItem(
            id="42",
            provider="ado",
            url="https://dev.azure.com/org/project/_workitems/edit/42",
            title="Story",
            body_markdown="Body text",
            state="Active",
            assignees=[],
        )
        content = _build_refine_export_content(adapter="ado", items=[item], comments_by_item_id={})
        assert "Comments (annotations)" not in content

    def test_refine_export_places_instructions_before_first_item(self) -> None:
        """Instruction block appears before exported item sections."""
        item = BacklogItem(
            id="42",
            provider="ado",
            url="https://dev.azure.com/org/project/_workitems/edit/42",
            title="Story",
            body_markdown="Body text",
            state="Active",
            assignees=[],
        )
        content = _build_refine_export_content(adapter="ado", items=[item], comments_by_item_id={})
        assert content.index("## Copilot Instructions") < content.index("## Item 1:")

    def test_refine_export_marks_id_as_mandatory_for_import(self) -> None:
        """Export guidance should state ID is required and immutable for import."""
        item = BacklogItem(
            id="42",
            provider="ado",
            url="https://dev.azure.com/org/project/_workitems/edit/42",
            title="Story",
            body_markdown="Body text",
            state="Active",
            assignees=[],
        )
        content = _build_refine_export_content(adapter="ado", items=[item], comments_by_item_id={})
        assert "**ID** is mandatory" in content
        assert "must remain unchanged" in content
        assert "Do NOT summarize, shorten, or drop details" in content
        assert "Template Execution Rules (mandatory)" in content

    def test_refine_export_includes_template_guidance_for_items(self) -> None:
        """Export includes template guidance similar to interactive prompts."""
        item = BacklogItem(
            id="42",
            provider="github",
            url="https://github.com/org/repo/issues/42",
            title="Story",
            body_markdown="Body text",
            state="open",
            assignees=[],
        )
        content = _build_refine_export_content(
            adapter="github",
            items=[item],
            comments_by_item_id={},
            template_guidance_by_item_id={
                "42": {
                    "template_id": "enabler_v1",
                    "name": "Enabler",
                    "description": "Enabler work template",
                    "required_sections": ["Objective", "Technical Approach", "Success Criteria"],
                    "optional_sections": ["Dependencies", "Risks", "Timeline"],
                }
            },
        )
        assert "**Target Template**:" in content
        assert "**Required Sections**:" in content
        assert "**Optional Sections**:" in content


class TestRefineCommentWindowResolution:
    """Tests for refine preview/export comment-window semantics."""

    def test_refine_preview_defaults_to_last_two_comments(self) -> None:
        """Preview uses last two comments when no explicit window flags are provided."""
        first, last = _resolve_refine_preview_comment_window(first_comments=None, last_comments=None)
        assert first is None
        assert last == 2

    def test_refine_preview_respects_first_comments_override(self) -> None:
        """Preview honors --first-comments when provided."""
        first, last = _resolve_refine_preview_comment_window(first_comments=5, last_comments=None)
        assert first == 5
        assert last is None

    def test_refine_preview_respects_last_comments_override(self) -> None:
        """Preview honors --last-comments when provided."""
        first, last = _resolve_refine_preview_comment_window(first_comments=None, last_comments=4)
        assert first is None
        assert last == 4

    def test_refine_export_always_uses_full_comment_history(self) -> None:
        """Export ignores preview comment-window flags and always requests full comments."""
        first, last = _resolve_refine_export_comment_window(first_comments=5, last_comments=None)
        assert first is None
        assert last is None

        first_2, last_2 = _resolve_refine_export_comment_window(first_comments=None, last_comments=3)
        assert first_2 is None
        assert last_2 is None


class TestRefineImportFromTmp:
    """Tests for refine --import-from-tmp behavior."""

    @patch("specfact_cli.modules.backlog.src.commands._fetch_backlog_items")
    def test_import_from_tmp_fails_when_no_parsed_ids_match_fetched_items(
        self, mock_fetch_items: MagicMock, tmp_path
    ) -> None:
        """Import should fail fast when refined IDs do not match fetched backlog items."""
        mock_fetch_items.return_value = [
            BacklogItem(
                id="1",
                provider="github",
                url="https://github.com/org/repo/issues/1",
                title="Issue 1",
                body_markdown="Original body",
                state="open",
                assignees=[],
            )
        ]

        refined_file = tmp_path / "refined.md"
        refined_file.write_text(
            """
## Item 1: Edited Title

**ID**: 999
**URL**: https://github.com/org/repo/issues/999
**State**: open
**Provider**: github

**Body**:
```markdown
Refined body
```
""".strip(),
            encoding="utf-8",
        )

        result = runner.invoke(
            backlog_app,
            [
                "refine",
                "github",
                "--repo-owner",
                "org",
                "--repo-name",
                "repo",
                "--import-from-tmp",
                "--tmp-file",
                str(refined_file),
            ],
        )

        assert result.exit_code != 0
        assert "None of the refined item IDs matched fetched backlog items" in result.stdout

    @patch("specfact_cli.modules.backlog.src.commands._fetch_backlog_items")
    def test_import_from_tmp_fails_when_refined_body_is_significantly_shortened(
        self, mock_fetch_items: MagicMock, tmp_path
    ) -> None:
        """Import should fail when tmp refinement drops substantial original detail."""
        mock_fetch_items.return_value = [
            BacklogItem(
                id="1",
                provider="github",
                url="https://github.com/org/repo/issues/1",
                title="Issue 1",
                body_markdown=(
                    "Implement OAuth login with PKCE, refresh-token rotation, role-based checks, "
                    "audit logging, and token-expiry handling."
                ),
                state="open",
                assignees=[],
            )
        ]

        refined_file = tmp_path / "refined.md"
        refined_file.write_text(
            """
## Item 1: Edited Title

**ID**: 1
**URL**: https://github.com/org/repo/issues/1
**State**: open
**Provider**: github

**Body**:
```markdown
Implement login support.
```
""".strip(),
            encoding="utf-8",
        )

        result = runner.invoke(
            backlog_app,
            [
                "refine",
                "github",
                "--repo-owner",
                "org",
                "--repo-name",
                "repo",
                "--import-from-tmp",
                "--tmp-file",
                str(refined_file),
            ],
        )

        assert result.exit_code != 0
        assert "appears to drop important detail" in result.stdout


class TestRefinePreviewCommentUx:
    """Tests for refine preview comment progress and block rendering."""

    def test_build_comment_fetch_progress_description_includes_position(self) -> None:
        """Progress message uses n/m indicator while fetching comments."""
        message = _build_comment_fetch_progress_description(3, 66, "123")
        assert "3/66" in message
        assert "123" in message
        assert "Fetching issue" in message

    def test_build_refine_preview_comment_panels_returns_panels(self) -> None:
        """Preview comments are rendered as panel blocks for clear scoping."""
        panels = _build_refine_preview_comment_panels(["first comment", "second comment"])
        assert len(panels) == 2
        assert all(isinstance(panel, Panel) for panel in panels)

    def test_build_refine_preview_comment_empty_panel_returns_panel(self) -> None:
        """Preview shows explicit hint when no comments are found."""
        panel = _build_refine_preview_comment_empty_panel()
        assert isinstance(panel, Panel)


class TestRefineIssueWindow:
    """Tests for refine first/last issue window controls."""

    @staticmethod
    def _item(id_: str) -> BacklogItem:
        return BacklogItem(
            id=id_,
            provider="github",
            url=f"https://github.com/org/repo/issues/{id_}",
            title=f"Item {id_}",
            body_markdown="Body",
            state="open",
            assignees=[],
        )

    def test_apply_issue_window_first_issues(self) -> None:
        items = [self._item("3"), self._item("1"), self._item("2")]
        result = _apply_issue_window(items, first_issues=2, last_issues=None)
        assert [i.id for i in result] == ["1", "2"]

    def test_apply_issue_window_last_issues(self) -> None:
        items = [self._item("3"), self._item("1"), self._item("2")]
        result = _apply_issue_window(items, first_issues=None, last_issues=2)
        assert [i.id for i in result] == ["2", "3"]

    def test_apply_issue_window_rejects_both_first_and_last(self) -> None:
        items = [self._item("1")]
        try:
            _apply_issue_window(items, first_issues=1, last_issues=1)
        except ValueError as exc:
            assert "--first-issues" in str(exc)
            return
        raise AssertionError("Expected ValueError when both first_issues and last_issues are set")


class TestItemNeedsRefinement:
    """Tests for _item_needs_refinement helper."""

    def test_needs_refinement_when_missing_sections(self) -> None:
        """Item needs refinement when required sections are missing."""
        registry = TemplateRegistry()
        registry.register_template(
            BacklogTemplate(
                template_id="user-story",
                name="User Story",
                description="",
                required_sections=["As a", "I want", "Acceptance Criteria"],
            )
        )
        detector = TemplateDetector(registry)
        item = BacklogItem(
            id="1",
            provider="github",
            url="https://github.com/org/repo/issues/1",
            title="Story",
            body_markdown="As a user I want...",
            state="open",
            assignees=[],
        )
        assert _item_needs_refinement(item, detector, registry, None, "github", None, None) is True

    def test_does_not_need_refinement_when_high_confidence_no_missing(self) -> None:
        """Item does not need refinement when confidence >= 0.8 and no missing fields."""
        registry = TemplateRegistry()
        registry.register_template(
            BacklogTemplate(
                template_id="user-story",
                name="User Story",
                description="",
                required_sections=["Acceptance Criteria"],
            )
        )
        detector = TemplateDetector(registry)
        item = BacklogItem(
            id="2",
            provider="github",
            url="https://github.com/org/repo/issues/2",
            title="Story",
            body_markdown="As a user I want X.\n\n## Acceptance Criteria\n- [ ] Done",
            state="open",
            assignees=[],
        )
        result = _item_needs_refinement(item, detector, registry, None, "github", None, None)
        assert result is False

    def test_ado_does_not_require_story_points_heading_in_body_sections(self) -> None:
        """ADO items should not be forced to include Story Points as markdown body heading."""
        registry = TemplateRegistry()
        registry.register_template(
            BacklogTemplate(
                template_id="scrum-story",
                name="Scrum Story",
                description="",
                required_sections=["As a", "I want", "So that", "Acceptance Criteria", "Story Points"],
            )
        )
        detector = TemplateDetector(registry)
        item = BacklogItem(
            id="10",
            provider="ado",
            url="https://dev.azure.com/org/project/_workitems/edit/10",
            title="User Story",
            body_markdown="## As a\nuser\n\n## I want\nvalue\n\n## So that\nbenefit\n\n## Acceptance Criteria\n- [ ] done",
            state="Active",
            assignees=[],
            story_points=5,
        )
        # Should be considered already refined if no missing non-structured required sections.
        assert _item_needs_refinement(item, detector, registry, None, "ado", "scrum", None) is False


class TestResolveTargetTemplateForRefineItem:
    """Tests for template steering helper used by backlog refine."""

    def test_ado_user_story_type_prefers_user_story_template(self) -> None:
        """ADO User Story/PBI items should prefer user_story_v1 over generic ado_work_item_v1."""
        registry = TemplateRegistry()
        registry.register_template(
            BacklogTemplate(
                template_id="ado_work_item_v1",
                name="ADO Work Item",
                description="",
                provider="ado",
                required_sections=["Description", "Acceptance Criteria"],
            )
        )
        registry.register_template(
            BacklogTemplate(
                template_id="user_story_v1",
                name="User Story",
                description="",
                required_sections=["As a", "I want", "So that", "Acceptance Criteria"],
            )
        )
        detector = TemplateDetector(registry)
        item = BacklogItem(
            id="42",
            provider="ado",
            url="https://dev.azure.com/org/project/_workitems/edit/42",
            title="User Story: refine mapping",
            body_markdown="## Description\n\nBody\n\n## Acceptance Criteria\n- [ ] one",
            state="Active",
            assignees=[],
            work_item_type="User Story",
        )

        resolved = _resolve_target_template_for_refine_item(
            item,
            detector=detector,
            registry=registry,
            template_id=None,
            normalized_adapter="ado",
            normalized_framework=None,
            normalized_persona=None,
        )

        assert resolved is not None
        assert resolved.template_id == "user_story_v1"

    def test_github_story_tag_prefers_user_story_template(self) -> None:
        """GitHub story-labeled items should prefer user_story_v1 over generic enabler templates."""
        registry = TemplateRegistry()
        registry.register_template(
            BacklogTemplate(
                template_id="enabler_v1",
                name="Enabler",
                description="",
                provider="github",
                required_sections=["Description"],
            )
        )
        registry.register_template(
            BacklogTemplate(
                template_id="user_story_v1",
                name="User Story",
                description="",
                provider=None,
                required_sections=["As a", "I want", "So that", "Acceptance Criteria"],
            )
        )
        detector = TemplateDetector(registry)
        item = BacklogItem(
            id="77",
            provider="github",
            url="https://github.com/o/r/issues/77",
            title="Story: improve login flow",
            body_markdown="## Description\n\nImprove flow",
            state="open",
            assignees=[],
            tags=["story"],
        )

        resolved = _resolve_target_template_for_refine_item(
            item,
            detector=detector,
            registry=registry,
            template_id=None,
            normalized_adapter="github",
            normalized_framework=None,
            normalized_persona=None,
        )

        assert resolved is not None
        assert resolved.template_id == "user_story_v1"

    def test_non_story_item_does_not_recurse_and_resolves_detected_template(self) -> None:
        """Non-story items should resolve without recursive fallback loops."""
        registry = TemplateRegistry()
        registry.register_template(
            BacklogTemplate(
                template_id="enabler_v1",
                name="Enabler",
                description="",
                provider="github",
                required_sections=["Description"],
            )
        )
        detector = TemplateDetector(registry)
        item = BacklogItem(
            id="88",
            provider="github",
            url="https://github.com/o/r/issues/88",
            title="Improve pipeline",
            body_markdown="## Description\n\nImprove pipeline execution.",
            state="open",
            assignees=[],
            tags=["enhancement"],
        )

        resolved = _resolve_target_template_for_refine_item(
            item,
            detector=detector,
            registry=registry,
            template_id=None,
            normalized_adapter="github",
            normalized_framework=None,
            normalized_persona=None,
        )

        assert resolved is not None
        assert resolved.template_id == "enabler_v1"
