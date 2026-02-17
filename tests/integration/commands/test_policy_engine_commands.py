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

    def test_policy_validate_requires_snapshot_input(self, tmp_path: Path) -> None:
        """Validate SHALL fail when snapshot input is omitted."""
        _write_policy_config(tmp_path)

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
        assert "snapshot path is required" in result.stdout.lower()

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
