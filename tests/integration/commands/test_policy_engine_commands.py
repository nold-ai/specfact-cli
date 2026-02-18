"""Integration tests for policy-engine module commands."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


def _write_policy_config(repo_path: Path) -> None:
    config_dir = repo_path / ".specfact"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "policy.yaml").write_text(
        """
scrum:
  dor_required_fields: [acceptance_criteria]
  dod_required_fields: [definition_of_done]
kanban:
  columns:
    In Progress:
      exit_required_fields: [qa_status]
safe:
  pi_readiness_required_fields: [risk_owner]
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_scrum_only_policy_config(repo_path: Path) -> None:
    config_dir = repo_path / ".specfact"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "policy.yaml").write_text(
        """
scrum:
  dor_required_fields: [acceptance_criteria, business_value]
  dod_required_fields: [definition_of_done]
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_snapshot(repo_path: Path) -> Path:
    snapshot_path = repo_path / "snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "ITEM-1",
                        "title": "Missing policy fields",
                        "column": "In Progress",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return snapshot_path


def _write_multi_item_snapshot(repo_path: Path) -> Path:
    snapshot_path = repo_path / "snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "ITEM-1",
                        "title": "Missing all policy fields",
                        "column": "In Progress",
                    },
                    {
                        "id": "ITEM-2",
                        "title": "Missing some policy fields",
                        "column": "In Progress",
                        "acceptance_criteria": "Present",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    return snapshot_path


def _write_baseline_snapshot(repo_path: Path) -> Path:
    baseline_path = repo_path / ".specfact" / "backlog-baseline.json"
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(
        json.dumps(
            {
                "items": {
                    "ITEM-1": {
                        "id": "ITEM-1",
                        "title": "Missing policy fields",
                        "column": "In Progress",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return baseline_path


def _write_baseline_snapshot_with_alias_fields(repo_path: Path) -> Path:
    baseline_path = repo_path / ".specfact" / "backlog-baseline.json"
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(
        json.dumps(
            {
                "items": {
                    "ITEM-1": {
                        "id": "ITEM-1",
                        "title": "Policy-complete item via alias mapping",
                        "description": """
## Acceptance Criteria
- API supports idempotent retries

## Definition of Done
- Tests updated
""".strip(),
                        "raw_data": {
                            "Microsoft.VSTS.Common.BusinessValue": 13,
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return baseline_path


def _write_plan_artifact(repo_path: Path) -> Path:
    plan_path = repo_path / ".specfact" / "plans" / "backlog-20260218-000000.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        """
bundle_name: backlog-sync-20260218-000000
backlog_graph:
  items:
    ITEM-1:
      id: ITEM-1
      title: Missing policy fields
      column: In Progress
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return plan_path


class TestPolicyEngineCommands:
    """Tests for `specfact policy validate` and `specfact policy suggest`."""

    def test_policy_validate_reports_required_result_fields_in_json_and_markdown(self, tmp_path: Path) -> None:
        """Validate SHALL emit deterministic failures with required fields in both outputs."""
        _write_policy_config(tmp_path)
        snapshot_path = _write_snapshot(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "validate",
                "--repo",
                str(tmp_path),
                "--snapshot",
                str(snapshot_path),
                "--format",
                "both",
            ],
        )

        assert result.exit_code == 1
        stdout = result.stdout
        assert "# Policy Validation Results" in stdout
        assert '"rule_id"' in stdout
        assert '"severity"' in stdout
        assert '"evidence_pointer"' in stdout
        assert '"recommended_action"' in stdout

    def test_policy_validate_reports_missing_config_clearly(self, tmp_path: Path) -> None:
        """Validate SHALL report missing .specfact/policy.yaml without crashing."""
        snapshot_path = _write_snapshot(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "validate",
                "--repo",
                str(tmp_path),
                "--snapshot",
                str(snapshot_path),
            ],
        )

        assert result.exit_code == 1
        assert "policy config not found" in result.stdout.lower()
        assert "not found" in result.stdout.lower()
        assert "agile-scrum-workflows.md" in result.stdout

    def test_policy_init_writes_selected_template_non_interactive(self, tmp_path: Path) -> None:
        """Init SHALL scaffold policy config from selected template in non-interactive mode."""
        result = runner.invoke(
            app,
            [
                "policy",
                "init",
                "--repo",
                str(tmp_path),
                "--template",
                "scrum",
            ],
        )
        assert result.exit_code == 0
        config_path = tmp_path / ".specfact" / "policy.yaml"
        assert config_path.exists()
        content = config_path.read_text(encoding="utf-8")
        assert "scrum:" in content

    def test_policy_init_prompts_for_template_interactive(self, tmp_path: Path) -> None:
        """Init SHALL ask for template selection when template is omitted."""
        result = runner.invoke(
            app,
            [
                "policy",
                "init",
                "--repo",
                str(tmp_path),
            ],
            input="kanban\n",
        )
        assert result.exit_code == 0
        config_path = tmp_path / ".specfact" / "policy.yaml"
        assert config_path.exists()
        content = config_path.read_text(encoding="utf-8")
        assert "kanban:" in content

    def test_policy_validate_autodiscovers_baseline_snapshot_when_snapshot_omitted(self, tmp_path: Path) -> None:
        """Validate SHALL use .specfact/backlog-baseline.json when snapshot arg is omitted."""
        _write_policy_config(tmp_path)
        _write_baseline_snapshot(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "validate",
                "--repo",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 1
        stdout = result.stdout
        assert '"rule_id"' in stdout
        assert '"evidence_pointer"' in stdout

    def test_policy_validate_autodiscovers_latest_plan_when_baseline_missing(self, tmp_path: Path) -> None:
        """Validate SHALL fallback to latest .specfact/plans/backlog-* artifact."""
        _write_policy_config(tmp_path)
        _write_plan_artifact(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "validate",
                "--repo",
                str(tmp_path),
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 1
        stdout = result.stdout
        assert '"rule_id"' in stdout
        assert '"recommended_action"' in stdout

    def test_policy_suggest_is_confidence_scored_and_does_not_write(self, tmp_path: Path) -> None:
        """Suggest SHALL provide confidence-scored patch-ready suggestions and avoid auto writes."""
        _write_policy_config(tmp_path)
        snapshot_path = _write_snapshot(tmp_path)
        before = snapshot_path.read_text(encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "policy",
                "suggest",
                "--repo",
                str(tmp_path),
                "--snapshot",
                str(snapshot_path),
            ],
        )

        assert result.exit_code == 0
        stdout = result.stdout.lower()
        assert "confidence" in stdout
        assert "patch" in stdout
        assert "no changes were written" in stdout
        after = snapshot_path.read_text(encoding="utf-8")
        assert after == before

    def test_policy_suggest_autodiscovers_baseline_snapshot_when_snapshot_omitted(self, tmp_path: Path) -> None:
        """Suggest SHALL use .specfact artifacts when snapshot arg is omitted."""
        _write_policy_config(tmp_path)
        _write_baseline_snapshot(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "suggest",
                "--repo",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        stdout = result.stdout.lower()
        assert "confidence" in stdout
        assert "patch" in stdout

    def test_policy_validate_maps_alias_and_description_fields_from_baseline(self, tmp_path: Path) -> None:
        """Validate SHALL map imported alias/description fields into canonical policy fields."""
        _write_scrum_only_policy_config(tmp_path)
        _write_baseline_snapshot_with_alias_fields(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "validate",
                "--repo",
                str(tmp_path),
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        stdout = result.stdout
        assert '"status": "passed"' in stdout
        assert '"total_findings": 0' in stdout

    def test_policy_validate_supports_rule_filter_and_limit(self, tmp_path: Path) -> None:
        """Validate SHALL support --rule filtering and --limit truncation."""
        _write_policy_config(tmp_path)
        snapshot_path = _write_snapshot(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "validate",
                "--repo",
                str(tmp_path),
                "--snapshot",
                str(snapshot_path),
                "--format",
                "json",
                "--rule",
                "scrum.dor.acceptance_criteria",
                "--limit",
                "1",
            ],
        )

        assert result.exit_code == 1
        stdout = result.stdout
        assert '"total_findings": 1' in stdout
        assert '"rule_id": "scrum.dor.acceptance_criteria"' in stdout
        assert '"rule_id": "scrum.dod.definition_of_done"' not in stdout

    def test_policy_validate_supports_group_by_item_output(self, tmp_path: Path) -> None:
        """Validate SHALL emit grouped payload when --group-by-item is set."""
        _write_policy_config(tmp_path)
        snapshot_path = _write_snapshot(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "validate",
                "--repo",
                str(tmp_path),
                "--snapshot",
                str(snapshot_path),
                "--format",
                "json",
                "--group-by-item",
            ],
        )

        assert result.exit_code == 1
        stdout = result.stdout
        assert '"groups"' in stdout
        assert '"item_index": 0' in stdout
        assert '\n  "failures": [' not in stdout

    def test_policy_suggest_supports_rule_filter_limit_and_grouping(self, tmp_path: Path) -> None:
        """Suggest SHALL support --rule, --limit, and --group-by-item output."""
        _write_policy_config(tmp_path)
        snapshot_path = _write_snapshot(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "suggest",
                "--repo",
                str(tmp_path),
                "--snapshot",
                str(snapshot_path),
                "--rule",
                "scrum.dor.acceptance_criteria",
                "--limit",
                "1",
                "--group-by-item",
            ],
        )

        assert result.exit_code == 0
        stdout = result.stdout
        assert '"suggestion_count": 1' in stdout
        assert '"grouped_suggestions"' in stdout
        assert '"rule_id": "scrum.dor.acceptance_criteria"' in stdout
        assert '"rule_id": "scrum.dod.definition_of_done"' not in stdout
        assert '\n  "suggestions": [' not in stdout

    def test_policy_validate_grouped_limit_applies_to_item_count(self, tmp_path: Path) -> None:
        """Grouped validate SHALL apply --limit to item groups, not individual findings."""
        _write_scrum_only_policy_config(tmp_path)
        snapshot_path = _write_multi_item_snapshot(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "validate",
                "--repo",
                str(tmp_path),
                "--snapshot",
                str(snapshot_path),
                "--format",
                "json",
                "--group-by-item",
                "--limit",
                "1",
            ],
        )

        assert result.exit_code == 1
        stdout = result.stdout
        assert '"item_index": 0' in stdout
        assert '"item_index": 1' not in stdout
        assert '"total_findings": 3' in stdout

    def test_policy_suggest_grouped_limit_applies_to_item_count(self, tmp_path: Path) -> None:
        """Grouped suggest SHALL apply --limit to item groups, not individual suggestions."""
        _write_scrum_only_policy_config(tmp_path)
        snapshot_path = _write_multi_item_snapshot(tmp_path)

        result = runner.invoke(
            app,
            [
                "policy",
                "suggest",
                "--repo",
                str(tmp_path),
                "--snapshot",
                str(snapshot_path),
                "--group-by-item",
                "--limit",
                "1",
            ],
        )

        assert result.exit_code == 0
        stdout = result.stdout
        assert '"item_index": 0' in stdout
        assert '"item_index": 1' not in stdout
        assert '"suggestion_count": 3' in stdout

    def test_policy_validate_resolves_relative_snapshot_against_repo(self, tmp_path: Path, monkeypatch) -> None:
        """Explicit relative --snapshot path SHALL resolve relative to --repo."""
        _write_scrum_only_policy_config(tmp_path)
        _write_snapshot(tmp_path)
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.chdir(outside_dir)

        result = runner.invoke(
            app,
            [
                "policy",
                "validate",
                "--repo",
                str(tmp_path),
                "--snapshot",
                "snapshot.json",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 1
        stdout = result.stdout
        assert "Snapshot file not found" not in stdout
        assert '"total_findings": 3' in stdout
