"""
Integration tests for multi-adapter backlog sync workflows.

These tests simulate GitHub ↔ OpenSpec ↔ ADO round-trips to ensure
no information loss, no duplication, and stable content formatting.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from beartype import beartype

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.change import ChangeTracking
from specfact_cli.sync.bridge_sync import BridgeSync


def _normalize_body(body: str) -> list[str]:
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    return [line.rstrip() for line in normalized.strip().split("\n")]


def _write_openspec_proposal(repo_path: Path, change_id: str, title: str, rationale: str, description: str) -> None:
    proposal_dir = repo_path / "openspec" / "changes" / change_id
    proposal_dir.mkdir(parents=True, exist_ok=True)
    proposal_file = proposal_dir / "proposal.md"
    proposal_file.write_text(
        f"# Change: {title}\n\n## Why\n\n{rationale}\n\n## What Changes\n\n{description}\n",
        encoding="utf-8",
    )


class TestMultiAdapterBacklogSync:
    """Integration tests for multi-adapter backlog sync."""

    @beartype
    @patch("specfact_cli.adapters.github.requests.post")
    @patch("specfact_cli.adapters.ado.requests.get")
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_github_to_ado_round_trip_preserves_content(
        self,
        mock_ado_patch: MagicMock,
        mock_ado_get: MagicMock,
        mock_gh_post: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test GitHub → OpenSpec → ADO → OpenSpec → GitHub round-trip keeps content stable."""
        change_id = "device-code-auth"
        title = "feat: Device Code Authentication"
        rationale = (
            "### Current Limitation\n"
            "SpecFact CLI requires PATs, which bypass MFA and complicate onboarding.\n\n"
            "---\n\n"
            "### Business Value\n"
            "- Improves UX for SSO orgs\n"
            "- Aligns with az/gh CLI device code flows"
        )
        description = (
            "### Architecture Overview\n"
            "Add RFC 8628 device code flow for GitHub and Azure DevOps.\n\n"
            "---\n\n"
            "## Acceptance Criteria\n"
            "- [ ] Device code prompt displays\n"
            "- [ ] Tokens stored with 0o600\n\n"
            "### Token Storage & Management\n"
            "Tokens stored at ~/.specfact/tokens.json with 0o600 permissions."
        )

        repo_path = tmp_path / "repo"
        repo_path.mkdir(parents=True, exist_ok=True)
        _write_openspec_proposal(repo_path, change_id, title, rationale, description)

        sync = BridgeSync(repo_path, bridge_config=BridgeConfig.preset_openspec())

        # Export OpenSpec proposal to GitHub (create issue)
        gh_post_response = MagicMock()
        gh_post_response.json.return_value = {
            "number": 101,
            "html_url": "https://github.com/test-org/test-repo/issues/101",
            "state": "open",
        }
        gh_post_response.raise_for_status = MagicMock()
        mock_gh_post.return_value = gh_post_response

        gh_result = sync.export_change_proposals_to_devops(
            adapter_type="github",
            repo_owner="test-org",
            repo_name="test-repo",
            api_token="test-token",
            use_gh_cli=False,
        )

        assert gh_result.success is True
        gh_payload = mock_gh_post.call_args[1]["json"]
        github_body_initial = gh_payload["body"]
        github_issue_number = str(gh_post_response.json.return_value["number"])
        github_issue_url = gh_post_response.json.return_value["html_url"]

        # Export OpenSpec proposal to ADO (create work item)
        ado_get_response = MagicMock()
        ado_get_response.json.return_value = {
            "processTemplate": {"templateTypeId": "adcc42ab-9882-485e-a3e4-38fb9b8c5e4e"},
        }
        ado_get_response.raise_for_status = MagicMock()
        mock_ado_get.return_value = ado_get_response

        ado_patch_response = MagicMock()
        ado_patch_response.json.return_value = {
            "id": 202,
            "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/202"}},
        }
        ado_patch_response.raise_for_status = MagicMock()
        mock_ado_patch.return_value = ado_patch_response

        ado_result = sync.export_change_proposals_to_devops(
            adapter_type="ado",
            api_token="ado-token",
            ado_org="test-org",
            ado_project="test-project",
            ado_work_item_type="User Story",
        )
        assert ado_result.success is True

        patch_document = mock_ado_patch.call_args[1]["json"]
        description_op = next(op for op in patch_document if op.get("path") == "/fields/System.Description")
        ado_description_html = description_op["value"]

        # Import ADO work item back to OpenSpec proposal
        ado_adapter = AdoAdapter(org="test-org", project="test-project", api_token="ado-token")
        project_bundle = MagicMock()
        project_bundle.change_tracking = ChangeTracking()
        project_bundle.bundle_dir = repo_path

        work_item_data = {
            "id": 202,
            "fields": {
                "System.Title": title,
                "System.Description": ado_description_html,
                "System.State": "New",
                "System.CreatedDate": "2025-01-01T10:00:00Z",
                "System.WorkItemType": "User Story",
            },
            "_links": {
                "html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/202"},
            },
        }

        ado_adapter.import_artifact(
            artifact_key="ado_work_item",
            artifact_path=work_item_data,
            project_bundle=project_bundle,
        )

        imported_key = change_id
        if imported_key not in project_bundle.change_tracking.proposals:
            imported_key = "202"

        imported_proposal = project_bundle.change_tracking.proposals[imported_key]

        existing = next(
            proposal
            for proposal in sync._read_openspec_change_proposals(include_archived=False)
            if proposal.get("change_id") == change_id
        )
        source_tracking_list = sync._normalize_source_tracking(existing.get("source_tracking", {}))
        github_entry = {
            "source_id": github_issue_number,
            "source_url": github_issue_url,
            "source_type": "github",
            "source_repo": "test-org/test-repo",
            "source_metadata": {"last_synced_status": imported_proposal.status},
        }
        source_tracking_list = sync._update_source_tracking_entry(
            source_tracking_list,
            "test-org/test-repo",
            github_entry,
        )
        ado_entry = {
            "source_id": "202",
            "source_url": "https://dev.azure.com/test-org/test-project/_workitems/edit/202",
            "source_type": "ado",
            "source_repo": "test-org/test-project",
            "source_metadata": {"last_synced_status": imported_proposal.status},
        }
        source_tracking_list = sync._update_source_tracking_entry(
            source_tracking_list,
            "test-org/test-project",
            ado_entry,
        )

        sync._save_openspec_change_proposal(
            {
                "change_id": imported_proposal.name,
                "title": imported_proposal.title,
                "description": imported_proposal.description,
                "rationale": imported_proposal.rationale,
                "status": imported_proposal.status,
                "source_tracking": source_tracking_list,
            }
        )

        # Export back to GitHub with update_existing to validate no duplication
        with (
            patch("specfact_cli.adapters.github.requests.get") as mock_gh_get,
            patch("specfact_cli.adapters.github.requests.patch") as mock_gh_patch,
        ):
            gh_get_response = MagicMock()
            gh_get_response.json.return_value = {
                "body": github_body_initial,
                "title": title,
                "state": "open",
            }
            gh_get_response.raise_for_status = MagicMock()
            mock_gh_get.return_value = gh_get_response

            gh_patch_response = MagicMock()
            gh_patch_response.json.return_value = {
                "number": 101,
                "html_url": "https://github.com/test-org/test-repo/issues/101",
                "state": "open",
            }
            gh_patch_response.raise_for_status = MagicMock()
            mock_gh_patch.return_value = gh_patch_response

            gh_update_result = sync.export_change_proposals_to_devops(
                adapter_type="github",
                repo_owner="test-org",
                repo_name="test-repo",
                api_token="test-token",
                use_gh_cli=False,
                update_existing=True,
            )

            assert gh_update_result.success is True
            github_body_updated = mock_gh_patch.call_args[1]["json"]["body"]

        assert _normalize_body(github_body_initial) == _normalize_body(github_body_updated)
        assert github_body_updated.count("## Acceptance Criteria") == 1
        assert "Token Storage & Management" in github_body_updated

        proposal_file = repo_path / "openspec" / "changes" / change_id / "proposal.md"
        proposal_content = proposal_file.read_text(encoding="utf-8")
        assert proposal_content.count("## Acceptance Criteria") == 1
        assert "## Source Tracking" in proposal_content
        assert proposal_content.count("- **GitHub Issue**:") == 1
        assert proposal_content.count("- **ADO Issue**:") == 1
