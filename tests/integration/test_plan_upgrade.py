"""
Integration tests for plan bundle upgrade command.
"""

import yaml
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.utils.yaml_utils import load_yaml


runner = CliRunner()


class TestPlanUpgrade:
    """Integration tests for plan upgrade command."""

    def test_upgrade_active_plan_dry_run(self, tmp_path, monkeypatch):
        """Test upgrading active plan in dry-run mode."""
        monkeypatch.chdir(tmp_path)

        # Create .specfact structure
        plans_dir = tmp_path / ".specfact" / "plans"
        plans_dir.mkdir(parents=True)

        # Create a plan bundle with old schema (1.0, no summary)
        plan_path = plans_dir / "test.bundle.yaml"
        plan_data = {
            "version": "1.0",
            "product": {"themes": ["Theme1"]},
            "features": [{"key": "FEATURE-001", "title": "Feature 1"}],
        }
        with plan_path.open("w") as f:
            yaml.dump(plan_data, f)

        # Set as active plan
        config_path = plans_dir / "config.yaml"
        with config_path.open("w") as f:
            yaml.dump({"active_plan": "test.bundle.yaml"}, f)

        # Run upgrade in dry-run mode
        result = runner.invoke(app, ["plan", "upgrade", "--dry-run"])

        assert result.exit_code == 0
        assert "Would upgrade" in result.stdout or "upgrade" in result.stdout.lower()
        assert "dry run" in result.stdout.lower()

        # Verify plan wasn't changed (dry run)
        plan_data_after = load_yaml(plan_path)
        assert plan_data_after.get("version") == "1.0"

    def test_upgrade_active_plan_actual(self, tmp_path, monkeypatch):
        """Test actually upgrading active plan."""
        monkeypatch.chdir(tmp_path)

        # Create .specfact structure
        plans_dir = tmp_path / ".specfact" / "plans"
        plans_dir.mkdir(parents=True)

        # Create a plan bundle with old schema (1.0, no summary)
        plan_path = plans_dir / "test.bundle.yaml"
        plan_data = {
            "version": "1.0",
            "product": {"themes": ["Theme1"]},
            "features": [{"key": "FEATURE-001", "title": "Feature 1"}],
        }
        with plan_path.open("w") as f:
            yaml.dump(plan_data, f)

        # Set as active plan
        config_path = plans_dir / "config.yaml"
        with config_path.open("w") as f:
            yaml.dump({"active_plan": "test.bundle.yaml"}, f)

        # Run upgrade
        result = runner.invoke(app, ["plan", "upgrade"])

        assert result.exit_code == 0
        assert "Upgraded" in result.stdout or "upgrade" in result.stdout.lower()

        # Verify plan was updated
        plan_data_after = load_yaml(plan_path)
        assert plan_data_after.get("version") == "1.1"
        assert "summary" in plan_data_after.get("metadata", {})

    def test_upgrade_specific_plan(self, tmp_path, monkeypatch):
        """Test upgrading a specific plan by path."""
        monkeypatch.chdir(tmp_path)

        # Create a plan bundle with old schema
        plan_path = tmp_path / "test.bundle.yaml"
        plan_data = {
            "version": "1.0",
            "product": {"themes": ["Theme1"]},
            "features": [],
        }
        with plan_path.open("w") as f:
            yaml.dump(plan_data, f)

        # Run upgrade on specific plan
        result = runner.invoke(app, ["plan", "upgrade", "--plan", str(plan_path)])

        assert result.exit_code == 0

        # Verify plan was updated
        plan_data_after = load_yaml(plan_path)
        assert plan_data_after.get("version") == "1.1"

    def test_upgrade_all_plans(self, tmp_path, monkeypatch):
        """Test upgrading all plans."""
        monkeypatch.chdir(tmp_path)

        # Create .specfact structure
        plans_dir = tmp_path / ".specfact" / "plans"
        plans_dir.mkdir(parents=True)

        # Create multiple plan bundles with old schema
        for i in range(3):
            plan_path = plans_dir / f"plan{i}.bundle.yaml"
            plan_data = {
                "version": "1.0",
                "product": {"themes": [f"Theme{i}"]},
                "features": [],
            }
            with plan_path.open("w") as f:
                yaml.dump(plan_data, f)

        # Run upgrade on all plans
        result = runner.invoke(app, ["plan", "upgrade", "--all"])

        assert result.exit_code == 0
        assert "3" in result.stdout or "upgraded" in result.stdout.lower()

        # Verify all plans were updated
        for i in range(3):
            plan_path = plans_dir / f"plan{i}.bundle.yaml"
            plan_data_after = load_yaml(plan_path)
            assert plan_data_after.get("version") == "1.1"

    def test_upgrade_already_up_to_date(self, tmp_path, monkeypatch):
        """Test upgrading a plan that's already up to date."""
        monkeypatch.chdir(tmp_path)

        # Create .specfact structure
        plans_dir = tmp_path / ".specfact" / "plans"
        plans_dir.mkdir(parents=True)

        # Create a plan bundle with current schema (1.1, with summary)
        from specfact_cli.generators.plan_generator import PlanGenerator
        from specfact_cli.models.plan import PlanBundle, Product

        product = Product(themes=["Theme1"])
        bundle = PlanBundle(
            version="1.1",
            product=product,
            features=[],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )
        bundle.update_summary(include_hash=True)

        plan_path = plans_dir / "test.bundle.yaml"
        generator = PlanGenerator()
        generator.generate(bundle, plan_path, update_summary=True)

        # Set as active plan
        config_path = plans_dir / "config.yaml"
        with config_path.open("w") as f:
            yaml.dump({"active_plan": "test.bundle.yaml"}, f)

        # Run upgrade
        result = runner.invoke(app, ["plan", "upgrade"])

        assert result.exit_code == 0
        assert "up to date" in result.stdout.lower() or "Up to date" in result.stdout
