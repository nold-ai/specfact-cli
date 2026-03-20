from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from beartype import beartype

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.sync.bridge_sync import BridgeSync
from specfact_cli.utils.bundle_loader import save_project_bundle


def _create_sample_bundle(base_path: Path, bundle_name: str = "demo-bundle") -> Path:
    projects_dir = base_path / ".specfact" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    bundle_dir = projects_dir / bundle_name
    manifest = BundleManifest(schema_metadata=None, project_metadata=None)
    bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=Product(themes=["Testing"]))
    save_project_bundle(bundle, bundle_dir, atomic=True)
    return bundle_dir


class TestBridgeSyncImport:
    @beartype
    def test_import_selected_ado_backlog_item_uses_native_payload_for_import(self, tmp_path: Path) -> None:
        _create_sample_bundle(tmp_path)
        sync = BridgeSync(tmp_path, bridge_config=BridgeConfig.preset_openspec())
        adapter = AdoAdapter(org="test-org", project="test-project", api_token="test-token")

        work_item_payload = {
            "id": 123,
            "fields": {
                "System.Title": "Add Feature X",
                "System.Description": "## Why\n\nNeeded\n\n## What Changes\n\nImplement",
                "System.State": "New",
                "System.CreatedDate": "2025-01-01T10:00:00Z",
                "System.WorkItemType": "User Story",
            },
            "_links": {
                "html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/123"},
            },
        }
        mock_response = MagicMock()
        mock_response.json.return_value = work_item_payload
        mock_response.raise_for_status = MagicMock()

        with (
            patch.object(adapter, "_ado_get", return_value=mock_response),
            patch.object(adapter, "generate_bridge_config", return_value=BridgeConfig.preset_ado()),
            patch.object(adapter, "_get_work_item_comments", return_value=[]),
            patch("specfact_cli.sync.bridge_sync.AdapterRegistry.get_adapter", return_value=adapter),
            patch.object(sync, "_write_openspec_change_from_proposal", return_value=[]),
        ):
            result = sync.import_backlog_items_to_bundle(
                adapter_type="ado",
                bundle_name="demo-bundle",
                backlog_items=["123"],
            )

        assert result.success is True
        assert result.errors == []
        assert len(result.operations) == 1
